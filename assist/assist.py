from pymongo import MongoClient
import os
import csv
import re
from bs4 import BeautifulSoup
import requests
import json

client = MongoClient('mongodb://localhost:27017/tutela_db')
db = client.get_default_database()

def constdf_from_csv():
    constdf_json = []

    with open('./assist/Constdf.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item = row['texto']
            text = item.split('.')
            articulo = text[0]
            text = articulo.split(' ')
            num = int(text[-1])
            article = articulo[:-len(text[-1])]
            texto = item[len(articulo)+2:]
            if 'transitorio' in article:
                article = 'Articulo Transitorio'
            else:
                article = 'Articulo'
            constdf_json.append({
                'num': num,
                'articulo': article,
                'texto': texto,
                'tutela': row['tutela']
            })

    print(constdf_json)

    constdf_collection = db['constdf']
    for each in constdf_json:
        constdf_collection.insert_one(each)

def sentencia_from_csv():
    sentencia_json = []

    with open('./assist/SenTencias.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sentencia_json.append({
                'providencia': row['providencia'],
                'tipo': row['tipo'],
                'ano': row['ano'],
                'fecha_sentencia': row['fecha sentencia'],
                'tema': row['tema'],
                'magistrado': row['magistrado'],
                'fecha_publicada': row['fecha publicada'],
                'expediente': row['expediente'],
                'url': row['url'],
                'texto': "",
            })


    sentencia_collection = db['sentencias']
    for each in sentencia_json:
        sentencia_collection.insert_one(each)

def update_texto():
    sentencia_collection = db['sentencias']
    
    for x in sentencia_collection.find():
        if 'uploaded' in x and x['uploaded'] == True:
            continue
        file_path = f'../site_output/{x['providencia']}.txt'
        if os.path.isfile(file_path):
            doc = open(file_path, "r", encoding='utf-8')
            texto = doc.read()
            myquery = { "_id": x['_id'] }
            newvalues = { "$set": { "texto": texto, "uploaded": True} }
            sentencia_collection.update_one(myquery, newvalues)
            # print(f'{x['providencia']} success')
        else:
            myquery = { "_id": x['_id'] }
            newvalues = { "$set": {"uploaded": False} }
            sentencia_collection.update_one(myquery, newvalues)
            print(f'No file: {x['providencia']}')


def get_website(item):
    output_folder = '../'
    url = item['url']
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        section_div = soup.find('div', class_='Section1')
        
        if not section_div:
            section_div = soup.find('div', class_='WordSection1')
        if section_div:
            p_tag = section_div.find('p', string=lambda text: text and "Referencia:" in text)
            
            title = item['providencia'].replace('.', '-').replace('/', '-')
            title = re.sub(r'\s+', '', title)
            
            file_name = os.path.join(output_folder, f'{title}.txt')

            cleaned_content = ""
            p_tags = section_div.findAll('p')
            for p in p_tags:
                txt = p.get_text(separator=' ', strip=True)
                cleaned_text = re.sub(r'\s+', ' ', txt)
                cleaned_content = f'{cleaned_content}{cleaned_text}\n'
            with open(file_name, 'w', encoding='utf-8') as txt_file:
                txt_file.write(cleaned_content)
        else:
            print("No <div> with class 'Section1' found.", url)
            # fail_url_list.append(item)
    else:
        print("Failed to retrieve the page. Status code:", response.status_code, url)
        # fail_url_list.append(item)

    return True

def make_pipeline():
    sentencias_fields = ['providencia', 'ano', 'fecha sentencia', 'fecha publicada', 'expediente', 'url']

    keyword = "T-001"
    sortColumn = 3
    dir = 'asc'
    start = 0
    length = 10
    pipeline = []
    match_keyword = ''
    if keyword != '':
        for field in sentencias_fields:
            match_keyword = match_keyword + '{"' + field + '": {"$regex": "' + keyword + '","$options": "i"}},'
        match_keyword = match_keyword[:-1]
        or_string = '{"$or":[' + match_keyword + ']}'
        recordsFiltered = db['sentencias'].count_documents(json.loads(or_string))
        match_string = '{"$match":{"$or":[' + match_keyword + ']}}'
        pipeline.append(json.loads(match_string))

    sort_string = '{"$sort": {"' + sentencias_fields[sortColumn-1] + '":'  + str(1 if dir == 'asc' else -1) + '}}'
    pipeline.append(json.loads(sort_string))



    skip_string = '{"$skip": ' + str(start) + '}'
    pipeline.append(json.loads(skip_string))
    length_string =  '{"$limit": ' + str(length) + '}'
    pipeline.append(json.loads(length_string))

    project_string = ''
    for field in sentencias_fields:
        project_string = project_string + '"' + field + '": 1,'
    project_string = project_string[:-1]
    project_string = '{"$project":{' + project_string + '}}'
    pipeline.append(json.loads(project_string))

    # print(pipeline)

    filter_list = list(db['sentencias'].aggregate(pipeline))

    recordsTotal = db['sentencias'].count_documents({})

    print(recordsTotal)
    print(recordsFiltered)
# update_texto()

def get_sentencia():
    constitution_list = [20,30,26,35]
    collection = db['sentencias']
    pipeline = [{"$project": {"_id": 1, "providencia": 1, "fecha_sentencia": 1}},
                {"$sort": {"fecha_sentencia" : -1}},
    ]
    sentencia_list = []
    
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

def find_setencia_list(list):
    collection = db['sentencias']

    json_data = []
    for item in list:
        doc = collection.find_one({"providencia": item})
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
    print(json_data)
    return json_data

list = ['T-243-24', 'T-245-24', 'T-232-24', 'A-1043-24', 'A-979-24', 'T-248-24', 'T-244-24', 'T-216-24']

find_setencia_list(list)