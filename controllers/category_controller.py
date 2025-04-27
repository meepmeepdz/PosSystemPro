"""
Category controller for POS application.
Handles category management operations.
"""

from models.category import Category


class CategoryController:
    """Controller for category operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.category_model = Category(db)
    
    def get_all_categories(self, order_by="name", include_inactive=True):
        """Get all categories.
        
        Args:
            order_by (str, optional): Column to order by
            include_inactive (bool, optional): Whether to include inactive categories
            
        Returns:
            list: List of categories
        """
        categories = self.category_model.get_all(order_by=order_by)
        
        # Filter out inactive categories if needed
        if not include_inactive:
            categories = [c for c in categories if c.get("is_active", True)]
            
        return categories
        
    def search_categories(self, search_term=None, include_inactive=False):
        """Search categories by name or description.
        
        Args:
            search_term (str, optional): Search term for name or description
            include_inactive (bool, optional): Whether to include inactive categories
            
        Returns:
            list: List of matching categories
        """
        # Use get_all if no search term
        if not search_term:
            categories = self.get_all_categories(include_inactive=include_inactive)
        else:
            # Execute search query
            query = """
                SELECT * FROM categories
                WHERE (name ILIKE %s OR description ILIKE %s)
                ORDER BY name
            """
            search_pattern = f"%{search_term}%"
            categories = self.db.fetch_all(query, (search_pattern, search_pattern))
            
        # Filter for active status if needed
        if not include_inactive:
            categories = [c for c in categories if c.get("is_active", True)]
            
        return categories
    
    def get_category_by_id(self, category_id):
        """Get a category by ID.
        
        Args:
            category_id (str): Category ID
            
        Returns:
            dict: Category data or None if not found
        """
        return self.category_model.get_by_id(category_id)
    
    def create_category(self, name, description=None, parent_id=None):
        """Create a new category.
        
        Args:
            name (str): Category name
            description (str, optional): Category description
            parent_id (str, optional): Parent category ID for hierarchical structure
            
        Returns:
            dict: Created category data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        return self.category_model.create_category(name, description, parent_id)
    
    def update_category(self, category_id, data):
        """Update category data.
        
        Args:
            category_id (str): ID of category to update
            data (dict): Data to update
            
        Returns:
            dict: Updated category data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        return self.category_model.update_category(category_id, data)
    
    def delete_category(self, category_id):
        """Delete a category if it has no associated products.
        
        Args:
            category_id (str): ID of category to delete
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If category has associated products or is a parent category
        """
        return self.category_model.delete_category(category_id)
    
    def get_category_tree(self):
        """Get all categories in a hierarchical structure.
        
        Returns:
            list: Categories with their children
        """
        return self.category_model.get_category_tree()
    
    def get_category_with_products(self, category_id):
        """Get a category with its associated products.
        
        Args:
            category_id (str): Category ID
            
        Returns:
            dict: Category with products
        """
        return self.category_model.get_category_with_products(category_id)
    
    def get_parent_categories(self):
        """Get all parent categories (those with no parent).
        
        Returns:
            list: Parent categories
        """
        return self.category_model.get_where("parent_id IS NULL", order_by="name")
    
    def get_subcategories(self, parent_id):
        """Get all subcategories of a parent category.
        
        Args:
            parent_id (str): Parent category ID
            
        Returns:
            list: Subcategories
        """
        return self.category_model.get_where("parent_id = %s", (parent_id,), order_by="name")
        
    def get_product_count(self, category_id):
        """Get the number of products in a category.
        
        Args:
            category_id (str): Category ID
            
        Returns:
            int: Number of products in the category
        """
        query = "SELECT COUNT(*) as count FROM products WHERE category_id = %s"
        result = self.db.fetch_one(query, (category_id,))
        return result["count"] if result else 0
