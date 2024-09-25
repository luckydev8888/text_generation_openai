import csv
from bs4 import BeautifulSoup
from docx import Document
import re
import PyPDF2
import json
from datetime import datetime
from app.mongo import get_db
from docx.shared import Pt
from docx.oxml.shared import OxmlElement
from docx.oxml.ns import qn
from pymongo import MongoClient
from difflib import SequenceMatcher

# Conectar a la base de datos MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["tutela_db"]
coleccion = db["sentencias"]


def get_pdf_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


def clean_text(str):
    cite_pattern = r"【\d+†source】|【\d+:\d+†source】|【\d+:\d+†fuente】|【.*?】"
    return re.sub(cite_pattern, "", str)


def find_setencia_list(list):
    db = get_db()
    collection = db["sentencias"]

    json_data = []
    for item in list:
        doc = collection.find_one({"providencia": item})
        if doc:
            json_data.append(
                {
                    "providencia": doc["providencia"],
                    "tipo": doc["tipo"],
                    "ano": doc["ano"],
                    "fecha_sentencia": doc["fecha_sentencia"],
                    "tema": doc["tema"],
                    "magistrado": doc["magistrado"],
                    "fecha_publicada": doc["fecha_publicada"],
                    "expediente": doc["expediente"],
                    "url": doc["url"],
                }
            )
    return json_data


def html_to_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()


def add_html_to_docx(soup, doc):
    for element in soup:
        if element == "\n":
            continue
        if element.name == "p":
            paragraph = doc.add_paragraph(element.get_text())
            run = paragraph.runs[0]
            run.font.size = Pt(11.5)
            paragraph_format = paragraph.paragraph_format
            paragraph_format.space_before = Pt(6)  # 0.5 line space before
            paragraph_format.space_after = Pt(6)  # 0.5 line space after
        elif element.name == "h1":
            paragraph = doc.add_heading(level=1)
            run = paragraph.add_run(element.get_text())
            run.font.size = Pt(20)
            paragraph_format = paragraph.paragraph_format
            paragraph_format.space_before = Pt(6)  # 0.5 line space before
            paragraph_format.space_after = Pt(6)  # 0.5 line space after
        elif element.name == "h2":
            paragraph = doc.add_heading(level=2)
            run = paragraph.add_run(element.get_text())
            run.font.size = Pt(16)
            paragraph_format = paragraph.paragraph_format
            paragraph_format.space_before = Pt(6)  # 0.5 line space before
            paragraph_format.space_after = Pt(6)  # 0.5 line space after
        elif element.name == "h3":
            paragraph = doc.add_heading(level=3)
            run = paragraph.add_run(element.get_text())
            run.font.size = Pt(14)
            paragraph_format = paragraph.paragraph_format
            paragraph_format.space_before = Pt(6)  # 0.5 line space before
            paragraph_format.space_after = Pt(6)  # 0.5 line space after
        elif element.name == "h4":
            paragraph = doc.add_heading(level=3)
            run = paragraph.add_run(element.get_text())
            run.font.size = Pt(13)
            paragraph_format = paragraph.paragraph_format
            paragraph_format.space_before = Pt(6)  # 0.5 line space before
            paragraph_format.space_after = Pt(6)  # 0.5 line space after
        elif element.name == "strong":
            run = doc.add_paragraph().add_run(element.get_text())
            paragraph_format = run.paragraph.paragraph_format
            paragraph_format.space_before = Pt(6)  # 0.5 line space before
            paragraph_format.space_after = Pt(6)  # 0.5 line space after
        elif element.name == "em":
            run = doc.add_paragraph().add_run(element.get_text())
            run.italic = True
            run.font.size = Pt(11.5)
            paragraph_format = run.paragraph.paragraph_format
            paragraph_format.space_before = Pt(6)  # 0.5 line space before
            paragraph_format.space_after = Pt(6)  # 0.5 line space after
        elif element.name == "ul":
            list_items = element.find_all("li")
            for i, li in enumerate(list_items):
                paragraph = doc.add_paragraph(li.get_text(), style="ListBullet")
                run = paragraph.runs[0]
                run.font.size = Pt(11.5)
                paragraph_format = paragraph.paragraph_format
                if i == 0:
                    paragraph_format.space_before = Pt(6)
                if i == len(list_items) - 1:
                    paragraph_format.space_after = Pt(6)
        elif element.name == "ol":
            list_items = element.find_all("li")
            for i, li in enumerate(list_items):
                paragraph = doc.add_paragraph(li.get_text(), style="ListNumber")
                run = paragraph.runs[0]
                run.font.size = Pt(11.5)
                paragraph_format = paragraph.paragraph_format
                if i == 0:
                    paragraph_format.space_before = Pt(6)
                if i == len(list_items) - 1:
                    paragraph_format.space_after = Pt(6)

        elif isinstance(element, str):
            paragraph = doc.add_paragraph(element)
            run = paragraph.runs[0]
            run.font.size = Pt(11.5)
            paragraph_format = paragraph.paragraph_format
            paragraph_format.space_before = Pt(6)  # 0.5 line space before
            paragraph_format.space_after = Pt(6)  # 0.5 line space after


