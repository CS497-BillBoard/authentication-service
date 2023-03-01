from flask import Flask, Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from flask import Response
import requests
import logging
from api.db import db

"""
This api is for handling authentication for users who are already registered.
"""

# TODO database stuff


# endpoint
auth_service = Blueprint('auth_page', __name__, template_folder='templates')

@auth_service.route('/login', methods = ["GET", "POST"])
def login():
    # placeholder response
    return Response("asdf", 200)

@auth_service.route('/test-add-to-db', methods = ["GET", "POST"])
def test_add():
    """
    Inserts a comment into the comments collection, with the following fields:

    - "name"
    - "email"
    - "movie_id"
    - "text"
    - "date"

    Name and email must be retrieved from the "user" object.
    """
    
    # TODO
    # comment_doc = { 'movie_id' : "movie_id_here", 'name' : "shitty name", 'email' : "asdf@example.com",'text' : "mid movie", 'date' : "January 20th"}
    # return db.comments.insert_one(comment_doc)

