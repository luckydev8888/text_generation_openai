from flask import render_template, request
from app.admin.script.const import get_const, add_const, update_const, delete_const

from . import admin_bp


# constdf page
@admin_bp.route('/')
def home():
    return render_template('constdf.html')

@admin_bp.route('/constdf/get', methods=['POST'])
def constdf_get():
    if request.method == 'POST':
        keyword = request.form.get('search[value]')
        start = request.form.get('start')
        length = request.form.get('length')
        sortColumn = request.form.get('order[0][column]')
        dir = request.form.get('order[0][dir]')
        print(sortColumn)
        return get_const(keyword, int(start), int(length), int(sortColumn), dir)

@admin_bp.route('/constdf/save', methods=['POST'])
def constdf_save():
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

@admin_bp.route('/constdf/delete', methods=['POST'])
def constdf_delete():
    if request.method == 'POST':
        id = request.form.get('id')
        
        return delete_const(id)
