from flask import Blueprint, request, jsonify, render_template
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, bcrypt

auth_bp = Blueprint('auth', __name__)

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

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, password_hash=hashed_password)
    
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
            return jsonify({"error": "Invalid JSON data or empty body"}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        # Debug logging
        print(f"Attempting login for: {email}")

        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"User not found: {email}")
            return jsonify({"error": "Invalid credentials"}), 401

        if bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            print(f"Login successful for: {email}")
            return jsonify({"message": "Logged in successfully", "user": {"id": user.id, "email": user.email}}), 200
        
        print(f"Password check failed for: {email}")
        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        import traceback
        traceback.print_exc()
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
