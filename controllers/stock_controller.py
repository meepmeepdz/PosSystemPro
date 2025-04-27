"""
Stock controller for POS application.
Handles stock management operations.
"""

from models.stock import Stock


class StockController:
    """Controller for stock operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.stock_model = Stock(db)
    
    def get_stock_by_product(self, product_id):
        """Get stock information for a product.
        
        Args:
            product_id (str): Product ID
            
        Returns:
            dict: Stock information or None if not found
        """
        return self.stock_model.get_stock_by_product(product_id)
        
    def get_stock_level(self, product_id):
        """Get the current stock level for a product.
        
        Args:
            product_id (str): Product ID
            
        Returns:
            int: Current stock level (0 if no stock record exists)
        """
        stock = self.get_stock_by_product(product_id)
        if stock and "quantity" in stock:
            return stock["quantity"]
        return 0
    
    def update_stock_quantity(self, product_id, quantity_change, reason=None, reference_id=None):
        """Update stock quantity for a product and record the movement.
        
        Args:
            product_id (str): Product ID
            quantity_change (int): Quantity to add (positive) or remove (negative)
            reason (str, optional): Reason for stock movement
            reference_id (str, optional): Reference ID (e.g., invoice_id, purchase_id)
            
        Returns:
            dict: Updated stock information
            
        Raises:
            ValueError: If resulting stock would be negative
        """
        return self.stock_model.update_stock_quantity(
            product_id, quantity_change, reason, reference_id
        )
    
    def get_low_stock_products(self, limit=50, offset=0):
        """Get products with stock below their threshold.
        
        Args:
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of products with low stock
        """
        return self.stock_model.get_low_stock_products(limit, offset)
    
    def get_stock_movements(self, product_id=None, start_date=None, end_date=None, 
                           movement_type=None, limit=100, offset=0):
        """Get stock movements with optional filters.
        
        Args:
            product_id (str, optional): Filter by product
            start_date (str, optional): Start date (ISO format)
            end_date (str, optional): End date (ISO format)
            movement_type (str, optional): Filter by movement type
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of stock movements
        """
        return self.stock_model.get_stock_movements(
            product_id, start_date, end_date, movement_type, limit, offset
        )
    
    def get_stock_value(self):
        """Get the total value of current stock.
        
        Returns:
            dict: Stock value statistics
        """
        return self.stock_model.get_stock_value()
    
    def add_stock(self, product_id, quantity, reason="Stock addition", reference_id=None):
        """Add stock to a product.
        
        Args:
            product_id (str): Product ID
            quantity (int): Quantity to add
            reason (str, optional): Reason for addition
            reference_id (str, optional): Reference ID
            
        Returns:
            dict: Updated stock information
            
        Raises:
            ValueError: If validation fails
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        
        return self.stock_model.update_stock_quantity(
            product_id, quantity, reason, reference_id
        )
    
    def remove_stock(self, product_id, quantity, reason="Stock removal", reference_id=None):
        """Remove stock from a product.
        
        Args:
            product_id (str): Product ID
            quantity (int): Quantity to remove
            reason (str, optional): Reason for removal
            reference_id (str, optional): Reference ID
            
        Returns:
            dict: Updated stock information
            
        Raises:
            ValueError: If validation fails or insufficient stock
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        
        return self.stock_model.update_stock_quantity(
            product_id, -quantity, reason, reference_id
        )
    
    def adjust_stock(self, product_id, new_quantity, reason="Stock adjustment"):
        """Adjust stock to a specific quantity.
        
        Args:
            product_id (str): Product ID
            new_quantity (int): New quantity
            reason (str, optional): Reason for adjustment
            
        Returns:
            dict: Updated stock information
            
        Raises:
            ValueError: If validation fails
        """
        if new_quantity < 0:
            raise ValueError("New quantity cannot be negative")
        
        # Get current stock
        current_stock = self.get_stock_by_product(product_id)
        
        if not current_stock:
            # If no stock exists, add the new quantity
            return self.add_stock(product_id, new_quantity, reason)
        
        # Get the current quantity, defaulting to 0 if None or not present
        current_quantity = 0
        if current_stock and "quantity" in current_stock:
            current_quantity = current_stock["quantity"]
        
        # Calculate difference
        difference = new_quantity - current_quantity
        
        if difference == 0:
            return current_stock
        
        # Update stock
        return self.stock_model.update_stock_quantity(
            product_id, difference, reason, None
        )
