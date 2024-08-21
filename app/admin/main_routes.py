from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, make_response
from functools import wraps
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
import json
import os
from dotenv import load_dotenv
from app.mongo import get_db

load_dotenv()

client_id = os.getenv('GOOGLE_CLIENT_ID')
client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
CONF_URL = os.getenv('GOOGLE_CONF_URL')

main_bp = Blueprint('main', __name__)

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

def create_token(email):
    return jwt.encode({
        'email': email,
        'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=8)
    }, current_app.config['FLASK_SECRET_KEY'], algorithm="HS256")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('admin_token')
        if not token:
            return redirect(url_for('admin.main.login'))
        try:
            data = jwt.decode(token, current_app.config['FLASK_SECRET_KEY'], algorithms=["HS256"])
            email = data['email']
            db = get_db()
            users_collection = db['users']
            current_user = users_collection.find_one({'email': data['email'], 'type':'admin'})
            if not current_user:
                raise Exception("User not found")
        except Exception as e:
            return redirect(url_for('admin.main.login'))
        new_token = create_token(email)
        response = make_response(f(current_user, *args, **kwargs))
        response.set_cookie('admin_token', new_token, httponly=True)
        return response
    return decorated

@main_bp.route('/', methods=['GET'])
@login_required
def admin_first(current_user):
    return redirect(url_for('admin.constdf.constdf'))

@main_bp.route('login', methods=['GET'])
def login():
    token = request.cookies.get('admin_token')
    if token:
        data = jwt.decode(token, current_app.config['FLASK_SECRET_KEY'], algorithms=["HS256"])
        db = get_db()
        users_collection = db['users']
        current_user = users_collection.find_one({'email': data['email'], 'type': 'admin'})
        if current_user:
            return redirect(url_for('admin.constdf.constdf'))
    return render_template('admin_login.html')
    
@main_bp.route('login/user', methods=['POST'])
def login_user():
    if request.method == 'POST':
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        db = get_db()
        users_collection = db['users']

        user = users_collection.find_one({'email': email, 'type': 'admin'})
        # if not user or not check_password_hash(user['password'], password):
        #     return jsonify({'message': 'Invalid username or password!'}), 401
        token = jwt.encode({
                'email': email,
                'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1)
            }, current_app.config['FLASK_SECRET_KEY'], algorithm="HS256")
        
        response = jsonify({'message': 'Login successfully'})
        response.set_cookie('admin_token', token, httponly=True)
        return response

@main_bp.route('logout', methods=['GET', 'POST'])
def logout_user():
    response = make_response(redirect(url_for('admin.main.login')))
    response.delete_cookie('admin_token')
    return response

#Routes for login
@main_bp.route('/login/google')
def googleLogin():
    return oauth.google.authorize_redirect(redirect_uri=url_for('admin.main.authorize', _external=True))


@main_bp.route('/google/authorize')
def authorize():
    token = oauth.google.authorize_access_token()
    user_info = json.dump(token, indent=4)
    print(user_info)
    return redirect('/')

