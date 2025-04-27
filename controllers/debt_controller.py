"""
Debt controller for POS application.
Handles customer debt management operations.
"""

from models.customer_debt import CustomerDebt


class DebtController:
    """Controller for customer debt operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.debt_model = CustomerDebt(db)
    
    def create_debt(self, customer_id, invoice_id, amount, amount_paid=0, notes=None, user_id=None):
        """Create a new customer debt record.
        
        Args:
            customer_id (str): Customer ID
            invoice_id (str): Invoice ID that generated the debt
            amount (float): Total debt amount
            amount_paid (float, optional): Initial amount paid
            notes (str, optional): Notes about the debt
            user_id (str, optional): User ID creating the debt
            
        Returns:
            dict: Created debt data
            
        Raises:
            ValueError: If validation fails
        """
        return self.debt_model.create_debt(customer_id, invoice_id, amount, amount_paid, notes, user_id)
    
    def record_payment(self, debt_id, payment_amount, payment_method, user_id, notes=None):
        """Record a payment for a debt.
        
        Args:
            debt_id (str): Debt ID
            payment_amount (float): Amount being paid
            payment_method (str): Payment method
            user_id (str): User ID recording the payment
            notes (str, optional): Payment notes
            
        Returns:
            dict: Updated debt data
            
        Raises:
            ValueError: If validation fails
        """
        return self.debt_model.record_payment(debt_id, payment_amount, payment_method, user_id, notes)
    
    def update_debt(self, debt_id, data):
        """Update debt data.
        
        Args:
            debt_id (str): ID of debt to update
            data (dict): Data to update
            
        Returns:
            dict: Updated debt data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        return self.debt_model.update_debt(debt_id, data)
    
    def get_debt_by_id(self, debt_id):
        """Get a debt by ID.
        
        Args:
            debt_id (str): Debt ID
            
        Returns:
            dict: Debt data or None if not found
        """
        return self.debt_model.get_by_id(debt_id)
    
    def get_customer_debts(self, customer_id, include_paid=False):
        """Get all debts for a customer.
        
        Args:
            customer_id (str): Customer ID
            include_paid (bool, optional): Whether to include paid debts
            
        Returns:
            list: List of debts for the customer
        """
        return self.debt_model.get_customer_debts(customer_id, include_paid)
    
    def get_customer_debt_total(self, customer_id):
        """Get the total outstanding debt for a customer.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            float: Total outstanding debt
        """
        return self.debt_model.get_customer_debt_total(customer_id)
    
    def get_all_outstanding_debts(self, order_by="created_at DESC", limit=100, offset=0):
        """Get all outstanding debts with customer information.
        
        Args:
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of outstanding debts
        """
        return self.debt_model.get_all_outstanding_debts(order_by, limit, offset)
    
    def get_debt_summary_by_age(self):
        """Get a summary of outstanding debts by age.
        
        Returns:
            dict: Summary of debts by age categories
        """
        return self.debt_model.get_debt_summary_by_age()
    
    def mark_debt_as_paid(self, debt_id, notes=None):
        """Mark a debt as paid.
        
        Args:
            debt_id (str): Debt ID
            notes (str, optional): Notes about the payment
            
        Returns:
            dict: Updated debt data
            
        Raises:
            ValueError: If debt not found or already paid
        """
        debt = self.debt_model.get_by_id(debt_id)
        if not debt:
            raise ValueError("Debt not found")
        
        if debt["is_paid"]:
            raise ValueError("Debt is already paid")
        
        # Calculate remaining amount
        remaining = debt["amount"] - debt["amount_paid"]
        
        # Update debt data
        now = self.debt_model.get_timestamp()
        update_data = {
            "amount_paid": debt["amount"],
            "is_paid": True,
            "last_payment_date": now,
            "notes": f"{debt['notes'] or ''}\nMarked as paid on {now}: {notes or ''}",
            "updated_at": now
        }
        
        return self.debt_model.update(debt_id, update_data)
