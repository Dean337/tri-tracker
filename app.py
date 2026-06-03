from flask import Flask
from config import Config
from db import register_db
from routes.main import main_bp
from routes.auth import auth_bp
from routes.activities import activities_bp
from routes.trends import trends_bp
from routes.predictor import predictor_bp
from routes.info import info_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_db(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(trends_bp)
    app.register_blueprint(predictor_bp)
    app.register_blueprint(info_bp)

    return app
