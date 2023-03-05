from flask import Flask, render_template, request
import requests
import logging

application = Flask(__name__)

@application.route('/sign-up', methods = ["GET", "POST"])
def signUp():
    logging.info("(register.py) /sign-up endpoint hit")

    return "hi"
