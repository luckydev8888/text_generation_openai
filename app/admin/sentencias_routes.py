from flask import render_template, request, Blueprint
from app.admin.script.sentencias import get_sentencias, get_sentencia, save_sentencias, delete_sentencias, texto_scrap
from app.admin.main_routes import login_required

sentencias_bp = Blueprint('sentencias', __name__, url_prefix="sentencias")
# sentencias page
@sentencias_bp.route('/')
@login_required
def sentencias(current_user):
    return render_template('sentencias.html', user=current_user)


@sentencias_bp.route('/get', methods=['POST'])
@login_required
def sentencias_get(current_user):
    if request.method == 'POST':
        keyword = request.form.get('search[value]')
        start = request.form.get('start')
        length = request.form.get('length')
        sortColumn = request.form.get('order[0][column]')
        dir = request.form.get('order[0][dir]')
        return get_sentencias(keyword, int(start), int(length), int(sortColumn), dir)

@sentencias_bp.route('/get/sentencia', methods=['POST'])
@login_required
def sentencia_get(current_user):
    if request.method == 'POST':
        id = request.form.get('id')
        return get_sentencia(id)


@sentencias_bp.route('/save', methods=['POST'])
@login_required
def sentencias_save(current_user):
    if request.method == 'POST':
        save_data = {
            "id": request.form.get('id'),
            "providencia": request.form.get('providencia'),
            "tipo": request.form.get('tipo'),
            "ano": request.form.get('ano'),
            "fecha_sentencia": request.form.get('fecha_sentencia'),
            "tema": request.form.get('tema'),
            "magistrado": request.form.get('magistrado'),
            "fecha_publicada": request.form.get('fecha_publicada'),
            "expediente": request.form.get('expediente'),
            "url": request.form.get('url'),
            "texto": request.form.get('texto'),
        }

        return save_sentencias(save_data)

@sentencias_bp.route('/delete', methods=['POST'])
@login_required
def sentencias_delete(current_user):
    if request.method == 'POST':
        id = request.form.get('id')
        
        return delete_sentencias(id)

@sentencias_bp.route('/scrap', methods=['POST'])
@login_required
def sentencias_texto_scrap(current_user):
    if request.method == 'POST':
        url = request.form.get('url')
        
        return texto_scrap(url)
