from flask import Flask, render_template, request
import requests
import logging

application = Flask(__name__)

@application.route('/signUp', methods = ["GET", "POST"])
def signUp():
    return
