"""
Invoice model for POS application.
Handles invoice data and related operations.
"""

from .base_model import BaseModel


class Invoice(BaseModel):
    """Invoice model for managing sales invoices."""
    
    # Invoice status constants
    STATUS_DRAFT = "DRAFT"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_VOIDED = "VOIDED"
    
    def __init__(self, db):
        """Initialize Invoice model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "invoices"
        self.primary_key = "invoice_id"
    
    def create_invoice(self, user_id, customer_id=None, status=STATUS_DRAFT, notes=None):
        """Create a new invoice.
        
        Args:
            user_id (str): ID of the user creating the invoice
            customer_id (str, optional): ID of the customer
            status (str, optional): Invoice status (default: DRAFT)
            notes (str, optional): Invoice notes
            
        Returns:
            dict: Created invoice data or None if failed
        """
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Generate invoice number
            invoice_number = self._generate_invoice_number()
            
            # Create invoice data
            invoice_id = self.generate_id()
            now = self.get_timestamp()
            
            invoice_data = {
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "user_id": user_id,
                "customer_id": customer_id,
                "total_amount": 0,  # Will be updated as items are added
                "status": status,
                "notes": notes,
                "created_at": now,
                "updated_at": now
            }
            
            # Create invoice
            invoice = self.create(invoice_data)
            
            # Commit transaction
            self.db.commit_transaction()
            
            return invoice
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def update_invoice(self, invoice_id, data):
        """Update invoice data.
        
        Args:
            invoice_id (str): ID of invoice to update
            data (dict): Data to update
            
        Returns:
            dict: Updated invoice data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        # Get existing invoice
        existing_invoice = self.get_by_id(invoice_id)
        if not existing_invoice:
            raise ValueError("Invoice not found")
        
        # Don't allow updating completed invoices
        if existing_invoice["status"] == self.STATUS_COMPLETED and "status" not in data:
            raise ValueError("Cannot update a completed invoice")
        
        # Don't allow updating voided invoices
        if existing_invoice["status"] == self.STATUS_VOIDED:
            raise ValueError("Cannot update a voided invoice")
        
        # Validate input
        update_data = {}
        
        if "customer_id" in data:
            update_data["customer_id"] = data["customer_id"]
        
        if "notes" in data:
            update_data["notes"] = data["notes"]
        
        if "status" in data:
            if data["status"] not in [self.STATUS_DRAFT, self.STATUS_COMPLETED, self.STATUS_VOIDED]:
                raise ValueError("Invalid invoice status")
            update_data["status"] = data["status"]
        
        # Update timestamp
        update_data["updated_at"] = self.get_timestamp()
        
        # Update invoice
        return self.update(invoice_id, update_data)
    
    def void_invoice(self, invoice_id, reason=None):
        """Void an invoice and revert all stock changes.
        
        Args:
            invoice_id (str): ID of invoice to void
            reason (str, optional): Reason for voiding
            
        Returns:
            dict: Voided invoice data
            
        Raises:
            ValueError: If invoice cannot be voided
        """
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Get existing invoice
            invoice = self.get_by_id(invoice_id)
            if not invoice:
                raise ValueError("Invoice not found")
            
            # Check if invoice can be voided
            if invoice["status"] == self.STATUS_VOIDED:
                raise ValueError("Invoice is already voided")
            
            # Get invoice items
            query = """
                SELECT ii.*, p.name as product_name
                FROM invoice_items ii
                JOIN products p ON ii.product_id = p.product_id
                WHERE ii.invoice_id = %s
            """
            items = self.db.fetch_all(query, (invoice_id,))
            
            # Revert stock changes for each item
            from models.stock import Stock
            stock_model = Stock(self.db)
            
            for item in items:
                # Add the quantity back to stock (opposite of what happened during sale)
                stock_model.update_stock_quantity(
                    item["product_id"], 
                    abs(item["quantity"]),  # Positive to add back to stock
                    f"Invoice void: {invoice['invoice_number']}", 
                    invoice_id
                )
            
            # Update invoice status
            update_data = {
                "status": self.STATUS_VOIDED,
                "notes": f"{invoice['notes'] or ''}\nVOIDED: {reason}" if reason else f"{invoice['notes'] or ''}\nVOIDED",
                "updated_at": self.get_timestamp()
            }
            
            voided_invoice = self.update(invoice_id, update_data)
            
            # Handle any payments already made
            query = "SELECT * FROM payments WHERE invoice_id = %s"
            payments = self.db.fetch_all(query, (invoice_id,))
            
            # Update cash register for each payment
            from models.cash_register import CashRegister
            register_model = CashRegister(self.db)
            
            for payment in payments:
                # Record a negative transaction to balance the payment
                register_model.record_transaction(
                    -payment["amount"],
                    "VOID",
                    f"Void payment for invoice {invoice['invoice_number']}",
                    payment["user_id"],
                    invoice_id
                )
            
            # Handle any customer debts
            query = "SELECT * FROM customer_debts WHERE invoice_id = %s AND is_paid = false"
            debts = self.db.fetch_all(query, (invoice_id,))
            
            # Update debts
            from models.customer_debt import CustomerDebt
            debt_model = CustomerDebt(self.db)
            
            for debt in debts:
                # Mark debt as paid (effectively cancelling it)
                debt_model.update_debt(
                    debt["debt_id"],
                    {
                        "is_paid": True,
                        "notes": f"{debt['notes'] or ''}\nCancelled due to voided invoice"
                    }
                )
            
            # Commit transaction
            self.db.commit_transaction()
            
            return voided_invoice
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def update_invoice_total(self, invoice_id):
        """Update the total amount of an invoice based on its items.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            dict: Updated invoice data
            
        Raises:
            ValueError: If invoice not found
        """
        # Get existing invoice
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        # Calculate total from items
        query = "SELECT SUM(subtotal) as total FROM invoice_items WHERE invoice_id = %s"
        result = self.db.fetch_one(query, (invoice_id,))
        
        total = result["total"] if result and result["total"] else 0
        
        # Update invoice total
        update_data = {
            "total_amount": total,
            "updated_at": self.get_timestamp()
        }
        
        return self.update(invoice_id, update_data)
    
    def get_invoice_with_items(self, invoice_id):
        """Get an invoice with all its items.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            dict: Invoice with items
        """
        # Get invoice
        query = """
            SELECT i.*, 
                   u.username as seller_name, 
                   c.full_name as customer_name,
                   c.phone as customer_phone,
                   c.email as customer_email,
                   c.address as customer_address,
                   c.tax_id as customer_tax_id,
                   COALESCE(p.total_paid, 0) as total_paid,
                   (CASE WHEN i.total_amount <= COALESCE(p.total_paid, 0) 
                         THEN true ELSE false END) as is_fully_paid
            FROM invoices i
            JOIN users u ON i.user_id = u.user_id
            LEFT JOIN customers c ON i.customer_id = c.customer_id
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) as total_paid
                FROM payments
                GROUP BY invoice_id
            ) p ON i.invoice_id = p.invoice_id
            WHERE i.invoice_id = %s
        """
        invoice = self.db.fetch_one(query, (invoice_id,))
        
        if not invoice:
            return None
        
        # Get invoice items
        query = """
            SELECT ii.*, 
                   p.name as product_name, 
                   p.sku,
                   p.tax_rate
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.product_id
            WHERE ii.invoice_id = %s
            ORDER BY ii.created_at
        """
        items = self.db.fetch_all(query, (invoice_id,))
        
        # Get payments
        query = """
            SELECT p.*,
                   u.username as user_name
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.invoice_id = %s
            ORDER BY p.payment_date
        """
        payments = self.db.fetch_all(query, (invoice_id,))
        
        # Add items and payments to invoice
        invoice["items"] = items
        invoice["payments"] = payments
        
        return invoice
    
    def search_invoices(self, search_term=None, customer_id=None, user_id=None, 
                         status=None, date_from=None, date_to=None,
                         is_paid=None, order_by="created_at DESC", 
                         limit=100, offset=0):
        """Search for invoices with various filters.
        
        Args:
            search_term (str, optional): Search term for invoice number or notes
            customer_id (str, optional): Filter by customer
            user_id (str, optional): Filter by user (seller)
            status (str, optional): Filter by status
            date_from (str, optional): Start date (ISO format)
            date_to (str, optional): End date (ISO format)
            is_paid (bool, optional): Filter by payment status
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of invoices matching the search criteria
        """
        query = """
            SELECT i.*, 
                   u.username as seller_name, 
                   c.full_name as customer_name,
                   COALESCE(p.total_paid, 0) as total_paid,
                   (CASE WHEN i.total_amount <= COALESCE(p.total_paid, 0) 
                         THEN true ELSE false END) as is_fully_paid,
                   (SELECT COUNT(*) FROM invoice_items ii WHERE ii.invoice_id = i.invoice_id) as item_count
            FROM invoices i
            JOIN users u ON i.user_id = u.user_id
            LEFT JOIN customers c ON i.customer_id = c.customer_id
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) as total_paid
                FROM payments
                GROUP BY invoice_id
            ) p ON i.invoice_id = p.invoice_id
            WHERE 1=1
        """
        params = []
        
        # Add search term filter
        if search_term:
            query += """ AND (
                i.invoice_number ILIKE %s OR 
                i.notes ILIKE %s
            )"""
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
        
        # Add customer filter
        if customer_id:
            query += " AND i.customer_id = %s"
            params.append(customer_id)
        
        # Add user filter
        if user_id:
            query += " AND i.user_id = %s"
            params.append(user_id)
        
        # Add status filter
        if status:
            query += " AND i.status = %s"
            params.append(status)
        
        # Add date filters
        if date_from:
            query += " AND i.created_at >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND i.created_at <= %s"
            params.append(date_to)
        
        # Add payment status filter
        if is_paid is not None:
            if is_paid:
                query += " AND i.total_amount <= COALESCE(p.total_paid, 0)"
            else:
                query += " AND (i.total_amount > COALESCE(p.total_paid, 0) OR p.total_paid IS NULL)"
        
        # Add ORDER BY clause
        if order_by:
            if order_by.startswith("seller_name"):
                # Special case for ordering by seller name
                direction = "DESC" if "DESC" in order_by else "ASC"
                query += f" ORDER BY u.username {direction}"
            elif order_by.startswith("customer_name"):
                # Special case for ordering by customer name
                direction = "DESC" if "DESC" in order_by else "ASC"
                query += f" ORDER BY c.full_name {direction} NULLS LAST"
            elif order_by.startswith("is_fully_paid"):
                # Special case for ordering by payment status
                direction = "DESC" if "DESC" in order_by else "ASC"
                query += f" ORDER BY is_fully_paid {direction}"
            else:
                query += f" ORDER BY i.{order_by}"
        
        # Add LIMIT and OFFSET clauses
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.db.fetch_all(query, tuple(params))
    
    def get_sales_summary(self, date_from=None, date_to=None, user_id=None):
        """Get a summary of sales for a period.
        
        Args:
            date_from (str, optional): Start date (ISO format)
            date_to (str, optional): End date (ISO format)
            user_id (str, optional): Filter by user (seller)
            
        Returns:
            dict: Sales summary statistics
        """
        # Base query for total sales
        query = """
            SELECT 
                COUNT(i.invoice_id) as total_invoices,
                SUM(i.total_amount) as total_sales,
                AVG(i.total_amount) as average_sale,
                COUNT(DISTINCT i.customer_id) as unique_customers,
                COUNT(DISTINCT i.user_id) as unique_sellers,
                COUNT(CASE WHEN i.status = 'VOIDED' THEN 1 END) as voided_invoices,
                SUM(CASE WHEN i.status = 'VOIDED' THEN i.total_amount ELSE 0 END) as voided_amount
            FROM invoices i
            WHERE i.status != 'DRAFT'
        """
        params = []
        
        # Add date filters
        if date_from:
            query += " AND i.created_at >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND i.created_at <= %s"
            params.append(date_to)
        
        # Add user filter
        if user_id:
            query += " AND i.user_id = %s"
            params.append(user_id)
        
        # Execute query
        summary = self.db.fetch_one(query, tuple(params))
        
        # Get payment method breakdown
        payment_query = """
            SELECT 
                p.payment_method,
                COUNT(p.payment_id) as count,
                SUM(p.amount) as total
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.invoice_id
            WHERE i.status != 'DRAFT'
        """
        payment_params = []
        
        # Add date filters
        if date_from:
            payment_query += " AND i.created_at >= %s"
            payment_params.append(date_from)
        
        if date_to:
            payment_query += " AND i.created_at <= %s"
            payment_params.append(date_to)
        
        # Add user filter
        if user_id:
            payment_query += " AND i.user_id = %s"
            payment_params.append(user_id)
        
        payment_query += " GROUP BY p.payment_method"
        
        payment_stats = self.db.fetch_all(payment_query, tuple(payment_params))
        
        # Get top selling products
        product_query = """
            SELECT 
                p.product_id,
                p.name as product_name,
                p.sku,
                SUM(ii.quantity) as quantity_sold,
                COUNT(DISTINCT ii.invoice_id) as invoice_count,
                SUM(ii.subtotal) as total_sales
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.product_id
            JOIN invoices i ON ii.invoice_id = i.invoice_id
            WHERE i.status = 'COMPLETED'
        """
        product_params = []
        
        # Add date filters
        if date_from:
            product_query += " AND i.created_at >= %s"
            product_params.append(date_from)
        
        if date_to:
            product_query += " AND i.created_at <= %s"
            product_params.append(date_to)
        
        # Add user filter
        if user_id:
            product_query += " AND i.user_id = %s"
            product_params.append(user_id)
        
        product_query += """
            GROUP BY p.product_id, p.name, p.sku
            ORDER BY quantity_sold DESC
            LIMIT 10
        """
        
        top_products = self.db.fetch_all(product_query, tuple(product_params))
        
        # Combine results
        result = summary or {}
        result["payment_methods"] = payment_stats
        result["top_products"] = top_products
        
        return result
    
    def _generate_invoice_number(self):
        """Generate a unique invoice number.
        
        Returns:
            str: Unique invoice number
        """
        # Get the current date in YYYYMMDD format
        from datetime import datetime
        date_prefix = datetime.now().strftime("%Y%m%d")
        
        # Get the maximum invoice number with this prefix
        query = """
            SELECT MAX(invoice_number) as max_number 
            FROM invoices 
            WHERE invoice_number LIKE %s
        """
        result = self.db.fetch_one(query, (f"{date_prefix}%",))
        
        if result and result["max_number"]:
            # Extract the numeric part and increment
            try:
                max_num = int(result["max_number"][8:])
                next_num = max_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        # Format the new invoice number
        return f"{date_prefix}{next_num:04d}"
