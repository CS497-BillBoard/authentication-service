import configparser
import os
import ssl
from flask import Flask
from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from flask_jwt_extended import JWTManager

from api.auth_service import auth_service
from create import create_app

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

app = create_app()
app.config['DEBUG'] = True
app.config['MONGO_URI'] = config['PROD']['DB_URI']
app.config["JWT_SECRET_KEY"] = config['PROD']['SECRET_KEY']

jwt = JWTManager(app)

if __name__ == "__main__":
    app.run()

