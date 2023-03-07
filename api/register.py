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

        bytePassword = body["password"].encode('UTF-8')

        salt = bcrypt.gensalt()

        password_hash = bcrypt.hashpw(bytePassword, salt)

        user = {"email": body["email"], "password_hash": password_hash, "verified": False}
        
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

        if dbResponse == -1:
            return {"error" : "Verification request associated with this email already exists"}, 400

    
    return {"status" : "success"}, 200
    