from flask import Flask, Blueprint, render_template, abort, jsonify, request, Response
import bcrypt
import requests
import logging
from db import db
register_service = Blueprint("register_page", __name__, template_folder="templates")


@register_service.route("/sign-up", methods=["GET", "POST"])
def signUp():
    logging.info("(register.py) /sign-up endpoint hit")

    if request.method == "POST":
        body = request.get_json()

        bytePassword = body["password"].encode("UTF-8")

        salt = bcrypt.gensalt()

        password_hash = bcrypt.hashpw(bytePassword, salt)

        user = {
            "email": body["email"],
            "password_hash": password_hash,
            "verified": False,
            "submittedVerificationPhoto": False,
        }

        # validate form data
        # TODO: check if email is valid and not duplicate
        # TODO: check if password is valid (not empty, etc.)
        
        insert_result = db.insert_new_user(user)

        if insert_result == -1:
            return {"error" : "Email already registered to an account"}, 400

    return "hi"

@register_service.route("/verification-request", methods = ["GET", "POST"])
def verificationRequest():
    logging.info("(register.py) /verification-request endpoint hit")

    if request.method == "POST":
        body = request.get_json()

        if body.get("email") is None or body.get("email") == "":
            return {"error" : "No email provided"}, 400
        
        # check if user exists
        if db.get_single_user(body["email"]) is None:
            return {"error" : "No account found with email"}, 400

        if body.get("driversLicenseImage") is None or body.get("driversLicenseImage") == "":
            return {"error" : "No drivers license provided"}, 400
        
        if body.get("selfieImage") is None or body.get("selfieImage") == "": 
            return {"error" : "No user photo provided"}, 400
        
        verification_request = {
            "email": body["email"],
            "drivers_license_image": body["driversLicenseImage"],
            "selfie_image": body["selfieImage"]
        }

        print("VERIFICATION REQUEST: ", verification_request)
        dbResponse = db.add_verification_request(verification_request)

        #TODO: need to add policy to db that documents that still exist after 30 days are deleted (to ensure user data privacy)

        if type(dbResponse) == Exception:
            return {"error" : "Verification request associated with this email already exists: " + str(dbResponse)}, 400

    
    return {"status" : "success"}, 200

@register_service.route("/update-verification-status", methods = ["POST"])
def updateVerificationStatus():
    """
    sample request body (approved request):
    {
        "email": "test@test.com",
        "status": true
        "driversLicenseNumber": "123456789"
    }

    sample request body (rejected request):
    {
        "email": "test@test.com",
        "status": false
    }
    
    """
    logging.info("(register.py) /update-verification-status endpoint hit")

    if request.method == "POST":
        body = request.get_json()

        if body.get("email") is None or body.get("email") == "":
            return {"error" : "No email provided"}, 400
        
        # check if user exists
        if db.get_single_user(body["email"]) is None:
            return {"error" : "No account found with email"}, 400
        
        # check if verification request exists
        if db.get_single_verification_request(body["email"]) is None:
            return {"error" : "No verification request found with email"}, 400

        if body.get("status") is None or body.get("status") == "":
            return {"error" : "No status provided"}, 400

        if body.get("status") == False:
            result = db.remove_verification_request(body["email"])

            if type(result) == Exception:
                return {"error" : "Error removing verification request from db: " + str(result)}, 400
            return {"status" : "success", "msg": "rejected verification - removed request from db"}, 200

        if body.get("driversLicenseNumber") is None or body.get("driversLicenseNumber") == "":
            return {"error" : "No drivers license number provided"}, 400
        
        email = body["email"]


        # get driver's license number and salt+hash it
        byteDriversLicenseNumber = body["driversLicenseNumber"].encode('UTF-8')
        salt = bcrypt.gensalt()
        driversLicenseNumberHash = bcrypt.hashpw(byteDriversLicenseNumber, salt)

        db.update_verification_status_to_approved(email, driversLicenseNumberHash)

    return {"status" : "success"}, 200
    
@register_service.route("/verification-request/drivers-license-info", methods = ["POST"])
def driversLicenseInfo():
    logging.info("(register.py) /verification-request/drivers-license-info endpoint hit")

    if request.method == "POST":
        body = request.get_json()

        db.update_verification_request(body["email"], {"mongo-trigger": True})
    
    return {"status" : "success"}, 200
