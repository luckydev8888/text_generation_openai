from flask import render_template, request, Blueprint
from app.admin.script.const import get_const, add_const, update_const, delete_const
from app.admin.main_routes import login_required

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
