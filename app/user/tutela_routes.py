from flask import render_template, Blueprint
from app.user.users_routes import user_login_required

tutela_bp = Blueprint('tutela', __name__, url_prefix="tutela")

@tutela_bp.route('/')
@user_login_required
def login_page(current_user):
    print("here")
    return render_template('tutela.html', user=current_user)