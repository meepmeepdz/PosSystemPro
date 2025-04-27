"""
Payment controller for POS application.
Handles payment management operations.
"""

from models.payment import Payment


class PaymentController:
    """Controller for payment operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.payment_model = Payment(db)
    
    def create_payment(self, invoice_id, user_id, amount, payment_method, reference_number=None, notes=None):
        """Create a new payment.
        
        Args:
            invoice_id (str): Invoice ID
            user_id (str): User ID making the payment
            amount (float): Payment amount
            payment_method (str): Payment method
            reference_number (str, optional): Reference number for card/check payments
            notes (str, optional): Payment notes
            
        Returns:
            dict: Created payment data
            
        Raises:
            ValueError: If validation fails
        """
        return self.payment_model.create_payment(
            invoice_id, user_id, amount, payment_method, reference_number, notes
        )
    
    def get_invoice_payments(self, invoice_id):
        """Get all payments for an invoice.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            list: List of payments
        """
        return self.payment_model.get_invoice_payments(invoice_id)
    
    def get_payment_total(self, invoice_id):
        """Get the total amount paid for an invoice.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            float: Total amount paid
        """
        return self.payment_model.get_payment_total(invoice_id)
    
    def calculate_change(self, invoice_id, tendered_amount):
        """Calculate change due for a cash payment.
        
        Args:
            invoice_id (str): Invoice ID
            tendered_amount (float): Amount tendered
            
        Returns:
            dict: Dictionary with remaining amount and change due
            
        Raises:
            ValueError: If invoice not found
        """
        return self.payment_model.calculate_change(invoice_id, tendered_amount)
    
    def void_payment(self, payment_id, reason=None):
        """Void a payment and update related records.
        
        Args:
            payment_id (str): Payment ID
            reason (str, optional): Reason for voiding
            
        Returns:
            dict: Result of operation
            
        Raises:
            ValueError: If payment cannot be voided
        """
        return self.payment_model.void_payment(payment_id, reason)
    
    def get_payment_methods_report(self, date_from=None, date_to=None, user_id=None):
        """Get a report of payments by method.
        
        Args:
            date_from (str, optional): Start date (ISO format)
            date_to (str, optional): End date (ISO format)
            user_id (str, optional): Filter by user
            
        Returns:
            list: Payment method summary
        """
        return self.payment_model.get_payment_methods_report(date_from, date_to, user_id)
    
    def search_payments(self, date_from=None, date_to=None, payment_method=None, invoice_id=None, user_id=None, limit=100, offset=0):
        """Search payments with various filters.
        
        Args:
            date_from (str, optional): Start date in ISO format
            date_to (str, optional): End date in ISO format
            payment_method (str, optional): Filter by payment method
            invoice_id (str, optional): Filter by invoice ID
            user_id (str, optional): Filter by user ID
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of payments matching the criteria
        """
        filters = {}
        
        # Add filters based on parameters
        if payment_method and payment_method != "All Methods":
            filters["payment_method"] = payment_method
            
        if invoice_id:
            filters["invoice_id"] = invoice_id
            
        if user_id:
            filters["user_id"] = user_id
            
        # Pass date filters to model
        return self.payment_model.search_payments(filters, date_from, date_to, limit, offset)

    def get_payment_methods(self):
        """Get valid payment methods.
        
        Returns:
            list: List of valid payment methods
        """
        return Payment.VALID_METHODS
