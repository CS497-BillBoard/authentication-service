from typing import Dict
from flask import Flask, Blueprint, jsonify, render_template, abort, request, current_app
import requests
import json
import logging
from db import db
from utils.bill_summary import get_plain_bill_text
from urllib.parse import urljoin
from datetime import datetime
from flask_jwt_extended import decode_token

"""
This api is for fetching bills, either a list of them or a specific bill, with a user_id optionally
"""

def get_user_id() -> int:
    """
    Function to authenticate user by checking jwt token
    returns: the user_id if present or None (no user)
    """
    user_id = None
    AUTHORIZATION_HEADER = 'Authorization'
    
    if request.headers.get(AUTHORIZATION_HEADER, None) is not None:
        try:
            jwtr = decode_token(request.headers.get(AUTHORIZATION_HEADER))
            logging.info("header authz={}".format(jwtr))
            user_id = jwtr['sub']
        except Exception:
            return {"data": "token present but invalid"}, 401
    
    return user_id

# endpoint
bills_service = Blueprint('bills_page', __name__, template_folder='templates')

@bills_service.route('/bills', defaults={'bill_id': None}, methods=["GET"])
@bills_service.route('/bills/<bill_id>', methods=["GET"])
def bills(bill_id=None):
    """
    Returns a list of the most recent bills in JSON format.
    bill_id is the legisinfo_id of the bill. if passed in, only a specific
    bill is returned, including all of its comments.
    """
    logging.info("(bills_service.py) /bills endpoint hit")
    
    # if no authorization, then it is a unverified user, return anonymous bill data
    user_id = get_user_id()
    
    # no bill id passed, so just return all bills
    if bill_id is None:
        return get_all_bills(user_id)

    # bill id passed, check it
    try:
        bill_id = int(bill_id)
    except Exception:
        return {"data": "invalid id passed"}, 400
        
    return get_one_bill(bill_id, user_id)

# endpoint if the user upvotes or downvotes or comments
@bills_service.route('/bills/<bill_id>', methods=["PUT", "POST"])
def update_bill(bill_id):
    """
    Endpoint for a single user to upvote/downvote or add a comment
    Takes in a json containing:
     - vote (optional)
     - comment (optional)
    """
    logging.info("(bills_service.py) /bills update endpoint hit")
    
    ### checking passed input
    try:
        bill_id = int(bill_id)
    except Exception:
        return {"data": "passed id param not an integer"}, 400
    
    data: Dict = request.get_json()
    if data is None:
        return {"data": "invalid json body"}, 400
    
    user_id = get_user_id()
    if user_id is None:
        return {"data": "no user token provided"}, 401
    
    ### parsing input
    user_vote = data.get("vote", None)
    user_comment = data.get("comment", None)
    if user_vote is not None:
        if abs(user_vote) > 1:  # sanity check on the vote, it must be -1, 0, or 1
            return {"data": "invalid argument for vote"}, 400
    
    updated_bill = db.perform_update(bill_id, user_id, user_vote, user_comment)
    if updated_bill is None:
        return {"data": "bill does not exist"}, 400
    
    return return_info_one_bill(updated_bill, user_id), 200


def fetch_new_bills():
    """
    fetch new bills from https://openparliament.ca/api/
    """
    # get a list of bills
    OPENPARLIAMENT_BASE_URL = "https://api.openparliament.ca"
    
    introduced_date = datetime.now().strftime("%Y-%m-01")
    params = {'format': 'json',
              'version': 'v1',
              'limit': 50,
              'introduced__gte': introduced_date}
    r = requests.get(urljoin(OPENPARLIAMENT_BASE_URL, 'bills'), params=params)
    
    if (r.status_code >= 400):  # status codes above 400 indicate an error
        logging.info(r.reason)
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
            logging.info(r.reason)
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
                "comments": {},  # format of comments is {user_id: comment, user_id2: comment, ...}
                "votes": {},  # format is {user_id: -1 | 0 | 1, user_id2: -1 | 0 | 1 ...}  to indicate they unvoted or downvoted this bill
                              # if a user has never voted on the bill, they won't be here either
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
        logging.info(e)
        return {"data": "something went wrong :("}, 500
        
    return {"data": "stored bills!"}, 200

def hide_users_ids_comments(comments: Dict, user_id=None):
    """
    Hides the user ids from the comments, except for a possibly
    signed-in user who can see what they've commented
    @param comments: the "comments" object on a bill
    returns: a list of {user: comment}, where user is either "You, or "anonymous user"
    """
    if user_id is None:
        hidden_comments = [
            { 
                "user": "anonymous user",
                "comment": comment 
            }
            for _, comment in comments.items()
        ]
    else:
        hidden_comments = [
            {
                "user": "anonymous user" if user != user_id else "You",
                "comment": comment
            }
            for user, comment in comments.items()
        ]
    return hidden_comments

def get_all_bills(user_id=None):
    bills = db.get_bills()
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
            # user upvote/downvote status, if provided
            "user_vote": bill["votes"][user_id] if user_id is not None and user_id in bill["votes"] else 0
        } for bill in bills
    ]
    return returned_info, 200
    
def return_info_one_bill(bill, user_id=None):
    """
    Helper function to only return neccessary fields from one bill
    """
    print("USER ID: ", user_id)
    print("comments: ", bill["comments"])
    returned_info = {
        "legisinfo_id": bill["legisinfo_id"],
        "full_text_url": bill["full_text_url"],
        "name": bill["name"],
        "summary": bill["summary"],
        "introduced": bill["introduced"],
        "total_upvotes": bill["total_upvotes"],
        "total_downvotes": bill["total_downvotes"],
        "total_comments": bill["total_comments"],
        "comments": hide_users_ids_comments(bill["comments"], user_id),
        "user_vote": bill["votes"][user_id] if user_id is not None and user_id in bill["votes"] else 0
    }
    return returned_info

def get_one_bill(bill_id, user_id=None):
    """
    Returns information about a specific bill, include all comments
    if user_id is provided, it will show the vote ("agree/disagree") state and also what they commented
    """
    bill = db.get_one_bill(bill_id)
    if bill is None:
        return {"data": "no bill found with the given id"}, 400
    return return_info_one_bill(bill, user_id), 200

