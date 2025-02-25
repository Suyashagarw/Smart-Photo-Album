import os

from flask import Flask
# from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
import logging, doctest


db = SQLAlchemy()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
STORAGE_URL=os.getenv('STORAGE_URL')
policyManagementUrl=os.getenv('app_manager_url')
backendUrl=os.getenv('backend_url')
nodeManagerUrl=os.getenv('node_manager')
grafanaUrl=os.getenv('grafanaUrl')
FE_url=os.getenv('FE_url')
app_manager_fe=os.getenv('app_manager_fe')
AWS_ACCESS_KEY=os.getenv('aws_access_key_id')
AWS_SECRET_KEY=os.getenv('aws_secret_access_key')
REDIS_ENDPOINT=os.getenv('REDIS_ENDPOINT')
STORAGE_BUCKET=os.getenv('STORAGE_BUCKET')
OS_ENDPOINT=os.getenv('OS_ENDPOINT')
OS_USERNAME=os.getenv('OS_USERNAME')
OS_PASSWORD=os.getenv('OS_PASSWORD')
API_ENDPOINT=os.getenv('API_ENDPOINT')
# login_manager = LoginManager()

def register_extensions(app):
    db.init_app(app)
    # login_manager.init_app(app)


def register_blueprints(app):
    for module_name in ('home', 'photoUpload', 'aws_redis', 'aws_dynamo', 'aws_sqs', 'aws_rekognition', 'aws_opensearch'):
        module = import_module('apps.services.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):

    @app.before_first_request
    def initialize_database():
        try:
            db.create_all()
        except Exception as e:

            print('> Error: DBMS Exception: ' + str(e) )

            # fallback to SQLite
            basedir = os.path.abspath(os.path.dirname(__file__))
            app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')

            print('> Fallback to SQLite ')
            db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove() 


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    # configure_database(app)
    return app
