from typing import Collection
import bson

from flask import current_app, g
from gridfs import Database
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo

from pymongo.errors import DuplicateKeyError, OperationFailure
from typing import TypedDict
from pymongo.collection import Collection
from bson.objectid import ObjectId
from bson.errors import InvalidId

"""
This file has code from the MongoDB tutorial at https://www.mongodb.com/compatibility/setting-up-flask-with-mongodb
"""

def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = PyMongo(current_app).db
    
    return db

def get_bills_db():
    """
    Method to return instance of the bills database
    """
    db_bills = getattr(g, "_databaseBills", None)
    if db_bills is None:
        db_bills = g._databaseBills = PyMongo(current_app, uri="mongodb+srv://admin:BillBoard2023@billboardcluster.flaylfh.mongodb.net/billsDatabase?retryWrites=true&w=majority").db

    return db_bills
    
# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(get_db)
db_bills = LocalProxy(get_bills_db)

def get_user_acc_collection():
    """
    returns the userAccount collection
    """
    collection: Collection = db['userAccounts']
    return collection


def get_bills():
    collection: Collection = db_bills['bills']
    
    # get all bills from the db more recent than a certain date
    query = {
        "introduced": {"$gte": "2023-01-01"}
    }
    
    bills = collection.find(query)
    return bills

# store new bills in the db
def store_new_bill():
    new_bill = {
        "introduced": "2023-02-16",
        "legisinfo_id": 12237277,
        "name": {
        "en": "An Act to amend the Criminal Code, to make consequential amendments to other Acts and to repeal a regulation (miscarriage of justice reviews)",
        "fr": "Loi modifiant le Code criminel et d'autres lois en cons\u00e9quence et abrogeant un r\u00e8glement (examen des erreurs judiciaires)"
        },
        "number": "C-40",
        "session": "44-1",
        "url": "/bills/44-1/C-40/"
    }
    
    collection: Collection = db_bills['bills']
    collection.insert_one(new_bill)
