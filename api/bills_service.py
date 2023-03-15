from typing import Dict
from flask import Flask, Blueprint, jsonify, render_template, abort, request
from jinja2 import TemplateNotFound
from flask import Response
import requests
import json
import logging
from db import db
from utils.bill_summary import get_plain_bill_text
from urllib.parse import urljoin

"""
This api is for fetching bills, either a list of them or a specific bill, with a user_id optionally
"""

# endpoint
bills_service = Blueprint('bills_page', __name__, template_folder='templates')

@bills_service.route('/bills', defaults={'bill_id': None}, methods=["GET"])
@bills_service.route('/bills/<bill_id>', methods=["GET"])
def bills(bill_id):
    """
    Returns a list of the most recent bills in JSON format.
    bill_id is the legisinfo_id of the bill. if passed in, only a specific
    bill is returned, including all of its comments.
    """
    logging.info("(bills_service.py) /bills endpoint hit")
    try:
        bill_id = int(bill_id)
    except ValueError:
        return {"data": "invalid id passed"}, 400
        
    if not bill_id:
        return get_all_bills()
    return get_one_bill(bill_id)

# endpoint if the user upvotes or downvotes or comments
@bills_service.route('/bills/<bill_id>', methods=["PUT", "POST"])
def update_bill(bill_id):
    """
    Endpoint for a single user to upvote/downvote or add a comment
    Takes in a json containing:
     - user_id (required)
     - vote (optional)
     - comment (optional)
    """
    if bill_id is None:
        return {"data": "no bill id given"}, 400
    try:
        data: Dict = request.get_json()
        if data is None:
            raise Exception()
    except Exception as e:
        return {"data": "data invalid"}, 400
    
    user_id = data.get("user_id", None)
    if user_id is None:
        return {"data": "user_id invalid"}, 400
    
    user_vote = data.get("vote", None)
    user_comment = data.get("comment", None)
    
    updated_bill = db.perform_update(bill_id, user_id, user_vote, user_comment)
    if updated_bill is None:
        return {"data": "bill does not exist"}, 400
    
    return updated_bill, 200


def fetch_new_bills():
    """
    fetch new bills from https://openparliament.ca/api/
    TODO eventually this will fetch bills from the db instead of the API
    """
    # get a list of bills
    OPENPARLIAMENT_BASE_URL = "https://api.openparliament.ca"
    
    params = {'format': 'json',
              'version': 'v1',
              'introduced__gte':'2023-01-01'}
    r = requests.get(urljoin(OPENPARLIAMENT_BASE_URL, 'bills'), params=params)
    
    if (r.status_code >= 400):  # status codes above 400 indicate an error
        print(r.reason)
        return {'data': f'{r.reason}'}, r.status_code
    
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
            return {'data': f'{r.reason}'}, r.status_code
        
        bill_info = resp_bill.json()
        
        # parse bill summary
        summary, text = get_plain_bill_text(bill_info['text_url'])
        
        # bill name
        # add the short title if it exists, otherwise use the regular name
        bill_name = bill_info['short_title']['en'] if bill_info['short_title']['en'] != "" else bill_info['name']['en']
        
        returned_bill_data.append(
            {
                "legisinfo_id": bill_info['legisinfo_id'],
                "full_text_url": bill_info['text_url'],
                "name": bill_name,
                "summary": summary,
                "introduced": bill_info['introduced'],
                "total_upvotes": 0,
                "total_downvotes": 0,
                "total_comments": 0,
                "comments": {},  # format of comments is [ {user_id: id, comment_text: string}, ... ]
                "votes": {},  # format is [ {user_id: -1 | 1} ]  to indicate they unvoted or downvoted this bill
                              # if a user is not in votes, then they also haven't voted
            }
        )    
    
    return returned_bill_data

def fetch_and_store_bills():
    """
    Store data that does not exist yet into mongodb
    """
    try:
        db.store_new_bills(fetch_new_bills())
    except Exception as e:
        print(e)
        return {"data": "something went wrong :("}, 500
        
    return {"data": "stored bills!"}, 200

def get_all_bills():
    bills = db.get_bills()
    # user upvote/downvote status, if provided
    # TODO user must be authenticated
    user_id = request.args.get("user_id")
    returned_info = [
        {
            "legisinfo_id": bill["legisinfo_id"],
            "full_text_url": bill["full_text_url"],
            "name": bill["name"],
            "summary": bill["summary"],
            "introduced": bill["introduced"],
            "total_upvotes": bill["total_upvotes"],
            "total_downvotes": bill["total_downvotes"],
            "total_comments": bill["total_comments"],
            "user_vote": bill["votes"]["user_id"] if user_id in bill["votes"] else 0
        } for bill in bills
    ]
    return returned_info, 200
    

def get_one_bill(bill_id):
    """
    Returns information about a specific bill, include all comments
    """
    bill = db.get_one_bill(bill_id)
    print("bill: ", bill)
    
    if bill is None:
        return {"data": "no bill found with the given id"}, 400
    
    # user_id here will show the vote ("agree/disagree") state and also what they commented
    # TODO user must be authenticated
    user_id = request.args.get("user_id")
    
    # change comments if user signed in
    # structure: [ {(anonymous user | You): "comment"}, ... ]
    if user_id is None:
        comments = [
            {
                "anonymous user": comment["comment_text"]
            }
            for comment in bill["comments"]
        ]
    else:
        comments = [
            {
                "anonymous user" if comment[user_id] != user_id else "You": comment["comment_text"]
            }
            for comment in bill["comments"]
        ]
    
    returned_info = {
        "legisinfo_id": bill["legisinfo_id"],
        "full_text_url": bill["full_text_url"],
        "name": bill["name"],
        "summary": bill["summary"],
        "introduced": bill["introduced"],
        "total_upvotes": bill["total_upvotes"],
        "total_downvotes": bill["total_downvotes"],
        "total_comments": bill["total_comments"],
        "comments": comments,
        "user_vote": bill["votes"]["user_id"] if user_id in bill["votes"] else 0
    }
    
    return returned_info, 200

