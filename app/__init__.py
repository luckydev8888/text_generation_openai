from flask import Flask
from .api.user import user_api_bp
from .admin import admin_bp
from .user import user_bp
from .mongo import get_db
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(user_api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/')

    app.teardown_appcontext(lambda ctx: get_db().client.close())

    return app
