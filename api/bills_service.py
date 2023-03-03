from flask import Flask, Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from flask import Response
import requests
import logging
from db.db import get_user_acc_collection

"""
This api is for fetching a list of bills
"""

# endpoint
bill_service = Blueprint('bills_page', __name__, template_folder='templates')

@bill_service.route('/bills', methods = ["GET"])
def login():
    # placeholder response
    return Response("asdf", 200)
