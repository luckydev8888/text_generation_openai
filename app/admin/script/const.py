from app.mongo import get_db

def get_const(keyword, start, length):
    db = get_db()
    total_list = list(db['constdf'].find())
    recordsTotal = total_list.count
    filter_list = []
    for each in total_list:
        if keyword == '':
            filter_list
        each[ar]

    response_data = {
        "recordsTotal": 0,
        "recordsFiltered": 0,
        "data": [
        ]
    }
    return response_data

def save_const(_id, type, number, text):

    return