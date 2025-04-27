"""
Payment model for POS application.
Handles payment data and related operations.
"""

from .base_model import BaseModel


class Payment(BaseModel):
    """Payment model for managing payments."""
    
    # Payment method constants
    METHOD_CASH = "CASH"
    METHOD_CARD = "CARD"
    METHOD_CHECK = "CHECK"
    METHOD_CREDIT = "CREDIT"
    METHOD_MOBILE = "MOBILE"
    
    # Valid payment methods
    VALID_METHODS = [METHOD_CASH, METHOD_CARD, METHOD_CHECK, METHOD_CREDIT, METHOD_MOBILE]
    
    def __init__(self, db):
        """Initialize Payment model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "payments"
        self.primary_key = "payment_id"
    
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
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Validate input
            self._validate_payment_data(invoice_id, amount, payment_method)
            
            # Get invoice information
            query = """
                SELECT i.*, 
                       COALESCE(SUM(p.amount), 0) as paid_amount
                FROM invoices i
                LEFT JOIN payments p ON i.invoice_id = p.invoice_id
                WHERE i.invoice_id = %s
                GROUP BY i.invoice_id
            """
            invoice = self.db.fetch_one(query, (invoice_id,))
            
            if not invoice:
                raise ValueError("Invoice not found")
            
            if invoice["status"] != "COMPLETED":
                raise ValueError("Cannot make payments on non-completed invoices")
            
            # Check if payment would exceed invoice total
            if invoice["paid_amount"] + amount > invoice["total_amount"]:
                raise ValueError(f"Payment amount of {amount} would exceed remaining balance of {invoice['total_amount'] - invoice['paid_amount']}")
            
            # Create payment data
            payment_id = self.generate_id()
            now = self.get_timestamp()
            
            payment_data = {
                "payment_id": payment_id,
                "invoice_id": invoice_id,
                "user_id": user_id,
                "amount": amount,
                "payment_method": payment_method,
                "reference_number": reference_number,
                "payment_date": now,
                "notes": notes,
                "created_at": now,
                "updated_at": now
            }
            
            # Create payment
            payment = self.create(payment_data)
            
            # Update cash register if payment method is cash
            if payment_method == self.METHOD_CASH:
                from .cash_register import CashRegister
                register = CashRegister(self.db)
                
                register.record_transaction(
                    amount,
                    CashRegister.TRANSACTION_SALE,
                    f"Payment for invoice {invoice['invoice_number']}",
                    user_id,
                    payment_id
                )
            
            # Create customer debt if this is a credit payment
            if payment_method == self.METHOD_CREDIT:
                from .customer_debt import CustomerDebt
                debt = CustomerDebt(self.db)
                
                if not invoice["customer_id"]:
                    raise ValueError("Cannot use credit payment without a customer")
                
                debt.create_debt(
                    invoice["customer_id"],
                    invoice_id,
                    amount,
                    0,  # Initial amount paid is 0
                    f"Credit payment for invoice {invoice['invoice_number']}",
                    user_id
                )
            
            # Check if this completes the payment for the invoice
            remaining = invoice["total_amount"] - (invoice["paid_amount"] + amount)
            is_fully_paid = remaining <= 0
            
            # Commit transaction
            self.db.commit_transaction()
            
            return {
                **payment,
                "is_fully_paid": is_fully_paid,
                "remaining_amount": remaining if remaining > 0 else 0
            }
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def get_invoice_payments(self, invoice_id):
        """Get all payments for an invoice.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            list: List of payments
        """
        query = """
            SELECT p.*, u.username as user_name
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.invoice_id = %s
            ORDER BY p.payment_date
        """
        return self.db.fetch_all(query, (invoice_id,))
    
    def get_payment_total(self, invoice_id):
        """Get the total amount paid for an invoice.
        
        Args:
            invoice_id (str): Invoice ID
            
        Returns:
            float: Total amount paid
        """
        query = "SELECT COALESCE(SUM(amount), 0) as total_paid FROM payments WHERE invoice_id = %s"
        result = self.db.fetch_one(query, (invoice_id,))
        return result["total_paid"] if result else 0
    
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
        # Get invoice total and existing payments
        query = """
            SELECT i.total_amount, COALESCE(SUM(p.amount), 0) as paid_amount
            FROM invoices i
            LEFT JOIN payments p ON i.invoice_id = p.invoice_id
            WHERE i.invoice_id = %s
            GROUP BY i.invoice_id
        """
        invoice = self.db.fetch_one(query, (invoice_id,))
        
        if not invoice:
            raise ValueError("Invoice not found")
        
        # Calculate remaining and change
        remaining = invoice["total_amount"] - invoice["paid_amount"]
        
        if tendered_amount >= remaining:
            change_due = tendered_amount - remaining
            remaining_after = 0
        else:
            change_due = 0
            remaining_after = remaining - tendered_amount
        
        return {
            "total_amount": invoice["total_amount"],
            "paid_amount": invoice["paid_amount"],
            "remaining_amount": remaining,
            "tendered_amount": tendered_amount,
            "change_due": change_due,
            "remaining_after": remaining_after
        }
    
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
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Get payment
            payment = self.get_by_id(payment_id)
            if not payment:
                raise ValueError("Payment not found")
            
            # Get invoice to check status
            query = "SELECT * FROM invoices WHERE invoice_id = %s"
            invoice = self.db.fetch_one(query, (payment["invoice_id"],))
            
            if not invoice:
                raise ValueError("Invoice not found")
            
            if invoice["status"] == "VOIDED":
                raise ValueError("Cannot void a payment for a voided invoice")
            
            # Handle cash payments - update cash register
            if payment["payment_method"] == self.METHOD_CASH:
                from .cash_register import CashRegister
                register = CashRegister(self.db)
                
                register.record_transaction(
                    payment["amount"],
                    CashRegister.TRANSACTION_VOID,
                    f"Void payment for invoice {invoice['invoice_number']}: {reason or 'No reason provided'}",
                    payment["user_id"],
                    payment_id
                )
            
            # Handle credit payments - update customer debt
            if payment["payment_method"] == self.METHOD_CREDIT:
                query = "SELECT * FROM customer_debts WHERE invoice_id = %s AND is_paid = false"
                debt = self.db.fetch_one(query, (payment["invoice_id"],))
                
                if debt:
                    from .customer_debt import CustomerDebt
                    debt_model = CustomerDebt(self.db)
                    
                    # Mark debt as paid (basically cancelling it since it's voided)
                    debt_model.update_debt(
                        debt["debt_id"],
                        {
                            "is_paid": True,
                            "notes": f"{debt['notes'] or ''}\nVoided: {reason or 'No reason provided'}"
                        }
                    )
            
            # Delete the payment
            self.delete(payment_id)
            
            # Commit transaction
            self.db.commit_transaction()
            
            return {
                "success": True,
                "message": f"Payment voided: {reason or 'No reason provided'}"
            }
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def get_payment_methods_report(self, date_from=None, date_to=None, user_id=None):
        """Get a report of payments by method.
        
        Args:
            date_from (str, optional): Start date (ISO format)
            date_to (str, optional): End date (ISO format)
            user_id (str, optional): Filter by user
            
        Returns:
            list: Payment method summary
        """
        query = """
            SELECT 
                payment_method,
                COUNT(payment_id) as count,
                SUM(amount) as total
            FROM payments
            WHERE 1=1
        """
        params = []
        
        # Add date filters
        if date_from:
            query += " AND payment_date >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND payment_date <= %s"
            params.append(date_to)
        
        # Add user filter
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        
        query += " GROUP BY payment_method ORDER BY total DESC"
        
        return self.db.fetch_all(query, tuple(params))
    
    def _validate_payment_data(self, invoice_id, amount, payment_method):
        """Validate payment data.
        
        Args:
            invoice_id (str): Invoice ID
            amount (float): Payment amount
            payment_method (str): Payment method
            
        Raises:
            ValueError: If validation fails
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero")
        
        # Validate payment method
        if payment_method not in self.VALID_METHODS:
            raise ValueError(f"Invalid payment method. Must be one of: {', '.join(self.VALID_METHODS)}")
