import os
from flask import Flask
from flask import render_template
from flask.json import JSONEncoder
from flask_cors import CORS
from flask import Response
from bson import json_util, ObjectId
from datetime import datetime, timedelta

from api.auth_service import auth_service
from api.bills_service import bills_service
from api.register import register_service

"""
Classes for creating app and encoding data, copied from the mongodb/flask tutorial
"""

class MongoJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_util.CANONICAL_JSON_OPTIONS)

def create_app():
    
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    STATIC_FOLDER = os.path.join(APP_DIR, 'build/static')
    TEMPLATE_FOLDER = os.path.join(APP_DIR, 'build')

    app = Flask(__name__, static_folder=STATIC_FOLDER,
                template_folder=TEMPLATE_FOLDER,
                )
    CORS(app)
    app.json_encoder = MongoJsonEncoder
    app.register_blueprint(auth_service)
    app.register_blueprint(bills_service)
    app.register_blueprint(register_service)
    
    # TODO on startup, simultaneously fetch from the openparliament api and db

    # TODO: remove this test route later or convert it into a health check
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def test_route(path):
        
        # temporary test
        return Response("Hello, World!", 200)

    return app

