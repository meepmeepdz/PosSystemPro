"""
Cash Register model for POS application.
Handles cash register data and related operations.
"""

from .base_model import BaseModel


class CashRegister(BaseModel):
    """Cash Register model for managing cash registers."""
    
    # Register status constants
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_PAUSED = "PAUSED"
    
    # Transaction type constants
    TRANSACTION_SALE = "SALE"
    TRANSACTION_REFUND = "REFUND"
    TRANSACTION_DEPOSIT = "DEPOSIT"
    TRANSACTION_WITHDRAWAL = "WITHDRAWAL"
    TRANSACTION_VOID = "VOID"
    TRANSACTION_DEBT_PAYMENT = "DEBT_PAYMENT"
    
    def __init__(self, db):
        """Initialize CashRegister model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "cash_registers"
        self.primary_key = "register_id"
    
    def open_register(self, user_id, initial_amount, notes=None):
        """Open a new cash register session.
        
        Args:
            user_id (str): ID of the user opening the register
            initial_amount (float): Initial cash amount
            notes (str, optional): Notes about the opening
            
        Returns:
            dict: Created register data
            
        Raises:
            ValueError: If validation fails
        """
        # Check if there's already an open register
        query = "SELECT * FROM cash_registers WHERE status != %s ORDER BY created_at DESC LIMIT 1"
        existing_register = self.db.fetch_one(query, (self.STATUS_CLOSED,))
        
        if existing_register:
            raise ValueError(f"There is already an open register (ID: {existing_register['register_id']})")
        
        # Create register data
        register_id = self.generate_id()
        now = self.get_timestamp()
        
        register_data = {
            "register_id": register_id,
            "user_id": user_id,
            "opening_amount": initial_amount,
            "current_amount": initial_amount,
            "closing_amount": None,
            "opening_time": now,
            "closing_time": None,
            "status": self.STATUS_OPEN,
            "notes": notes,
            "created_at": now,
            "updated_at": now
        }
        
        # Create register
        created_register = self.create(register_data)
        
        # Record opening transaction
        self.record_transaction(
            initial_amount, 
            self.TRANSACTION_DEPOSIT, 
            "Register opening", 
            user_id,
            None,
            register_id
        )
        
        return created_register
    
    def close_register(self, register_id, user_id, counted_amount, notes=None):
        """Close a cash register session.
        
        Args:
            register_id (str): ID of the register to close
            user_id (str): ID of the user closing the register
            counted_amount (float): Physically counted cash amount
            notes (str, optional): Notes about the closing
            
        Returns:
            dict: Summary of register closing
            
        Raises:
            ValueError: If register cannot be closed
        """
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Get register
            register = self.get_by_id(register_id)
            if not register:
                raise ValueError("Register not found")
            
            if register["status"] == self.STATUS_CLOSED:
                raise ValueError("Register is already closed")
            
            # Calculate discrepancy
            discrepancy = counted_amount - register["current_amount"]
            
            # Update register
            now = self.get_timestamp()
            update_data = {
                "closing_amount": counted_amount,
                "closing_time": now,
                "status": self.STATUS_CLOSED,
                "notes": notes,
                "updated_at": now
            }
            
            updated_register = self.update(register_id, update_data)
            
            # Get transaction summary
            summary = self.get_register_summary(register_id) or {}
            
            # Add closing information
            summary["closing_user_id"] = user_id
            summary["counted_amount"] = counted_amount
            summary["discrepancy"] = discrepancy
            
            # Record discrepancy if it exists
            if discrepancy != 0:
                transaction_type = self.TRANSACTION_DEPOSIT if discrepancy > 0 else self.TRANSACTION_WITHDRAWAL
                self.record_transaction(
                    abs(discrepancy),
                    transaction_type,
                    f"Register closing adjustment: {'Excess' if discrepancy > 0 else 'Shortage'}",
                    user_id,
                    None,
                    register_id
                )
            
            # Commit transaction
            self.db.commit_transaction()
            
            # Make sure both are dictionaries
            if updated_register is None:
                updated_register = {}
            if summary is None:
                summary = {}
                
            combined_data = {}
            combined_data.update(updated_register)
            combined_data.update(summary)
            
            return combined_data
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def pause_register(self, register_id, user_id, notes=None):
        """Pause a cash register session.
        
        Args:
            register_id (str): ID of the register to pause
            user_id (str): ID of the user pausing the register
            notes (str, optional): Notes about the pausing
            
        Returns:
            dict: Updated register data
            
        Raises:
            ValueError: If register cannot be paused
        """
        # Get register
        register = self.get_by_id(register_id)
        if not register:
            raise ValueError("Register not found")
        
        if register["status"] != self.STATUS_OPEN:
            raise ValueError("Register must be open to be paused")
        
        # Update register
        now = self.get_timestamp()
        update_data = {
            "status": self.STATUS_PAUSED,
            "notes": f"{register['notes'] or ''}\nPAUSED at {now} by user {user_id}. {notes or ''}",
            "updated_at": now
        }
        
        return self.update(register_id, update_data)
    
    def resume_register(self, register_id, user_id, notes=None):
        """Resume a paused cash register session.
        
        Args:
            register_id (str): ID of the register to resume
            user_id (str): ID of the user resuming the register
            notes (str, optional): Notes about the resuming
            
        Returns:
            dict: Updated register data
            
        Raises:
            ValueError: If register cannot be resumed
        """
        # Get register
        register = self.get_by_id(register_id)
        if not register:
            raise ValueError("Register not found")
        
        if register["status"] != self.STATUS_PAUSED:
            raise ValueError("Register must be paused to be resumed")
        
        # Update register
        now = self.get_timestamp()
        update_data = {
            "status": self.STATUS_OPEN,
            "notes": f"{register['notes'] or ''}\nRESUMED at {now} by user {user_id}. {notes or ''}",
            "updated_at": now
        }
        
        return self.update(register_id, update_data)
    
    def add_cash(self, register_id, amount, notes=None):
        """Add cash to a register.
        
        Args:
            register_id (str): ID of the register
            amount (float): Amount to add
            notes (str, optional): Notes about the addition
            
        Returns:
            dict: Created transaction data
        """
        # Get register
        register = self.get_by_id(register_id)
        if not register:
            raise ValueError("Register not found")
        
        if register["status"] == self.STATUS_CLOSED:
            raise ValueError("Cannot add cash to a closed register")
        
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Add to register balance
            new_balance = register["current_amount"] + amount
            self.update(register_id, {"current_amount": new_balance, "updated_at": self.get_timestamp()})
            
            # Record transaction
            transaction = self.record_transaction(
                amount,
                self.TRANSACTION_DEPOSIT,
                notes or "Cash added to register",
                register.get("user_id"),  # Use the register's user_id as fallback
                None,
                register_id
            )
            
            # Commit changes
            self.db.commit_transaction()
            
            return transaction
            
        except Exception as e:
            self.db.rollback_transaction()
            raise e
    
    def remove_cash(self, register_id, amount, notes=None):
        """Remove cash from a register.
        
        Args:
            register_id (str): ID of the register
            amount (float): Amount to remove
            notes (str, optional): Notes about the removal
            
        Returns:
            dict: Created transaction data
            
        Raises:
            ValueError: If insufficient funds or register not found
        """
        # Get register
        register = self.get_by_id(register_id)
        if not register:
            raise ValueError("Register not found")
        
        if register["status"] == self.STATUS_CLOSED:
            raise ValueError("Cannot remove cash from a closed register")
        
        # Check sufficient funds
        if register["current_amount"] < amount:
            raise ValueError(f"Insufficient funds: Register has {register['current_amount']}, trying to remove {amount}")
        
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Subtract from register balance
            new_balance = register["current_amount"] - amount
            self.update(register_id, {"current_amount": new_balance, "updated_at": self.get_timestamp()})
            
            # Record transaction
            transaction = self.record_transaction(
                amount,
                self.TRANSACTION_WITHDRAWAL,
                notes or "Cash removed from register",
                register.get("user_id"),  # Use the register's user_id as fallback
                None,
                register_id
            )
            
            # Commit changes
            self.db.commit_transaction()
            
            return transaction
            
        except Exception as e:
            self.db.rollback_transaction()
            raise e
    
    def record_transaction(self, amount, transaction_type, description, user_id, 
                           reference_id=None, register_id=None):
        """Record a cash register transaction.
        
        Args:
            amount (float): Transaction amount
            transaction_type (str): Type of transaction
            description (str): Description of transaction
            user_id (str): ID of the user performing the transaction
            reference_id (str, optional): Reference ID (e.g. invoice_id)
            register_id (str, optional): Register ID (if not provided, uses the current open register)
            
        Returns:
            dict: Created transaction data
            
        Raises:
            ValueError: If no open register is found
        """
        # If register_id is not provided, find the current open register
        if not register_id:
            query = "SELECT register_id FROM cash_registers WHERE status = %s ORDER BY created_at DESC LIMIT 1"
            current_register = self.db.fetch_one(query, (self.STATUS_OPEN,))
            
            if not current_register:
                raise ValueError("No open register found")
            
            register_id = current_register["register_id"]
        
        # Begin a transaction
        self.db.begin_transaction()
        
        try:
            # Get current register amount
            query = "SELECT current_amount FROM cash_registers WHERE register_id = %s"
            register = self.db.fetch_one(query, (register_id,))
            
            if not register:
                raise ValueError("Register not found")
            
            # Calculate new amount based on transaction type
            current_amount = register["current_amount"]
            
            if transaction_type in [self.TRANSACTION_SALE, self.TRANSACTION_DEPOSIT, self.TRANSACTION_DEBT_PAYMENT]:
                new_amount = current_amount + amount
            elif transaction_type in [self.TRANSACTION_REFUND, self.TRANSACTION_WITHDRAWAL, self.TRANSACTION_VOID]:
                new_amount = current_amount - amount
                if new_amount < 0:
                    raise ValueError("Register amount cannot be negative")
            else:
                # For custom types, use the sign of the amount to determine if it's an addition or subtraction
                new_amount = current_amount + amount
            
            # Update register amount
            update_query = """
                UPDATE cash_registers 
                SET current_amount = %s, updated_at = %s 
                WHERE register_id = %s
            """
            self.db.execute(update_query, (new_amount, self.get_timestamp(), register_id))
            
            # Create transaction record
            transaction = CashRegisterTransaction(self.db)
            transaction_id = transaction.generate_id()
            now = self.get_timestamp()
            
            transaction_data = {
                "transaction_id": transaction_id,
                "register_id": register_id,
                "user_id": user_id,
                "amount": amount,
                "transaction_type": transaction_type,
                "description": description,
                "reference_id": reference_id,
                "previous_amount": current_amount,
                "new_amount": new_amount,
                "created_at": now
            }
            
            result = transaction.create(transaction_data)
            
            # Commit transaction
            self.db.commit_transaction()
            
            return result
            
        except Exception as e:
            # Rollback transaction on error
            self.db.rollback_transaction()
            raise e
    
    def get_current_register(self):
        """Get the current open register.
        
        Returns:
            dict: Current register data or None if no open register
        """
        query = """
            SELECT r.*, u.username as user_name
            FROM cash_registers r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.status != %s
            ORDER BY r.created_at DESC
            LIMIT 1
        """
        return self.db.fetch_one(query, (self.STATUS_CLOSED,))
    
    def get_register_transactions(self, register_id, limit=100, offset=0):
        """Get transactions for a register.
        
        Args:
            register_id (str): Register ID
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of transactions
        """
        query = """
            SELECT t.*, u.username as user_name
            FROM cash_register_transactions t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.register_id = %s
            ORDER BY t.created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.db.fetch_all(query, (register_id, limit, offset))
    
    def get_register_summary(self, register_id):
        """Get a summary of register activities.
        
        Args:
            register_id (str): Register ID
            
        Returns:
            dict: Register summary
        """
        # Get basic register info
        query = """
            SELECT r.*, u.username as opening_user_name
            FROM cash_registers r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.register_id = %s
        """
        register = self.db.fetch_one(query, (register_id,))
        
        if not register:
            return None
        
        # Get transaction summary by type
        query = """
            SELECT 
                transaction_type,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount
            FROM cash_register_transactions
            WHERE register_id = %s
            GROUP BY transaction_type
        """
        transactions_by_type = self.db.fetch_all(query, (register_id,))
        
        # Get transaction summary by user
        query = """
            SELECT 
                t.user_id,
                u.username as user_name,
                COUNT(*) as transaction_count,
                SUM(CASE WHEN t.transaction_type IN ('SALE', 'DEPOSIT', 'DEBT_PAYMENT') THEN t.amount ELSE 0 END) as total_in,
                SUM(CASE WHEN t.transaction_type IN ('REFUND', 'WITHDRAWAL', 'VOID') THEN t.amount ELSE 0 END) as total_out
            FROM cash_register_transactions t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.register_id = %s
            GROUP BY t.user_id, u.username
        """
        transactions_by_user = self.db.fetch_all(query, (register_id,))
        
        # Get sales summary
        query = """
            SELECT 
                COUNT(DISTINCT t.reference_id) as total_sales,
                SUM(t.amount) as total_sales_amount
            FROM cash_register_transactions t
            WHERE t.register_id = %s AND t.transaction_type = 'SALE'
        """
        sales_summary = self.db.fetch_one(query, (register_id,))
        
        # Get payment method breakdown
        query = """
            SELECT 
                p.payment_method,
                COUNT(p.payment_id) as payment_count,
                SUM(p.amount) as payment_amount
            FROM payments p
            JOIN cash_register_transactions t ON p.payment_id = t.reference_id
            WHERE t.register_id = %s AND t.transaction_type = 'SALE'
            GROUP BY p.payment_method
        """
        payment_methods = self.db.fetch_all(query, (register_id,))
        
        # Combine results
        summary = {
            "register": register,
            "transactions_by_type": transactions_by_type,
            "transactions_by_user": transactions_by_user,
            "sales_summary": sales_summary,
            "payment_methods": payment_methods
        }
        
        return summary


class CashRegisterTransaction(BaseModel):
    """Cash Register Transaction model for tracking register movements."""
    
    def __init__(self, db):
        """Initialize CashRegisterTransaction model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "cash_register_transactions"
        self.primary_key = "transaction_id"