def create_docx_from_html(html_content, filename):
    soup = BeautifulSoup(html_content, "lxml")

    doc = Document()
    add_html_to_docx(soup.body.contents, doc)

    doc.save(filename)


def get_constitution(str):
    pattern = r"Artículo (?P<number>\d+)"  # Named group to capture the number
    matches = re.findall(pattern, str)
    print("Found:", matches)

    return matches


def proccess_code(codigo):
    codigo = re.sub(
        r"[^A-Za-z0-9]", "-", codigo
    )  # Replace non-alphanumeric characters with hyphens
    codigo = re.sub(r"de-", "-", codigo)  # Remove 'de-' followed by a hyphen
    codigo = re.sub(
        r"-+", "-", codigo
    )  # Replace multiple consecutive hyphens with a single hyphen
    codigo = re.sub(
        r"-(\d{2})(\d{2})$", r"-\2", codigo
    )  # Convert 4-digit years to 2-digit if necessary
    return codigo


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


# Función para calcular la similitud entre dos textos
def es_similar(texto1, texto2):
    return SequenceMatcher(None, texto1, texto2).ratio()


def buscar_patrones_en_texto(TutelaSentTemp):
    print(
        f"TutelaSentTemp contiene {len(TutelaSentTemp)} elementos para análisis de sentencias adjuntas"
    )

    # Verificar que TutelaSentTemp sea una lista válida
    if not isinstance(TutelaSentTemp, list) or not TutelaSentTemp:
        print("Error: TutelaSentTemp no es una lista válida o está vacía.")
        return []

    # Inicializar la lista de sentencias coincidentes
    salida1 = []

    # Conectar a la base de datos MongoDB
    db = get_db()
    collection = db["sentenciasOld"]

    # Iterar sobre cada sentencia en TutelaSentTemp
    for sentencia_adjunta in TutelaSentTemp:
        sentencia_adjunta_normalizada = (
            re.sub(r"(\w+)-(\d+)/(\d+)", r"\1-\2-\3", sentencia_adjunta).lower().strip()
        )

        # Iterar sobre los documentos de la base de datos para buscar coincidencias con 'providencia'
        for doc in collection.find():
            providencia_db = doc["providencia"].lower().strip()

            # Normalizar el formato de 'providencia' en la base de datos (ej: 'T-310/24' a 'T-310-24')
            providencia_db_normalizada = re.sub(
                r"(\w+)-(\d+)/(\d+)", r"\1-\2-\3", providencia_db
            )

            # Comparar la sentencia de la base de datos con la sentencia adjunta normalizada
            if sentencia_adjunta_normalizada == providencia_db_normalizada:
                print(
                    f"Coincidencia encontrada: '{sentencia_adjunta_normalizada}' en documento ID: {doc['_id']}"
                )
                salida1.append(providencia_db_normalizada)

    print(f"Total de coincidencias encontradas salida1: {len(salida1)}")
    return salida1


