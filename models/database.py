"""
Database connection and management for POS application.
"""

import os
import time
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor


class Database:
    """Database connection manager."""
    
    def __init__(self):
        """Initialize the database connection."""
        self.connection_pool = None
        self.connection = None
        self.cursor = None
        self.in_transaction = False
    
    def initialize(self):
        """Initialize the database connection pool and create tables if needed.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            Exception: If database connection fails
        """
        # Use DATABASE_URL if available, otherwise use individual env vars
        db_url = os.environ.get("DATABASE_URL")
        
        # Create connection pool
        try:
            if db_url:
                # Connect using DATABASE_URL
                self.connection_pool = pool.SimpleConnectionPool(
                    1,  # min connections
                    10,  # max connections
                    db_url
                )
            else:
                # Connect using individual parameters
                db_host = os.environ.get("PGHOST", "localhost")
                db_port = os.environ.get("PGPORT", "5432")
                db_name = os.environ.get("PGDATABASE", "pos_db")
                db_user = os.environ.get("PGUSER", "postgres")
                db_password = os.environ.get("PGPASSWORD", "postgres")
                
                self.connection_pool = pool.SimpleConnectionPool(
                    1,  # min connections
                    10,  # max connections
                    host=db_host,
                    port=db_port,
                    database=db_name,
                    user=db_user,
                    password=db_password
                )
            
            # Test connection
            with self.get_connection():
                pass
            
            # Create tables if they don't exist
            self._create_tables()
            
            return True
            
        except psycopg2.Error as e:
            raise Exception(f"Failed to connect to database: {str(e)}")
    
    def get_connection(self):
        """Get a connection from the pool.
        
        Returns:
            connection: Database connection
        """
        if not self.connection:
            self.connection = self.connection_pool.getconn()
        
        return self.connection
    
    def get_cursor(self):
        """Get a cursor for executing queries.
        
        Returns:
            cursor: Database cursor
        """
        if not self.cursor or self.cursor.closed:
            self.cursor = self.get_connection().cursor(cursor_factory=RealDictCursor)
        
        return self.cursor
    
    def close(self):
        """Close database resources."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        
        if self.connection:
            # Return connection to pool
            self.connection_pool.putconn(self.connection)
            self.connection = None
    
    def execute(self, query, params=None):
        """Execute a query.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters
            
        Returns:
            int: Number of affected rows
        """
        cursor = self.get_cursor()
        cursor.execute(query, params or ())
        
        # If not in transaction, commit immediately
        if not self.in_transaction:
            self.connection.commit()
            
        return cursor.rowcount
    
    def fetch_one(self, query, params=None):
        """Execute a query and fetch one result.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters
            
        Returns:
            dict: Query result as dictionary or None if no result
        """
        cursor = self.get_cursor()
        cursor.execute(query, params or ())
        return cursor.fetchone()
    
    def fetch_all(self, query, params=None):
        """Execute a query and fetch all results.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters
            
        Returns:
            list: Query results as dictionary list
        """
        cursor = self.get_cursor()
        cursor.execute(query, params or ())
        return cursor.fetchall()
    
    def begin_transaction(self):
        """Begin a transaction."""
        self.in_transaction = True
    
    def commit_transaction(self):
        """Commit the current transaction."""
        if self.in_transaction and self.connection:
            self.connection.commit()
            self.in_transaction = False
    
    def rollback_transaction(self):
        """Rollback the current transaction."""
        if self.in_transaction and self.connection:
            self.connection.rollback()
            self.in_transaction = False
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        # Read schema file
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "schema.sql")
        
        try:
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            
            # Execute schema
            self.get_connection().autocommit = True
            cursor = self.get_cursor()
            cursor.execute(schema_sql)
            self.get_connection().autocommit = False
            
        except FileNotFoundError:
            # Create minimal schema required to run
            self._create_minimal_schema()
    
    def _create_minimal_schema(self):
        """Create a minimal schema if schema.sql is not found."""
        # Users table
        self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                role VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                last_login TIMESTAMP
            )
        """)
        
        # Categories table
        self.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                parent_id VARCHAR(36),
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES categories(category_id)
            )
        """)
        
        # Products table
        self.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                sku VARCHAR(50) UNIQUE NOT NULL,
                barcode VARCHAR(50) UNIQUE,
                category_id VARCHAR(36) NOT NULL,
                description TEXT,
                purchase_price NUMERIC(10, 2) NOT NULL,
                selling_price NUMERIC(10, 2) NOT NULL,
                tax_rate NUMERIC(5, 2) NOT NULL DEFAULT 0,
                low_stock_threshold INTEGER NOT NULL DEFAULT 10,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        """)
        
        # Stock table
        self.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                stock_id VARCHAR(36) PRIMARY KEY,
                product_id VARCHAR(36) UNIQUE NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        
        # Stock movements table
        self.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                movement_id VARCHAR(36) PRIMARY KEY,
                product_id VARCHAR(36) NOT NULL,
                quantity INTEGER NOT NULL,
                movement_type VARCHAR(10) NOT NULL,
                reason TEXT,
                reference_id VARCHAR(36),
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        
        # Customers table
        self.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id VARCHAR(36) PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                address TEXT,
                tax_id VARCHAR(50),
                notes TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        
        # Invoices table
        self.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id VARCHAR(36) PRIMARY KEY,
                invoice_number VARCHAR(20) UNIQUE NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                customer_id VARCHAR(36),
                total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
                status VARCHAR(20) NOT NULL,
                notes TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)
        
        # Invoice items table
        self.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                invoice_item_id VARCHAR(36) PRIMARY KEY,
                invoice_id VARCHAR(36) NOT NULL,
                product_id VARCHAR(36) NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price NUMERIC(10, 2) NOT NULL,
                discount_price NUMERIC(10, 2),
                subtotal NUMERIC(10, 2) NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        
        # Cash registers table
        self.execute("""
            CREATE TABLE IF NOT EXISTS cash_registers (
                register_id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                opening_amount NUMERIC(10, 2) NOT NULL,
                current_amount NUMERIC(10, 2) NOT NULL,
                closing_amount NUMERIC(10, 2),
                opening_time TIMESTAMP NOT NULL,
                closing_time TIMESTAMP,
                status VARCHAR(20) NOT NULL,
                notes TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Cash register transactions table
        self.execute("""
            CREATE TABLE IF NOT EXISTS cash_register_transactions (
                transaction_id VARCHAR(36) PRIMARY KEY,
                register_id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                transaction_type VARCHAR(20) NOT NULL,
                description TEXT,
                reference_id VARCHAR(36),
                previous_amount NUMERIC(10, 2) NOT NULL,
                new_amount NUMERIC(10, 2) NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (register_id) REFERENCES cash_registers(register_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Payments table
        self.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id VARCHAR(36) PRIMARY KEY,
                invoice_id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                payment_method VARCHAR(20) NOT NULL,
                reference_number VARCHAR(50),
                payment_date TIMESTAMP NOT NULL,
                notes TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Customer debts table
        self.execute("""
            CREATE TABLE IF NOT EXISTS customer_debts (
                debt_id VARCHAR(36) PRIMARY KEY,
                customer_id VARCHAR(36) NOT NULL,
                invoice_id VARCHAR(36) NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                amount_paid NUMERIC(10, 2) NOT NULL DEFAULT 0,
                is_paid BOOLEAN NOT NULL DEFAULT FALSE,
                created_by VARCHAR(36),
                notes TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                last_payment_date TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        """)
        
        # Create admin user if no users exist
        query = "SELECT COUNT(*) as count FROM users"
        result = self.fetch_one(query)
        
        if result and result["count"] == 0:
            # Import user model to create admin
            from models.user import User
            user_model = User(self)
            
            try:
                user_model.create_user(
                    username="admin",
                    password="admin123",  # This should be changed immediately
                    full_name="System Administrator",
                    role="ADMIN",
                    email="admin@example.com"
                )
                print("Created default admin user (username: admin, password: admin123)")
            except Exception as e:
                print(f"Failed to create admin user: {str(e)}")
