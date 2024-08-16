from pymongo import MongoClient
from flask import current_app
from flask_jwt_extended import JWTManager

def get_db():
    client = MongoClient(current_app.config['MONGO_URI'])
    return client.get_default_database()

jwt = JWTManager()
