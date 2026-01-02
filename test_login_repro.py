
import os
import json
from app import create_app
from models import db, User, bcrypt

# Setup environment
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['ADMIN_EMAILS'] = 'admin@example.com'
os.environ['DEV_ADMIN_PW'] = 'password123'

app = create_app()

def test_login():
    with app.test_client() as client:
        # 1. Check if admin user was seeded
        with app.app_context():
            user = User.query.filter_by(email='admin@example.com').first()
            if not user:
                print("FAIL: Admin user not seeded")
                return
            print(f"SUCCESS: Admin user seeded: {user.email}")
            
            # Verify password
            if bcrypt.check_password_hash(user.password_hash, 'password123'):
                print("SUCCESS: Password hash verified")
            else:
                print("FAIL: Password hash verification failed")

        # 2. Try login endpoint (Success)
        response = client.post('/auth/login', 
            data=json.dumps({'email': 'admin@example.com', 'password': 'password123'}),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            print("SUCCESS: Login endpoint returned 200")
            print(response.get_json())
        else:
            print(f"FAIL: Login endpoint returned {response.status_code}")
            print(response.data.decode('utf-8'))

        # 3. Try login endpoint (Invalid Password)
        response = client.post('/auth/login', 
            data=json.dumps({'email': 'admin@example.com', 'password': 'wrongpassword'}),
            content_type='application/json'
        )
        if response.status_code == 401:
             print("SUCCESS: Invalid password returned 401")
        else:
             print(f"FAIL: Invalid password returned {response.status_code}")

        # 4. Try login endpoint (User Not Found)
        response = client.post('/auth/login', 
            data=json.dumps({'email': 'nonexistent@example.com', 'password': 'password123'}),
            content_type='application/json'
        )
        if response.status_code == 401:
             print("SUCCESS: User not found returned 401")
        else:
             print(f"FAIL: User not found returned {response.status_code}")


if __name__ == "__main__":
    test_login()
