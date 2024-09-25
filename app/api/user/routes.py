from flask import jsonify, request, send_file, send_from_directory, abort, session, redirect, url_for, flash
from datetime import datetime
import time
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import re

from . import user_api_bp
from .script import openAI_response
from .utils import find_setencia_list, create_docx_from_html, get_pdf_text, get_constitution, get_sentencia, generate_evidence_checklist, get_current_state, update_current_state, get_current_data_field, get_settings, get_title_list, save_tutela, set_tutela, reset_current_state
from .models import get_users

load_dotenv()
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
STAY_TIME = int(os.getenv("STAY_TIME"))
file_path = ""
sentence_result = []
articulo_result = []
pdf_content = ""
analysis_start_time = time.time() - STAY_TIME

def check_login_user():
    if 'user_info' not in session:
        flash('We need you to log in to proceed.', 'warning')
        return True
    return False

@user_api_bp.route('/pdf/<path:filename>')
def pdf_serve_static(filename):
    if check_login_user():
        return jsonify("no user"), 401
    if '..' in filename or filename.startswith('/'):
        return abort(400)

    uploads_dir = 'uploads'
    safe_path = os.path.join(UPLOAD_FOLDER,filename)
    if os.path.isfile(safe_path):
        return send_from_directory(uploads_dir, filename)
    else:
        return abort(404)

