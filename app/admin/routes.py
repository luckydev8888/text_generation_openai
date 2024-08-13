from flask import render_template, request
from app.admin.script.const import get_const 

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

        return get_const(keyword, start, length)
