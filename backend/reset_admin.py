import os
import sys

from app.core.database import get_engine, get_session_factory
from app.models.user import User
from app.core.config import get_settings
from app.core.security import hash_password, verify_password

def reset_admin():
    settings = get_settings()
    engine = get_engine()
    Session = get_session_factory()
    db = Session()
    
    print(f"Env ARBOR_ADMIN_EMAIL: {settings.admin_email}")
    print(f"Env ARBOR_ADMIN_PASSWORD: '{settings.admin_password}'")
    
    users = db.query(User).all()
    print(f"Total users in DB: {len(users)}")
    
    admin = db.query(User).filter(User.email == settings.admin_email).first()
    if not admin:
        print("ERROR: Admin user not found in the database!")
        for u in users:
            print(f" - Found user: {u.email}")
        return
        
    print(f"Admin found! Email: {admin.email}")
    
    # Check if the env password matches
    is_valid = verify_password(settings.admin_password, admin.hashed_password)
    print(f"Does the env password match the DB hash? {is_valid}")
    
    # Reset password to a known safe value
    new_password = "password123"
    admin.hashed_password = hash_password(new_password)
    db.commit()
    print(f"SUCCESS: Admin password has been hard-reset to '{new_password}'")

if __name__ == "__main__":
    reset_admin()
