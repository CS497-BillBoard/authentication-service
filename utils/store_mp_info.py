import json
import logging
from pymongo.collection import Collection
import requests
from db import db

def store_mp_info(filename: str):
    """
    A function to store riding, mp, and contact info
    """
    logging.info("storing mp information into the db")
    
    openparliament_base_url = "https://api.openparliament.ca/"
    stored_info = []
    
    with open(filename, "r") as f:
        # store with structure
        # [
        #     {
        #         riding_name,
        #         mp_name,
        #         party,
        #         phone?,
        #         email?,
        #     }
        # ]
        
        mp_info = json.load(f)["objects"]
        for mp in mp_info:
            riding = mp["current_riding"]["name"]["en"]
            name = mp["name"]
            party = mp["current_party"]["short_name"]["en"]
            
            # get contact info
            print(f"getting info for {name}")
            resp = requests.get(openparliament_base_url + mp["url"],
                                params={'format': 'json', 'version': 'v1'})
            resp_info = resp.json()
            phone = resp_info["voice"] if "voice" in resp_info else "no phone num"
            email = resp_info["email"] if "email" in resp_info else "no email"
            
            stored_info.append({
                "riding_name": riding,
                "mp_name": name,
                "party": party,
                "phone": phone,
                "email": email
            })
    
    collection: Collection = db.get_mp_db()["mpInfo"]
    collection.insert_many(stored_info)
