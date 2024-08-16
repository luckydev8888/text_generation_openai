from flask import Flask,jsonify
from .api.user import user_api_bp
from .admin import admin_bp
from .user import user_bp
from .mongo import get_db, jwt
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(user_api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/')
    
    app.teardown_appcontext(lambda ctx: get_db().client.close())

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_headers, jwt_data):
        identity = jwt_data['sub']
        return identity

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({"message", "token has expired"}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message", "Signature verification failed"}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"message", "token has expired"}), 401


    return app
