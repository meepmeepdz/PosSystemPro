"""
Stock model for POS application.
Handles stock data and related operations.
"""

from .base_model import BaseModel


class Stock(BaseModel):
    """Stock model for managing product stock."""
    
    def __init__(self, db):
        """Initialize Stock model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "stock"
        self.primary_key = "stock_id"
    
    def get_stock_by_product(self, product_id):
        """Get stock information for a product.
        
        Args:
            product_id (str): Product ID
            
        Returns:
            dict: Stock information or None if not found
        """
        query = """
            SELECT s.*, p.name as product_name, p.low_stock_threshold
            FROM stock s
            JOIN products p ON s.product_id = p.product_id
            WHERE s.product_id = %s
        """
        return self.db.fetch_one(query, (product_id,))
    
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
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Get current stock
            query = "SELECT * FROM stock WHERE product_id = %s"
            stock = self.db.fetch_one(query, (product_id,))
            
            if stock:
                # Update existing stock
                new_quantity = stock["quantity"] + quantity_change
                if new_quantity < 0:
                    raise ValueError("Stock quantity cannot be negative")
                
                update_query = "UPDATE stock SET quantity = %s, updated_at = %s WHERE stock_id = %s RETURNING *"
                updated_stock = self.db.fetch_one(update_query, (new_quantity, self.get_timestamp(), stock["stock_id"]))
            else:
                # Create new stock entry
                if quantity_change < 0:
                    raise ValueError("Cannot remove stock from non-existent inventory")
                
                stock_id = self.generate_id()
                now = self.get_timestamp()
                
                stock_data = {
                    "stock_id": stock_id,
                    "product_id": product_id,
                    "quantity": quantity_change,
                    "created_at": now,
                    "updated_at": now
                }
                
                updated_stock = self.create(stock_data)
            
            # Record stock movement
            self._create_stock_movement(product_id, quantity_change, reason, reference_id)
            
            # Commit transaction
            self.db.commit_transaction()
            
            return updated_stock
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def get_low_stock_products(self, limit=50, offset=0):
        """Get products with stock below their threshold.
        
        Args:
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of products with low stock
        """
        query = """
            SELECT p.*, c.name as category_name, 
                   s.quantity as stock_quantity, 
                   (p.low_stock_threshold - s.quantity) as shortage
            FROM products p
            JOIN stock s ON p.product_id = s.product_id
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_active = true
              AND s.quantity < p.low_stock_threshold
            ORDER BY shortage DESC
            LIMIT %s OFFSET %s
        """
        return self.db.fetch_all(query, (limit, offset))
    
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
        query = """
            SELECT sm.*, p.name as product_name, p.sku
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.product_id
            WHERE 1=1
        """
        params = []
        
        # Add product filter
        if product_id:
            query += " AND sm.product_id = %s"
            params.append(product_id)
        
        # Add date filters
        if start_date:
            query += " AND sm.created_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND sm.created_at <= %s"
            params.append(end_date)
        
        # Add movement type filter
        if movement_type:
            query += " AND sm.movement_type = %s"
            params.append(movement_type)
        
        # Add ORDER BY clause
        query += " ORDER BY sm.created_at DESC"
        
        # Add LIMIT and OFFSET clauses
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.db.fetch_all(query, tuple(params))
    
    def get_stock_value(self):
        """Get the total value of current stock.
        
        Returns:
            dict: Stock value statistics
        """
        query = """
            SELECT 
                COUNT(p.product_id) as total_products,
                SUM(s.quantity) as total_units,
                SUM(s.quantity * p.purchase_price) as total_cost_value,
                SUM(s.quantity * p.selling_price) as total_retail_value
            FROM stock s
            JOIN products p ON s.product_id = p.product_id
            WHERE p.is_active = true
        """
        return self.db.fetch_one(query)
    
    def _create_stock_movement(self, product_id, quantity_change, reason=None, reference_id=None):
        """Create a stock movement record.
        
        Args:
            product_id (str): Product ID
            quantity_change (int): Quantity change
            reason (str, optional): Reason for stock movement
            reference_id (str, optional): Reference ID
            
        Returns:
            dict: Created stock movement record
        """
        movement_id = self.generate_id()
        now = self.get_timestamp()
        
        # Determine movement type
        if quantity_change > 0:
            movement_type = "IN"
        elif quantity_change < 0:
            movement_type = "OUT"
        else:
            movement_type = "ADJUST"
        
        # Create movement data
        movement_data = {
            "movement_id": movement_id,
            "product_id": product_id,
            "quantity": abs(quantity_change),  # Store absolute value
            "movement_type": movement_type,
            "reason": reason,
            "reference_id": reference_id,
            "created_at": now
        }
        
        # Use StockMovement model to create record
        stock_movement = StockMovement(self.db)
        return stock_movement.create(movement_data)


class StockMovement(BaseModel):
    """Stock movement model for tracking inventory changes."""
    
    def __init__(self, db):
        """Initialize StockMovement model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "stock_movements"
        self.primary_key = "movement_id"
