from flask import Flask, Blueprint, render_template, abort, jsonify, request, Response
import bcrypt
import requests
import logging
from db import db

user_service = Blueprint("user_page", __name__, template_folder="templates")

@user_service.route('/user-info/', defaults={'id': None}, methods=["GET"])
@user_service.route("/user-info/<id>", methods=["GET"])
def get_user(id=None):
    """
    This endpoint is for getting a user's information
    sample request body:
    {
        "id": "64209dc50c078a1bc328b7z3"
    }

    sample response:
    {
        "id": "64209dc50c078a1bc328b7z3",
        "parliament_member_name": "John Doe",
        "constituency_name": "Toronto"
    }

    """

    logging.info("(user_service.py) /get-user endpoint hit")
        
    if request.method == "GET":
        if id is None or id == "":
            return {"error": "No id provided"}, 400
        
        userAccount = db.get_single_user_by_id(id)

        if userAccount is None:
            return {"error": "No user account found with id: " + id}, 400
        
        return {
            "id": id,
            "parliament_member_name": userAccount.get("parliament_member_name", ""),
            "constituency_name": userAccount.get("constituency_name", "")
        }
        
