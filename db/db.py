import bson

from flask import current_app, g
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo

from pymongo.errors import DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId
from bson.errors import InvalidId

"""
This file based on MongoDB tutorial at https://www.mongodb.com/compatibility/setting-up-flask-with-mongodb
"""

def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_database", None)

    if db is None:

        db = g._database = PyMongo(current_app).db
    
    return db


# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(get_db)

def get_user_acc_collection():
    """
    returns the userAccount collection
    """
    collection = db['userAccounts']
    return collection