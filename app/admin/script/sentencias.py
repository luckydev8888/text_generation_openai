from flask import jsonify
from bson import ObjectId
from app.mongo import get_db
import json
from bs4 import BeautifulSoup
import re
import requests

sentencias_fields = ['providencia', 'ano', 'fecha sentencia', 'fecha publicada', 'expediente', 'url']

collenctionName = 'sentencias'

def get_sentencias(keyword, start, length, sortColumn, dir):
    db = get_db()
    collection = db[collenctionName]

    recordsTotal = collection.count_documents({})

    pipeline = []
    recordsFiltered = 0
    match_keyword = ''
    if keyword != '':
        for field in sentencias_fields:
            match_keyword = match_keyword + '{"' + field + '": {"$regex": "' + keyword + '","$options": "i"}},'
        match_keyword = match_keyword[:-1]
        or_string = '{"$or":[' + match_keyword + ']}'
        recordsFiltered = collection.count_documents(json.loads(or_string))
        match_string = '{"$match":{"$or":[' + match_keyword + ']}}'
        pipeline.append(json.loads(match_string))
    else:
        recordsFiltered = recordsTotal
    sort_string = '{"$sort": {"' + sentencias_fields[sortColumn-1] + '":'  + str(1 if dir == 'asc' else -1) + '}}'
    pipeline.append(json.loads(sort_string))



    skip_string = '{"$skip": ' + str(start) + '}'
    pipeline.append(json.loads(skip_string))
    length_string =  '{"$limit": ' + str(length) + '}'
    pipeline.append(json.loads(length_string))

    project_string = '"_id":1,'
    for field in sentencias_fields:
        project_string = project_string + '"' + field + '": 1,'
    project_string = project_string[:-1]
    project_string = '{"$project":{' + project_string + '}}'
    pipeline.append(json.loads(project_string))

    filter_list = list(collection.aggregate(pipeline))
                
    if recordsFiltered != 0:
        return_data = []
        number = 0
        for each in filter_list:
            number += 1
            return_data.append({
                'order': number,
                '_id': str(each['_id']),
                'providencia': str(each['providencia']),
                'ano': str(each['ano']),
                'fecha_sentencia': str(each['fecha sentencia']),
                'fecha_publicada': str(each['fecha publicada']),
                'expediente': str(each['expediente']),
                'url': str(each['url']),
            })
        response_data = {
            "recordsTotal": recordsTotal,
            "recordsFiltered": recordsFiltered,
            "data": return_data
        }
        return response_data
    else:
        response_data = {
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": []
        }
        return response_data
    
def get_sentencia(id):
    db = get_db()
    collection = db[collenctionName]
    get_data = collection.find_one({"_id": ObjectId(id)})
    
    response_data = {
        "_id": str(get_data['_id']),
        "providencia": str(get_data["providencia"]),
        "tipo": str(get_data["tipo"]),
        "ano": str(get_data["ano"]),
        "fecha_sentencia": str(get_data["fecha sentencia"]),
        "tema": str(get_data["tema"]),
        "magistrado": str(get_data["magistrado"]),
        "fecha_publicada": str(get_data["fecha publicada"]),
        "expediente":str(get_data["expediente"]),
        "url": str(get_data["url"]),
        "texto": str(get_data["texto"])
    }
    return response_data, 200
    

def save_sentencias(save_data):
    db = get_db()
    collection = db[collenctionName]
    id = save_data["id"]
    if id == '':
        try:
            collection.insert_one({
                "providencia": save_data["providencia"],
                "tipo": save_data["tipo"],
                "ano": save_data["ano"],
                "fecha sentencia":save_data["fecha_sentencia"],
                "tema":save_data["tema"],
                "magistrado":save_data["magistrado"],
                "fecha publicada": save_data["fecha_publicada"],
                "expediente":save_data["expediente"],
                "url": save_data["url"],
                "texto": save_data["texto"]
            })
            return jsonify({'message': 'Successfully added'}), 200
        except:
            return jsonify({'message': 'Error occur'}), 500
    else:
        try:
            query_filter = {'_id' : ObjectId(id)}
            update_operation = { '$set' : 
                {
                    "providencia": save_data["providencia"],
                    "tipo": save_data["tipo"],
                    "ano": save_data["ano"],
                    "fecha sentencia":save_data["fecha_sentencia"],
                    "tema":save_data["tema"],
                    "magistrado":save_data["magistrado"],
                    "fecha publicada": save_data["fecha_publicada"],
                    "expediente":save_data["expediente"],
                    "url": save_data["url"],
                    "texto": save_data["texto"]
                }
            }
            collection.update_one(query_filter, update_operation)
            return jsonify({'message': 'Successfully added'}), 200
        except:
            return jsonify({'message': 'Error occur'}), 500


def update_sentencias(id, type, number, texto, tutela):
    db = get_db()
    collection = db[collenctionName]
    try:
        query_filter = {'_id' : ObjectId(id)}
        update_operation = { '$set' : 
            { 
                'articulo': type,
                'num': int(number),
                'texto': texto,
                'tutela': tutela
            }
        }
        collection.update_one(query_filter, update_operation)
        return jsonify({'message': 'Successfully update'}), 200
    except :
        return jsonify({'message': 'Error occur'}), 500

def delete_sentencias(id):
    db = get_db()
    collection = db[collenctionName]
    try:
        query_filter = {'_id' : ObjectId(id)}
        collection.delete_many(query_filter)
        return jsonify({'message': 'Successfully deleted'}), 200
    except :
        return jsonify({'message': 'Error occur'}), 500
    
def texto_scrap(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        section_div = soup.find('div', class_='Section1')
        
        if not section_div:
            section_div = soup.find('div', class_='WordSection1')
        if section_div:
            cleaned_content = ""
            p_tags = section_div.findAll('p')
            for p in p_tags:
                txt = p.get_text(separator=' ', strip=True)
                cleaned_text = re.sub(r'\s+', ' ', txt)
                cleaned_content = f'{cleaned_content}{cleaned_text}\n'
            return jsonify({"texto" : cleaned_content}), 200
        else:
            return jsonify({"message" : "Scarping failed"}), 404
    else:
        return jsonify({"message" : "Scarping failed"}), 404