import logging
import configparser
import os
import ssl
from flask import Flask
from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from flask_jwt_extended import JWTManager
from flask_apscheduler import APScheduler
from api.bills_service import fetch_and_store_bills

from api.auth_service import auth_service
from create import create_app


# set logging level
logging.basicConfig(level=logging.INFO)
logging.info("(app.py) logging level set to INFO")

if os.environ.get('LOGGING_LEVEL_DEBUG') == 'True':
    logging.basicConfig(level=logging.DEBUG)
    logging.info("(app.py) logging level set to DEBUG")

# create app
app = create_app()
logging.info("(app.py) app created")
# scheduler to update bills db
scheduler = APScheduler()
logging.info("scheduler created")

# get mongo uri from config file
config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

# add mongo config to app
app.config['DEBUG'] = True
app.config['MONGO_URI'] = config['PROD']['DB_URI']
logging.info("(app.py) mongo uri added to app config")

app.config["JWT_SECRET_KEY"] = config['PROD']['SECRET_KEY']

jwt = JWTManager(app)

'''
 note: 
    This if statement is only true if you run this file directly (ie. locally).
    When running this project on azure, it will be false because the deployment 
    script does not do "python app.py", it does "gunicorn app:app" instead 
    (the format is {module_import}:{app_variable} where module_import is 
    module/filename with your application and app_variable is the variable with 
    the Flask application var).

 '''

# On startup and at set intervals, fetch from the openparliament api and db
def update_db_bills():
    with app.app_context():
        logging.info("updating the db with new bills!")
        fetch_and_store_bills()
        logging.info("finished updating the db.")

if __name__ == "__main__":
    # set logging level to DEBUG if running it locally (not on azure)
    logging.basicConfig(level=logging.DEBUG)

    # start the scheduler
    scheduler.add_job(id = 'Bill Update Task', func=update_db_bills, trigger="interval", hours=24)
    scheduler.start()
    # run app locally
    app.run()