def buscar_derechos_en_mongo(TutelaDerecTemp, salida1, limitar_busqueda=True):
    print(
        "TutelaDerecTemp contiene",
        len(TutelaDerecTemp),
        "elementos como entrada analisis derechos",
    )
    for i, derecho in enumerate(TutelaDerecTemp):
        print(f"Petición {i + 1}: {derecho}")

    # Verificar si hay derechos fundamentales invocados
    if not TutelaDerecTemp:
        print(
            "Error: No se encontraron los datos de derechos fundamentales invocados en la sesión."
        )
        return salida1, []

    # Imprimir el número de derechos fundamentales
    print(
        f"TutelaDerecTemp contiene {len(TutelaDerecTemp)} elementos para análisis en MongoDB"
    )

    # Inicializar la lista de documentos coincidentes
    SentDerecTempFiles = []

    # Conectar a la base de datos MongoDB
    db = get_db()
    collection = db["sentencias"]

    # Iterar sobre los documentos de la colección 'sentencias'
    for doc in collection.find():
        if "derechos" in doc and isinstance(
            doc["derechos"], list
        ):  # Verificar que el campo 'derechos' es una lista
            derechos_db = [derecho.lower().strip() for derecho in doc["derechos"]]
            print(
                f"Verificando derechos en documento ID: {doc['_id']} con derechos: {derechos_db}"
            )

            # Normalizar los derechos de MongoDB (eliminar caracteres especiales, limpiar guiones, etc.)
            derechos_db_normalizados = [
                re.sub(r"[\W_]+$", "", d.replace("-", "").strip().lower())
                for d in derechos_db
            ]
            print(f"Derechos en documento (normalizados): {derechos_db_normalizados}")

            coincidencias_derechos = 0  # Contador de coincidencias de derechos

            # Verificar coincidencias exactas y parciales entre los derechos de MongoDB y los invocados en TutelaDerecTemp
            for derecho_invocado in TutelaDerecTemp:
                derecho_invocado_normalizado = re.sub(
                    r"[\W_]+$", "", derecho_invocado.replace("-", "").strip().lower()
                )

                # Comparar cada derecho invocado con los derechos de la base de datos
                if derecho_invocado_normalizado in derechos_db_normalizados:
                    coincidencias_derechos += 1
                    print(
                        f"Coincidencia exacta encontrada para '{derecho_invocado_normalizado}' en documento ID: {doc['_id']}"
                    )

                # Comparar similitud parcial
                for derecho_db in derechos_db_normalizados:
                    similitud = es_similar(derecho_invocado_normalizado, derecho_db)
                    if similitud > 0.6:
                        coincidencias_derechos += 1
                        print(
                            f"Similitud alta encontrada entre '{derecho_invocado_normalizado}' y '{derecho_db}' en documento ID: {doc['_id']} (Similitud: {similitud})"
                        )

            # Si hay coincidencias, añadir el documento a SentDerecTempFiles
            if coincidencias_derechos > 0:
                SentDerecTempFiles.append((doc["_id"], coincidencias_derechos))
                print(
                    f"Total de coincidencias de derechos para documento ID {doc['_id']}: {coincidencias_derechos}"
                )

    # salida2 será el resultado de agregar los documentos encontrados a salida1
    salida2 = salida1  # Partimos de la lista de salida1
    for doc_id, _ in SentDerecTempFiles:
        doc = collection.find_one({"_id": doc_id})
        if doc and doc.get("providencia"):
            salida2.append(
                doc["providencia"]
            )  # Agregar la providencia a la lista de salida2

    return salida2, SentDerecTempFiles


