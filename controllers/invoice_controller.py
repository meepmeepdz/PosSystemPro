"""
Invoice controller for POS application.
Handles invoice management operations.
"""

from models.invoice import Invoice
from models.invoice_item import InvoiceItem


class InvoiceController:
    """Controller for invoice operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.invoice_model = Invoice(db)
        self.invoice_item_model = InvoiceItem(db)
    
    def create_invoice(self, user_id, customer_id=None, notes=None):
        """Create a new invoice.
        
        Args:
            user_id (str): ID of the user creating the invoice
            customer_id (str, optional): ID of the customer
            notes (str, optional): Invoice notes
            
        Returns:
            dict: Created invoice data or None if failed
        """
        return self.invoice_model.create_invoice(user_id, customer_id, Invoice.STATUS_DRAFT, notes)
    
    def get_invoice_by_id(self, invoice_id):
        """Get an invoice by ID.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            dict: Invoice data or None if not found
        """
        return self.invoice_model.get_by_id(invoice_id)
    
    def get_invoice_with_items(self, invoice_id):
        """Get an invoice with all its items.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            dict: Invoice with items
        """
        return self.invoice_model.get_invoice_with_items(invoice_id)
    
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
        return self.invoice_model.update_invoice(invoice_id, data)
    
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
        return self.invoice_model.void_invoice(invoice_id, reason)
    
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
        return self.invoice_model.search_invoices(
            search_term, customer_id, user_id, 
            status, date_from, date_to,
            is_paid, order_by, 
            limit, offset
        )
    
    def get_sales_summary(self, date_from=None, date_to=None, user_id=None):
        """Get a summary of sales for a period.
        
        Args:
            date_from (str, optional): Start date (ISO format)
            date_to (str, optional): End date (ISO format)
            user_id (str, optional): Filter by user (seller)
            
        Returns:
            dict: Sales summary statistics
        """
        return self.invoice_model.get_sales_summary(date_from, date_to, user_id)
    
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
            dict: Created or updated invoice item data
            
        Raises:
            ValueError: If validation fails or insufficient stock
        """
        return self.invoice_item_model.add_item_to_invoice(
            invoice_id, product_id, quantity, unit_price, discount_price
        )
    
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
        return self.invoice_item_model.update_item_quantity(invoice_item_id, quantity)
    
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
        return self.invoice_item_model.update_item_discount(invoice_item_id, discount_price)
    
    def remove_item_from_invoice(self, invoice_item_id):
        """Remove an item from an invoice.
        
        Args:
            invoice_item_id (str): Invoice item ID
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If item cannot be removed
        """
        return self.invoice_item_model.remove_item_from_invoice(invoice_item_id)
    
    def finalize_invoice(self, invoice_id):
        """Finalize an invoice by updating stock quantities.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            dict: Updated invoice data
            
        Raises:
            ValueError: If invoice cannot be finalized
        """
        return self.invoice_item_model.finalize_invoice(invoice_id)
    
    def get_invoice_total(self, invoice_id):
        """Get the total amount of an invoice.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            float: Total amount
            
        Raises:
            ValueError: If invoice not found
        """
        invoice = self.invoice_model.get_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        return invoice["total_amount"]
