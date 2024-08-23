from flask import render_template, request, Blueprint, jsonify
from app.admin.script.const import get_const, add_const, update_const, delete_const
from app.admin.main_routes import login_required
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import csv
from app.mongo import get_db

load_dotenv()
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
CONSTDF_ID = os.getenv("CONSTDF_ID")
file_path = ""


constdf_bp = Blueprint('constdf', __name__, url_prefix="constdf")
# constdf page
@constdf_bp.route('/')
@login_required
def constdf(current_user):
    return render_template('constdf.html', user=current_user)


@constdf_bp.route('/get', methods=['POST'])
@login_required
def constdf_get(current_user):
    if request.method == 'POST':
        keyword = request.form.get('search[value]')
        start = request.form.get('start')
        length = request.form.get('length')
        sortColumn = request.form.get('order[0][column]')
        dir = request.form.get('order[0][dir]')
        return get_const(keyword, int(start), int(length), int(sortColumn), dir)

@constdf_bp.route('/save', methods=['POST'])
@login_required
def constdf_save(current_user):
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
@login_required
def constdf_delete(current_user):
    if request.method == 'POST':
        id = request.form.get('id')
        
        return delete_const(id)
    
@constdf_bp.route('/uploadconstdfcsv', methods=['POST'])
@login_required
def constdf_upload_constdf_csv(current_user):
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
@login_required
def constdf_update_constdf_csv(current_user):
    if request.method == 'POST':
        constdf_json = []
        try:
            with open(file_path, newline='') as csvfile:
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
            db = get_db()
            constdf_collection = db['constdf']
            constdf_collection.delete_many({})
            for each in constdf_json:
                constdf_collection.insert_one(each)
            response = {
                'message' : "successfully updated"
            }
            return jsonify(response), 200
        except Exception as e:
            response = {
                'message' : "error"
            }
            return jsonify(response), 500
        
@constdf_bp.route('/uploadconstdfdelete', methods=['POST'])
@login_required
def constdf_delete_constdf_csv(current_user):
    if request.method == 'POST':
        if os.path.exists(file_path):
            os.remove(file_path)
