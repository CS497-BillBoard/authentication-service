from flask import Flask, Blueprint, render_template, abort, jsonify, request, Response
import bcrypt
import requests
import logging
from db import db

user_service = Blueprint("user_page", __name__, template_folder="templates")

@user_service.route("/user-info", methods=["GET"])
def get_user():
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
        body = request.get_json()

        if body.get("email") is None or body.get("email") == "":
            return {"error": "No email provided"}, 400
        
        userAccount = db.get_single_user(body["email"])

        if userAccount is None:
            return {"error": "No user account found with email: " + body["email"]}, 400
        
        return {
            "email": body["email"],
            "parliament_member_name": userAccount.get("parliament_member_name", ""),
            "constituency_name": userAccount.get("constituency_name", "")
        }
        
