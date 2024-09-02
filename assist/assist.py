from pymongo import MongoClient
import os
import csv
import re
from bs4 import BeautifulSoup
import requests
import json
from flask_bcrypt import Bcrypt
from flask import Flask
import PyPDF2
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

OPENAI_KEY = os.getenv("OPENAI_KEY")
client2 = OpenAI(api_key=OPENAI_KEY)

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

# list = ['T-243-24', 'T-245-24', 'T-232-24', 'A-1043-24', 'A-979-24', 'T-248-24', 'T-244-24', 'T-216-24']

#find_setencia_list(list)

# app = Flask(__name__)
# bcrypt = Bcrypt(app)

# def make_hash():
#     pw_hash = bcrypt.generate_password_hash('123456').decode('utf-8')
#     print(pw_hash)
# make_hash()


# file_list = client2.files.list().data
# print(file_list)


def generate_evidence_checklist():
    text = '''
Visto que no se encontraron resultados de búsqueda coincidentes, enumero a continuación las evidencias necesarias basándome en el contenido del documento proporcionado:

```json
[
    {
        "descripcion": "Compra del bien inmueble ubicado en la Calle 54c sur #88I71 – Bosa (Bogotá-Colombia) el día 29 de abril de 2023",
        "evidencias": [
            {
                "tipo": "documento",
                "descripcion": "Copia de la cédula de ciudadanía del propietario del inmueble, Danilo Quevedo Vaca",
                "archivo": "cedula_danilo_quevedo.pdf"
            },
            {
                "tipo": "documento",
                "descripcion": "Documento de compra-venta del inmueble",
                "archivo": "compra_venta_inmueble.pdf"
            }
        ]
    },
    {
        "descripcion": "Elección del Sr. QUEVEDO VACA como parte del consejo de administración en el año 2017",
        "evidencias": [
            {
                "tipo": "documento",
                "descripcion": "Acta de la elección del consejo de administración",
                "archivo": "acta_eleccion_consejo_2017.pdf"
            }
        ]
    },
    {
        "descripcion": "Presentación de derecho de petición ante la administración del Conjunto Residencial Tangara Etapa 2 el 29 de abril de 2023",
        "evidencias": [
            {
                "tipo": "documento",
                "descripcion": "Copia del derecho de petición presentado ante la Administración del Conjunto Residencial Tangara Etapa 2",
                "archivo": "derecho_peticion_29042023.pdf"
            },
            {
                "tipo": "documento",
                "descripcion": "Sello de recibido confirmando la recepción del derecho de petición",
                "archivo": "sello_recibido_derecho_peticion.pdf"
            }
        ]
    },
    {
        "descripcion": "Fallos judiciales y otros actos administrativos relacionados",
        "evidencias": [
            {
                "tipo": "documento",
                "descripcion": "Sentencia de tutela a favor del solicitante",
                "archivo": "sentencia_tutela.pdf"
            },
            {
                "tipo": "documento",
                "descripcion": "Comunicaciones con la administración del conjunto residencial sobre el seguimiento de la tutela",
                "archivo": "comunicaciones_administracion.pdf"
            }
        ]
    },
    {
        "descripcion": "Visita de la Secretaría Distrital de Salud para la verificación de las instalaciones",
        "evidencias": [
            {
                "tipo": "documento",
                "descripcion": "Informe de la visita realizada por la Secretaría Distrital de Salud",
                "archivo": "informe_visita_salud.pdf"
            }
        ]
    }
]
```

Por favor, revisa el documento original o suministra los archivos mencionados para proporcionar una evaluación más precisa.
'''

    match = re.search(r'```json(.*?)```', text, re.DOTALL)
    if match:
        json_text = match.group(1).strip()
    else:
        print("No JSON block found.")
        return
    json_object = json.loads(json_text)
    
    return json_object

