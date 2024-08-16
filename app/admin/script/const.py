from flask import jsonify
from bson import ObjectId
from app.mongo import get_db

field = ['id', 'articulo', 'texto', 'tutela']

def get_const(keyword, start, length, sortColumn, dir):
    db = get_db()
    total_list = list(db['constdf'].find())
    recordsTotal = len(total_list)
    filter_list = []
    for each in total_list:
        if keyword == '':
            filter_list.append(each)
        else:
            if keyword in each['articulo'] or keyword in each['texto'] or keyword in each['tutela'] or keyword in str(each['num']):
                filter_list.append(each)
    recordsFiltered = len(filter_list)
    if recordsFiltered != 0:
        if sortColumn == 1:
            if dir == 'asc':
                filter_list.sort(key=lambda x: (x['articulo'], x['num']), reverse=True)
            else:
                filter_list.sort(key=lambda x: (x['articulo'], x['num']))
        else:
            if dir == 'asc':
                filter_list.sort(key=lambda x: x[field[sortColumn]], reverse=True)
            else:
                filter_list.sort(key=lambda x: x[field[sortColumn]])
        return_data = []
        number = 0
        for n in range(start, start + length):
            if n >= recordsTotal: break
            number += 1
            return_data.append({
                'order': number,
                '_id': str(filter_list[n]['_id']),
                'texto': str(filter_list[n]['texto']),
                'articulo': f"{filter_list[n]['articulo']} {filter_list[n]['num']}",
                'tutela': str(filter_list[n]['tutela']),
            })
        response_data = {
            "recordsTotal": recordsTotal,
            "recordsFiltered": recordsFiltered,
            "data": return_data
        }
        return response_data
    else:
        response_data = {
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": []
        }
        return response_data

def add_const(type, number, texto, tutela):
    db = get_db()
    try:
        db['constdf'].insert_one({
            'articulo': type,
            'num': int(number),
            'texto': texto,
            'tutela': tutela
        })
        return jsonify({'message': 'Successfully added'}), 200
    except:
        return jsonify({'message': 'Error occur'}), 500

def update_const(id, type, number, texto, tutela):
    db = get_db()
    constdb = db['constdf']
    try:
        query_filter = {'_id' : ObjectId(id)}
        update_operation = { '$set' : 
            { 
                'articulo': type,
                'num': int(number),
                'texto': texto,
                'tutela': tutela
            }
        }
        constdb.update_one(query_filter, update_operation)
        return jsonify({'message': 'Successfully update'}), 200
    except :
        # Code that runs if an exception occurs
        return jsonify({'message': 'Error occur'}), 500

def delete_const(id):
    db = get_db()
    constdb = db['constdf']
    try:
        query_filter = {'_id' : ObjectId(id)}
        constdb.delete_many(query_filter)
        return jsonify({'message': 'Successfully deleted'}), 200
    except :
        # Code that runs if an exception occurs
        return jsonify({'message': 'Error occur'}), 500