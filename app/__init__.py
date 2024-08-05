from flask import Flask
from .api.user import user_api_bp
# from .admin import admin_bp
from .user import user_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')


    mongo.init_app(app)

    # Register blueprints
    app.register_blueprint(user_api_bp, url_prefix='/api')
    # app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/')

    return app
