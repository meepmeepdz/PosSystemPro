"""
Product model for POS application.
Handles product data and related operations.
"""

from .base_model import BaseModel


class Product(BaseModel):
    """Product model for managing products."""
    
    def __init__(self, db):
        """Initialize Product model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "products"
        self.primary_key = "product_id"
    
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
        # Validate input
        self._validate_product_data(name, sku, barcode, category_id, 
                                   purchase_price, selling_price, tax_rate)
        
        # Check if SKU already exists
        query = "SELECT sku FROM products WHERE sku = %s"
        existing_sku = self.db.fetch_one(query, (sku,))
        if existing_sku:
            raise ValueError("SKU already exists")
        
        # Check if barcode already exists if provided
        if barcode:
            query = "SELECT barcode FROM products WHERE barcode = %s"
            existing_barcode = self.db.fetch_one(query, (barcode,))
            if existing_barcode:
                raise ValueError("Barcode already exists")
        
        # Create product data
        product_id = self.generate_id()
        now = self.get_timestamp()
        
        product_data = {
            "product_id": product_id,
            "name": name,
            "sku": sku,
            "barcode": barcode,
            "category_id": category_id,
            "description": description,
            "purchase_price": purchase_price,
            "selling_price": selling_price,
            "tax_rate": tax_rate,
            "low_stock_threshold": low_stock_threshold,
            "is_active": is_active,
            "created_at": now,
            "updated_at": now
        }
        
        return self.create(product_data)
    
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
        # Get existing product
        existing_product = self.get_by_id(product_id)
        if not existing_product:
            raise ValueError("Product not found")
        
        # Validate input (partial validation based on what's being updated)
        update_data = {}
        
        if "name" in data:
            if not data["name"] or len(data["name"]) < 1:
                raise ValueError("Product name is required")
            update_data["name"] = data["name"]
        
        if "sku" in data and data["sku"] != existing_product["sku"]:
            # Check if new SKU already exists
            query = "SELECT sku FROM products WHERE sku = %s AND product_id != %s"
            sku_exists = self.db.fetch_one(query, (data["sku"], product_id))
            if sku_exists:
                raise ValueError("SKU already exists")
            
            if not data["sku"] or len(data["sku"]) < 1:
                raise ValueError("SKU is required")
            
            update_data["sku"] = data["sku"]
        
        if "barcode" in data and data["barcode"] != existing_product["barcode"]:
            # Check if new barcode already exists
            if data["barcode"]:  # Only check if barcode is not empty
                query = "SELECT barcode FROM products WHERE barcode = %s AND product_id != %s"
                barcode_exists = self.db.fetch_one(query, (data["barcode"], product_id))
                if barcode_exists:
                    raise ValueError("Barcode already exists")
            
            update_data["barcode"] = data["barcode"]
        
        if "category_id" in data:
            # Verify category exists
            query = "SELECT category_id FROM categories WHERE category_id = %s"
            category_exists = self.db.fetch_one(query, (data["category_id"],))
            if not category_exists:
                raise ValueError("Category not found")
            
            update_data["category_id"] = data["category_id"]
        
        if "purchase_price" in data:
            if data["purchase_price"] < 0:
                raise ValueError("Purchase price cannot be negative")
            update_data["purchase_price"] = data["purchase_price"]
        
        if "selling_price" in data:
            if data["selling_price"] < 0:
                raise ValueError("Selling price cannot be negative")
            update_data["selling_price"] = data["selling_price"]
        
        if "tax_rate" in data:
            if data["tax_rate"] < 0:
                raise ValueError("Tax rate cannot be negative")
            update_data["tax_rate"] = data["tax_rate"]
        
        if "description" in data:
            update_data["description"] = data["description"]
        
        if "low_stock_threshold" in data:
            if data["low_stock_threshold"] < 0:
                raise ValueError("Low stock threshold cannot be negative")
            update_data["low_stock_threshold"] = data["low_stock_threshold"]
        
        if "is_active" in data:
            update_data["is_active"] = bool(data["is_active"])
        
        # Update timestamp
        update_data["updated_at"] = self.get_timestamp()
        
        # Update product
        return self.update(product_id, update_data)
    
    def search_products(self, search_term=None, category_id=None, is_active=None, 
                         order_by="name", limit=100, offset=0):
        """Search for products with various filters.
        
        Args:
            search_term (str, optional): Search term for name, SKU, or barcode
            category_id (str, optional): Filter by category ID
            is_active (bool, optional): Filter by active status
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of products matching the search criteria
        """
        query = """
            SELECT p.*, c.name as category_name, 
                   COALESCE(s.quantity, 0) as stock_quantity
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN stock s ON p.product_id = s.product_id
            WHERE 1=1
        """
        params = []
        
        # Add search term filter
        if search_term:
            query += """ AND (
                p.name ILIKE %s OR 
                p.sku ILIKE %s OR 
                p.barcode ILIKE %s OR
                p.description ILIKE %s
            )"""
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        
        # Add category filter
        if category_id:
            query += " AND p.category_id = %s"
            params.append(category_id)
        
        # Add active filter
        if is_active is not None:
            query += " AND p.is_active = %s"
            params.append(is_active)
        
        # Add ORDER BY clause
        if order_by:
            query += f" ORDER BY p.{order_by}"
        
        # Add LIMIT and OFFSET clauses
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.db.fetch_all(query, tuple(params))
    
    def get_product_by_barcode(self, barcode):
        """Get a product by its barcode.
        
        Args:
            barcode (str): Barcode to look up
            
        Returns:
            dict: Product data or None if not found
        """
        query = """
            SELECT p.*, c.name as category_name, 
                   COALESCE(s.quantity, 0) as stock_quantity
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN stock s ON p.product_id = s.product_id
            WHERE p.barcode = %s
        """
        return self.db.fetch_one(query, (barcode,))
    
    def get_product_by_sku(self, sku):
        """Get a product by its SKU.
        
        Args:
            sku (str): SKU to look up
            
        Returns:
            dict: Product data or None if not found
        """
        query = """
            SELECT p.*, c.name as category_name, 
                   COALESCE(s.quantity, 0) as stock_quantity
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN stock s ON p.product_id = s.product_id
            WHERE p.sku = %s
        """
        return self.db.fetch_one(query, (sku,))
    
    def get_products_with_low_stock(self):
        """Get all products with stock below their threshold.
        
        Returns:
            list: List of products with low stock
        """
        query = """
            SELECT p.*, c.name as category_name, 
                   COALESCE(s.quantity, 0) as stock_quantity
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN stock s ON p.product_id = s.product_id
            WHERE p.is_active = true
              AND s.quantity < p.low_stock_threshold
            ORDER BY s.quantity ASC
        """
        return self.db.fetch_all(query)
    
    def get_product_sales_history(self, product_id, start_date=None, end_date=None):
        """Get sales history for a product.
        
        Args:
            product_id (str): Product ID
            start_date (str, optional): Start date for filtering (ISO format)
            end_date (str, optional): End date for filtering (ISO format)
            
        Returns:
            list: Sales history for the product
        """
        query = """
            SELECT ii.invoice_item_id, ii.invoice_id, ii.quantity, 
                   ii.unit_price, ii.discount_price, ii.subtotal,
                   i.invoice_number, i.created_at as sale_date,
                   u.username as seller_name,
                   c.customer_id, c.full_name as customer_name
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.invoice_id
            JOIN users u ON i.user_id = u.user_id
            LEFT JOIN customers c ON i.customer_id = c.customer_id
            WHERE ii.product_id = %s
        """
        params = [product_id]
        
        if start_date:
            query += " AND i.created_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND i.created_at <= %s"
            params.append(end_date)
        
        query += " ORDER BY i.created_at DESC"
        
        return self.db.fetch_all(query, tuple(params))
    
    def _validate_product_data(self, name, sku, barcode, category_id, 
                              purchase_price, selling_price, tax_rate):
        """Validate product data.
        
        Args:
            name (str): Product name
            sku (str): SKU
            barcode (str): Barcode
            category_id (str): Category ID
            purchase_price (float): Purchase price
            selling_price (float): Selling price
            tax_rate (float): Tax rate
            
        Raises:
            ValueError: If validation fails
        """
        # Validate name
        if not name or len(name) < 1:
            raise ValueError("Product name is required")
        
        # Validate SKU
        if not sku or len(sku) < 1:
            raise ValueError("SKU is required")
        
        # Validate category ID
        query = "SELECT category_id FROM categories WHERE category_id = %s"
        category_exists = self.db.fetch_one(query, (category_id,))
        if not category_exists:
            raise ValueError("Category not found")
        
        # Validate prices
        if purchase_price < 0:
            raise ValueError("Purchase price cannot be negative")
        
        if selling_price < 0:
            raise ValueError("Selling price cannot be negative")
        
        if tax_rate < 0:
            raise ValueError("Tax rate cannot be negative")
