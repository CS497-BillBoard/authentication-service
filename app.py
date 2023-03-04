import configparser
import os
import ssl
from flask import Flask
from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

from api.auth_service import auth_service
from create import create_app

app = Flask(__name__)
app.register_blueprint(auth_service)
# TODO add register service


config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

if __name__ == "__main__":
    # TODO, this wasn't working for me, so ive commented it out
    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # context.load_cert_chain('cert.pem', 'private.pem')
    
    app = create_app()
    app.config['DEBUG'] = True
    app.config['MONGO_URI'] = config['PROD']['DB_URI']

    app.run()