def make_fine_tuning_train_data():
    folder_path = '../'
    cnt = 0
    with open('output.jsonl', 'w') as f:
        for filename in os.listdir(folder_path):
            print(filename)
            if filename.endswith('.pdf'):
                if 'respuesta' in filename:
                    continue
                pdf_path1 = os.path.join(folder_path, filename)
                name, extension = filename.rsplit('.', 1)
                new_filename = f"{name}_respuesta.{extension}"
                pdf_path2 = os.path.join(folder_path, new_filename)
                try:
                    pdf_content1 = ''
                    pdf_content2 = ''
                    with open(pdf_path1, 'rb') as pdf_file:
                        reader = PyPDF2.PdfReader(pdf_file)
                        for page_num in range(len(reader.pages)):
                            page = reader.pages[page_num]
                            pdf_content1 = f'{pdf_content1}{page.extract_text()}'
                    
                    with open(pdf_path2, 'rb') as pdf_file:
                        reader = PyPDF2.PdfReader(pdf_file)
                        for page_num in range(len(reader.pages)):
                            page = reader.pages[page_num]
                            pdf_content2 = f'{pdf_content2}{page.extract_text()}'
                    cnt += 1
                    item = {"messages": [{"role": "system", "content": "Eres asistente de un abogado."}, {"role": "user", "content": f"Nuevo documento:\'{pdf_content1}\' Con base en el nuevo documento, la lista de revisiones judiciales relevantes (cuyo contenido está disponible en la tienda de vectores) y las disposiciones constitucionales proporcionadas, redacte una sentencia para el nuevo documento."}, {"role": "assistant", "content": pdf_content2}]}
                    f.write(json.dumps(item) + '\n')
                except Exception as e:
                    print(e)
        with open('output-test.jsonl', 'r', encoding='utf-8') as fi:
            for line in fi:
                json_object = json.loads(line.strip())
                f.write(json.dumps(json_object) + '\n')
                cnt += 1
                if cnt >= 10: break
            
    return

# make_fine_tuning_train_data()
def fine_tuning_upload():
    client2.files.delete("file-Og2S0kOgbIXHzVUIBpJV4AtU")
    message = client2.files.list()
    print(message.data)
    file_path = 'formato_respuesta_textanalizer.docx'
    message_file = client2.files.create(
        file=open(file_path, "rb"), purpose="assistants"
    )

    print(message_file.id)

    message = client2.fine_tuning.jobs.create(
      training_file=message_file.id,
      model="gpt-4o-mini-2024-07-18"
    )

    message = client2.fine_tuning.jobs.list()
    print(message.data)

import smtplib
def send_email_via_smtp(email, message):
    
    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)
    # start TLS for security
    s.starttls()
    # Authentication
    # s.login("mailer@theastralabs.com", "oxgvjlpoxhpzfvoq")
    
    MESSAGE_SENDER = str(os.getenv('MESSAGE_SENDER'))
    MESSAGE_SENDER_APP_PASSWORD = str(os.getenv('MESSAGE_SENDER_APP_PASSWORD'))
    print(email, message, MESSAGE_SENDER, MESSAGE_SENDER_APP_PASSWORD)
    s.login(MESSAGE_SENDER, MESSAGE_SENDER_APP_PASSWORD)
    # message to be sent
    # message = "Message_you_need_to_send 1"
    # sending the mail
    s.sendmail("mailer@theastralabs.com", email, message)
    # terminating the session
    s.quit()
# send_email()

def send_email_via_smtp(email, message):
    import smtplib
    import os
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    MESSAGE_SENDER = str(os.getenv('MESSAGE_SENDER'))
    MESSAGE_SENDER_APP_PASSWORD = str(os.getenv('MESSAGE_SENDER_APP_PASSWORD'))
    msg = MIMEMultipart()
    msg['From'] = MESSAGE_SENDER
    msg['To'] = email
    msg['Subject'] = "Verify your email"
    
    # Attach the message body (it could be plain text or HTML)
    msg.attach(MIMEText(message, 'HTML')) 

    try:
        s.login(MESSAGE_SENDER, MESSAGE_SENDER_APP_PASSWORD)
        s.sendmail(MESSAGE_SENDER, email, msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        s.quit()
    return


def send_email_with_other_way(email):
    import smtplib
    import ssl
    from email.message import EmailMessage

    MESSAGE_SENDER = str(os.getenv('MESSAGE_SENDER'))
    MESSAGE_SENDER_APP_PASSWORD = str(os.getenv('MESSAGE_SENDER_APP_PASSWORD'))

    sender_email = MESSAGE_SENDER
    receiver_email = email
    password = MESSAGE_SENDER_APP_PASSWORD

    em = EmailMessage()
    em['From'] = MESSAGE_SENDER
    em['To'] = receiver_email
    em["Subject"] = "multipart test"

    # Create the plain-text and HTML version of your message
    text = """\
    Hi,
    How are you?
    Real Python has many great tutorials:
    www.realpython.com"""
    html = """\
    <html>
    <body>
        <p>Hi,<br>
        How are you?<br>
        <a href="http://www.realpython.com">Real Python</a> 
        has many great tutorials.
        </p>
    </body>
    </html>
    """

    em.set_content(html)

    context = ssl.create_default_context()
    
    print(sender_email, password)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, em.as_string()
        )
    return

email = "crystaldev1003@gmail.com"
message = """
    <div><p>Welcome Tutela</p>
    Click <a href='http://localhost:5000/confirm_email/ImNyeXN0YWxkZXYxMDAzQGdtYWlsLmNvbSI.ZtRzgg.cCKm8J38B7L3uCTXhSH7vFLskgs'>here</a> for verify
    </div>
    """
send_email_via_smtp(email, message)
# send_email_with_other_way(email)