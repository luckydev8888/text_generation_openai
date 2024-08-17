from flask import Blueprint

admin_bp = Blueprint('admin', __name__, template_folder='templates', static_folder='static', static_url_path='/admin/static')

from .main_routes import main_bp
from .constdf_routes import constdf_bp

admin_bp.register_blueprint(main_bp)
admin_bp.register_blueprint(constdf_bp)