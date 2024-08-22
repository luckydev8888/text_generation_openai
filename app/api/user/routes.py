from flask import jsonify, request, send_file, send_from_directory, abort, session, redirect, url_for
from datetime import datetime
import time
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from . import user_api_bp
from .script import openAI_response
from .utils import find_setencia_list, create_docx_from_html, get_pdf_text, get_constitution, get_sentencia, generate_evidence_checklist
from .models import get_users
from app.user.users_routes import user_login_required

load_dotenv()
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
CONSTDF_ID = os.getenv("CONSTDF_ID")
SAMPLE_ID = os.getenv("SAMPLE_ID")
STAY_TIME = int(os.getenv("STAY_TIME"))
file_path = ""
sentence_result = []
articulo_result = []
pdf_content = ""
analysis_start_time = time.time() - STAY_TIME


@user_api_bp.route('/pdf/<path:filename>')
def pdf_serve_static(filename):
    if 'user_info' not in session:
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
    if 'user_info' not in session:
        return jsonify("no user"), 401
    content = request.form.get('content')
    create_docx_from_html(content, 'app/output.docx')
    return send_file('output.docx', as_attachment=True, download_name='output.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


@user_api_bp.route('/reset', methods=['POST'])
def reset():
    if 'user_info' not in session:
        return jsonify("no user"), 401
    if request.method == 'POST':
        global file_path
        global sentence_result
        global articulo_result
        global pdf_content
        file_path = ""
        sentence_result = []
        articulo_result = []
        pdf_content = ""

        response = {
            'message': "Reset done"
        }
        return jsonify(response), 200

@user_api_bp.route('/uploadfile', methods=['POST'])
def uploadfile():
    if 'user_info' not in session:
        return jsonify("no user"), 401
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return jsonify("no file"), 400
        file = request.files['pdf_file']
        if file.filename == '':
            return jsonify("no file name"), 400
        now = datetime.now()

        formatted_datetime = now.strftime("%y%m%d%H%M%S")

        filename = formatted_datetime + secure_filename(file.filename)

        
        global file_path
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(file_path)

        global file_name
        file_name = filename

        global pdf_content
        pdf_content = get_pdf_text(file_path)

        result_message = {'file_path': file_name}
        response = {
            'message' : result_message
        }

        return jsonify(response), 200

@user_api_bp.route('/analysis_pdf', methods=['POST'])
def analysis_pdf():
    if 'user_info' not in session:
        return jsonify("no user"), 401
    if request.method == 'POST':
        global analysis_start_time
        during_time = time.time() - analysis_start_time
        if during_time < STAY_TIME: time.sleep(STAY_TIME - during_time)
        
        # pdf_content = get_pdf_text(file_path)
        send_message = f'Este es el contenido del documento: \"{pdf_content}\". Resumir este documento'

        result_message = openAI_response(send_message)

        response = {
            'message': result_message
        }
        analysis_start_time = time.time()

        return jsonify(response), 200
    
@user_api_bp.route('/analysis_judgement', methods=['POST'])
def analysis_judgement():
    if 'user_info' not in session:
        return jsonify("no user"), 401
    if request.method == 'POST':

        sentencia_list = get_sentencia(pdf_content, articulo_result)

        print(sentencia_list)
        global sentence_result

        sentence_result = find_setencia_list(sentencia_list)

        response = {
            'message': sentence_result
        }

        return jsonify(response), 200

@user_api_bp.route('/analysis_constitucion', methods=['POST'])
def analysis_constitucion():
    if 'user_info' not in session:
        return jsonify("no user"), 401
    if request.method == 'POST':
        global articulo_result

        global analysis_start_time
        during_time = time.time() - analysis_start_time
        if during_time < STAY_TIME: time.sleep(STAY_TIME - during_time)

        # pdf_content = get_pdf_text(file_path)

        send_message = f"""El archivo ConstDf.txt contiene el texto de una constitución. Su tarea es identificar y extraer todas las disposiciones constitucionales relevantes para el contenido de este documento: \"{pdf_content}\"

                            Cada disposición extraída debe incluir su número de disposición correspondiente, con el siguiente formato: 'Artículo 33'.

                            Asegúrese de que todas las disposiciones extraídas estén claramente etiquetadas con sus números.
                            """
        analysis_start_time = time.time()
        result_message = openAI_response(send_message, CONSTDF_ID)
        articulo_result = get_constitution(result_message)

        response = {
            'message': result_message
        }
        
        analysis_start_time = time.time()

        return jsonify(response), 200
    

@user_api_bp.route('/analysis_evidence', methods=['POST'])
def analysis_evidence():
    if 'user_info' not in session:
        return jsonify("no user"), 401
    if request.method == 'POST':
        global evidence_checklist


        global analysis_start_time
        during_time = time.time() - analysis_start_time
        if during_time < STAY_TIME: time.sleep(STAY_TIME - during_time)

        # pdf_content = get_pdf_text(file_path)

        send_message = f'Este es el contenido del documento: \"{pdf_content}\". Liste las evidencias que se necesitan para confirmar cada hecho del documento'
        result_message = openAI_response(send_message)
        print(result_message)

        evidence_checklist = generate_evidence_checklist(result_message)
        
        print(evidence_checklist)
        response = {
            'message': evidence_checklist
        }
        analysis_start_time = time.time()

        return jsonify(response), 200
    
@user_api_bp.route('/submit_evidence', methods=['POST'])
def submit_evidence():
    if 'user_info' not in session:
        return jsonify("no user"), 401
    if request.method == 'POST':
        global evidence_checklist
        
        try:
            data = request.get_json()
            evidence_data = data.get('evidence_data')
            evidence_checklist = evidence_data
            print(evidence_checklist)
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
    if 'user_info' not in session:
        return jsonify("no user"), 401
    if request.method == 'POST':
        
        global analysis_start_time
        during_time = time.time() - analysis_start_time
        if during_time < STAY_TIME: time.sleep(STAY_TIME - during_time)

        # pdf_content = get_pdf_text(file_path)

        constitucion_text = ""
        for item in sentence_result:
            constitucion_text = f'{constitucion_text} , {item['providencia']}'
        
        send_message = f"""Nuevo documento: \"{pdf_content}\"

                Revisiones judiciales relevantes: \"{constitucion_text}\"

                Disposiciones constitucionales relevantes para el documento: \"{articulo_result}\"

                Con base en el nuevo documento, la lista de revisiones judiciales relevantes (cuyo contenido está disponible en la tienda de vectores) y las disposiciones constitucionales proporcionadas, redacte una sentencia para el nuevo documento.
                
                El archivo borrador de muestra es "sample.docx"
                """
        result_message = openAI_response(send_message,SAMPLE_ID)

        print(result_message)
        
        response = {
            'message': result_message
        }
        analysis_start_time = time.time()

        return jsonify(response), 200
    
@user_api_bp.route('/users/get', methods=['POST'])
def users_get():
    if 'user_info' not in session:
        return jsonify("no user"), 401
    result_data = get_users()
    response = {
        'message': result_data
    }
    print(response)
    return  response, 200