@user_api_bp.route('/save_resultados', methods=['POST'])
def save_resultados():
    if check_login_user():
        return jsonify("no user"), 401
    content = request.form.get('content')
    print(content)
    user = session['user_info']
    title = get_current_data_field(user, 'title')
    if title == '': 
        file_name = 'output.docx'
    else:
        file_name = f'{title}.docx'
    create_docx_from_html(content, f'app/{file_name}')
    return send_file(file_name, as_attachment=True, download_name=file_name, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

@user_api_bp.route('/reset', methods=['POST'])
def reset():
    if check_login_user():
        return jsonify("no user"), 401
    if request.method == 'POST':
        user = session['user_info']
        reset_current_state(user)

        response = {
            'message': "Reset done"
        }
        return jsonify(response), 200

@user_api_bp.route('/uploadfile', methods=['POST'])
def uploadfile():
    if check_login_user():
        return jsonify("no user"), 401
    if request.method == 'POST':
        user = session['user_info']
        if 'pdf_file' not in request.files:
            return jsonify("no file"), 400
        file = request.files['pdf_file']
        if file.filename == '':
            return jsonify("no file name"), 400
        now = datetime.now()

        formatted_datetime = now.strftime("%y%m%d%H%M%S")

        filename = formatted_datetime + secure_filename(file.filename)
        update_current_state(user, 'file_name', filename)

        
        global file_path
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(file_path)
        update_current_state(user, 'file_path', file_path)

        global file_name
        file_name = filename

        global pdf_content
        pdf_content = get_pdf_text(file_path)
        update_current_state(user, 'pdf_content', pdf_content)

        result_message = {'file_path': file_name}
        response = {
            'message' : result_message
        }

        return jsonify(response), 200

def normalize_peticiones(peticiones):
    """
    Normaliza las peticiones eliminando prefijos de numeración (palabras, números, letras, viñetas),
    y limpiando los textos para que puedan buscarse de manera coherente.
    """
    peticiones_normalizadas = []
    for peticion in peticiones:
        # Eliminar prefijos de numeración como "Primero", "1.", "a)", "•", etc.
        peticion = re.sub(r'^\b(primero|segundo|tercero|cuarto|quinto|sexto|séptimo|octavo|noveno|décimo|Las peticiones o solicitudes presentadas en el documento son|[a-zA-Z]\)|\d+[*,+]+[\.\)]|•|-)\b[\s]*', '', peticion, flags=re.IGNORECASE).strip()

        # Dividir la petición usando puntos para separar ideas completas
        sub_peticiones = re.split(r'[.]', peticion)
        
        def eliminar_guiones_inicio(sub_peticion):
            return sub_peticion.lstrip("- ")
        
        # Limpiar cada sub-petición
        for sub_peticion in sub_peticiones:
            sub_peticion = re.sub(r'^\d+\.\s*', '', sub_peticion).strip()  # Eliminar números al inicio
            sub_peticion = re.sub(r'[\W_]+$', '', sub_peticion).strip()  # Eliminar caracteres especiales al final
            sub_peticion = re.sub(r'\s+', ' ', sub_peticion).strip()  # Unificar espacios múltiples
            sub_peticion = eliminar_guiones_inicio(sub_peticion)

            # Asegurarse de que la sub-petición no esté vacía y sea válida
            if sub_peticion and len(sub_peticion) > 2:  # Evitar entradas cortas irrelevantes
                peticiones_normalizadas.append(sub_peticion)
    
    return peticiones_normalizadas

def normalize_derechos(derechos):
    """
    Normaliza las derechos eliminando prefijos de numeración (palabras, números, letras, viñetas),
    y limpiando los textos para que puedan buscarse de manera coherente.
    """
    derechos_normalizados = []
    for derecho in derechos:
        # Eliminar prefijos de numeración como "Primero", "1.", "a)", etc.
        derecho = re.sub(r'^\b(primero|segundo|tercero|cuarto|quinto|sexto|séptimo|octavo|noveno|décimo|Los derechos fundamentales invocados en el documento son|[a-zA-Z]\)|\d+[*,+]+[\.\)]|•|-)\b[\s]*', '', derecho, flags=re.IGNORECASE).strip()

        # Dividir la petición usando puntos para separar ideas completas
        sub_derechos = re.split(r'[.]', derecho)
        
        def eliminar_guiones_inicio(sub_prueba):
            return sub_prueba.lstrip("- ")
        
        # Limpiar cada sub-petición
        for sub_derecho in sub_derechos:
            sub_derecho = re.sub(r'^\d+\.\s*', '', sub_derecho).strip()  # Eliminar números al inicio
            sub_derecho = re.sub(r'[\W_]+$', '', sub_derecho).strip()  # Eliminar caracteres especiales al final
            sub_derecho = re.sub(r'\s+', ' ', sub_derecho).strip()  # Unificar espacios múltiples
            sub_derecho = eliminar_guiones_inicio(sub_derecho)
            # Asegurarse de que la sub-petición no esté vacía y sea válida
            if sub_derecho and len(sub_derecho) > 2:  # Evitar entradas cortas irrelevantes
                derechos_normalizados.append(sub_derecho)
                
    return derechos_normalizados

def normalize_pruebas(pruebas):
    """
     Normaliza las pruebas eliminando prefijos de numeración (palabras, números, letras, viñetas),
    y limpiando los textos para que puedan buscarse de manera coherente.
    """
    pruebas_normalizadas = []
    for prueba in pruebas:
        # Eliminar prefijos de numeración como "Primero", "1.", "a)", etc.
        prueba = re.sub(r'^\b(primero|segundo|tercero|cuarto|quinto|sexto|séptimo|octavo|noveno|décimo|Las pruebas o documentos adjuntos mencionados en el documento son|[a-zA-Z]\)|\d+[*,+]+[\.\)]|•|-)\b[\s]*', '', prueba, flags=re.IGNORECASE).strip()

        # Dividir la petición usando puntos para separar ideas completas
        sub_pruebas = re.split(r'[.]', prueba)
        
        def eliminar_guiones_inicio(sub_prueba):
            return sub_prueba.lstrip("- ")
        
        # Limpiar cada sub-petición
        for sub_prueba in sub_pruebas:
            sub_prueba = re.sub(r'^\d+\.\s*', '', sub_prueba).strip()  # Eliminar números al inicio
            sub_prueba = re.sub(r'[\W_]+$', '', sub_prueba).strip()  # Eliminar caracteres especiales al final
            sub_prueba = re.sub(r'\s+', ' ', sub_prueba).strip()  # Unificar espacios múltiples
            sub_prueba = eliminar_guiones_inicio(sub_prueba)

            # Asegurarse de que la sub-petición no esté vacía y sea válida
            if sub_prueba and len(sub_prueba) > 2:  # Evitar entradas cortas irrelevantes
                pruebas_normalizadas.append(sub_prueba)
    
    return pruebas_normalizadas

def normalize_hechos(hechos):
    """
    Normaliza los hechos relevantes eliminando prefijos de numeración (palabras, números, letras, viñetas),
    y limpiando los textos para que puedan buscarse de manera coherente.
    """
    hechos_normalizados = []
    
    for hecho in hechos:
        # Eliminar prefijos de numeración como "Primero", "1.", "a)", etc.
        hecho = re.sub(r'^\b(primero|segundo|Documentales|tercero|cuarto|quinto|sexto|séptimo|octavo|noveno|décimo|Los hechos principales mencionados en el documento son|[a-zA-Z]\)|\d+[*,+]+[\.\)]|•|-)\b[\s]*', '', hecho, flags=re.IGNORECASE).strip()

       # Dividir la petición usando puntos para separar ideas completas
        sub_hechos = re.split(r'[.]', hecho)
        
        def eliminar_guiones_inicio(sub_hecho):
            return sub_hecho.lstrip("- ")
        
        # Limpiar cada sub-petición
        for sub_hecho in sub_hechos:
            sub_hecho = re.sub(r'^\d+\.\s*', '', sub_hecho).strip()  # Eliminar números al inicio
            sub_hecho = re.sub(r'[\W_]+$', '', sub_hecho).strip()  # Eliminar caracteres especiales al final
            sub_hecho = re.sub(r'\s+', ' ', sub_hecho).strip()  # Unificar espacios múltiples
            sub_hecho = eliminar_guiones_inicio(sub_hecho)

            # Asegurarse de que la sub-petición no esté vacía y sea válida
            if sub_hecho and len(sub_hecho) > 2:  # Evitar entradas cortas irrelevantes
                hechos_normalizados.append(sub_hecho)
                
    return hechos_normalizados

def normalize_sentencias(sentencias):
    """
    Normaliza las sentencias eliminando prefijos de numeracion (palabras, viñeas, guiones, espacios al iniciar o finalizar),
    y limpieando los textos para que puedan buscarse de manera coherente, una muestra del formato 'T-444-99', 'SU-509-01', 'A-001-00', 'C-014-00', etc.
    """
    sentencias_normalizadas = []
    
    for sentencia in sentencias:
        # Eliminar prefijos innecesarios como 'Sentencia', '-', etc.
        sentencia = re.sub(r'^\b(sentencia|Sentencia|\d+[\.\)]|•|-)\b[\s]*', '', sentencia, flags=re.IGNORECASE).strip()
        
        # Dividir la petición usando puntos para separar ideas completas
        sub_sentencias = re.split(r'[.]', sentencia)
        
        def reemplazar_slash_por_guion(sub_sentencia):
            return sub_sentencia.replace("/", "-")
        
        def eliminar_palabra_sentencia(sub_sentencia):
            return sub_sentencia.replace("Sentencia ", "", 1)
        
        def eliminar_guiones_inicio(sub_sentencia):
            return sub_sentencia.lstrip("- ")
        
        sub_sentencias = [
            "Sentencia T-444/99",
            "- Sentencia T-555/00",
            "Sentencia T-666/01"
        ]
        
        # Limpiar cada sub-petición
        for sub_sentencia in sub_sentencias:
            sub_sentencia = re.sub(r'^\d+\.\s*', '', sub_sentencia).strip()  # Eliminar números al inicio
            sub_sentencia = re.sub(r'[\W_]+$', '', sub_sentencia).strip()  # Eliminar caracteres especiales al final
            sub_sentencia = re.sub(r'\s+', ' ', sub_sentencia).strip()  # Unificar espacios múltiples
            sub_sentencia = eliminar_palabra_sentencia(sub_sentencia)
            sub_sentencia = eliminar_guiones_inicio(sub_sentencia)
            sub_sentencia = reemplazar_slash_por_guion(sub_sentencia)
            
            # Asegurarse de que la sub-petición no esté vacía y sea válida
            if sub_sentencia and len(sub_sentencia) > 2:  # Evitar entradas cortas irrelevantes
                sentencias_normalizadas.append(sub_sentencia)
    
    return sentencias_normalizadas


@user_api_bp.route('/analysis_pdf', methods=['POST'])
def analysis_pdf():
    if check_login_user():
        return jsonify("no user"), 401
    if request.method == 'POST':
        user = session['user_info']
        
        # Tiempo de espera antes del análisis, si es necesario
        global analysis_start_time
        during_time = time.time() - analysis_start_time
        if during_time < STAY_TIME:
            time.sleep(STAY_TIME - during_time)
        
        # Obtener el contenido PDF desde el estado del usuario
        pdf_content = get_current_data_field(user, 'pdf_content')
        if not pdf_content:
            return jsonify({"error": "No se encontró el contenido del PDF"}), 400
        
        print(f"Contenido del PDF procesado: {pdf_content}")

        # Crear el mensaje para OpenAI solicitando los datos dinámicos
        send_message = f"""
        A continuación se presenta el contenido de un documento legal. Por favor, extrae la siguiente información:
        
        1. Derechos Fundamentales Invocados: Enumera todos los derechos fundamentales que se mencionan o invocan en el documento.
        2. Hechos Relevantes: Resume los hechos principales que se mencionan en el documento.
        3. Peticiones: Enumera las peticiones o solicitudes que se presentan en el documento.
        4. Pruebas Adjuntas: Enumera las pruebas o documentos adjuntos que se mencionan para respaldar las peticiones o hechos.
        5. Sentencias: Liste el codigo de las sentencias presentes en el documento.

        Este es el contenido del documento:
        {pdf_content}
        """
        
        # Llamada a OpenAI para procesar el contenido del PDF
        result_message = openAI_response(send_message)
        
        if not result_message:
            return jsonify({"error": "Error en la respuesta de OpenAI"}), 500

        # Extraer secciones de la respuesta de OpenAI
        derechos_fundamentales_invocados = extract_section(result_message, "Derechos Fundamentales Invocados")
        hechos_relevantes = extract_section(result_message, "Hechos Relevantes")
        peticiones = extract_section(result_message, "Peticiones")
        pruebas_adjuntas = extract_section(result_message, "Pruebas Adjuntas")
        sentencias_adjuntas = extract_section(result_message, "Sentencias")

        # Normalizar sentencias, derechos, peticiones, y demás secciones
        pruebas_adjuntas = normalize_pruebas(pruebas_adjuntas)
        hechos_relevantes = normalize_hechos(hechos_relevantes)
        derechos_fundamentales_invocados = normalize_derechos(derechos_fundamentales_invocados)
        peticiones = normalize_peticiones(peticiones)
        sentencias_adjuntas = normalize_sentencias(sentencias_adjuntas)

        # Verificación de los resultados extraídos
        print(f"Derechos Fundamentales (antes de guardar en session): {derechos_fundamentales_invocados}")
        print(f"Hechos Relevantes (antes de guardar en session): {hechos_relevantes}")
        print(f"Peticiones (antes de guardar en session): {peticiones}")
        print(f"Pruebas Adjuntas (antes de guardar en session): {pruebas_adjuntas}")
        print(f"Sentencias Adjuntas (antes de guardar en session): {sentencias_adjuntas}")

        # Guardar los resultados extraídos en la sesión para acceder desde otros puntos
        session['derechos_fundamentales_invocados'] = derechos_fundamentales_invocados
        session['peticiones'] = peticiones
        session['pruebas_adjuntas'] = pruebas_adjuntas
        session['hechos_relevantes'] = hechos_relevantes
        session['sentencias_adjuntas'] = sentencias_adjuntas

        # Actualizar el estado del usuario con el resumen del documento
        update_current_state(user, 'pdf_resume', result_message)

        # Preparar la respuesta para enviar al frontend
        response = {
            'message': result_message
        }
        
        # Actualizar el tiempo de análisis
        analysis_start_time = time.time()

        return jsonify(response), 200


def extract_section(text, section_title):
    """
    Función auxiliar que busca una sección en el texto devuelto por OpenAI.
    Extrae la información basada en el título de la sección especificada.
    """
    section_start = text.find(section_title)
    if section_start == -1:
        return []
    
    section_end = text.find('\n\n', section_start)
    if section_end == -1:
        section_end = len(text)
    
    section_content = text[section_start:section_end].split('\n')[1:]  # Ignorar el título
    return [item.strip() for item in section_content if item.strip()]
        
@user_api_bp.route('/analysis_judgement', methods=['POST'])
def analysis_judgement():
    if check_login_user():
        return jsonify("no user"), 401
    if request.method == 'POST':
        user = session['user_info']
        
        # Cambiar 'pdf_resumen' a 'pdf_resume' porque así se guarda en analysis_pdf
        pdf_resume = get_current_data_field(user, 'pdf_resume')  # Aquí usamos el nombre correcto
        if not pdf_resume:
            return jsonify({"error": "No se encontró el resumen del PDF"}), 400
        
        # Obtener derechos fundamentales, peticiones y sentencias desde la sesión
        TutelaDerecTemp = session.get('derechos_fundamentales_invocados', []) 
        TutelaPetTemp = session.get('peticiones', [])  # Obtener las peticiones
        TutelaSentTemp = session.get('sentencias_adjuntas', [])
                
        print("Iniciando la función analysis_judgement...")
        
        # Verificar el formato de TutelaSentTemp, TutelaDerecTemp y TutelaPetTemp
        print(f"TutelaSentTemp (después de cargar de sesión): {TutelaSentTemp}")
        print(f"Tipo de TutelaSentTemp: {type(TutelaSentTemp)}")
       
        print(f"TutelaDerecTemp (después de cargar de sesión): {TutelaDerecTemp}")
        print(f"Tipo de TutelaDerecTemp: {type(TutelaDerecTemp)}") # Verificar el formato de TutelaSentTemp
        
        print(f"TutelaPetTemp (después de cargar de sesión): {TutelaPetTemp}")
        print(f"Tipo de TutelaPetTemp: {type(TutelaPetTemp)}")
        
        # Usar pdf_resume en lugar de pdf_resumen para obtener las sentencias
        sentencia_list = get_sentencia(TutelaDerecTemp, TutelaPetTemp, TutelaSentTemp) #aqui va pdf_resume en el futuro
        update_current_state(user, 'sentencia_list', sentencia_list)  
        
        global sentence_result
        sentence_result = find_setencia_list(sentencia_list)  # Procesa sentencia_list para obtener sentence_result
        update_current_state(user, 'sentence_result', sentence_result)
       
        response = {
            'message': sentence_result
        }
        print("Finalizando la función analysis_judgement...")
        return jsonify(response), 200

@user_api_bp.route('/analysis_constitucion', methods=['POST'])
def analysis_constitucion():
    if check_login_user():
        return jsonify("no user"), 401
    if request.method == 'POST':
        user = session['user_info']
        global articulo_result

        global analysis_start_time
        during_time = time.time() - analysis_start_time
        if during_time < STAY_TIME: time.sleep(STAY_TIME - during_time)

        pdf_content = get_current_data_field(user, 'pdf_content')

        send_message = f"""El archivo ConstDf.txt contiene el texto de una constitución. Su tarea es identificar y extraer todas las disposiciones constitucionales relevantes para el contenido de este documento: \"{pdf_content}\"

                            Cada disposición extraída debe incluir su número de disposición correspondiente, con el siguiente formato: 'Artículo 33'.

                            Asegúrese de que todas las disposiciones extraídas estén claramente etiquetadas con sus números.
                            """
        analysis_start_time = time.time()
        
        CONSTDF_ID = get_settings('constdf_file_id')
        result_message = openAI_response(send_message, CONSTDF_ID)
        update_current_state(user, 'constitution', result_message)
        
        articulo_result = get_constitution(result_message)
        update_current_state(user, 'articulo_result', articulo_result)
        
        response = {
            'message': result_message
        }
        
        analysis_start_time = time.time()

        return jsonify(response), 200

@user_api_bp.route('/analysis_evidence', methods=['POST'])
def analysis_evidence():
    if check_login_user():
        return jsonify("no user"), 401
    if request.method == 'POST':
        user = session['user_info']
        global evidence_checklist

        global analysis_start_time
        during_time = time.time() - analysis_start_time
        if during_time < STAY_TIME: time.sleep(STAY_TIME - during_time)

        pdf_content = get_current_data_field(user, 'pdf_content')

        # send_message = f'Este es el contenido del documento: \"{pdf_content}\". Liste las evidencias que se necesitan para confirmar cada hecho del documento'
        send_message = f'El contenido del documento es \"{pdf_content}\". Por favor, enumera en formato JSON las evidencias necesarias para verificar cada hecho mencionado en el documento. El formato JSON es el siguiente:' + """[{
                "descripcion": "Compra del bien inmueble ubicado en la Calle 54c sur #88I71 – Bosa (Bogotá-Colombia) el día 29 de abril de 2023",
                "evidencias": [
                {
                    "tipo": "documento",
                    "descripcion": "Copia de la cédula de ciudadanía del propietario del inmueble, Danilo Quevedo Vaca",
                    "archivo": "cedula_danilo_quevedo.pdf"
                },
                {
                    "tipo": "fotografías",
                    "descripcion": "Imágenes de los depósitos de basura ubicados hacia las áreas comunes",
                    "archivo": "fotos_basura.pdf"
                },
                {
                    "tipo": "videos",
                    "descripcion": "Videos mostrando la disposición indebida de los depósitos",
                    "archivo": "videos_basura.mp4"
                }
                ]
            },...]
            
            La clave json es importante"""
        result_message = openAI_response(send_message)
        print(result_message)

        evidence_checklist = generate_evidence_checklist(result_message)
        update_current_state(user, 'evidence_checklist', evidence_checklist)
        
        response = {
            'message': evidence_checklist
        }
        analysis_start_time = time.time()

        return jsonify(response), 200
    
@user_api_bp.route('/submit_evidence', methods=['POST'])
def submit_evidence():
    if check_login_user():
        return jsonify("no user"), 401
    if request.method == 'POST':
        try:
            data = request.get_json()
            evidence_data = data.get('evidence_data')
            evidence_checklist = evidence_data
        except Exception as e:
            return jsonify({"message": "Error procesando las evidencias.", "error": str(e)}), 500

        # Verifica si todas las evidencias están presentes
            
        missing_evidences = []
        for each in evidence_checklist:
            if each['state'] == False:
                missing_evidences.append(each['value'])
        if len(missing_evidences) == 0:
            return jsonify({"message": "All evidences provided. Proceeding with further analysis."}), 200
        else:
            return jsonify({"message": "Tutela rechazada", "missing_evidences": missing_evidences}), 400

@user_api_bp.route('/analysis_resultados', methods=['POST'])
def analysis_resultados():
    if check_login_user():
        return jsonify("no user"), 401
    if request.method == 'POST':
        user = session['user_info']
        global analysis_start_time
        during_time = time.time() - analysis_start_time
        if during_time < STAY_TIME: time.sleep(STAY_TIME - during_time)

        pdf_content = get_current_data_field(user, 'pdf_content')
        sentence_result = get_current_data_field(user, 'sentence_result')
        sentence_result = [] if sentence_result == '' else sentence_result
        articulo_result = get_current_data_field(user, 'articulo_result')
        articulo_result = [] if articulo_result == '' else articulo_result

        constitucion_text = ""
        for item in sentence_result:
            constitucion_text = f'{constitucion_text} , {item['providencia']}'

        sample_docs = get_settings("sampleDoc_id")
        result_message = """### REPÚBLICA DE COLOMBIA\n\n## JUZGADO [NOMBRE DEL JUZGADO]\n\n## [Ciudad, Fecha]\n\n## REFERENCIA: Acción de Tutela promovida por \n\n
            """
        for index, item in enumerate(sample_docs):
            content = item['content']
        
            send_message = f"""Nuevo documento: \"{pdf_content}\"

                    Revisiones judiciales relevantes: \"{constitucion_text}\"

                    Disposiciones constitucionales relevantes para el documento: \"{articulo_result}\"

                    estas son sentencias de la corte constitucional: \"{sentence_result}\", son respuestas a casos similares a \"{pdf_content}\", tienes que entender la relacion que hay entre los hechos, antecedentes, tramite procesal, la competencia, la procedencia de la acccion de tutela, la solucion de cada caso, el problema juridico con la decision y el resuelve, tenga en cuenta que todos los puntos de resuelve son las respuestas a las peticiones de "{pdf_content}\"

                    Utilizando el nuevo documento, la lista de revisiones judiciales relevantes almacenadas en la base de datos vectorial, las disposiciones constitucionales proporcionadas, y el entendimiento de las relaciones de las sentencias con el resuelve y las peticiones, redacte las siguientes secciones para la sentencia:\"{content}\"
                    
                    El número de palabras debe ser de al menos 700.

                    La estructura del documento y el archivo de salida estándar son los siguientes:
                    """
            
            SAMPLE_ID = []
            for doc in item['samples']:
                send_message = send_message + f' "{doc['name']}"'
                SAMPLE_ID.append(doc['file_id'])
            text = openAI_response(send_message, SAMPLE_ID)
            if index == 0:
                pattern = r'\s*[#*]*\s*1. Síntesis de la sentencia'
            elif index == 1:
                pattern = r'\s*[#*]*\s*8. Procedencia de la acción de tutela'
            elif index == 2:
                pattern = r'\s*[#*]*\s*12. Consideraciones'
    
            print(text)
            match = re.search(pattern, text)
            if match:
                cleaned_text = text[match.start():].strip()
            else:
                cleaned_text = text.strip()

            horizontal_line_index = cleaned_text.find('---')
            if horizontal_line_index != -1:
                cleaned_text = cleaned_text[:horizontal_line_index].strip()
            else:
                cleaned_text = cleaned_text.strip()
            
            result_message = result_message + '\n\n' + cleaned_text
        
        if "[Nombre del Juez]" not in result_message:
            result_message = result_message + "\n\n[Nombre del Juez]"
        result_message = result_message + "Notas: \n\nRevisión de la jurisprudencia relevante: \n\n"
        for item in sentence_result:
            result_message = result_message + "\n\n" + item['providencia']
        update_current_state(user, 'resultados', result_message)
        
        response = {
            'message': result_message
        }
        analysis_start_time = time.time()

        return jsonify(response), 200
    
@user_api_bp.route('/users/get', methods=['POST'])
def users_get():
    if check_login_user():
        return jsonify("no user"), 401
    result_data = get_users()
    response = {
        'message': result_data
    }
    print(response)
    return  response, 200

@user_api_bp.route('/get/state', methods=['POST'])
def history_get():
    if check_login_user():
        return jsonify("no user"), 401
    current_user = session['user_info']
    loading_data = get_current_state(current_user)
    
    return  jsonify(loading_data), 200

@user_api_bp.route('/get/list', methods=['POST'])
def list_get():
    if check_login_user():
        return jsonify("no user"), 401
    current_user = session['user_info']
    title_list = get_title_list(current_user)

    # result_data = get_users()
    
    return  jsonify(title_list), 200

@user_api_bp.route('/save/state', methods=['POST'])
def save_state():
    if check_login_user():
        return jsonify("no user"), 401
    if request.method == 'POST':
        
        try:
            data = request.get_json()
            title = data.get('title')
        except Exception as e:
            return jsonify({"message": "Error procesando las evidencias.", "error": str(e)}), 500

        # Verifica si todas las evidencias están presentes
        current_user = session['user_info']

        message, code = save_tutela(current_user, title)
        return jsonify(message), code
    
@user_api_bp.route('/set/state', methods=['POST'])
def set_state():
    if check_login_user():
        return jsonify("no user"), 401
    if request.method == 'POST':
        try:
            data = request.get_json()
            title = data.get('title')
        except Exception as e:
            return jsonify({"message": "Error procesando las evidencias.", "error": str(e)}), 500

        # Verifica si todas las evidencias están presentes
        current_user = session['user_info']

        message, code = set_tutela(current_user, title)
        return jsonify(message), code