def buscar_peticiones_con_ids(SentDerecTempFiles, salida2, TutelaPetTemp):
    print(
        "TutelaPetTemp contiene",
        len(TutelaPetTemp),
        "elementos como entrada analisis id´s",
    )
    for i, peticion in enumerate(TutelaPetTemp):
        print(f"Petición {i + 1}: {peticion}")

    # Inicializar salida3 para evitar errores si no se encuentran coincidencias
    salida3 = (
        salida2  # Si no se encuentran coincidencias, salida3 debe ser igual a salida2
    )

    # Verificar si hay peticiones
    if not TutelaPetTemp:
        print("Error: No se encontraron las peticiones.")
        return salida3

    db = get_db()
    collection = db["sentencias"]

    SentPetTempFiles = []

    # Recorrer los IDs obtenidos en SentDerecTempFiles
    for doc_id, _ in SentDerecTempFiles:
        doc = collection.find_one({"_id": doc_id})
        if doc:
            texto = doc["texto"].lower()  # Texto completo del documento
            coincidencias_peticiones = 0

            print(f"Analizando documento con ID {doc_id}")

            # Comparar las peticiones con el texto del documento (similitud flexible)
            for peticion in TutelaPetTemp:
                peticion_normalizada = peticion.lower().strip()

                # Coincidencia directa
                if peticion_normalizada in texto:
                    coincidencias_peticiones += 1
                    print(
                        f"Coincidencia directa para petición: '{peticion_normalizada}' en documento ID: {doc_id}"
                    )

                # Coincidencia parcial utilizando similitud
                oraciones_documento = re.split(r"[.!?]", texto)
                for oracion in oraciones_documento:
                    similitud = es_similar(peticion_normalizada, oracion.strip())
                    if similitud > 0.65:  # Umbral de similitud flexible
                        coincidencias_peticiones += 1
                        print(
                            f"Similitud entre '{peticion}' y '{oracion[:50]}...' en documento ID: {doc_id}, Similitud: {similitud}"
                        )

            if coincidencias_peticiones > 0:
                SentPetTempFiles.append((doc, coincidencias_peticiones))

    if SentPetTempFiles:
        SentPetTempFiles = sorted(SentPetTempFiles, key=lambda x: x[1], reverse=True)[
            :5
        ]
        # Agregar los documentos con coincidencias a la lista final de sentencias
        salida3 = salida2 + [doc["providencia"] for doc, _ in SentPetTempFiles]

    return salida3


# habilita los siguiente codigos si quieres limitar la busqueda
# def get_sentencia(str, limitar_busqueda=True):  # Procesa solo 100 documentos
# Parte 2: Búsqueda de derechos en la base de datos (TutelaDerecTemp)
# sentencia_list, SentDerecTempFiles = buscar_derechos_en_mongo(sentencia_list, limitar_busqueda)

# habilita los siguiente codigos si NO quieres limitar la busqueda
# def get_sentencia(str, limitar_busqueda=False):  # Procesa todos los documentos
# Parte 2: Búsqueda de derechos en la base de datos (TutelaDerecTemp)
# sentencia_list, SentDerecTempFiles = buscar_derechos_en_mongo(sentencia_list, limitar_busqueda=False)


def get_sentencia(TutelaDerecTemp, TutelaPetTemp, TutelaSentTemp):
    print("Iniciando get_sentencia...")
    print(f"TutelaDerecTemp: {TutelaDerecTemp}")
    print(f"TutelaPetTemp: {TutelaPetTemp}")
    print(f"TutelaSentTemp: {TutelaSentTemp}")

    # Parte 1: Búsqueda de patrones en el texto (pattern matching)
    salida1 = buscar_patrones_en_texto(TutelaSentTemp)
    print(f"Resultados de buscar_patrones_en_texto: {salida1}")

    # Parte 2: Búsqueda de derechos en la base de datos (TutelaDerecTemp)
    salida2, SentDerecTempFiles = buscar_derechos_en_mongo(TutelaDerecTemp, salida1)
    print(
        f"Resultados de buscar_derechos_en_mongo: Salida2: {salida2}, SentDerecTempFiles: {SentDerecTempFiles}"
    )

    # Parte 3: Búsqueda en Mongo de los IDs obtenidos y matching con TutelaPetTemp
    salida3 = buscar_peticiones_con_ids(SentDerecTempFiles, salida2, TutelaPetTemp)
    print(f"Resultados de buscar_peticiones_con_ids: {salida3}")

    # Combinar las salidas sin duplicar elementos
    sentencia_list = []
    for salida in [salida1, salida2, salida3]:
        for item in salida:
            if item not in sentencia_list:
                sentencia_list.append(item)

    # Imprimir sentencia_list para asegurar que los resultados son correctos
    print(
        f"Sentencia list final (combinación de salida1, salida2 y salida3 sin duplicados): {sentencia_list}"
    )

    return sentencia_list


