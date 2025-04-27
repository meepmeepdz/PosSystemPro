"""
Customer controller for POS application.
Handles customer management operations.
"""

from models.customer import Customer


class CustomerController:
    """Controller for customer operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.customer_model = Customer(db)
    
    def get_all_customers(self, order_by="full_name", limit=None, offset=None):
        """Get all customers.
        
        Args:
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of customers
        """
        return self.customer_model.get_all(order_by=order_by, limit=limit, offset=offset)
    
    def get_customer_by_id(self, customer_id):
        """Get a customer by ID.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            dict: Customer data or None if not found
        """
        return self.customer_model.get_by_id(customer_id)
    
    def create_customer(self, full_name, email=None, phone=None, address=None, 
                         tax_id=None, notes=None):
        """Create a new customer.
        
        Args:
            full_name (str): Customer's full name
            email (str, optional): Customer's email address
            phone (str, optional): Customer's phone number
            address (str, optional): Customer's address
            tax_id (str, optional): Customer's tax ID
            notes (str, optional): Additional notes
            
        Returns:
            dict: Created customer data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        return self.customer_model.create_customer(
            full_name, email, phone, address, tax_id, notes
        )
    
    def update_customer(self, customer_id, data):
        """Update customer data.
        
        Args:
            customer_id (str): ID of customer to update
            data (dict): Data to update
            
        Returns:
            dict: Updated customer data or None if failed
            
        Raises:
            ValueError: If validation fails
        """
        return self.customer_model.update_customer(customer_id, data)
    
    def delete_customer(self, customer_id):
        """Delete a customer if they have no associated records.
        
        Args:
            customer_id (str): ID of customer to delete
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If customer has associated records
        """
        # Check if customer has invoices
        query = "SELECT COUNT(*) as count FROM invoices WHERE customer_id = %s"
        result = self.db.fetch_one(query, (customer_id,))
        if result and result["count"] > 0:
            raise ValueError("Cannot delete customer with associated invoices")
        
        # Check if customer has debts
        query = "SELECT COUNT(*) as count FROM customer_debts WHERE customer_id = %s"
        result = self.db.fetch_one(query, (customer_id,))
        if result and result["count"] > 0:
            raise ValueError("Cannot delete customer with associated debts")
        
        # If no associated records, delete the customer
        return self.customer_model.delete(customer_id)
    
    def search_customers(self, search_term=None, order_by="full_name", limit=100, offset=0):
        """Search for customers.
        
        Args:
            search_term (str, optional): Search term for name, email, or phone
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of customers matching the search criteria
        """
        return self.customer_model.search_customers(search_term, order_by, limit, offset)
    
    def get_customer_purchase_history(self, customer_id, order_by="created_at DESC", limit=50, offset=0):
        """Get a customer's purchase history.
        
        Args:
            customer_id (str): Customer ID
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of invoices for the customer
        """
        return self.customer_model.get_customer_purchase_history(customer_id, order_by, limit, offset)
    
    def get_customer_debt_history(self, customer_id, include_paid=False):
        """Get a customer's debt history.
        
        Args:
            customer_id (str): Customer ID
            include_paid (bool, optional): Whether to include paid debts
            
        Returns:
            list: List of debts for the customer
        """
        return self.customer_model.get_customer_debt_history(customer_id, include_paid)
    
    def get_customer_statistics(self, customer_id):
        """Get statistics for a customer.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            dict: Customer statistics
        """
        return self.customer_model.get_customer_statistics(customer_id)
