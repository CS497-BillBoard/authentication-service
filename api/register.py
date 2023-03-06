from flask import Flask, render_template, request
from flask import Flask, Blueprint, render_template, abort, jsonify, request, Response
import requests
import logging
import bcrypt
from db.db import insert_new_user

register_service = Blueprint("register_page", __name__, template_folder="templates")


@register_service.route("/sign-up", methods=["GET", "POST"])
def signUp():

    if request.method == "POST":
        body = request.get_json()

        bytePassword = body["password"].encode('UTF-8')

        salt = bcrypt.gensalt()

        password_hash = bcrypt.hashpw(bytePassword, salt)

        user = {"email": body["email"], "password_hash": password_hash, "verified": False}
        
        # validate form data
        # TODO: check if email is valid and not duplicate
        # TODO: check if password is valid (not empty, etc.)

        insert_result = insert_new_user(user)

        if insert_result == -1:
            return Response("Email already registered to an account", 400)

    return "hi"
