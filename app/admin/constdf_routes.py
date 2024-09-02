from flask import render_template, request, Blueprint, jsonify, session, redirect, url_for
from app.admin.script.const import get_const, add_const, update_const, delete_const, update_constdf_csv, get_constdf_text
from app.admin.main_routes import login_required, check_login_admin
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os

from openai import OpenAI
from app.mongo import get_db, get_user_info
from bson import ObjectId

load_dotenv()
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
OPENAI_KEY = os.getenv("OPENAI_KEY")

file_path = ""


constdf_bp = Blueprint('constdf', __name__, url_prefix="constdf")
# constdf page
@constdf_bp.route('/')
def constdf():
    if check_login_admin():
        return redirect(url_for('admin.main.login'))
    current_user = get_user_info(session['admin_info'], 'admin')
    return render_template('constdf.html', user=current_user)


@constdf_bp.route('/get', methods=['POST'])
def constdf_get():
    if check_login_admin():
        return redirect(url_for('admin.main.login'))
    if request.method == 'POST':
        keyword = request.form.get('search[value]')
        start = request.form.get('start')
        length = request.form.get('length')
        sortColumn = request.form.get('order[0][column]')
        dir = request.form.get('order[0][dir]')
        return get_const(keyword, int(start), int(length), int(sortColumn), dir)

@constdf_bp.route('/save', methods=['POST'])
def constdf_save():
    if check_login_admin():
        return redirect(url_for('admin.main.login'))
    if request.method == 'POST':
        id = request.form.get('id')
        type = request.form.get('type')
        number = request.form.get('number')
        texto = request.form.get('texto')
        tutela = request.form.get('tutela')
        
        if id == '':
            return add_const(type, number, texto, tutela)
        else:
            return update_const(id, type, number, texto, tutela)

@constdf_bp.route('/delete', methods=['POST'])
def constdf_delete():
    if check_login_admin():
        return redirect(url_for('admin.main.login'))
    if request.method == 'POST':
        id = request.form.get('id')
        
        return delete_const(id)
    
@constdf_bp.route('/uploadconstdfcsv', methods=['POST'])
def constdf_upload_constdf_csv():
    if check_login_admin():
        return redirect(url_for('admin.main.login'))
    if request.method == 'POST':
        if 'constdf_csv_file' not in request.files:
            return jsonify("no file"), 400
        file = request.files['constdf_csv_file']
        if file.filename == '':
            return jsonify("no file name"), 400

        filename = secure_filename(file.filename)

        
        global file_path
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(file_path)
        
        response = {
            'message' : "successfully uploaded"
        }

        return jsonify(response), 200
    
@constdf_bp.route('/updateconstdf', methods=['POST'])
def constdf_update_csv():
    if check_login_admin():
        return redirect(url_for('admin.main.login'))
    if request.method == 'POST':

        return update_constdf_csv(file_path)
        
        
@constdf_bp.route('/uploadconstdfdelete', methods=['POST'])
def constdf_delete_csv():
    if 'admin_info' not in session:
        return redirect(url_for('admin.main.login'))
    if request.method == 'POST':
        if os.path.exists(file_path):
            os.remove(file_path)

@constdf_bp.route('/upload2openaiconstdf', methods=['POST'])
def constdf_upload_openai():
    if 'admin_info' not in session:
        return redirect(url_for('admin.main.login'))
    if request.method == 'POST':
        constdf_txt = get_constdf_text()
        constdf_path = os.path.join(UPLOAD_FOLDER, 'ConstDf.txt')
        with open(constdf_path, "w") as file:
            file.write(constdf_txt)

        try:
            client = OpenAI(api_key=OPENAI_KEY)
            db = get_db()
            collection = db['settings']
            settings = collection.find_one()
            file_id = settings['constdf_file_id']
            client.files.delete(file_id)
            message_file = client.files.create(
                file=open(constdf_path, "rb"), purpose="assistants"
            )

            query_filter = {'_id' : settings['_id']}
            update_operation = { '$set' : 
                { 
                    'constdf_file_id': message_file.id
                }
            }
            collection.update_one(query_filter, update_operation)
            response = {
                'message' : "Successfully uploaded"
            }
            return jsonify(response), 200
        except Exception as e:
            response = {
                'message' : f"An error occurred: {e}"
            }
            return jsonify(response), 500
        
        

        


