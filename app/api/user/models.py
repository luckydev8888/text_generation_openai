
import app.mongo as mongo

def get_users():
    db = mongo.get_db()
    users_collection = db['users']
    result = users_collection.find_one({'name' : 'almart'})
    print(result)
    return result