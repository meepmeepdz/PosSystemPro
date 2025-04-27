"""
Customer Debt model for POS application.
Handles customer debt data and related operations.
"""

from .base_model import BaseModel


class CustomerDebt(BaseModel):
    """Customer Debt model for managing customer debts."""
    
    def __init__(self, db):
        """Initialize CustomerDebt model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "customer_debts"
        self.primary_key = "debt_id"
    
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
        # Validate input
        self._validate_debt_data(customer_id, invoice_id, amount, amount_paid)
        
        # Create debt data
        debt_id = self.generate_id()
        now = self.get_timestamp()
        
        # Determine if debt is fully paid
        is_paid = (amount_paid >= amount)
        
        debt_data = {
            "debt_id": debt_id,
            "customer_id": customer_id,
            "invoice_id": invoice_id,
            "amount": amount,
            "amount_paid": amount_paid,
            "is_paid": is_paid,
            "created_by": user_id,
            "notes": notes,
            "created_at": now,
            "updated_at": now,
            "last_payment_date": now if amount_paid > 0 else None
        }
        
        return self.create(debt_data)
    
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
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Get debt
            debt = self.get_by_id(debt_id)
            if not debt:
                raise ValueError("Debt not found")
            
            if debt["is_paid"]:
                raise ValueError("Debt is already paid")
            
            # Calculate remaining to pay
            remaining = debt["amount"] - debt["amount_paid"]
            
            if payment_amount <= 0:
                raise ValueError("Payment amount must be greater than zero")
            
            if payment_amount > remaining:
                raise ValueError(f"Payment amount of {payment_amount} exceeds remaining debt of {remaining}")
            
            # Update debt data
            new_amount_paid = debt["amount_paid"] + payment_amount
            is_paid = (new_amount_paid >= debt["amount"])
            
            now = self.get_timestamp()
            update_data = {
                "amount_paid": new_amount_paid,
                "is_paid": is_paid,
                "last_payment_date": now,
                "notes": (debt["notes"] + "\n" if debt["notes"] else "") + 
                         f"Payment of {payment_amount} on {now}: {notes or ''}",
                "updated_at": now
            }
            
            updated_debt = self.update(debt_id, update_data)
            
            # Record payment in payments table
            from .payment import Payment
            payment_model = Payment(self.db)
            
            payment = payment_model.create_payment(
                debt["invoice_id"],
                user_id,
                payment_amount,
                payment_method,
                None,  # reference_number
                f"Debt payment for debt ID: {debt_id}"
            )
            
            # Update cash register if payment method is cash
            if payment_method == "CASH":
                from .cash_register import CashRegister
                register = CashRegister(self.db)
                
                register.record_transaction(
                    payment_amount,
                    CashRegister.TRANSACTION_DEBT_PAYMENT,
                    f"Debt payment for customer: {debt['customer_id']}",
                    user_id,
                    payment["payment_id"]
                )
            
            # Commit transaction
            self.db.commit_transaction()
            
            return {
                **updated_debt,
                "payment": payment,
                "remaining": debt["amount"] - new_amount_paid
            }
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
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
        # Get existing debt
        existing_debt = self.get_by_id(debt_id)
        if not existing_debt:
            raise ValueError("Debt not found")
        
        # Validate input
        update_data = {}
        
        if "amount" in data:
            if data["amount"] < 0:
                raise ValueError("Amount cannot be negative")
            
            # Ensure amount is not less than amount_paid
            if data["amount"] < existing_debt["amount_paid"]:
                raise ValueError("Total amount cannot be less than amount already paid")
            
            update_data["amount"] = data["amount"]
            
            # Update is_paid status
            update_data["is_paid"] = (existing_debt["amount_paid"] >= data["amount"])
        
        if "amount_paid" in data:
            if data["amount_paid"] < 0:
                raise ValueError("Amount paid cannot be negative")
            
            # Ensure amount_paid does not exceed total amount
            if data["amount_paid"] > existing_debt["amount"]:
                raise ValueError("Amount paid cannot exceed total debt amount")
            
            update_data["amount_paid"] = data["amount_paid"]
            
            # Update is_paid status
            update_data["is_paid"] = (data["amount_paid"] >= existing_debt["amount"])
            
            # Update last payment date if increasing the amount paid
            if data["amount_paid"] > existing_debt["amount_paid"]:
                update_data["last_payment_date"] = self.get_timestamp()
        
        if "is_paid" in data:
            update_data["is_paid"] = bool(data["is_paid"])
            
            # If marking as paid, set amount_paid to amount
            if data["is_paid"] and existing_debt["amount_paid"] < existing_debt["amount"]:
                update_data["amount_paid"] = existing_debt["amount"]
                update_data["last_payment_date"] = self.get_timestamp()
        
        if "notes" in data:
            update_data["notes"] = data["notes"]
        
        # Update timestamp
        update_data["updated_at"] = self.get_timestamp()
        
        # Update debt
        return self.update(debt_id, update_data)
    
    def get_customer_debts(self, customer_id, include_paid=False):
        """Get all debts for a customer.
        
        Args:
            customer_id (str): Customer ID
            include_paid (bool, optional): Whether to include paid debts
            
        Returns:
            list: List of debts for the customer
        """
        query = """
            SELECT cd.*, 
                   i.invoice_number,
                   i.created_at as invoice_date,
                   u.username as created_by_name
            FROM customer_debts cd
            JOIN invoices i ON cd.invoice_id = i.invoice_id
            LEFT JOIN users u ON cd.created_by = u.user_id
            WHERE cd.customer_id = %s
        """
        params = [customer_id]
        
        if not include_paid:
            query += " AND cd.is_paid = false"
        
        query += " ORDER BY cd.created_at DESC"
        
        return self.db.fetch_all(query, tuple(params))
    
    def get_customer_debt_total(self, customer_id):
        """Get the total outstanding debt for a customer.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            float: Total outstanding debt
        """
        query = """
            SELECT 
                SUM(amount - amount_paid) as total_debt
            FROM customer_debts
            WHERE customer_id = %s AND is_paid = false
        """
        result = self.db.fetch_one(query, (customer_id,))
        return result["total_debt"] if result and result["total_debt"] else 0
    
    def get_all_outstanding_debts(self, order_by="created_at DESC", limit=100, offset=0):
        """Get all outstanding debts with customer information.
        
        Args:
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of outstanding debts
        """
        query = """
            SELECT cd.*, 
                   c.full_name as customer_name,
                   c.phone as customer_phone,
                   i.invoice_number,
                   i.created_at as invoice_date,
                   (cd.amount - cd.amount_paid) as remaining_amount,
                   EXTRACT(DAY FROM (NOW() - cd.created_at)) as days_outstanding
            FROM customer_debts cd
            JOIN customers c ON cd.customer_id = c.customer_id
            JOIN invoices i ON cd.invoice_id = i.invoice_id
            WHERE cd.is_paid = false
        """
        
        # Add ORDER BY clause
        if order_by:
            if order_by.startswith("customer_name"):
                # Special case for ordering by customer name
                direction = "DESC" if "DESC" in order_by else "ASC"
                query += f" ORDER BY c.full_name {direction}"
            elif order_by.startswith("remaining_amount"):
                # Special case for ordering by remaining amount
                direction = "DESC" if "DESC" in order_by else "ASC"
                query += f" ORDER BY remaining_amount {direction}"
            elif order_by.startswith("days_outstanding"):
                # Special case for ordering by days outstanding
                direction = "DESC" if "DESC" in order_by else "ASC"
                query += f" ORDER BY days_outstanding {direction}"
            else:
                query += f" ORDER BY cd.{order_by}"
        
        # Add LIMIT and OFFSET clauses
        query += " LIMIT %s OFFSET %s"
        
        return self.db.fetch_all(query, (limit, offset))
    
    def search_debts(self, filters=None, limit=100, offset=0):
        """Search debts with various filters.
        
        Args:
            filters (dict, optional): Dictionary of filters to apply
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of debts matching the criteria
        """
        # Build query
        query = """
            SELECT cd.*, 
                   c.full_name as customer_name,
                   c.phone as customer_phone,
                   i.invoice_number,
                   i.created_at as invoice_date,
                   (cd.amount - cd.amount_paid) as remaining_amount,
                   EXTRACT(DAY FROM (NOW() - cd.created_at)) as days_outstanding,
                   u.username as created_by_name
            FROM customer_debts cd
            JOIN customers c ON cd.customer_id = c.customer_id
            JOIN invoices i ON cd.invoice_id = i.invoice_id
            LEFT JOIN users u ON cd.created_by = u.user_id
            WHERE 1=1
        """
        params = []
        
        # Apply filters
        if filters:
            if "customer_id" in filters:
                query += " AND cd.customer_id = %s"
                params.append(filters["customer_id"])
            
            if "is_paid" in filters:
                query += " AND cd.is_paid = %s"
                params.append(filters["is_paid"])
        
        # Add ORDER BY clause
        query += " ORDER BY cd.created_at DESC"
        
        # Add LIMIT and OFFSET clauses
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.db.fetch_all(query, tuple(params))
        
    def get_debt_summary_by_age(self):
        """Get a summary of outstanding debts by age.
        
        Returns:
            dict: Summary of debts by age categories
        """
        query = """
            SELECT 
                COUNT(*) as total_debts,
                SUM(amount - amount_paid) as total_amount,
                COUNT(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) <= 30 THEN 1 END) as debts_0_30_days,
                SUM(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) <= 30 THEN (amount - amount_paid) ELSE 0 END) as amount_0_30_days,
                COUNT(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) BETWEEN 31 AND 60 THEN 1 END) as debts_31_60_days,
                SUM(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) BETWEEN 31 AND 60 THEN (amount - amount_paid) ELSE 0 END) as amount_31_60_days,
                COUNT(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) BETWEEN 61 AND 90 THEN 1 END) as debts_61_90_days,
                SUM(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) BETWEEN 61 AND 90 THEN (amount - amount_paid) ELSE 0 END) as amount_61_90_days,
                COUNT(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) > 90 THEN 1 END) as debts_over_90_days,
                SUM(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) > 90 THEN (amount - amount_paid) ELSE 0 END) as amount_over_90_days
            FROM customer_debts
            WHERE is_paid = false
        """
        summary = self.db.fetch_one(query)
        
        # Get customer breakdown for severe cases (over 90 days)
        if summary and summary["debts_over_90_days"] > 0:
            query = """
                SELECT 
                    cd.customer_id,
                    c.full_name as customer_name,
                    COUNT(*) as debt_count,
                    SUM(cd.amount - cd.amount_paid) as total_amount,
                    MIN(cd.created_at) as oldest_debt_date
                FROM customer_debts cd
                JOIN customers c ON cd.customer_id = c.customer_id
                WHERE cd.is_paid = false
                  AND EXTRACT(DAY FROM (NOW() - cd.created_at)) > 90
                GROUP BY cd.customer_id, c.full_name
                ORDER BY total_amount DESC
            """
            severe_customers = self.db.fetch_all(query)
            summary["severe_customers"] = severe_customers
        
        return summary
    
    def _validate_debt_data(self, customer_id, invoice_id, amount, amount_paid):
        """Validate debt data.
        
        Args:
            customer_id (str): Customer ID
            invoice_id (str): Invoice ID
            amount (float): Total debt amount
            amount_paid (float): Initial amount paid
            
        Raises:
            ValueError: If validation fails
        """
        # Validate customer_id
        query = "SELECT customer_id FROM customers WHERE customer_id = %s"
        customer_exists = self.db.fetch_one(query, (customer_id,))
        if not customer_exists:
            raise ValueError("Customer not found")
        
        # Validate invoice_id
        query = "SELECT invoice_id FROM invoices WHERE invoice_id = %s"
        invoice_exists = self.db.fetch_one(query, (invoice_id,))
        if not invoice_exists:
            raise ValueError("Invoice not found")
        
        # Check for existing debt for this invoice
        query = "SELECT debt_id FROM customer_debts WHERE invoice_id = %s AND is_paid = false"
        existing_debt = self.db.fetch_one(query, (invoice_id,))
        if existing_debt:
            raise ValueError("An unpaid debt already exists for this invoice")
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        
        # Validate amount_paid
        if amount_paid < 0:
            raise ValueError("Amount paid cannot be negative")
        
        if amount_paid > amount:
            raise ValueError("Amount paid cannot exceed total amount")