def generate_evidence_checklist(text):
    match = re.search(r"```json(.*?)```", text, re.DOTALL)
    if match:
        json_text = match.group(1).strip()
    else:
        print("No JSON block found.")
        return
    json_object = json.loads(json_text)

    return json_object


def get_history(user, title=""):
    db = get_db()
    collection = db["saves"]
    pipeline = []
    if title == "":
        pipeline.append({"$project": {"_id": 1, "user": 1, "modifiedAt": 1}})
        pipeline.append({"$match": {"user": user}})
        pipeline.append({"$sort": {"modifiedAt": -1}})
        pipeline.append({"$limit": 1})
    else:
        pipeline.append(
            {"$project": {"_id": 1, "user": 1, "modifiedAt": 1, "title": 1}}
        )
        pipeline.append({"$match": {"user": user, "title": title}})
    find_data = list(collection.aggregate(pipeline=pipeline))
    if len(find_data) > 1:
        return "Error"
    elif len(find_data) == 1:
        history = collection.find_one({"_id": find_data[0]["_id"]})
        print(history)
        return history
    else:
        return "No data"


def get_current_state(user):
    print(user)
    db = get_db()
    collection = db["current_state"]
    history = collection.find_one({"user": user})
    if history:
        history.pop("_id", None)
        return history
    else:
        collection.insert_one({"user": user})
        return {"user": user}


def update_current_state(user, field, data):
    db = get_db()
    collection = db["current_state"]
    query_filter = {"user": user}
    update_date = {}
    update_date[field] = data
    update_operation = {}
    update_operation["$set"] = update_date
    collection.update_one(query_filter, update_operation)


def get_current_data_field(user, field):
    db = get_db()
    collection = db["current_state"]
    history = collection.find_one({"user": user})
    if field in history:
        return history[field]
    else:
        return ""


def get_settings(field):
    db = get_db()
    collection = db["settings"]
    settings = collection.find_one()
    return settings[field]


def get_title_list(user):
    db = get_db()
    collection = db["results"]
    pipeline = [{"$project": {"title": 1, "user": 1}}, {"$match": {"user": user}}]
    res = list(collection.aggregate(pipeline=pipeline))
    return_data = []
    for each in res:
        return_data.append(each["title"])
    return return_data


def save_tutela(user, title):
    loading_data = get_current_state(user)
    loading_data["title"] = title
    loading_data["modifiedAt"] = datetime.now()
    db = get_db()
    results = db["results"]
    currents = db["current_state"]
    pipeline = [
        {"$project": {"_id": 1, "title": 1, "user": 1}},
        {"$match": {"user": user, "title": title}},
    ]
    res = list(results.aggregate(pipeline=pipeline))
    if len(res) > 0:
        results.delete_one({"user": user, "title": title})

    results.insert_one(loading_data)
    currents.delete_one({"user": user})
    currents.insert_one(loading_data)
    return {"message": "sucess"}, 200


def set_tutela(user, title):
    db = get_db()
    results = db["results"]
    currents = db["current_state"]
    set_data = results.find_one({"user": user, "title": title})

    currents.delete_one({"user": user})
    currents.insert_one(set_data)
    return {"message": "sucess"}, 200


def reset_current_state(user):
    db = get_db()
    currents = db["current_state"]
    currents.delete_one({"user": user})

    return
