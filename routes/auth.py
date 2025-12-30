from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user

auth_bp = Blueprint('auth', __name__, template_folder='../templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        # NOTE: this scaffold does not implement password checks. Implement securely.
        # For now we just pretend login succeeded.
        from models import User, db
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.session.add(user)
            db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard.index'))
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('dashboard.index'))
