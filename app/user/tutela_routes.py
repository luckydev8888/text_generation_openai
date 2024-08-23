from flask import render_template, Blueprint, session, jsonify, request, redirect, url_for

tutela_bp = Blueprint('tutela', __name__, url_prefix="tutela")

@tutela_bp.route('/')
def tutela_page():
    if 'user_info' not in session:
        return redirect(url_for('user.users.login_page'))
    current_user = session['user_info']
    print("tutela", current_user)
    
    return render_template('tutela.html', user=current_user)


@tutela_bp.route('/get')
def get_title():
    if 'user_info' not in session:
        return redirect(url_for('user.users.login_page'))
    current_user = session['user_info']
    title = request.args.get('title', '')

    return render_template('tutela.html', user=current_user, title=title)