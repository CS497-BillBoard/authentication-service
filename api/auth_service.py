from flask import Flask, Blueprint, render_template, abort, jsonify, request
from jinja2 import TemplateNotFound
from flask import Response
import requests
import logging
from db.db import get_user_acc_collection, get_single_user
from flask_jwt_extended import create_access_token
import bcrypt

"""
This api is for handling authentication for users who are already registered.
"""

# TODO database stuff

# endpoint
auth_service = Blueprint("auth_page", __name__, template_folder="templates")


@auth_service.route("/login", methods=["GET", "POST", "PUT"])
def login():
    # placeholder response

    if request.method == "POST":
        print(request.get_json()["email"])
        user = get_single_user(request.get_json()["email"])
        if user is None:
            return Response("No account found with email", 401)

        passwordMatch = bcrypt.checkpw(
            request.get_json()["password"].encode("UTF-8"), user["password_hash"]
        )

        if passwordMatch:

            access_token = create_access_token(identity=user["email"])
            return {
                "token": access_token,
                "user_id": user["email"],
                "verified": user["verified"],
            }, 200
            print(access_token)

    if request.method == "PUT":
        
        print(request.get_json)

        return {"data": "LOL"}, 200

    return {"data": "invalid password"}, 400


@auth_service.route("/test-get-collection", methods=["GET", "POST"])
def test_get_collection():
    """
    Inserts a comment into the comments collection, with the following fields:

    - "name"
    - "email"
    - "movie_id"
    - "text"
    - "date"

    Name and email must be retrieved from the "user" object.
    """

    print("ACCOUNT COLLECTION: ", get_user_acc_collection())
    return Response("hi!", 200)  # TODO
