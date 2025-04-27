"""
Customer model for POS application.
Handles customer data and related operations.
"""

import re
from .base_model import BaseModel


class Customer(BaseModel):
    """Customer model for managing customers."""
    
    def __init__(self, db):
        """Initialize Customer model.
        
        Args:
            db: Database connection instance
        """
        super().__init__(db)
        self.table_name = "customers"
        self.primary_key = "customer_id"
    
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
        # Validate input
        self._validate_customer_data(full_name, email, phone, tax_id)
        
        # Create customer data
        customer_id = self.generate_id()
        now = self.get_timestamp()
        
        customer_data = {
            "customer_id": customer_id,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "address": address,
            "tax_id": tax_id,
            "notes": notes,
            "created_at": now,
            "updated_at": now
        }
        
        return self.create(customer_data)
    
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
        # Get existing customer
        existing_customer = self.get_by_id(customer_id)
        if not existing_customer:
            raise ValueError("Customer not found")
        
        # Validate input
        update_data = {}
        
        if "full_name" in data:
            if not data["full_name"] or len(data["full_name"]) < 2:
                raise ValueError("Full name is required")
            update_data["full_name"] = data["full_name"]
        
        if "email" in data:
            if data["email"] and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", data["email"]):
                raise ValueError("Invalid email format")
            update_data["email"] = data["email"]
        
        if "phone" in data:
            update_data["phone"] = data["phone"]
        
        if "address" in data:
            update_data["address"] = data["address"]
        
        if "tax_id" in data:
            update_data["tax_id"] = data["tax_id"]
        
        if "notes" in data:
            update_data["notes"] = data["notes"]
        
        # Update timestamp
        update_data["updated_at"] = self.get_timestamp()
        
        # Update customer
        return self.update(customer_id, update_data)
    
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
        query = """
            SELECT c.*,
                   COALESCE(
                     (SELECT SUM(cd.amount - cd.amount_paid)
                      FROM customer_debts cd
                      WHERE cd.customer_id = c.customer_id
                        AND cd.is_paid = false
                     ), 0) as outstanding_debt,
                   COUNT(DISTINCT i.invoice_id) as purchase_count,
                   COALESCE(SUM(i.total_amount), 0) as total_spent
            FROM customers c
            LEFT JOIN invoices i ON c.customer_id = i.customer_id
            WHERE 1=1
        """
        params = []
        
        # Add search term filter
        if search_term:
            query += """ AND (
                c.full_name ILIKE %s OR 
                c.email ILIKE %s OR 
                c.phone ILIKE %s OR
                c.address ILIKE %s OR
                c.tax_id ILIKE %s
            )"""
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern, 
                          search_pattern, search_pattern])
        
        # Group by customer_id to combine the aggregations
        query += " GROUP BY c.customer_id"
        
        # Add ORDER BY clause
        if order_by:
            # Handle special case for ordering by aggregated columns
            if order_by == "purchase_count":
                query += " ORDER BY purchase_count DESC"
            elif order_by == "total_spent":
                query += " ORDER BY total_spent DESC"
            elif order_by == "outstanding_debt":
                query += " ORDER BY outstanding_debt DESC"
            else:
                query += f" ORDER BY c.{order_by}"
        
        # Add LIMIT and OFFSET clauses
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.db.fetch_all(query, tuple(params))
    
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
        query = """
            SELECT i.*,
                   u.username as seller_name,
                   (SELECT COUNT(*) FROM invoice_items ii WHERE ii.invoice_id = i.invoice_id) as item_count,
                   (SELECT SUM(p.amount) FROM payments p WHERE p.invoice_id = i.invoice_id) as paid_amount,
                   (CASE WHEN i.total_amount <= (SELECT COALESCE(SUM(p.amount), 0) FROM payments p 
                                               WHERE p.invoice_id = i.invoice_id)
                         THEN true ELSE false END) as is_fully_paid
            FROM invoices i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.customer_id = %s
        """
        params = [customer_id]
        
        # Add ORDER BY clause
        if order_by:
            query += f" ORDER BY i.{order_by}"
        
        # Add LIMIT and OFFSET clauses
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.db.fetch_all(query, tuple(params))
    
    def get_customer_debt_history(self, customer_id, include_paid=False):
        """Get a customer's debt history.
        
        Args:
            customer_id (str): Customer ID
            include_paid (bool, optional): Whether to include paid debts
            
        Returns:
            list: List of debts for the customer
        """
        query = """
            SELECT cd.*,
                   i.invoice_number,
                   u.username as seller_name
            FROM customer_debts cd
            JOIN invoices i ON cd.invoice_id = i.invoice_id
            JOIN users u ON i.user_id = u.user_id
            WHERE cd.customer_id = %s
        """
        params = [customer_id]
        
        if not include_paid:
            query += " AND cd.is_paid = false"
        
        query += " ORDER BY cd.created_at DESC"
        
        return self.db.fetch_all(query, tuple(params))
    
    def get_customer_statistics(self, customer_id):
        """Get statistics for a customer.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            dict: Customer statistics
        """
        # Get purchase statistics
        purchase_query = """
            SELECT 
                COUNT(i.invoice_id) as total_purchases,
                COALESCE(SUM(i.total_amount), 0) as total_spent,
                AVG(i.total_amount) as average_purchase,
                MAX(i.created_at) as last_purchase_date,
                MIN(i.created_at) as first_purchase_date
            FROM invoices i
            WHERE i.customer_id = %s
        """
        purchase_stats = self.db.fetch_one(purchase_query, (customer_id,))
        
        # Get debt statistics
        debt_query = """
            SELECT 
                COUNT(cd.debt_id) as total_debts,
                SUM(cd.amount) as total_debt_amount,
                SUM(cd.amount_paid) as total_debt_paid,
                SUM(cd.amount - cd.amount_paid) as outstanding_debt,
                COUNT(CASE WHEN cd.is_paid = false THEN 1 END) as active_debts
            FROM customer_debts cd
            WHERE cd.customer_id = %s
        """
        debt_stats = self.db.fetch_one(debt_query, (customer_id,))
        
        # Get product statistics
        product_query = """
            SELECT 
                p.product_id,
                p.name as product_name,
                COUNT(ii.invoice_item_id) as purchase_count,
                SUM(ii.quantity) as total_quantity
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.product_id
            JOIN invoices i ON ii.invoice_id = i.invoice_id
            WHERE i.customer_id = %s
            GROUP BY p.product_id, p.name
            ORDER BY purchase_count DESC
            LIMIT 5
        """
        favorite_products = self.db.fetch_all(product_query, (customer_id,))
        
        # Combine results
        stats = {}
        if purchase_stats:
            stats.update(purchase_stats)
        if debt_stats:
            stats.update(debt_stats)
        stats["favorite_products"] = favorite_products
        
        return stats
    
    def _validate_customer_data(self, full_name, email=None, phone=None, tax_id=None):
        """Validate customer data.
        
        Args:
            full_name (str): Customer's full name
            email (str, optional): Customer's email
            phone (str, optional): Customer's phone
            tax_id (str, optional): Customer's tax ID
            
        Raises:
            ValueError: If validation fails
        """
        # Validate full name
        if not full_name or len(full_name) < 2:
            raise ValueError("Full name is required")
        
        # Validate email if provided
        if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Invalid email format")
        
        # Validate phone if provided - just ensure it's not empty
        if phone == "":
            raise ValueError("Phone number cannot be empty if provided")
        
        # Validate tax ID if provided - just ensure it's not empty
        if tax_id == "":
            raise ValueError("Tax ID cannot be empty if provided")
