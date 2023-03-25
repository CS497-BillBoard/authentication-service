import bson

from flask import current_app, session, g
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
import certifi

"""
This file has code from the MongoDB tutorial at https://www.mongodb.com/compatibility/setting-up-flask-with-mongodb
"""


def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = MongoClient(current_app.config["MONGO_URI"], tlsCAFile=certifi.where())

    return db


# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(get_db)



# ------------------------------------------------
# Get Database Methods
# ------------------------------------------------
def get_bills_db():
    """
    Method to return instance of the bills database
    """
    return db["billsDatabase"]


def get_accounts_db():
    return db["accountsDatabase"]


def get_verification_db():
    return db["verificationDatabase"]



# ------------------------------------------------
# Get Collection Methods
# ------------------------------------------------
def get_user_acc_collection():
    """
    returns the userAccount collection
    """

    collection: Collection = get_accounts_db()["userAccounts"]
    return collection

def get_drivers_license_collection():
    """
    returns the driversLicense collection
    """

    collection: Collection = get_accounts_db()["driversLicense"]
    return collection


def get_verification_requests_collection():
    """
    returns the verificationRequests collection
    """

    collection: Collection = get_verification_db()["verificationRequests"]
    return collection



# ------------------------------------------------
# accountsDatabase.userAccounts Collection Methods
# ------------------------------------------------

def get_single_user(emails):

    Collection = get_user_acc_collection()

    return Collection.find_one({"email": emails})


def insert_new_user(user):
    Collection = get_user_acc_collection()

    try:
        Collection.insert_one(document=user)
    except pymongo.errors.DuplicateKeyError as e:
        logging.error(e)
        return -1


def update_user(email: str, updateFieldsDict: dict):
    collection = get_user_acc_collection()

    try:
        result = collection.update_one({"email": email}, {"$set": updateFieldsDict})

        if result.modified_count != 1:
            logging.info(
                "update_user(): updated unexpected number of modified documents: "
                + str(result.modified_count)
            )
            return -1
    except Exception as e:
        logging.info("update_user(): error updating user: " + str(e))
        return e

    return 1

def update_user_riding(email: str, updatedFields: dict):
    """
    Updates the riding of a user
    """

    userAccountsCollection = get_user_acc_collection()

    try:
        result = userAccountsCollection.update_one({"email": email}, {"$set": updatedFields})

        if result.modified_count != 1:
            logging.info(
                "update_verification_request(): updated unexpected number of modified documents: "
                + str(result.modified_count)
            )
            return -1
    except Exception as e:
        logging.error(e)
        return e



# ------------------------------------------------
# billsDatabase.bills Collection Methods
# ------------------------------------------------
def get_bills():
    logging.info("fetching bills from the db")
    bills_collection: Collection = get_bills_db()["bills"]
    return list(bills_collection.find({}).sort("introduced",pymongo.DESCENDING))  # return most recent bills


def get_one_bill(legisinfo_id):
    logging.info(f"fetching bill with id {legisinfo_id} from the db")
    bills_collection: Collection = get_bills_db()["bills"]
    return bills_collection.find_one({"legisinfo_id": legisinfo_id})


def store_new_bills(bills: list[dict]):
    """
    store all new bills in the db, where they don't exist yet
    """
    logging.info("storing new bills")

    collection: Collection = get_bills_db()["bills"]
    inserted_bills = []
    for bill in bills:
        # only insert bills that dont already exist
        if collection.find_one({"legisinfo_id": bill["legisinfo_id"]}) == None:
            inserted_bills.append(bill)

    if len(inserted_bills) > 0:
        collection.insert_many(inserted_bills)


def recalc_votes(up_total: int, down_total: int, prev: int, new: int):
    """
    Helper function to recalculate the total based on a new vote
    returns: a tuple of total_upvotes, total_downvotes
    """
    if abs(prev) > 1 or abs(new) > 1:
        return ValueError
    up_total -= 1 if prev == 1 else 0
    down_total -= 1 if prev == -1 else 0
    up_total += 1 if new == 1 else 0
    down_total += 1 if new == -1 else 0
    return up_total, down_total


