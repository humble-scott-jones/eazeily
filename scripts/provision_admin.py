import os
import sys
# Add parent dir to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, get_db, _hash_password

def provision_admin():
    admin_emails = os.getenv('ADMIN_EMAILS', '')
    admin_pw = os.getenv('DEV_ADMIN_PW')
    
    if not admin_emails or not admin_pw:
        print("Error: ADMIN_EMAILS or DEV_ADMIN_PW not set.")
        return

    # Take the first email if comma-separated
    email = admin_emails.split(',')[0].strip()
    
    print(f"Provisioning admin user: {email}")
    
    with app.app_context():
        db = get_db()
        # Check if user exists
        user = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        
        pw_hash = _hash_password(admin_pw)
        
        if user:
            print("User exists. Updating password and admin status...")
            db.execute('''
                UPDATE users 
                SET password_hash = ?, is_admin = 1, subscription_tier = 'team'
                WHERE email = ?
            ''', (pw_hash, email))
        else:
            print("User does not exist. Creating new admin user...")
            import uuid
            uid = str(uuid.uuid4())
            db.execute('''
                INSERT INTO users (id, email, password_hash, is_admin, subscription_tier, is_paid)
                VALUES (?, ?, ?, 1, 'team', 1)
            ''', (uid, email, pw_hash))
            
        db.commit()
        print("Success!")

if __name__ == '__main__':
    provision_admin()
