from flask import Flask, Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from flask import Response
import requests
import json
import logging
from db.db import get_user_acc_collection

"""
This api is for fetching a list of bills
"""

# endpoint
bills_service = Blueprint('bills_page', __name__, template_folder='templates')

@bills_service.route('/bills', methods = ["GET"])
def bills():
    """
    Returns a list of the most recent bills in JSON format
    TODO allow returning older bills
    """
    
    # for now, just request bills from api.openparliament.ca, TODO eventually store in db
    params = {'format': 'json', 'version': 'v1'}
    r = requests.get('https://api.openparliament.ca/bills/', params=params)
    bills_data = r.json()['objects']
    print("First bill: ", bills_data[0]['name']['en'])
    
    # placeholder response
    return Response(f"First bill: {bills_data[0]['name']['en']}", 200)

