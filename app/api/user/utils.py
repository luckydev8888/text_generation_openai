import csv
from bs4 import BeautifulSoup
from docx import Document
import re
import PyPDF2
import json
from datetime import datetime
from app.mongo import get_db


def get_pdf_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def clean_text(str):
    cite_pattern = r'【\d+†source】|【\d+:\d+†source】|【\d+:\d+†fuente】|【.*?】'
    return re.sub(cite_pattern, '', str)


def find_setencia_list(list):
    db = get_db()
    collection = db['sentencias']

    json_data = []
    for item in list:
        doc = collection.find_one({"providencia": item})
        if doc :
            json_data.append({
                'providencia': doc['providencia'],
                'tipo': doc['tipo'],
                'ano': doc['ano'],
                'fecha_sentencia': doc['fecha_sentencia'],
                'tema': doc['tema'],
                'magistrado': doc['magistrado'],
                'fecha_publicada': doc['fecha_publicada'],
                'expediente': doc['expediente'],
                'url': doc['url'],
            })
    return json_data


def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def create_docx_from_html(html_content, filename):
    text_content = html_to_text(html_content)
    
    doc = Document()
    
    doc.add_paragraph(text_content)
    
    doc.save(filename)

def get_constitution(str):
    pattern = r"Artículo (?P<number>\d+)"  # Named group to capture the number
    matches = re.findall(pattern, str)
    print("Found:", matches)

    return matches

def proccess_code(codigo):
    codigo = re.sub(r"[^A-Za-z0-9]", "-", codigo)  # Replace non-alphanumeric characters with hyphens
    codigo = re.sub(r"de-", "-", codigo)          # Remove 'de-' followed by a hyphen
    codigo = re.sub(r"-+", "-", codigo)           # Replace multiple consecutive hyphens with a single hyphen
    codigo = re.sub(r"-(\d{2})(\d{2})$", r"-\2", codigo)  # Convert 4-digit years to 2-digit if necessary
    return codigo

def parse_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d')

def get_sentencia(str, constitution_list):
    str = str.lower()

    pattern = r"(?i)(providencia|jurisprudencia|sentencia)[^a-zA-Z0-9]*([A-Za-z]*-?\d+[a-zA-Z]*[^a-zA-Z0-9]*(?:de[^a-zA-Z0-9]*)?\d{2,4})"

    sentencia = re.findall(pattern, str, re.IGNORECASE)

    sentencia_list = []
    if sentencia:
        for match in sentencia:
            code = proccess_code(match[1])
            sentencia_list.append(code.upper())

    else:
        # constitution_list = [20, 30]
        db = get_db()
        collection = db['sentencias']
        pipeline = [{"$project": {"_id": 1, "providencia": 1, "fecha_sentencia": 1}},
                    {"$sort": {"fecha_sentencia" : -1}},
        ]
        sentencias_list = list(collection.aggregate(pipeline=pipeline))
        for each in constitution_list:
            num = 0
            for item in sentencias_list:
                doc = collection.find_one({"_id": item['_id']})
                if fr"artículo {each}" in doc['texto']:
                    sentencia_list.append(doc['providencia'])
                    num += 1
                if num == 3: break
        sentencia_list = list(set(sentencia_list))
    print(sentencia_list)
    return sentencia_list

def generate_evidence_checklist(text):
    checklist = []
    for line in text.split('\n'):
        if ':' in line:
            evidence, _ = line.split(':', 1)
            checklist.append({
                "value": evidence.strip(),
                "state":  False
                })
    return checklist

def get_history(user, title=''):
    db = get_db()
    collection = db['saves']
    pipeline = []
    if title == '':
        pipeline.append({"$project":{"_id": 1, "user":1, "modifiedAt":1}})
        pipeline.append({"$match":{"user":user}})
        pipeline.append({"$sort":{"modifiedAt":-1}})
        pipeline.append({"$limit":1})
    else:
        pipeline.append({"$project":{"_id": 1, "user":1, "modifiedAt":1, "title":1}})
        pipeline.append({"$match":{"user":user, "title": title}})
    find_data = list(collection.aggregate(pipeline=pipeline))
    if len(find_data) > 1:
        return "Error"
    elif len(find_data) == 1:
        history = collection.find_one({'_id': find_data[0]['_id']})
        print(history)
        return history
    else:
        return "No data"
    
def get_current_state(user):
    print(user)
    db = get_db()
    collection = db['current_state']
    history = collection.find_one({'user': user})
    if history:
        history.pop('_id', None)
        return history
    else:
        collection.insert_one({"user": user})
        return {"user": user}
    
def update_current_state(user, field, data):
    db = get_db()
    collection = db['current_state']
    query_filter = {"user": user}
    update_date = {}
    update_date[field] = data
    update_operation = {}
    update_operation['$set'] = update_date
    collection.update_one(query_filter, update_operation)

def get_current_data_field(user, field):
    db = get_db()
    collection = db['current_state']
    history = collection.find_one({'user': user})
    if field in history:
        return history[field]
    else:
        return ''
    
def get_settings(field):
    db = get_db()
    collection = db['settings']
    settings = collection.find_one()
    return settings[field]

    
def get_title_list(user):
    db = get_db()
    collection = db['results']
    pipeline = [{'$project':{'title':1, 'user':1}},
                {'$match': {'user':user}}]
    res = list(collection.aggregate(pipeline=pipeline))
    return_data = []
    for each in res:
        return_data.append(each['title'])
    return return_data

def save_tutela(user, title):
    loading_data = get_current_state(user)
    loading_data['title'] = title
    loading_data['modifiedAt'] = datetime.now()
    db = get_db()
    results = db['results']
    currents = db['current_state']
    pipeline = [{'$project':{'_id': 1, 'title':1, 'user':1}},
                {'$match': {'user':user, 'title': title}}]
    res = list(results.aggregate(pipeline=pipeline))
    if len(res) > 0:
        results.delete_one( {'user':user, 'title': title})

    results.insert_one(loading_data)
    currents.delete_one({'user':user})
    currents.insert_one(loading_data)
    return {'message': "sucess"}, 200


def set_tutela(user, title):
    db = get_db()
    results = db['results']
    currents = db['current_state']
    set_data = results.find_one({'user':user, 'title': title})
    
    currents.delete_one({'user':user})
    currents.insert_one(set_data)
    return {'message': "sucess"}, 200
