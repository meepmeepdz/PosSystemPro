"""
Cash Register controller for POS application.
Handles cash register management operations.
"""

from models.cash_register import CashRegister


class CashRegisterController:
    """Controller for cash register operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.register_model = CashRegister(db)
    
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
        return self.register_model.open_register(user_id, initial_amount, notes)
    
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
        return self.register_model.close_register(register_id, user_id, counted_amount, notes)
    
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
        return self.register_model.pause_register(register_id, user_id, notes)
    
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
        return self.register_model.resume_register(register_id, user_id, notes)
    
    def get_current_register(self):
        """Get the current open register.
        
        Returns:
            dict: Current register data or None if no open register
        """
        return self.register_model.get_current_register()
    
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
        return self.register_model.record_transaction(
            amount, transaction_type, description, user_id, reference_id, register_id
        )
    
    def get_register_transactions(self, register_id, limit=100, offset=0):
        """Get transactions for a register.
        
        Args:
            register_id (str): Register ID
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of transactions
        """
        return self.register_model.get_register_transactions(register_id, limit, offset)
    
    def get_register_summary(self, register_id):
        """Get a summary of register activities.
        
        Args:
            register_id (str): Register ID
            
        Returns:
            dict: Register summary
        """
        return self.register_model.get_register_summary(register_id)
    
    def record_deposit(self, amount, description, user_id):
        """Record a deposit to the current register.
        
        Args:
            amount (float): Amount to deposit
            description (str): Description of deposit
            user_id (str): ID of the user making the deposit
            
        Returns:
            dict: Created transaction data
            
        Raises:
            ValueError: If no open register is found
        """
        return self.register_model.record_transaction(
            amount, 
            CashRegister.TRANSACTION_DEPOSIT, 
            description, 
            user_id
        )
    
    def record_withdrawal(self, amount, description, user_id):
        """Record a withdrawal from the current register.
        
        Args:
            amount (float): Amount to withdraw
            description (str): Description of withdrawal
            user_id (str): ID of the user making the withdrawal
            
        Returns:
            dict: Created transaction data
            
        Raises:
            ValueError: If no open register is found or insufficient funds
        """
        return self.register_model.record_transaction(
            amount, 
            CashRegister.TRANSACTION_WITHDRAWAL, 
            description, 
            user_id
        )
    
    def get_transaction_types(self):
        """Get valid transaction types.
        
        Returns:
            dict: Dictionary of transaction types
        """
        return {
            "SALE": CashRegister.TRANSACTION_SALE,
            "REFUND": CashRegister.TRANSACTION_REFUND,
            "DEPOSIT": CashRegister.TRANSACTION_DEPOSIT,
            "WITHDRAWAL": CashRegister.TRANSACTION_WITHDRAWAL,
            "VOID": CashRegister.TRANSACTION_VOID,
            "DEBT_PAYMENT": CashRegister.TRANSACTION_DEBT_PAYMENT
        }
