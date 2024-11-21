# app/__init__.py
from flask import Flask
from .routes import main

def create_app():
    app = Flask(__name__)

    # Set configuration here, not on the blueprint
    app.config['UPLOAD_FOLDER'] = 'uploads'  # Set the upload folder here

    app.register_blueprint(main)

    return app
