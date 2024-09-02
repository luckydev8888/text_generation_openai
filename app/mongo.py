from pymongo import MongoClient
from flask import current_app

def get_db():
    client = MongoClient(current_app.config['MONGO_URI'])
    return client.get_default_database()

def get_user_info(email, type):
    db = get_db()
    collection = db['users']
    try:
        user = collection.find_one({'email': email, 'type': type})
        return user
    except Exception as e:
        return "Something went wrong"
