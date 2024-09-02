from pymongo import MongoClient
from flask import current_app
from flask_jwt_extended import JWTManager
from itsdangerous import URLSafeTimedSerializer

import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    client = MongoClient(current_app.config['MONGO_URI'])
    return client.get_default_database()

jwt = JWTManager()

s = URLSafeTimedSerializer(os.getenv('APP_SECRET_KEY'))