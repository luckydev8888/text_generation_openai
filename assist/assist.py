from pymongo import MongoClient
import os
import csv
import re
from bs4 import BeautifulSoup
import requests

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
                'fecha sentencia': row['fecha sentencia'],
                'tema': row['tema'],
                'magistrado': row['magistrado'],
                'fecha publicada': row['fecha publicada'],
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
        file_path = f'../{x['providencia']}.txt'
        if os.path.isfile(file_path):
            doc = open(file_path, "r", encoding='utf-8')
            texto = doc.read()
            myquery = { "_id": x['_id'] }
            newvalues = { "$set": { "texto": texto, "uploaded": True} }
            sentencia_collection.update_one(myquery, newvalues)
            print(f'{x['providencia']} success')
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


update_texto()