"""
Invoice Item model for POS application.
Handles invoice item data and related operations.
"""

from .base_model import BaseModel


class InvoiceItem(BaseModel):
    """Invoice Item model for managing items in invoices."""
    
    def __init__(self, db):
        """Initialize InvoiceItem model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "invoice_items"
        self.primary_key = "invoice_item_id"
    
    def add_item_to_invoice(self, invoice_id, product_id, quantity, 
                           unit_price=None, discount_price=None):
        """Add an item to an invoice.
        
        Args:
            invoice_id (str): Invoice ID
            product_id (str): Product ID
            quantity (int): Quantity
            unit_price (float, optional): Override unit price
            discount_price (float, optional): Discount price
            
        Returns:
            dict: Created invoice item data
            
        Raises:
            ValueError: If validation fails or insufficient stock
        """
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Check if invoice exists and is not completed or voided
            query = "SELECT * FROM invoices WHERE invoice_id = %s"
            invoice = self.db.fetch_one(query, (invoice_id,))
            
            if not invoice:
                raise ValueError("Invoice not found")
            
            if invoice["status"] != "DRAFT":
                raise ValueError("Cannot add items to a completed or voided invoice")
            
            # Get product information
            query = """
                SELECT p.*, COALESCE(s.quantity, 0) as stock_quantity
                FROM products p
                LEFT JOIN stock s ON p.product_id = s.product_id
                WHERE p.product_id = %s
            """
            product = self.db.fetch_one(query, (product_id,))
            
            if not product:
                raise ValueError("Product not found")
            
            if not product["is_active"]:
                raise ValueError("Product is not active")
            
            # Check if there's enough stock
            if product["stock_quantity"] < quantity:
                raise ValueError(f"Insufficient stock. Available: {product['stock_quantity']}, Requested: {quantity}")
            
            # Check if item already exists in invoice
            query = "SELECT * FROM invoice_items WHERE invoice_id = %s AND product_id = %s"
            existing_item = self.db.fetch_one(query, (invoice_id, product_id))
            
            if existing_item:
                # Update existing item
                new_quantity = existing_item["quantity"] + quantity
                
                # Recheck stock with new quantity
                if product["stock_quantity"] < new_quantity:
                    raise ValueError(f"Insufficient stock. Available: {product['stock_quantity']}, Requested: {new_quantity}")
                
                # Use provided unit price or existing item's unit price
                if unit_price is None:
                    unit_price = existing_item["unit_price"]
                
                # Calculate subtotal
                if discount_price is not None and discount_price >= 0:
                    subtotal = new_quantity * discount_price
                else:
                    subtotal = new_quantity * unit_price
                
                # Update item
                update_data = {
                    "quantity": new_quantity,
                    "unit_price": unit_price,
                    "discount_price": discount_price,
                    "subtotal": subtotal,
                    "updated_at": self.get_timestamp()
                }
                
                result = self.update(existing_item["invoice_item_id"], update_data)
            else:
                # Create new item
                # Use provided unit price or product's selling price
                if unit_price is None:
                    unit_price = product["selling_price"]
                
                # Calculate subtotal
                if discount_price is not None and discount_price >= 0:
                    subtotal = quantity * discount_price
                else:
                    subtotal = quantity * unit_price
                
                # Create item data
                item_id = self.generate_id()
                now = self.get_timestamp()
                
                item_data = {
                    "invoice_item_id": item_id,
                    "invoice_id": invoice_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount_price": discount_price,
                    "subtotal": subtotal,
                    "created_at": now,
                    "updated_at": now
                }
                
                result = self.create(item_data)
            
            # Update invoice total
            from .invoice import Invoice
            invoice_model = Invoice(self.db)
            invoice_model.update_invoice_total(invoice_id)
            
            # Commit transaction
            self.db.commit_transaction()
            
            return result
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def update_item_quantity(self, invoice_item_id, quantity):
        """Update the quantity of an invoice item.
        
        Args:
            invoice_item_id (str): Invoice item ID
            quantity (int): New quantity
            
        Returns:
            dict: Updated invoice item data
            
        Raises:
            ValueError: If validation fails or insufficient stock
        """
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Get existing item
            query = """
                SELECT ii.*, i.status as invoice_status
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.invoice_id
                WHERE ii.invoice_item_id = %s
            """
            item = self.db.fetch_one(query, (invoice_item_id,))
            
            if not item:
                raise ValueError("Invoice item not found")
            
            if item["invoice_status"] != "DRAFT":
                raise ValueError("Cannot update items in a completed or voided invoice")
            
            # Get product information and check stock
            query = """
                SELECT p.*, COALESCE(s.quantity, 0) as stock_quantity
                FROM products p
                LEFT JOIN stock s ON p.product_id = s.product_id
                WHERE p.product_id = %s
            """
            product = self.db.fetch_one(query, (item["product_id"],))
            
            # Check new stock requirement
            # If decreasing quantity, no need to check stock
            # If increasing, check if there's enough additional stock
            if quantity > item["quantity"]:
                additional_needed = quantity - item["quantity"]
                if product["stock_quantity"] < additional_needed:
                    raise ValueError(f"Insufficient stock. Available: {product['stock_quantity']}, Additional needed: {additional_needed}")
            
            # Calculate subtotal
            if item["discount_price"] is not None:
                subtotal = quantity * item["discount_price"]
            else:
                subtotal = quantity * item["unit_price"]
            
            # Update item
            update_data = {
                "quantity": quantity,
                "subtotal": subtotal,
                "updated_at": self.get_timestamp()
            }
            
            result = self.update(invoice_item_id, update_data)
            
            # Update invoice total
            from .invoice import Invoice
            invoice_model = Invoice(self.db)
            invoice_model.update_invoice_total(item["invoice_id"])
            
            # Commit transaction
            self.db.commit_transaction()
            
            return result
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def update_item_discount(self, invoice_item_id, discount_price=None):
        """Update the discount price of an invoice item.
        
        Args:
            invoice_item_id (str): Invoice item ID
            discount_price (float, optional): New discount price (None to remove discount)
            
        Returns:
            dict: Updated invoice item data
            
        Raises:
            ValueError: If validation fails
        """
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Get existing item
            query = """
                SELECT ii.*, i.status as invoice_status
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.invoice_id
                WHERE ii.invoice_item_id = %s
            """
            item = self.db.fetch_one(query, (invoice_item_id,))
            
            if not item:
                raise ValueError("Invoice item not found")
            
            if item["invoice_status"] != "DRAFT":
                raise ValueError("Cannot update items in a completed or voided invoice")
            
            # Calculate subtotal
            if discount_price is not None:
                subtotal = item["quantity"] * discount_price
            else:
                subtotal = item["quantity"] * item["unit_price"]
            
            # Update item
            update_data = {
                "discount_price": discount_price,
                "subtotal": subtotal,
                "updated_at": self.get_timestamp()
            }
            
            result = self.update(invoice_item_id, update_data)
            
            # Update invoice total
            from .invoice import Invoice
            invoice_model = Invoice(self.db)
            invoice_model.update_invoice_total(item["invoice_id"])
            
            # Commit transaction
            self.db.commit_transaction()
            
            return result
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def remove_item_from_invoice(self, invoice_item_id):
        """Remove an item from an invoice.
        
        Args:
            invoice_item_id (str): Invoice item ID
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If item cannot be removed
        """
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Get existing item
            query = """
                SELECT ii.*, i.status as invoice_status, i.invoice_id
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.invoice_id
                WHERE ii.invoice_item_id = %s
            """
            item = self.db.fetch_one(query, (invoice_item_id,))
            
            if not item:
                raise ValueError("Invoice item not found")
            
            if item["invoice_status"] != "DRAFT":
                raise ValueError("Cannot remove items from a completed or voided invoice")
            
            # Store invoice_id for later
            invoice_id = item["invoice_id"]
            
            # Delete item
            result = self.delete(invoice_item_id)
            
            # Update invoice total
            from .invoice import Invoice
            invoice_model = Invoice(self.db)
            invoice_model.update_invoice_total(invoice_id)
            
            # Commit transaction
            self.db.commit_transaction()
            
            return result
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def finalize_invoice(self, invoice_id):
        """Finalize an invoice by updating stock quantities.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            dict: Updated invoice data
            
        Raises:
            ValueError: If invoice cannot be finalized
        """
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Get invoice
            query = "SELECT * FROM invoices WHERE invoice_id = %s"
            invoice = self.db.fetch_one(query, (invoice_id,))
            
            if not invoice:
                raise ValueError("Invoice not found")
            
            if invoice["status"] != "DRAFT":
                raise ValueError("Invoice is already finalized or voided")
            
            # Get invoice items
            query = "SELECT * FROM invoice_items WHERE invoice_id = %s"
            items = self.db.fetch_all(query, (invoice_id,))
            
            if not items:
                raise ValueError("Invoice has no items")
            
            # Update stock for each item
            from models.stock import Stock
            stock_model = Stock(self.db)
            
            for item in items:
                # Remove quantity from stock
                stock_model.update_stock_quantity(
                    item["product_id"], 
                    -item["quantity"],  # Negative to remove from stock
                    f"Sale: {invoice['invoice_number']}", 
                    invoice_id
                )
            
            # Update invoice status
            from .invoice import Invoice
            invoice_model = Invoice(self.db)
            
            updated_invoice = invoice_model.update_invoice(invoice_id, {"status": "COMPLETED"})
            
            # Commit transaction
            self.db.commit_transaction()
            
            return updated_invoice
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
