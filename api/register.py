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
            "set_riding": False,
        }

        # validate form data
        # TODO: check if email is valid and not duplicate
        # TODO: check if password is valid (not empty, etc.)

        insert_result = db.insert_new_user(user)

        if insert_result == -1:
            return {"error": "Email already registered to an account"}, 400

        return {"status": "success"}, 200


@register_service.route("/set-riding", methods=["POST"])
def setRidingRequest():
    logging.info("(register.py) /set-riding endpoint hit")

    if request.method == "POST":
        body = request.get_json()
        print(body)

        if body.get("email") is None or body.get("email") == "":
            return {"error": "No email provided"}, 400

        # check if user exists
        if db.get_single_user(body.get("email")) is None:
            return {"error": "No account found with email"}, 400
        
        if body.get("constituencyName") is None or body.get("constituencyName") == "":
            return {"error": "No constituency name provided"}

        riding_information = {
            "set_riding": True,
            "constituency_name": body["constituencyName"],
            "parliament_member_name": body["parliamentMemberName"],
        }

        dbResponse = db.update_user_riding(body.get("email"), riding_information)

        if type(dbResponse) == Exception:
            return {"error": str(dbResponse)}, 400

        return {"status": "success"}, 200


@register_service.route("/verification-request", methods=["GET", "POST"])
def verificationRequest():
    logging.info("(register.py) /verification-request endpoint hit")

    if request.method == "POST":
        body = request.get_json()

        if body.get("email") is None or body.get("email") == "":
            return {"error": "No email provided"}, 400

        # check if user exists
        if db.get_single_user(body["email"]) is None:
            return {"error": "No account found with email"}, 400

        if (
            body.get("driversLicenseImage") is None
            or body.get("driversLicenseImage") == ""
        ):
            return {"error": "No drivers license provided"}, 400

        if (
            body.get("driversLicenseImage") is None
            or body.get("driversLicenseImage") == ""
        ):
            return {"error": "No drivers license provided"}, 400

        if body.get("selfieImage") is None or body.get("selfieImage") == "":
            return {"error": "No user photo provided"}, 400

        verification_request = {
            "email": body["email"],
            "drivers_license_image": body["driversLicenseImage"],
            "selfie_image": body["selfieImage"],
        }

        print("VERIFICATION REQUEST: ", verification_request)
        dbResponse = db.add_verification_request(verification_request)

        # TODO: need to add policy to db that documents that still exist after 30 days are deleted (to ensure user data privacy)

        if type(dbResponse) == Exception:
            return {
                "error": "Verification request associated with this email already exists: "
                + str(dbResponse)
            }, 400

    if request.method == "GET":
        return {"data": db.get_all_verification_requests()}, 200

    return {"status": "success"}, 200


@register_service.route("/update-verification-status", methods=["POST"])
def updateVerificationStatus():
    """
    sample request body (approved request):
    {
        "email": "test@test.com",
        "status": true
        "driversLicenseNumber": "123456789",
        "province": "Ontario",
        "expiryDate": "2020-12-31",
        "postalCode": "M5H 2N2"
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
            return {"error": "No email provided"}, 400

        # check if user exists
        if db.get_single_user(body["email"]) is None:
            return {"error": "No account found with email"}, 400

        # check if verification request exists
        if db.get_single_verification_request(body["email"]) is None:
            return {"error": "No verification request found with email"}, 400

        if body.get("status") is None or body.get("status") == "":
            return {"error": "No status provided"}, 400

        if body.get("status") == False:
            result = db.remove_verification_request(body["email"])

            if type(result) == Exception:
                return {
                    "error": "Error removing verification request from db: "
                    + str(result)
                }, 400
            return {
                "status": "success",
                "msg": "rejected verification - removed request from db",
            }, 200

        if (
            body.get("driversLicenseNumber") is None
            or body.get("driversLicenseNumber") == ""
        ):
            return {"error": "No drivers license number provided"}, 400

        if (
            body.get("province") is None
            or body.get("province") == ""
        ):
            return {"error": "No province provided"}, 400
        
        if (
            body.get("expiryDate") is None
            or body.get("expiryDate") == ""
        ):
            return {"error": "No expiry date provided"}, 400
        
        if (
            body.get("postalCode") is None
            or body.get("postalCode") == ""
        ):
            return {"error": "No postal code provided"}, 400

        email = body["email"]
        province = body["province"]
        expiryDate = body["expiryDate"]
        postalCode = body["postalCode"]

        # -------------------------------------------------------
        # TODO: include province in drivers license number hash?
        # -------------------------------------------------------

        # get driver's license number and salt+hash it
        byteDriversLicenseNumber = body["driversLicenseNumber"].encode("UTF-8")
        salt = bcrypt.gensalt()
        driversLicenseNumberHash = bcrypt.hashpw(byteDriversLicenseNumber, salt)

        db.update_verification_status_to_approved(email, driversLicenseNumberHash, expiryDate, postalCode)

    return {"status": "success"}, 200


@register_service.route("/verification-request/drivers-license-info", methods=["POST"])
def driversLicenseInfo():
    """
    sample request body:
    {
      "email": "test@test.com",
      "driversLicenseBase64": "base64 string"
    }
    """
    logging.info(
        "(register.py) /verification-request/drivers-license-info endpoint hit"
    )

    AZURE_CUSTOM_AI_BUILDER_MODEL_URL = "https://prod-16.canadacentral.logic.azure.com:443/workflows/e1f01f174d674c23b55390ae3d620421/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=WpPWTMZJz05Q6Yc19jabyjtYY3Q6zXLrbBXgEAtvHps"

    if request.method == "POST":
        body = request.get_json()

        if body.get("email") is None or body.get("email") == "":
            return {"error": "No email provided"}, 400

        if (
            body.get("driversLicenseBase64") is None
            or body.get("driversLicenseBase64") == ""
        ):
            return {"error": "No drivers license image provided"}, 400

        request_body = {
            "emailAddress": body["email"],
            "driversLicenseBase64": body["driversLicenseBase64"],
        }

        # TODO: remove the line below once testing of this endpoint is complete
        db.update_verification_request(body["email"], {"mongo-trigger": True})

        response = requests.post(AZURE_CUSTOM_AI_BUILDER_MODEL_URL, json=request_body)

        if response.status_code != 200:
            return {
                "error": "Error calling custom AI builder model: "
                + str(response.status_code)
            }, 400

        response_body = response.json()

        response_body.pop("emailAddress")
        predictedDriversLicenseInfo = {"predicted-drivers-license-info": response_body}

        db.update_verification_request(body["email"], predictedDriversLicenseInfo)

    return {"status": "success"}, 200
