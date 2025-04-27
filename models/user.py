"""
User model for POS application.
Handles authentication, user management and role-based access control.
"""

import bcrypt
from datetime import datetime
import re

from .base_model import BaseModel


class User(BaseModel):
    """User model for authentication and user management."""
    
    # Role constants
    ROLE_ADMIN = "ADMIN"
    ROLE_MANAGER = "MANAGER"
    ROLE_SELLER = "SELLER"
    
    # Valid roles
    VALID_ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_SELLER]
    
    def __init__(self, db):
        """Initialize User model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "users"
        self.primary_key = "user_id"
    
    def create_user(self, username, password, full_name, role, email=None, phone=None):
        """Create a new user.
        
        Args:
            username (str): Unique username
            password (str): User password
            full_name (str): User's full name
            role (str): User role (ADMIN, MANAGER, SELLER)
            email (str, optional): User's email address
            phone (str, optional): User's phone number
            
        Returns:
            dict: Created user data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        # Validate input
        self._validate_user_data(username, password, full_name, role, email, phone)
        
        # Check if username already exists
        query = "SELECT username FROM users WHERE username = %s"
        existing_user = self.db.fetch_one(query, (username,))
        if existing_user:
            raise ValueError("Username already exists")
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Create user data
        user_id = self.generate_id()
        now = self.get_timestamp()
        
        user_data = {
            "user_id": user_id,
            "username": username,
            "password_hash": password_hash,
            "full_name": full_name,
            "role": role,
            "email": email,
            "phone": phone,
            "active": True,
            "created_at": now,
            "updated_at": now,
            "last_login": None
        }
        
        return self.create(user_data)
    
    def update_user(self, user_id, data):
        """Update user data.
        
        Args:
            user_id (str): ID of user to update
            data (dict): Data to update (username, full_name, role, email, phone, active)
            
        Returns:
            dict: Updated user data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        # Get existing user
        existing_user = self.get_by_id(user_id)
        if not existing_user:
            raise ValueError("User not found")
        
        # Validate input
        update_data = {}
        
        if "username" in data and data["username"] != existing_user["username"]:
            # Check if new username already exists
            query = "SELECT username FROM users WHERE username = %s AND user_id != %s"
            username_exists = self.db.fetch_one(query, (data["username"], user_id))
            if username_exists:
                raise ValueError("Username already exists")
            
            if not re.match(r"^[a-zA-Z0-9_]{3,20}$", data["username"]):
                raise ValueError("Invalid username format")
            
            update_data["username"] = data["username"]
        
        if "password" in data:
            update_data["password_hash"] = self._hash_password(data["password"])
        
        if "full_name" in data:
            if not data["full_name"] or len(data["full_name"]) < 2:
                raise ValueError("Full name is required")
            update_data["full_name"] = data["full_name"]
        
        if "role" in data:
            if data["role"] not in self.VALID_ROLES:
                raise ValueError(f"Invalid role. Must be one of: {', '.join(self.VALID_ROLES)}")
            update_data["role"] = data["role"]
        
        if "email" in data:
            if data["email"] and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", data["email"]):
                raise ValueError("Invalid email format")
            update_data["email"] = data["email"]
        
        if "phone" in data:
            update_data["phone"] = data["phone"]
        
        if "active" in data:
            update_data["active"] = bool(data["active"])
        
        # Update timestamp
        update_data["updated_at"] = self.get_timestamp()
        
        # Update user
        return self.update(user_id, update_data)
    
    def authenticate(self, username, password):
        """Authenticate a user with username and password.
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            dict: User data if authenticated, None otherwise
        """
        query = "SELECT * FROM users WHERE username = %s AND active = true"
        user = self.db.fetch_one(query, (username,))
        
        if user and self._verify_password(password, user["password_hash"]):
            # Update last login time
            now = self.get_timestamp()
            self.update(user["user_id"], {"last_login": now})
            
            # Return user without password hash
            user.pop("password_hash", None)
            return user
        
        return None
    
    def change_password(self, user_id, current_password, new_password):
        """Change user password.
        
        Args:
            user_id (str): User ID
            current_password (str): Current password
            new_password (str): New password
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If validation fails
        """
        # Get existing user
        query = "SELECT password_hash FROM users WHERE user_id = %s"
        user = self.db.fetch_one(query, (user_id,))
        
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        if not self._verify_password(current_password, user["password_hash"]):
            raise ValueError("Current password is incorrect")
        
        # Validate new password
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Update password
        password_hash = self._hash_password(new_password)
        update_data = {
            "password_hash": password_hash,
            "updated_at": self.get_timestamp()
        }
        
        result = self.update(user_id, update_data)
        return result is not None
    
    def get_user_sales(self, user_id, start_date=None, end_date=None):
        """Get sales statistics for a user.
        
        Args:
            user_id (str): User ID
            start_date (str, optional): Start date for filtering (ISO format)
            end_date (str, optional): End date for filtering (ISO format)
            
        Returns:
            dict: Sales statistics
        """
        query = """
            SELECT 
                COUNT(i.invoice_id) as total_sales,
                SUM(i.total_amount) as total_amount,
                AVG(i.total_amount) as average_sale,
                COUNT(DISTINCT i.customer_id) as unique_customers
            FROM invoices i
            WHERE i.user_id = %s
        """
        params = [user_id]
        
        if start_date:
            query += " AND i.created_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND i.created_at <= %s"
            params.append(end_date)
        
        result = self.db.fetch_one(query, tuple(params))
        
        # Get additional payment statistics
        payment_query = """
            SELECT 
                p.payment_method,
                COUNT(p.payment_id) as count,
                SUM(p.amount) as total
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.invoice_id
            WHERE i.user_id = %s
        """
        payment_params = [user_id]
        
        if start_date:
            payment_query += " AND p.payment_date >= %s"
            payment_params.append(start_date)
        
        if end_date:
            payment_query += " AND p.payment_date <= %s"
            payment_params.append(end_date)
        
        payment_query += " GROUP BY p.payment_method"
        
        payment_stats = self.db.fetch_all(payment_query, tuple(payment_params))
        
        # Combine results
        stats = result or {}
        stats["payment_methods"] = payment_stats
        
        return stats
    
    def _hash_password(self, password):
        """Hash a password using bcrypt.
        
        Args:
            password (str): Plain text password
            
        Returns:
            str: Hashed password
        """
        # Convert password to bytes if it's a string
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        
        # Return the hashed password as a string
        return hashed.decode('utf-8')
    
    def _verify_password(self, plain_password, hashed_password):
        """Verify a password against its hash.
        
        Args:
            plain_password (str): Plain text password
            hashed_password (str): Hashed password
            
        Returns:
            bool: True if password matches, False otherwise
        """
        # Convert inputs to bytes if they're strings
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        
        # Verify the password
        return bcrypt.checkpw(plain_password, hashed_password)
    
    def _validate_user_data(self, username, password, full_name, role, email, phone):
        """Validate user data.
        
        Args:
            username (str): Username
            password (str): Password
            full_name (str): Full name
            role (str): Role
            email (str, optional): Email
            phone (str, optional): Phone
            
        Raises:
            ValueError: If validation fails
        """
        # Validate username
        if not username or not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            raise ValueError("Username must be 3-20 characters and contain only letters, numbers, and underscores")
        
        # Validate password
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Validate full name
        if not full_name or len(full_name) < 2:
            raise ValueError("Full name is required")
        
        # Validate role
        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(self.VALID_ROLES)}")
        
        # Validate email if provided
        if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Invalid email format")
