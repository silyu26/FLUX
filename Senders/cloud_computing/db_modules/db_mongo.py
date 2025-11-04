from pymongo import MongoClient

def init_db(uri, db_name, collection):
    client = MongoClient(uri)
    db = client[db_name]
    return db[collection]

def save_metadata(collection, data):
    collection.insert_one(data)
