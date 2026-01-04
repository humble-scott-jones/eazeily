from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin
from models import db, User, bcrypt

auth_bp = Blueprint('auth', __name__)

def is_safe_url(target):
    """Check if the target URL is safe for redirect (prevents open redirect attacks)."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_bp.route('/auth/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
        
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    new_user = User(email=email, password_hash='')  # Temporary value
    new_user.set_password(password)  # Use the set_password method
    
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)
    return jsonify({"message": "User created and logged in", "user": {"id": new_user.id, "email": new_user.email}}), 201

@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    try:
        data = request.get_json(silent=True)
        if not data:
            flash('Invalid request data', 'error')
            return jsonify({"error": "Invalid JSON data or empty body"}), 400

        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember', False)

        if not email or not password:
            flash('Email and password are required', 'error')
            return jsonify({"error": "Email and password required"}), 400

        # Debug logging
        print(f"Attempting login for: {email}")

        user = User.query.filter_by(email=email).first()
        
        # The "Gold Standard" Check - separate user not found vs bad password
        if not user:
            print(f"User not found: {email}")
            flash('Please check your login details and try again.', 'error')
            return jsonify({"error": "Invalid credentials"}), 401

        # Use User.check_password() method - do NOT hash password here
        if not user.check_password(password):
            print(f"Password check failed for: {email}")
            flash('Please check your login details and try again.', 'error')
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Success
        login_user(user, remember=remember)
        print(f"Login successful for: {email}")
        flash(f'Welcome back, {user.email}!', 'success')
        
        # Smart Redirect (Go back to where they tried to access) with security check
        next_page = request.args.get('next')
        if next_page and is_safe_url(next_page):
            validated_next = next_page
        else:
            validated_next = None
        
        return jsonify({
            "message": "Logged in successfully", 
            "user": {"id": user.id, "email": user.email},
            "next": validated_next
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash('Login failed. Please try again.', 'error')
        return jsonify({"error": "Login failed", "details": str(e)}), 500

@auth_bp.route('/auth/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/api/me', methods=['GET'])
def me():
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "user": {"id": current_user.id, "email": current_user.email}}), 200
    return jsonify({"authenticated": False}), 200
