"""
User controller for POS application.
Handles user management operations.
"""

from models.user import User


class UserController:
    """Controller for user operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.user_model = User(db)
    
    def get_all_users(self, order_by="username", active_only=True):
        """Get all users.
        
        Args:
            order_by (str, optional): Column to order by
            active_only (bool, optional): Whether to return only active users
            
        Returns:
            list: List of users
        """
        filters = {}
        if active_only:
            filters["active"] = True
        
        users = self.user_model.get_all(order_by=order_by, filters=filters)
        
        # Remove password hashes from results
        for user in users:
            if "password_hash" in user:
                user.pop("password_hash")
        
        return users
    
    def get_user_by_id(self, user_id):
        """Get a user by ID.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: User data or None if not found
        """
        user = self.user_model.get_by_id(user_id)
        
        if user and "password_hash" in user:
            user.pop("password_hash")
        
        return user
    
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
        user = self.user_model.create_user(username, password, full_name, role, email, phone)
        
        if user and "password_hash" in user:
            user.pop("password_hash")
        
        return user
    
    def update_user(self, user_id, data):
        """Update user data.
        
        Args:
            user_id (str): ID of user to update
            data (dict): Data to update
            
        Returns:
            dict: Updated user data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        user = self.user_model.update_user(user_id, data)
        
        if user and "password_hash" in user:
            user.pop("password_hash")
        
        return user
    
    def deactivate_user(self, user_id):
        """Deactivate a user.
        
        Args:
            user_id (str): ID of user to deactivate
            
        Returns:
            dict: Updated user data or None if failed
            
        Raises:
            ValueError: If deactivation fails
        """
        # Can't deactivate the last active admin
        if self.is_last_active_admin(user_id):
            raise ValueError("Cannot deactivate the only active admin user")
        
        return self.user_model.update_user(user_id, {"active": False})
    
    def activate_user(self, user_id):
        """Activate a user.
        
        Args:
            user_id (str): ID of user to activate
            
        Returns:
            dict: Updated user data or None if failed
            
        Raises:
            ValueError: If activation fails
        """
        return self.user_model.update_user(user_id, {"active": True})
    
    def is_last_active_admin(self, user_id):
        """Check if a user is the last active admin.
        
        Args:
            user_id (str): User ID to check
            
        Returns:
            bool: True if user is the last active admin, False otherwise
        """
        # Get the user to check their role
        user = self.user_model.get_by_id(user_id)
        if not user or user["role"] != User.ROLE_ADMIN or not user["active"]:
            return False
        
        # Count active admins
        query = """
            SELECT COUNT(*) as count
            FROM users
            WHERE role = %s AND active = true
        """
        result = self.db.fetch_one(query, (User.ROLE_ADMIN,))
        
        # If there's only one active admin and it's this user, they're the last
        return result and result["count"] == 1
    
    def get_user_sales(self, user_id, start_date=None, end_date=None):
        """Get sales statistics for a user.
        
        Args:
            user_id (str): User ID
            start_date (str, optional): Start date for filtering (ISO format)
            end_date (str, optional): End date for filtering (ISO format)
            
        Returns:
            dict: Sales statistics
        """
        return self.user_model.get_user_sales(user_id, start_date, end_date)
    
    def set_valid_roles(self):
        """Get valid user roles.
        
        Returns:
            list: List of valid user roles
        """
        return User.VALID_ROLES
