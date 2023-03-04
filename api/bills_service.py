from flask import Flask, Blueprint, jsonify, render_template, abort
from flask_pymongo import DESCENDING
from jinja2 import TemplateNotFound
from flask import Response
import requests
import json
import logging
from db.db import get_bills

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
    # TODO currently the filter is hardcoded for bills since 2023 january 1st
    params = {'format': 'json',
              'version': 'v1',
              'introduced__gte':'2023-01-01'}
    r = requests.get('https://api.openparliament.ca/bills/', params=params)
    
    # status codes above 400 indicate an error
    if (r.status_code >= 400):
        print(r.reason)
        return Response(f"{r.reason}", r.status_code)
    
    # parse to get data about the bills
    bills_data = r.json()['objects']
    
    # sort descending by date
    sorted_bills = sorted(bills_data, key=lambda x: x["introduced"], reverse=True)
    return jsonify(sorted_bills)


def fetch_new_bills():
    """
    fetch new bills from https://openparliament.ca/api/
    TODO eventually this will update the list of bills in the db
    """
    bills_list = [i for i in get_bills()]
    print("BILLS: ", bills_list)
    
    return