def perform_update(legisinfo_id, user_id, vote=None, comment=None):
    """
    Update a single bill with a user's vote and/or comment
    @param legisinfo_id: the id of the bill
    @param user_id: the id of the user voting/commenting
    @param vote: the vote of the user, if none, then the user hasn't changed their vote
    @param comment: a new comment, if any. this will override the user's last comment
    """
    # TODO
    collection: Collection = get_bills_db()["bills"]
    bill = collection.find_one({"legisinfo_id": legisinfo_id})
    user_id = str(user_id)  # mongodb only accepts strings as keys for documents

    if vote is not None:
        # set user's vote
        previous_vote = bill["votes"][user_id] if user_id in bill["votes"] else 0
        bill["votes"][user_id] = vote
        # update total_upvotes and downvotes
        bill["total_upvotes"], bill["total_downvotes"] = recalc_votes(
            bill["total_upvotes"], bill["total_downvotes"], previous_vote, vote
        )

    if comment is not None:
        # TODO check if the user has already commented, remove existing comment subtract total_comments if they have
        if user_id in bill["comments"]:
            bill["total_comments"] -= 1

        # add new comment, update total_comments
        bill["comments"][user_id] = comment
        bill["total_comments"] += 1

    # update db, TODO maybe asyncrhonously and with update_one instead of replace_one?
    collection.replace_one({"legisinfo_id": legisinfo_id}, bill)
    return bill



# ------------------------------------------------------------
# accountsDatabase.driversLicense Collection Methods
# ------------------------------------------------------------
def get_all_hashed_drivers_licenses():
    """
    Returns a list of all hashed drivers licenses in the database
    """
    collection = get_drivers_license_collection()

    return collection.find({}, {"province_and_drivers_license_hash": 1})


def add_drivers_license_hash(provinceAndDriversLicenseHash: str, expiryYear: str):
    """
    Adds a hashed drivers license to the database
    """
    driversLicenseCollection = get_drivers_license_collection()

    new_document = {
        "province_and_drivers_license_hash": provinceAndDriversLicenseHash,
        "expiry_year": expiryYear
    }

    try:
        logging.info("inserting hashed drivers license")
        driversLicenseCollection.insert_one(document=new_document)
        logging.info("inserted hashed drivers license")

    except pymongo.errors.DuplicateKeyError as e:
        logging.info("add_drivers_license_hash(): duplicate key error: " + str(e))
        return e
    
    except Exception as e:
        logging.info("add_drivers_license_hash(): error adding hashed driver's license: " + str(e))
        return e

    return 1



# ------------------------------------------------------------
# verificationDatabase.verificationRequests Collection Methods
# ------------------------------------------------------------
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
        logging.info("add_verification_request(): error adding verification request: " + str(e))
        return e

    # update "submittedVerificationPhoto" field in accountsDatabase collection
    result = update_user(
        verification_request["email"], {"submittedVerificationPhoto": True}
    )
    if type(result) == Exception:
        logging.error(result)
        return result

    return 1


def remove_verification_request(email: str, isRequestApproved: bool):
    """
    Removes a verification request from the database

    email: the email of the user
    isRequestApproved: whether or not the verification request was approved by BillBoard staff in verification process
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

    if not isRequestApproved:
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
            logging.info(
                "update_verification_request(): updated unexpected number of modified documents: "
                + str(result.modified_count)
            )
            return -1
    except Exception as e:
        logging.error(e)
        return e


def update_verification_status_to_approved(email: str, driversLicenseHash: str, expiryYear: str):
    """
    Updates the verification status of a user to approved
    """
    userAccountsCollection = get_user_acc_collection()


    # store the drivers license hash *separately* in the driversLicense collection
    result = add_drivers_license_hash(driversLicenseHash, expiryYear)
    if type(result) == Exception:
        logging.error(result)
        return result

    # update the user's verification status to approved and store the drivers license hash
    try:
        result = userAccountsCollection.update_one(
            {"email": email},
            {"$set": {"verified": True, "expiry_year": expiryYear}},
        )

        if result.modified_count != 1:
            logging.info(
                "update_verification_status_to_approved(): updated unexpected number of modified documents: "
                + str(result.modified_count)
            )

    except Exception as e:
        logging.error(e)
        return e

    # remove the verification request from the db
    result = remove_verification_request(email, True)

    if type(result) == Exception:
        logging.error(result)

    return 1

