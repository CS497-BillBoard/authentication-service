from flask import Flask, Blueprint, render_template, abort
from jinja2 import TemplateNotFound
import requests
import logging

"""
This api is for handling authentication for users who are already registered.
"""

# TODO database stuff


# endpoint
auth_service = Blueprint('simple_page', __name__, template_folder='templates')

@auth_service.route('/login', methods = ["GET", "POST"])
def login():
    # TODO
    return

