"""
Product controller for POS application.
Handles product management operations.
"""

from models.product import Product


class ProductController:
    """Controller for product operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.product_model = Product(db)
    
    def get_all_products(self, include_inactive=False, order_by="name", limit=None, offset=None):
        """Get all products.
        
        Args:
            include_inactive (bool, optional): Whether to include inactive products
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of products
        """
        filters = {}
        if not include_inactive:
            filters["is_active"] = True
        
        return self.product_model.get_all(order_by=order_by, limit=limit, offset=offset, filters=filters)
    
    def get_product_by_id(self, product_id):
        """Get a product by ID.
        
        Args:
            product_id (str): Product ID
            
        Returns:
            dict: Product data or None if not found
        """
        return self.product_model.get_by_id(product_id)
    
    def create_product(self, name, sku, barcode, category_id, purchase_price, 
                       selling_price, description=None, tax_rate=0, 
                       low_stock_threshold=10, is_active=True):
        """Create a new product.
        
        Args:
            name (str): Product name
            sku (str): Stock Keeping Unit - unique identifier
            barcode (str): Barcode (EAN, UPC, etc.)
            category_id (str): Category ID
            purchase_price (float): Purchase price
            selling_price (float): Selling price
            description (str, optional): Product description
            tax_rate (float, optional): Tax rate percentage
            low_stock_threshold (int, optional): Stock level for alerts
            is_active (bool, optional): Whether product is active
            
        Returns:
            dict: Created product data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        return self.product_model.create_product(
            name, sku, barcode, category_id, purchase_price, 
            selling_price, description, tax_rate, 
            low_stock_threshold, is_active
        )
    
    def update_product(self, product_id, data):
        """Update product data.
        
        Args:
            product_id (str): ID of product to update
            data (dict): Data to update
            
        Returns:
            dict: Updated product data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        return self.product_model.update_product(product_id, data)
    
    def search_products(self, search_term=None, category_id=None, is_active=None, 
                         order_by="name", limit=100, offset=0, include_inactive=None):
        """Search for products with various filters.
        
        Args:
            search_term (str, optional): Search term for name, SKU, or barcode
            category_id (str, optional): Filter by category ID
            is_active (bool, optional): Filter by active status
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            include_inactive (bool, optional): Whether to include inactive products (overrides is_active)
            
        Returns:
            list: List of products matching the search criteria
        """
        # If include_inactive is explicitly set, use it to determine is_active
        if include_inactive is not None:
            is_active = None if include_inactive else True
            
        return self.product_model.search_products(
            search_term, category_id, is_active, order_by, limit, offset
        )
    
    def get_product_by_barcode(self, barcode):
        """Get a product by its barcode.
        
        Args:
            barcode (str): Barcode to look up
            
        Returns:
            dict: Product data or None if not found
        """
        return self.product_model.get_product_by_barcode(barcode)
    
    def get_product_by_sku(self, sku):
        """Get a product by its SKU.
        
        Args:
            sku (str): SKU to look up
            
        Returns:
            dict: Product data or None if not found
        """
        return self.product_model.get_product_by_sku(sku)
    
    def get_products_with_low_stock(self):
        """Get all products with stock below their threshold.
        
        Returns:
            list: List of products with low stock
        """
        return self.product_model.get_products_with_low_stock()
    
    def get_product_sales_history(self, product_id, start_date=None, end_date=None):
        """Get sales history for a product.
        
        Args:
            product_id (str): Product ID
            start_date (str, optional): Start date for filtering (ISO format)
            end_date (str, optional): End date for filtering (ISO format)
            
        Returns:
            list: Sales history for the product
        """
        return self.product_model.get_product_sales_history(product_id, start_date, end_date)
    
    def deactivate_product(self, product_id):
        """Deactivate a product.
        
        Args:
            product_id (str): ID of product to deactivate
            
        Returns:
            dict: Updated product data or None if failed
            
        Raises:
            ValueError: If deactivation fails
        """
        return self.product_model.update_product(product_id, {"is_active": False})
    
    def activate_product(self, product_id):
        """Activate a product.
        
        Args:
            product_id (str): ID of product to activate
            
        Returns:
            dict: Updated product data or None if failed
            
        Raises:
            ValueError: If activation fails
        """
        return self.product_model.update_product(product_id, {"is_active": True})
