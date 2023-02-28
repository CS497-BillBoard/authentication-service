import configparser
import os
import ssl
from flask import Flask
from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

from api.auth_service import auth_service

# TODO
def create_app():
    
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    STATIC_FOLDER = os.path.join(APP_DIR, 'build/static')
    TEMPLATE_FOLDER = os.path.join(APP_DIR, 'build')

    app = Flask(__name__, static_folder=STATIC_FOLDER,
                template_folder=TEMPLATE_FOLDER,
                )
    CORS(app)
    app.json_encoder = MongoJsonEncoder
    app.register_blueprint(movies_api_v1)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        return render_template('index.html')

    return 

app = Flask(__name__)
app.register_blueprint(auth_service)
# TODO add register service

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

if __name__ == "__main__":
    app = create_app()  # todo need to do this
    app.config['DEBUG'] = True
    app.config['MONGO_URI'] = config['PROD']['DB_URI']

    app.run()

"""
def main():
    print("Hello World")
    
    # TODO, this wasn't working for me, so ive commented it out
    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # context.load_cert_chain('cert.pem', 'private.pem')

main()
"""
