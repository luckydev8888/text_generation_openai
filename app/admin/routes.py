from flask import render_template, request, redirect, url_for, jsonify, current_app, make_response
from functools import wraps
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.admin.script.const import get_const, add_const, update_const, delete_const
from app.mongo import get_db

from . import admin_bp

def create_token(email):
    return jwt.encode({
        'email': email,
        'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=10)
    }, current_app.config['FLASK_SECRET_KEY'], algorithm="HS256")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('admin.login'))
        try:
            data = jwt.decode(token, current_app.config['FLASK_SECRET_KEY'], algorithms=["HS256"])
            email = data['email']
            db = get_db()
            users_collection = db['users']
            current_user = users_collection.find_one({'email': data['email']})
            if not current_user:
                raise Exception("User not found")
        except Exception as e:
            return redirect(url_for('admin.login'))
        new_token = create_token(email)
        response = make_response(f(current_user, *args, **kwargs))
        response.set_cookie('token', token, httponly=True)
        return response
    return decorated

@admin_bp.route('login', methods=['GET'])
def login():
    return render_template('login.html')
    
@admin_bp.route('login/user', methods=['POST'])
def login_user():
    if request.method == 'POST':
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        db = get_db()
        users_collection = db['users']

        user = users_collection.find_one({'email': email})
        # if not user or not check_password_hash(user['password'], password):
        #     return jsonify({'message': 'Invalid username or password!'}), 401
        token = jwt.encode({
                'email': email,
                'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1)
            }, current_app.config['FLASK_SECRET_KEY'], algorithm="HS256")
        
        response = jsonify({'message': 'Login successfully'})
        response.set_cookie('token', token, httponly=True)
        return response

@admin_bp.route('logout', methods=['GET', 'POST'])
@login_required
def logout_user(current_user):
    response = make_response(redirect(url_for('admin.login')))
    response.delete_cookie('token')
    return response


# constdf page
@admin_bp.route('/constdf')
@login_required
def constdf(current_user):
    return render_template('constdf.html', user=current_user)

@admin_bp.route('/constdf/get', methods=['POST'])
@login_required
def constdf_get(current_user):
    if request.method == 'POST':
        keyword = request.form.get('search[value]')
        start = request.form.get('start')
        length = request.form.get('length')
        sortColumn = request.form.get('order[0][column]')
        dir = request.form.get('order[0][dir]')
        print(sortColumn)
        return get_const(keyword, int(start), int(length), int(sortColumn), dir)

@admin_bp.route('/constdf/save', methods=['POST'])
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

@admin_bp.route('/constdf/delete', methods=['POST'])
@login_required
def constdf_delete(current_user):
    if request.method == 'POST':
        id = request.form.get('id')
        
        return delete_const(id)
