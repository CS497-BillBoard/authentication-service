import ssl
from flask import Flask
from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

from api.auth_service import auth_service

app = Flask(__name__)
app.register_blueprint(auth_service)
# TODO add register service

def main():
    print("Hello World")
    
    # TODO, this wasn't working for me, so ive commented it out
    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # context.load_cert_chain('cert.pem', 'private.pem')

main()
