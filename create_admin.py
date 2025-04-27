#!/usr/bin/env python3
"""
Create default admin user for POS application.
This script creates an admin user if one doesn't already exist.
"""

import sys
import os
import traceback

from models.database import Database
from models.user import User

def main():
    """Main entry point for the script."""
    try:
        print("Connecting to database...")
        db = Database()
        db.initialize()
        
        print("Creating user model...")
        user_model = User(db)
        
        # Check if admin user already exists
        query = "SELECT username FROM users WHERE username = %s"
        existing_user = db.fetch_one(query, ("admin",))
        
        if existing_user:
            print("Admin user already exists.")
            return True
        
        print("Creating admin user...")
        # Use direct SQL instead of model to ensure it works
        user_id = str(user_model.generate_id())
        timestamp = user_model.get_timestamp()
        
        # Hash password manually
        import bcrypt
        password = "admin123"
        if isinstance(password, str):
            password = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password, salt).decode('utf-8')
        
        # Insert user directly
        query = """
        INSERT INTO users (
            user_id, username, password_hash, full_name, role, 
            email, active, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """
        
        admin_user = db.fetch_one(query, (
            user_id, "admin", password_hash, "System Administrator", "ADMIN",
            "admin@example.com", True, timestamp, timestamp
        ))
        
        # Force a commit
        if hasattr(db, 'connection') and db.connection:
            db.connection.commit()
        
        if admin_user:
            print("Successfully created admin user:")
            print(f"- Username: {admin_user['username']}")
            print(f"- Role: {admin_user['role']}")
            print(f"- Full Name: {admin_user['full_name']}")
            print("You should change the default password immediately after login.")
            return True
        else:
            print("Failed to create admin user")
            return False
            
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)