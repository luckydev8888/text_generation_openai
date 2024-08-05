from flask import render_template

from . import user_bp

@user_bp.route('/')
def home():
    return render_template('tutela.html')
