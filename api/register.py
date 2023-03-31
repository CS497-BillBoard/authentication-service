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

        if body.get("userAccountsId") is None or body.get("userAccountsId") == "":
            return {"error": "No userAccountsId provided"}, 400

        # check if user exists
        if db.get_single_user_by_id(body.get("userAccountsId")) is None:
            return {"error": "No account found with provided userAccountsId"}, 400
        
        if body.get("constituencyName") is None or body.get("constituencyName") == "":
            return {"error": "No constituency name provided"}

        riding_information = {
            "set_riding": True,
            "constituency_name": body["constituencyName"],
            "parliament_member_name": body["parliamentMemberName"],
        }

        dbResponse = db.update_user_riding_by_id(body.get("userAccountsId"), riding_information)

        if type(dbResponse) == Exception:
            logging.error("Error: " + str(dbResponse))
            return {"error": str(dbResponse)}, 400
        
        if dbResponse == -1:
            logging.error("Error: no account found with provided userAccountsId")
            return {"error": "No account found with provided userAccountsId"}, 400

        return {"status": "success"}, 200


@register_service.route("/verification-request", methods=["GET", "POST"])
def verificationRequest():
    """
    sample request body:
    {
        "userAccountsId": "64209dc50c078a1bc328b7x9",
        "driversLicenseImage": "base64 img"
    }
    """

    logging.info("(register.py) /verification-request endpoint hit")

    if request.method == "POST":
        body = request.get_json()

        if body.get("userAccountsId") is None or body.get("userAccountsId") == "":
            return {"error": "No userAccountsId provided"}, 400

        # check if user exists and that user is not verified
        userAccount = db.get_single_user_by_id(body["userAccountsId"])
        if userAccount is None:
            return {"error": "No account found with provided userAccountsId"}, 400
        
        if userAccount["verified"] == True:
            return {"error": "Account already verified"}, 400

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
            "userAccountsId": body["userAccountsId"],
            "drivers_license_image": body["driversLicenseImage"],
            "selfie_image": body["selfieImage"],
        }

        print("VERIFICATION REQUEST: ", verification_request)
        dbResponse = db.add_verification_request(verification_request)

        # note: there is a policy in the db that documents which still exist after 30 days are deleted (to ensure user data privacy)

        if type(dbResponse) == Exception:
            return {
                "error": "Verification request associated with this userAccountsId already exists: "
                + str(dbResponse)
            }, 400

    if request.method == "GET":
        return {"data": db.get_all_verification_requests()}, 200

    return {"status": "success"}, 200


def addSuspiciousFlagToUser(userAccountsId):
    result = db.update_user(userAccountsId, {"suspicious": True})

    if type(result) == Exception:
        logging.error(result)
        return result
    
    return


def removeRejectedVerificationRequest(userAccountsId):
    """
    Removes a verification request from the database and marks the user as suspicious
    """
    result = db.remove_verification_request(userAccountsId, False)

    if type(result) == Exception:
        return {
            "error": "Error removing verification request from db: "
            + str(result)
        }, 400
    
    result = addSuspiciousFlagToUser(userAccountsId)
    if type(result) == Exception:
        logging.error(result)
    
    return {
        "status": "success",
        "msg": "rejected verification - removed request from db",
    }, 200



