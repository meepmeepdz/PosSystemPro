"""
Authentication controller for POS application.
Handles user authentication and session management.
"""

from models.user import User


class AuthController:
    """Controller for authentication operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.user_model = User(db)
        self.current_user = None
    
    def login(self, username, password):
        """Authenticate a user with username and password.
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            dict: User data if authenticated, None otherwise
        """
        user = self.user_model.authenticate(username, password)
        if user:
            self.current_user = user
        return user
    
    def logout(self):
        """Log out the current user.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.current_user:
            self.current_user = None
            return True
        return False
    
    def get_current_user(self):
        """Get the currently authenticated user.
        
        Returns:
            dict: Current user data or None if not authenticated
        """
        return self.current_user
    
    def change_password(self, user_id, current_password, new_password):
        """Change a user's password.
        
        Args:
            user_id (str): User ID
            current_password (str): Current password
            new_password (str): New password
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If password change fails
        """
        return self.user_model.change_password(user_id, current_password, new_password)
    
    def check_permission(self, required_role):
        """Check if the current user has the required role.
        
        Args:
            required_role (str or list): Required role(s) for access
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        if not self.current_user:
            return False
        
        # Admin role has access to everything
        if self.current_user["role"] == User.ROLE_ADMIN:
            return True
        
        # Convert required_role to list if it's a single string
        if isinstance(required_role, str):
            required_role = [required_role]
        
        # Check if user role is in the required roles
        return self.current_user["role"] in required_role
    
    def is_admin(self):
        """Check if the current user is an admin.
        
        Returns:
            bool: True if admin, False otherwise
        """
        if not self.current_user:
            return False
        return self.current_user["role"] == User.ROLE_ADMIN
    
    def is_manager_or_admin(self):
        """Check if the current user is a manager or admin.
        
        Returns:
            bool: True if manager or admin, False otherwise
        """
        if not self.current_user:
            return False
        return self.current_user["role"] in [User.ROLE_ADMIN, User.ROLE_MANAGER]
