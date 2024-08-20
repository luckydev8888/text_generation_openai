from flask import Blueprint, render_template

admin_bp = Blueprint('admin', __name__, template_folder='templates', static_folder='static', static_url_path='/admin/static')

from .main_routes import main_bp
from .constdf_routes import constdf_bp
from .sentencias_routes import sentencias_bp

admin_bp.register_blueprint(main_bp)
admin_bp.register_blueprint(constdf_bp)
admin_bp.register_blueprint(sentencias_bp)

def page_not_found(e):
    return render_template('404.html'), 404