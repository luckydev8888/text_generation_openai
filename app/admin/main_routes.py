from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, make_response
from functools import wraps
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.mongo import get_db

main_bp = Blueprint('main', __name__)

def create_token(email):
    return jwt.encode({
        'email': email,
        'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=1)
    }, current_app.config['FLASK_SECRET_KEY'], algorithm="HS256")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('admin.main.login'))
        try:
            data = jwt.decode(token, current_app.config['FLASK_SECRET_KEY'], algorithms=["HS256"])
            email = data['email']
            db = get_db()
            users_collection = db['users']
            current_user = users_collection.find_one({'email': data['email']})
            if not current_user:
                raise Exception("User not found")
        except Exception as e:
            return redirect(url_for('admin.main.login'))
        new_token = create_token(email)
        response = make_response(f(current_user, *args, **kwargs))
        response.set_cookie('token', new_token, httponly=True)
        return response
    return decorated

@main_bp.route('login', methods=['GET'])
def login():
    return render_template('login.html')
    
@main_bp.route('login/user', methods=['POST'])
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

@main_bp.route('logout', methods=['GET', 'POST'])
@login_required
def logout_user(current_user):
    response = make_response(redirect(url_for('admin.main.login')))
    response.delete_cookie('token')
    return response