@register_service.route("/update-verification-status", methods=["POST"])
def updateVerificationStatus():
    """
    sample request body (approved request):
    {
        "userAccountsId": "test@test.com",
        "status": true
        "driversLicenseNumber": "123456789",
        "province": "Ontario",
        "expiryYear": "2020"    
    }

    sample request body (rejected request):
    {
        "userAccountsId": "test@test.com",
        "status": false
    }

    """
    logging.info("(register.py) /update-verification-status endpoint hit")

    if request.method == "POST":
        body = request.get_json()

        # Validate Request Body Data
        if body.get("userAccountsId") is None or body.get("userAccountsId") == "":
            return {"error": "No userAccountsId provided"}, 400

        # check if user exists and that user is not verified
        userAccount = db.get_single_user_by_id(body["userAccountsId"])
        if userAccount is None:
            return {"error": "No account found with userAccountsId"}, 400
        
        if userAccount["verified"] == True:
            return {"error": "Account already verified"}, 400

        # check if verification request exists
        if db.get_single_verification_request(body["userAccountsId"]) is None:
            return {"error": "No verification request found with userAccountsId"}, 400

        if body.get("status") is None or body.get("status") == "":
            return {"error": "No status provided"}, 400

        if body.get("status") == False:
            return removeRejectedVerificationRequest(body["userAccountsId"])

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
            body.get("expiryYear") is None
            or body.get("expiryYear") == ""
        ):
            return {"error": "No expiry year provided"}, 400
        
        userAccountsId = body["userAccountsId"]
        driversLicenseNumber = body["driversLicenseNumber"]
        province = body["province"]
        expiryYear = body["expiryYear"]

        # get province + driver's license number and salt+hash it
        # note: use province in the hash as well to ensure uniqueness because driver's license numbers can 
        # be the same across diff provinces
        plaintextStringToHash = province + " " + driversLicenseNumber
        bytedriversLicenseNumber = plaintextStringToHash.encode("UTF-8")
        salt = bcrypt.gensalt()
        driversLicenseNumberHash = bcrypt.hashpw(bytedriversLicenseNumber, salt)

        # check that driversLicenseNumberHash does not already exist in accountsDatabase.driversLicense DB
        exisitingdriversLicenseNumberHash = db.get_all_hashed_drivers_licenses()
        for existingHash in exisitingdriversLicenseNumberHash:
            if bcrypt.checkpw(bytedriversLicenseNumber, existingHash.get("province_and_drivers_license_hash")):

                result = removeRejectedVerificationRequest(userAccountsId)
                if result[1] != 200:
                    return result

                return {"error": "drivers license number already exists"}, 400

        db.update_verification_status_to_approved(userAccountsId, driversLicenseNumberHash, expiryYear)

    return {"status": "success"}, 200


@register_service.route("/verification-request/drivers-license-info", methods=["POST"])
def driversLicenseInfo():
    """
    sample request body:
    {
      "userAccountsId": "64209dc50c078a1bc328b7z3",
      "driversLicenseBase64": "base64 string"
    }
    """
    logging.info(
        "(register.py) /verification-request/drivers-license-info endpoint hit"
    )

    AZURE_CUSTOM_AI_BUILDER_MODEL_URL = "https://prod-16.canadacentral.logic.azure.com:443/workflows/e1f01f174d674c23b55390ae3d620421/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=WpPWTMZJz05Q6Yc19jabyjtYY3Q6zXLrbBXgEAtvHps"

    if request.method == "POST":
        body = request.get_json()

        if body.get("userAccountsId") is None or body.get("userAccountsId") == "":
            return {"error": "No userAccountsId provided"}, 400

        if (
            body.get("driversLicenseBase64") is None
            or body.get("driversLicenseBase64") == ""
        ):
            return {"error": "No drivers license image provided"}, 400

        request_body = {
            "userAccountsId": body["userAccountsId"],
            "driversLicenseBase64": body["driversLicenseBase64"],
        }

        db.update_verification_request(body["userAccountsId"], {"image-sent-for-ai-parsing": True})

        response = requests.post(AZURE_CUSTOM_AI_BUILDER_MODEL_URL, json=request_body)

        if response.status_code != 200:
            return {
                "error": "Error calling custom AI builder model: "
                + str(response.status_code)
            }, 400

        response_body = response.json()

        response_body.pop("userAccountsId")
        predictedDriversLicenseInfo = {"predicted-drivers-license-info": response_body}

        db.update_verification_request(body["userAccountsId"], predictedDriversLicenseInfo)

    return {"status": "success"}, 200
