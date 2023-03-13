from typing import Collection
import bson

from flask import current_app, g
from gridfs import Database
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo
import logging
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
        db = g._database = MongoClient(current_app.config["MONGO_URI"])

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


def get_verification_db():
    return db["verificationDatabase"]


def get_user_acc_collection():
    """
    returns the userAccount collection
    """

    collection: Collection = get_user_acc_db()["userAccounts"]
    return collection


def get_verification_requests_collection():
    """
    returns the verificationRequests collection
    """

    collection: Collection = get_verification_db()["verificationRequests"]
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

def update_user(email: str, updateFieldsDict: dict):
    collection = get_user_acc_collection()

    try:
        result = collection.update_one({"email": email}, {"$set": updateFieldsDict})

        if result.modified_count != 1:
            logging.info("update_user(): updated unexpected number of modified documents: " + str(result.modified_count))
            return -1
    except Exception as e:
        logging.info("update_user(): error updating user: " + str(e))
        return e
    
    return 1


def get_bills():
    # TODO call this after setup
    bills_collection = getattr(g, "_db_bills", None)
    
    # fetch bills from db if we havent already
    if bills_collection is None:
        bills_collection = g._db_bills = get_bills_db()["bills"]
    
    query = {"introduced": {"$gte": "2023-01-01"}}
    bills = bills_collection.find(query)
    
    print("BILLS::: ", list(bills))
    
    return dict(bills)

# store new bills in the db
def store_new_bills(bills: list[dict]):
    collection: Collection = get_bills_db()["bills"]
    inserted_bills = []
    for bill in bills:
        # only insert bills that dont already exist
        if collection.find_one({"legisinfo_id": bill["legisinfo_id"]}) == None:
            inserted_bills.append(bill)

    if len(inserted_bills) > 0:
        collection.insert_many(inserted_bills)


def get_single_verification_request(email):

    Collection = get_verification_requests_collection()

    return Collection.find_one({"email": email})


def get_all_verification_requests():
    Collection = get_verification_requests_collection()

    requests = []

    cur = Collection.find({})
    for request in cur:
        requests.append(request)

    return requests


def add_verification_request(verification_request: dict):
    """
    Adds a verification request to the database
    """
    # get the verificationRequests collection
    verificationRequestsCollection = get_verification_requests_collection()
    
    # insert the verification request into the db
    try:
        logging.info("inserting verification request")
        verificationRequestsCollection.insert_one(document=verification_request)
        logging.info("inserted verification request")
    except pymongo.errors.DuplicateKeyError as e:
        print(e)
        return e
    
    # update "submittedVerificationPhoto" field in accountsDatabase collection
    result = update_user(verification_request["email"], {"submittedVerificationPhoto": True})
    if type(result) == Exception:
        logging.error(result)
        return result

    return 1


def remove_verification_request(email: str):
    """
    Removes a verification request from the database
    """
    # get the verificationRequests collection
    collection = get_verification_requests_collection()

    # remove the verification request from the db
    try:
        result = collection.delete_one({"email": email})

        if result.deleted_count == 0:
            logging.info(
                "remove_verification_request(): no verification request found for email: "
                + email
            )
            return -1
        elif result.deleted_count > 1:
            logging.info(
                "remove_verification_request(): multiple verification requests found for email: "
                + email
            )
            return -2

    except Exception as e:
        logging.error(e)
        return e
    
    # update "submittedVerificationPhoto" field in accountsDatabase collection
    result = update_user(email, {"submittedVerificationPhoto": False})
    if type(result) == Exception:
        logging.error(result)
        return result
        
    return 1

def update_verification_request(email: str, updatedFields: dict):
    """
    Updates verification request
    """
    # get the verificationRequests collection
    collection = get_verification_requests_collection()
    
    # update the user's verification status to approved and store the drivers license hash
    try:
        result = collection.update_one({"email": email}, {"$set": updatedFields})
        
        if result.modified_count != 1:
            logging.info("update_verification_request(): updated unexpected number of modified documents: " + str(result.modified_count))
            return -1
    except Exception as e:
        logging.error(e)
        return e

def update_verification_status_to_approved(email: str, drivers_license_hash: str):
    """
    Updates the verification status of a user to approved
    """
    # get the userAccounts collection
    userAccountsCollection = get_user_acc_collection()

    # update the user's verification status to approved and store the drivers license hash
    try:
        result = userAccountsCollection.update_one(
            {"email": email},
            {"$set": {"verified": True, "drivers_license_hash": drivers_license_hash}},
        )

        if result.modified_count != 1:
            logging.info("update_verification_status_to_approved(): updated unexpected number of modified documents: " + str(result.modified_count))
            return -1
    except Exception as e:
        logging.error(e)
        return e

    # remove the verification request from the db
    result = remove_verification_request(email)

    if type(result) == Exception:
        logging.error(result)

    return 1
