"""
Category model for POS application.
Handles category data and related operations.
"""

from .base_model import BaseModel


class Category(BaseModel):
    """Category model for managing product categories."""
    
    def __init__(self, db):
        """Initialize Category model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "categories"
        self.primary_key = "category_id"
    
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
        # Validate input
        self._validate_category_data(name, parent_id)
        
        # Check if name already exists
        query = "SELECT name FROM categories WHERE name = %s"
        existing_name = self.db.fetch_one(query, (name,))
        if existing_name:
            raise ValueError("Category name already exists")
        
        # Create category data
        category_id = self.generate_id()
        now = self.get_timestamp()
        
        category_data = {
            "category_id": category_id,
            "name": name,
            "description": description,
            "parent_id": parent_id,
            "created_at": now,
            "updated_at": now
        }
        
        return self.create(category_data)
    
    def update_category(self, category_id, data):
        """Update category data.
        
        Args:
            category_id (str): ID of category to update
            data (dict): Data to update (name, description, parent_id)
            
        Returns:
            dict: Updated category data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        # Get existing category
        existing_category = self.get_by_id(category_id)
        if not existing_category:
            raise ValueError("Category not found")
        
        # Validate input
        update_data = {}
        
        if "name" in data and data["name"] != existing_category["name"]:
            # Check if new name already exists
            query = "SELECT name FROM categories WHERE name = %s AND category_id != %s"
            name_exists = self.db.fetch_one(query, (data["name"], category_id))
            if name_exists:
                raise ValueError("Category name already exists")
            
            if not data["name"] or len(data["name"]) < 1:
                raise ValueError("Category name is required")
            
            update_data["name"] = data["name"]
        
        if "description" in data:
            update_data["description"] = data["description"]
        
        if "parent_id" in data:
            # Don't allow self-reference
            if data["parent_id"] == category_id:
                raise ValueError("Category cannot be its own parent")
            
            # Don't allow circular references
            if data["parent_id"] is not None:
                self._check_circular_reference(category_id, data["parent_id"])
            
            update_data["parent_id"] = data["parent_id"]
        
        # Update timestamp
        update_data["updated_at"] = self.get_timestamp()
        
        # Update category
        return self.update(category_id, update_data)
    
    def delete_category(self, category_id):
        """Delete a category if it has no associated products.
        
        Args:
            category_id (str): ID of category to delete
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If category has associated products or is a parent category
        """
        # Check if category is a parent to other categories
        query = "SELECT category_id FROM categories WHERE parent_id = %s"
        child_categories = self.db.fetch_all(query, (category_id,))
        if child_categories:
            raise ValueError("Cannot delete category with child categories")
        
        # Check if category has associated products
        query = "SELECT product_id FROM products WHERE category_id = %s LIMIT 1"
        associated_products = self.db.fetch_one(query, (category_id,))
        if associated_products:
            raise ValueError("Cannot delete category with associated products")
        
        # Delete category
        return self.delete(category_id)
    
    def get_category_tree(self):
        """Get all categories in a hierarchical structure.
        
        Returns:
            list: Categories with their children
        """
        # Get all categories
        query = """
            SELECT c.*, 
                   COUNT(p.product_id) as product_count
            FROM categories c
            LEFT JOIN products p ON c.category_id = p.category_id
            GROUP BY c.category_id
            ORDER BY c.name
        """
        categories = self.db.fetch_all(query)
        
        # Build category tree
        category_map = {category["category_id"]: dict(category, children=[]) for category in categories}
        
        # Root categories have no parent
        root_categories = []
        
        # Organize into hierarchical structure
        for category_id, category in category_map.items():
            parent_id = category["parent_id"]
            if parent_id is None:
                root_categories.append(category)
            elif parent_id in category_map:
                category_map[parent_id]["children"].append(category)
        
        return root_categories
    
    def get_category_with_products(self, category_id):
        """Get a category with its associated products.
        
        Args:
            category_id (str): Category ID
            
        Returns:
            dict: Category with products
        """
        # Get category
        category = self.get_by_id(category_id)
        if not category:
            return None
        
        # Get products in category
        query = """
            SELECT p.*, COALESCE(s.quantity, 0) as stock_quantity
            FROM products p
            LEFT JOIN stock s ON p.product_id = s.product_id
            WHERE p.category_id = %s
            ORDER BY p.name
        """
        products = self.db.fetch_all(query, (category_id,))
        
        # Add products to category
        category["products"] = products
        
        return category
    
    def _validate_category_data(self, name, parent_id=None):
        """Validate category data.
        
        Args:
            name (str): Category name
            parent_id (str, optional): Parent category ID
            
        Raises:
            ValueError: If validation fails
        """
        # Validate name
        if not name or len(name) < 1:
            raise ValueError("Category name is required")
        
        # Validate parent_id if provided
        if parent_id:
            query = "SELECT category_id FROM categories WHERE category_id = %s"
            parent_exists = self.db.fetch_one(query, (parent_id,))
            if not parent_exists:
                raise ValueError("Parent category not found")
    
    def _check_circular_reference(self, category_id, parent_id):
        """Check if setting parent_id would create a circular reference.
        
        Args:
            category_id (str): Category ID
            parent_id (str): Potential parent category ID
            
        Raises:
            ValueError: If circular reference would be created
        """
        current_parent_id = parent_id
        
        # Follow the parent chain up to 100 levels (to prevent infinite loops)
        for _ in range(100):
            if current_parent_id is None:
                # Reached a root category, no circular reference
                return
            
            if current_parent_id == category_id:
                # Found circular reference
                raise ValueError("Circular reference detected in category hierarchy")
            
            # Get the next parent
            query = "SELECT parent_id FROM categories WHERE category_id = %s"
            parent = self.db.fetch_one(query, (current_parent_id,))
            if not parent:
                # Parent not found, no circular reference
                return
            
            current_parent_id = parent["parent_id"]
        
        # If we get here, the chain is too long
        raise ValueError("Category hierarchy is too deep")
