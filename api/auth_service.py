from flask import Flask, Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from flask import Response
import requests
import logging
from db.db import get_user_acc_collection

"""
This api is for handling authentication for users who are already registered.
"""

# TODO database stuff


# endpoint
auth_service = Blueprint('auth_page', __name__, template_folder='templates')

@auth_service.route('/login', methods = ["GET", "POST"])
def login():
    # placeholder response
    logging.info("(auth_service.py) /login endpoint hit")

    return Response("asdf", 200)

@auth_service.route('/test-get-collection', methods = ["GET", "POST"])
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
    logging.info("(auth_service.py) /test-get-collection endpoint hit")

    print("ACCOUNT COLLECTION: ", get_user_acc_collection())
    return Response("hi!", 200) # TODO

