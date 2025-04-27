"""
Base model class to be inherited by all model classes.
Provides common functionality for database operations.
"""

import uuid
from datetime import datetime
from abc import ABC


class BaseModel(ABC):
    """Base model class for all database models."""
    
    def __init__(self, db):
        """Initialize the model with database connection.
        
        Args:
            db: Database instance for executing queries
        """
        self.db = db
        self.table_name = None  # To be defined by child classes
        self.primary_key = None  # To be defined by child classes
    
    def generate_id(self):
        """Generate a unique ID for new records.
        
        Returns:
            str: A UUID4 string representation
        """
        return str(uuid.uuid4())
    
    def get_timestamp(self):
        """Get current timestamp for database records.
        
        Returns:
            str: Current datetime in ISO format
        """
        return datetime.now().isoformat()
    
    def get_by_id(self, id_value):
        """Get a record by its primary key.
        
        Args:
            id_value: Value of the primary key to look up
            
        Returns:
            dict: Record as a dictionary or None if not found
        """
        query = f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = %s"
        return self.db.fetch_one(query, (id_value,))
    
    def get_all(self, order_by=None, limit=None, offset=None, filters=None):
        """Get all records with optional filtering and pagination.
        
        Args:
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            filters (dict, optional): Dictionary of column/value pairs for filtering
            
        Returns:
            list: List of records as dictionaries
        """
        query = f"SELECT * FROM {self.table_name}"
        params = []
        
        # Add WHERE clauses for filters
        if filters:
            conditions = []
            for column, value in filters.items():
                if isinstance(value, (list, tuple)):
                    # Handle IN clauses
                    placeholders = ', '.join(['%s'] * len(value))
                    conditions.append(f"{column} IN ({placeholders})")
                    params.extend(value)
                elif value is None:
                    conditions.append(f"{column} IS NULL")
                else:
                    conditions.append(f"{column} = %s")
                    params.append(value)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        # Add ORDER BY clause
        if order_by:
            query += f" ORDER BY {order_by}"
        
        # Add LIMIT and OFFSET clauses
        if limit:
            query += f" LIMIT %s"
            params.append(limit)
        
        if offset:
            query += f" OFFSET %s"
            params.append(offset)
        
        return self.db.fetch_all(query, tuple(params))
    
    def create(self, data):
        """Create a new record.
        
        Args:
            data (dict): Dictionary of column/value pairs
            
        Returns:
            dict: Created record as a dictionary
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())
        
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders}) RETURNING *"
        return self.db.fetch_one(query, values)
    
    def update(self, id_value, data):
        """Update an existing record.
        
        Args:
            id_value: Value of the primary key to update
            data (dict): Dictionary of column/value pairs to update
            
        Returns:
            dict: Updated record as a dictionary
        """
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        values = list(data.values())
        values.append(id_value)
        
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.primary_key} = %s RETURNING *"
        return self.db.fetch_one(query, tuple(values))
    
    def delete(self, id_value):
        """Delete a record by its primary key.
        
        Args:
            id_value: Value of the primary key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = %s RETURNING {self.primary_key}"
        result = self.db.fetch_one(query, (id_value,))
        return result is not None
    
    def count(self, filters=None):
        """Count records, optionally with filters.
        
        Args:
            filters (dict, optional): Dictionary of column/value pairs for filtering
            
        Returns:
            int: Number of records
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        params = []
        
        # Add WHERE clauses for filters
        if filters:
            conditions = []
            for column, value in filters.items():
                if isinstance(value, (list, tuple)):
                    # Handle IN clauses
                    placeholders = ', '.join(['%s'] * len(value))
                    conditions.append(f"{column} IN ({placeholders})")
                    params.extend(value)
                elif value is None:
                    conditions.append(f"{column} IS NULL")
                else:
                    conditions.append(f"{column} = %s")
                    params.append(value)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        result = self.db.fetch_one(query, tuple(params))
        return result['count'] if result else 0
    
    def get_where(self, conditions, params=None, order_by=None, limit=None, offset=None):
        """Get records with custom WHERE clause.
        
        Args:
            conditions (str): WHERE conditions as string
            params (tuple, optional): Parameters for the query
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of records as dictionaries
        """
        query = f"SELECT * FROM {self.table_name} WHERE {conditions}"
        
        # Add ORDER BY clause
        if order_by:
            query += f" ORDER BY {order_by}"
        
        # Add LIMIT and OFFSET clauses
        if limit:
            query += f" LIMIT {limit}"
        
        if offset:
            query += f" OFFSET {offset}"
        
        return self.db.fetch_all(query, params)
