
import os
import json
import logging
from app import create_app
from models import db, User, bcrypt

# Setup environment
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['ADMIN_EMAILS'] = 'admin@example.com'
os.environ['DEV_ADMIN_PW'] = 'password123'

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

app = create_app()
app.config['TESTING'] = True
app.config['DEBUG'] = True

def debug_login():
    with app.test_client() as client:
        print("--- Starting Debug Session ---")
        
        # 1. Create a user manually to ensure DB works
        with app.app_context():
            try:
                hashed = bcrypt.generate_password_hash('password123').decode('utf-8')
                u = User(email='test@example.com', password_hash=hashed)
                db.session.add(u)
                db.session.commit()
                print("User created successfully")
            except Exception as e:
                print(f"ERROR creating user: {e}")
                import traceback
                traceback.print_exc()

        # 2. Try login
        print("\n--- Attempting Login ---")
        try:
            response = client.post('/auth/login', 
                data=json.dumps({'email': 'test@example.com', 'password': 'password123'}),
                content_type='application/json'
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response Data: {response.data.decode('utf-8')}")
        except Exception as e:
            print(f"EXCEPTION during login request: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_login()
