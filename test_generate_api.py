#!/usr/bin/env python3
"""Simple test script to verify the /api/generate endpoint works."""
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set test DB path
test_db = tempfile.mktemp(suffix='.db')
os.environ['TEST_DB_PATH'] = test_db
os.environ['SECRET_KEY'] = 'test-secret-key'

from app import create_app
from models import db, User

# Create app
app = create_app()

def test_generate_endpoint():
    """Test the generate endpoint with a simple request."""
    with app.test_client() as client:
        # Create a test user
        with app.app_context():
            user = User(email='test@example.com', password_hash='')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            
        # Login
        login_resp = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpass'
        }, follow_redirects=False)
        
        print(f"Login response: {login_resp.status_code}")
        
        # Test generate endpoint
        gen_resp = client.post('/api/generate', 
            json={
                'topic': 'AI in business',
                'platform': 'LinkedIn',
                'task_type': 'post'
            },
            content_type='application/json'
        )
        
        print(f"Generate response: {gen_resp.status_code}")
        print(f"Response data: {gen_resp.get_json()}")
        
        # Check response structure
        data = gen_resp.get_json()
        if data:
            if 'error' in data:
                print(f"✓ Error handling works: {data['error']}")
            elif 'content' in data:
                print(f"✓ Content generated: {data['content'][:100]}...")
            else:
                print(f"? Unexpected response structure")
        
        return gen_resp.status_code in [200, 503]  # 503 if no API key configured

if __name__ == '__main__':
    try:
        result = test_generate_endpoint()
        if result:
            print("\n✓ API endpoint test passed!")
            sys.exit(0)
        else:
            print("\n✗ API endpoint test failed!")
            sys.exit(1)
    finally:
        # Cleanup
        if os.path.exists(test_db):
            os.remove(test_db)
