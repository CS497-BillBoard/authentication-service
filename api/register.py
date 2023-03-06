from flask import Flask, render_template, request
from flask import Flask, Blueprint, render_template, abort, jsonify, request
import requests
import logging
import bcrypt
from db.db import insert_new_user

register_service = Blueprint("register_page", __name__, template_folder="templates")


@register_service.route("/sign-up", methods=["GET", "POST"])
def signUp():
    logging.info("(register.py) /sign-up endpoint hit")

    if request.method == "POST":
        body = request.get_json()

        bytePassword = body["password"].encode('UTF-8')

        salt = bcrypt.gensalt()

        password_hash = bcrypt.hashpw(bytePassword, salt)

        user = {"email": body["email"], "password_hash": password_hash}

        insert_new_user(user)

        

    return "hi"
