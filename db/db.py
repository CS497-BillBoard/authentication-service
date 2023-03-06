from typing import Collection, Dict, List
import bson

from flask import current_app, g
from gridfs import Database
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo

from pymongo.errors import DuplicateKeyError, OperationFailure
from typing import TypedDict
from pymongo.collection import Collection
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
import pymongo

"""
This file has code from the MongoDB tutorial at https://www.mongodb.com/compatibility/setting-up-flask-with-mongodb
"""


def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_database", None)

    if db is None:
        db = MongoClient(current_app.config["MONGO_URI"])

    return db

# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(get_db)

def get_bills_db():
    """
    Method to return instance of the bills database
    """
    return db["billsDatabase"]

def get_user_acc_db():
    return db["accountsDatabase"]

def get_user_acc_collection():
    """
    returns the userAccount collection
    """

    collection: Collection = get_user_acc_db()["userAccounts"]
    return collection


def get_single_user(emails):

    Collection = get_user_acc_collection()

    return Collection.find_one({"email": emails})

def insert_new_user(user):
    Collection = get_user_acc_collection()

    try:
        Collection.insert_one(document=user)
    except pymongo.errors.DuplicateKeyError as e:

        print(e)
        return -1


def get_bills():
    collection: Collection = get_bills_db()["bills"]

    # get all bills from the db more recent than a certain date
    query = {"introduced": {"$gte": "2023-01-01"}}

    bills = collection.find(query)
    return bills


# store new bills in the db
def store_new_bill(bills: List[Dict]):
    collection: Collection = get_bills_db()["bills"]
    inserted_bills = []
    for bill in bills:
        # only insert bills that dont already exist
        if collection.find_one({'legisinfo_id': bill['legisinfo_id']}) == None:
            inserted_bills.append(bill)
    
    if len(inserted_bills) > 0:
        collection.insert_many(inserted_bills)
