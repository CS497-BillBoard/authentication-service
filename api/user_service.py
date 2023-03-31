from flask import Flask, Blueprint, render_template, abort, jsonify, request, Response
import bcrypt
import requests
import logging
from db import db

user_service = Blueprint("user_page", __name__, template_folder="templates")

@user_service.route('/user-info/', defaults={'email': None}, methods=["GET"])
@user_service.route("/user-info/<email>", methods=["GET"])
def get_user(email=None):
    """
    This endpoint is for getting a user's information
    sample request body:
    {
        "email": "test@gmail.com"
    }

    sample response:
    {
        "email": "test@gmail.com",
        "parliament_member_name": "John Doe",
        "constituency_name": "Toronto"
    }

    """

    logging.info("(user_service.py) /get-user endpoint hit")
        
    if request.method == "GET":
        if email is None or email == "":
            return {"error": "No email provided"}, 400
        
        userAccount = db.get_single_user(email)

        if userAccount is None:
            return {"error": "No user account found with email: " + email}, 400
        
        return {
            "email": email,
            "parliament_member_name": userAccount.get("parliament_member_name", ""),
            "constituency_name": userAccount.get("constituency_name", "")
        }
        
