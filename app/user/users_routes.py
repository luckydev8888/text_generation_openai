from flask import render_template, Blueprint, current_app, request, redirect, url_for, make_response, jsonify, session
import jwt
import datetime
from functools import wraps
from flask_bcrypt import Bcrypt
from app.mongo import get_db
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os

users_bp = Blueprint('users', __name__)

load_dotenv()

client_id = os.getenv('GOOGLE_CLIENT_ID')
client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
CONF_URL = os.getenv('GOOGLE_CONF_URL')

oauth = OAuth(current_app)
google = oauth.register(
    'google',
    client_id=client_id,
    client_secret=client_secret,
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)


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
        bcrypt = Bcrypt(current_app)
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        db = get_db()
        users_collection = db['users']

        user = users_collection.find_one({'email': email, 'type': 'user'})
        if not user or not bcrypt.check_password_hash(user['pwd'], pwd):
            return jsonify({'message': 'Invalid username or password!'}), 401
        token = jwt.encode({
                'email': email,
                'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1)
            }, current_app.config['FLASK_SECRET_KEY'], algorithm="HS256")
        
        response = jsonify({'message': 'Login successfully'})
        response.set_cookie('user_token', token, httponly=True)
        session['user_info'] = user['email']
        return response
    
@users_bp.route('logout', methods=['GET', 'POST'])
def logout_user():
    response = make_response(redirect(url_for('user.users.login_page')))
    response.delete_cookie('user_token')
    session.pop('user_info', None)
    return response

#Routes for login
@users_bp.route('/login/google')
def userGoogleLogin():
    return oauth.google.authorize_redirect(redirect_uri=url_for('user.users.userAuthorize', _external=True))


@users_bp.route('/google/authorize')
def userAuthorize():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        print(user_info)
        db = get_db()
        collection = db['users']
        current_user = collection.find_one({'email': user_info['email'], 'type': 'user'})
        print(current_user)
        if not current_user:
            collection.insert_one({
                'email': user_info['email'],
                'type': 'user',
                'given_name': user_info['given_name'],
                'family_name': user_info['family_name'],
                'picture': user_info['picture'],
                'createdAt': datetime.datetime.now()
            })
        new_token = create_user_token(user_info['email'])
        response = make_response(redirect(url_for('user.users.home')))
        response.set_cookie('user_token', new_token, httponly=True)
        session['user_info'] = current_user['email']
        return response
    except Exception as e:
        return redirect('/')
    
@users_bp.route('/register')
def userRegisterPage():
    return render_template('user_register.html')

@users_bp.route('register/users', methods=['POST'])
def register_user():
    if request.method == 'POST':
        bcrypt = Bcrypt(current_app)
        givenName = request.form.get('givenName')
        familyName = request.form.get('familyName')
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        db = get_db()
        users_collection = db['users']

        user = users_collection.find_one({'email': email, 'type': 'user'})
        if user:
            return jsonify({'message': 'The email exists'}), 400
        users_collection.insert_one({
            'email': email,
            'type': 'user',
            'pwd': bcrypt.generate_password_hash(pwd),
            'given_name': givenName,
            'family_name': familyName,
            'createdAt': datetime.datetime.now()
        })
        
        
        return jsonify({'message': 'Successfully registered'}), 200