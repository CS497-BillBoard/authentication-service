from typing import Dict
from flask import Flask, Blueprint, jsonify, render_template, abort
from jinja2 import TemplateNotFound
from flask import Response
import requests
import json
import logging
from db.db import get_bills
from utils.bill_summary import get_plain_bill_text
from urllib.parse import urljoin

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
    
    # get a list of bills
    OPENPARLIAMENT_BASE_URL = "https://api.openparliament.ca"
    
    params = {'format': 'json',
              'version': 'v1',
              'introduced__gte':'2023-01-01'}
    r = requests.get(urljoin(OPENPARLIAMENT_BASE_URL, 'bills'), params=params)
    
    if (r.status_code >= 400):  # status codes above 400 indicate an error
        print(r.reason)
        return Response(f"{r.reason}", r.status_code)
    
    # return a list of bills. each bill is a dictionary with params "name", "summary", "introduced"
    returned_bill_data = []
    
    # parse to get data about the bills
    sorted_bills_data = sorted(r.json()['objects'], key=lambda x: x["introduced"], reverse=True)
    
    # get a summary for each bill
    for bill in sorted_bills_data:
        bill_url = bill['url']
        
        single_bill_params = {'format': 'json', 'version': 'v1'}
        resp_bill = requests.get(urljoin(OPENPARLIAMENT_BASE_URL, bill_url), params=single_bill_params)
        if (resp_bill.status_code >= 400):  # status codes above 400 indicate an error
            print(r.reason)
            return Response(f'{r.reason}', r.status_code)
        
        bill_info = resp_bill.json()
        
        # parse bill summary
        summary, text = get_plain_bill_text(bill_info['text_url'])
        
        # bill name
        bill_name = bill_info['short_title']['en'] if bill_info['short_title']['en'] != "" else bill_info['name']['en']
        
        # add the short title if it exists
        returned_bill_data.append(
            {
                "name": bill_name,
                "summary": summary,
                "introduced": bill_info['introduced']
            }
        )    
    
    return jsonify(returned_bill_data)


def fetch_new_bills():
    """
    fetch new bills from https://openparliament.ca/api/
    TODO eventually this will update the list of bills in the db
    """
    bills_list = [i for i in get_bills()]
    print("BILLS: ", bills_list)
    
    return
