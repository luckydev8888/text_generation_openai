from flask import render_template, Blueprint, current_app, request, redirect, url_for, make_response, jsonify, session
import jwt
import datetime
from functools import wraps
from app.mongo import get_db

users_bp = Blueprint('users', __name__)

def create_user_token(email):
    return jwt.encode({
        'email': email,
        'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=8)
    }, current_app.config['FLASK_SECRET_KEY'], algorithm="HS256")

def user_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('user_token')
        if not token:
            return redirect(url_for('user.users.login_page'))
        try:
            data = jwt.decode(token, current_app.config['FLASK_SECRET_KEY'], algorithms=["HS256"])
            email = data['email']
            db = get_db()
            users_collection = db['users']
            current_user = users_collection.find_one({'email': data['email'], 'type': 'user'})
            if not current_user:
                raise Exception("User not found")
        except Exception as e:
            return redirect(url_for('user.users.login_page'))
        new_token = create_user_token(email)
        response = make_response(f(current_user, *args, **kwargs))
        response.set_cookie('user_token', new_token, httponly=True)
        session['user_info'] = current_user['email']
        return response
    return decorated

@users_bp.route('/')
def home():
    token = request.cookies.get('user_token')
    if not token:
        current_user = {}
    else:
        try:
            data = jwt.decode(token, current_app.config['FLASK_SECRET_KEY'], algorithms=["HS256"])
            email = data['email']
            db = get_db()
            users_collection = db['users']
            current_user = users_collection.find_one({'email': email, 'type': 'user'})
        except Exception as e:
            current_user = {}
    return render_template('landing.html', user=current_user)

@users_bp.route('/login')
def login_page():
    token = request.cookies.get('user_token')
    if token:
        try:
            data = jwt.decode(token, current_app.config['FLASK_SECRET_KEY'], algorithms=["HS256"])
            db = get_db()
            users_collection = db['users']
            current_user = users_collection.find_one({'email': data['email'], 'type': 'user'})

            if current_user:
                session['user_info'] = current_user['email']
                return redirect(url_for('user.users.home'))
            else:
                raise Exception("User not found")
        except Exception as e:
            return render_template('user_login.html')
    return render_template('user_login.html')

@users_bp.route('login/users', methods=['POST'])
def login_user():
    if request.method == 'POST':
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        db = get_db()
        users_collection = db['users']

        user = users_collection.find_one({'email': email, 'type': 'user'})
        # if not user or not check_password_hash(user['password'], password):
        #     return jsonify({'message': 'Invalid username or password!'}), 401
        token = jwt.encode({
                'email': email,
                'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1)
            }, current_app.config['FLASK_SECRET_KEY'], algorithm="HS256")
        
        response = jsonify({'message': 'Login successfully'})
        response.set_cookie('user_token', token, httponly=True)
        return response
    
@users_bp.route('logout', methods=['GET', 'POST'])
def logout_user():
    response = make_response(redirect(url_for('user.users.login_page')))
    response.delete_cookie('user_token')
    session.pop('user_info', None)
    return response