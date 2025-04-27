#!/usr/bin/env python3
"""
Create test data for POS application.
This script creates sample categories, products, customers, and inventory for testing.
"""

import sys
import traceback
import random
from datetime import datetime, timedelta

from models.database import Database
from models.category import Category
from models.product import Product
from models.customer import Customer
from models.stock import Stock

def main():
    """Main entry point for the script."""
    try:
        print("Connecting to database...")
        db = Database()
        db.initialize()
        
        # Create categories
        print("\nCreating sample categories...")
        category_model = Category(db)
        
        categories = [
            {"name": "Electronics", "description": "Electronic devices and accessories"},
            {"name": "Clothing", "description": "Apparel and fashion items"},
            {"name": "Groceries", "description": "Food and household items"},
            {"name": "Stationery", "description": "Office and school supplies"}
        ]
        
        created_categories = []
        for cat_data in categories:
            # Check if category already exists
            existing = db.fetch_one(
                "SELECT * FROM categories WHERE name = %s", 
                (cat_data["name"],)
            )
            
            if existing:
                print(f"  - Category '{cat_data['name']}' already exists.")
                created_categories.append(existing)
            else:
                category = category_model.create_category(
                    name=cat_data["name"],
                    description=cat_data["description"]
                )
                print(f"  - Created category: {category['name']}")
                created_categories.append(category)
        
        # Create products
        print("\nCreating sample products...")
        product_model = Product(db)
        
        products = [
            {
                "name": "Smartphone", 
                "category_id": next(cat["category_id"] for cat in created_categories if cat["name"] == "Electronics"),
                "sku": "PHONE001",
                "barcode": "1234567890123",
                "purchase_price": 300.00,
                "selling_price": 499.99,
                "description": "Latest smartphone model"
            },
            {
                "name": "Laptop", 
                "category_id": next(cat["category_id"] for cat in created_categories if cat["name"] == "Electronics"),
                "sku": "LAPT001",
                "barcode": "1234567890124",
                "purchase_price": 600.00,
                "selling_price": 999.99,
                "description": "High performance laptop"
            },
            {
                "name": "T-Shirt", 
                "category_id": next(cat["category_id"] for cat in created_categories if cat["name"] == "Clothing"),
                "sku": "TSHIRT001",
                "barcode": "2234567890123",
                "purchase_price": 5.00,
                "selling_price": 15.99,
                "description": "Cotton T-shirt"
            },
            {
                "name": "Jeans", 
                "category_id": next(cat["category_id"] for cat in created_categories if cat["name"] == "Clothing"),
                "sku": "JEANS001",
                "barcode": "2234567890124",
                "purchase_price": 20.00,
                "selling_price": 39.99,
                "description": "Denim jeans"
            },
            {
                "name": "Milk", 
                "category_id": next(cat["category_id"] for cat in created_categories if cat["name"] == "Groceries"),
                "sku": "MILK001",
                "barcode": "3234567890123",
                "purchase_price": 0.80,
                "selling_price": 1.99,
                "description": "Fresh milk 1L"
            },
            {
                "name": "Bread", 
                "category_id": next(cat["category_id"] for cat in created_categories if cat["name"] == "Groceries"),
                "sku": "BREAD001",
                "barcode": "3234567890124",
                "purchase_price": 1.00,
                "selling_price": 2.49,
                "description": "Fresh bread loaf"
            },
            {
                "name": "Notebook", 
                "category_id": next(cat["category_id"] for cat in created_categories if cat["name"] == "Stationery"),
                "sku": "NOTE001",
                "barcode": "4234567890123",
                "purchase_price": 1.50,
                "selling_price": 3.99,
                "description": "100-page notebook"
            },
            {
                "name": "Pen Set", 
                "category_id": next(cat["category_id"] for cat in created_categories if cat["name"] == "Stationery"),
                "sku": "PEN001",
                "barcode": "4234567890124",
                "purchase_price": 2.00,
                "selling_price": 4.99,
                "description": "Set of 5 ballpoint pens"
            }
        ]
        
        created_products = []
        for prod_data in products:
            # Check if product already exists
            existing = db.fetch_one(
                "SELECT * FROM products WHERE sku = %s", 
                (prod_data["sku"],)
            )
            
            if existing:
                print(f"  - Product '{prod_data['name']}' already exists.")
                created_products.append(existing)
            else:
                product = product_model.create_product(
                    name=prod_data["name"],
                    category_id=prod_data["category_id"],
                    sku=prod_data["sku"],
                    barcode=prod_data["barcode"],
                    purchase_price=prod_data["purchase_price"],
                    selling_price=prod_data["selling_price"],
                    description=prod_data["description"]
                )
                print(f"  - Created product: {product['name']} (SKU: {product['sku']})")
                created_products.append(product)
        
        # Create customers
        print("\nCreating sample customers...")
        customer_model = Customer(db)
        
        customers = [
            {
                "full_name": "John Smith",
                "email": "john.smith@example.com",
                "phone": "555-123-4567",
                "address": "123 Main St, Anytown, USA"
            },
            {
                "full_name": "Jane Doe",
                "email": "jane.doe@example.com",
                "phone": "555-987-6543",
                "address": "456 Oak Ave, Somecity, USA"
            },
            {
                "full_name": "Bob Johnson",
                "email": "bob.johnson@example.com",
                "phone": "555-456-7890",
                "address": "789 Elm St, Anothercity, USA"
            }
        ]
        
        created_customers = []
        for cust_data in customers:
            # Check if customer already exists
            existing = db.fetch_one(
                "SELECT * FROM customers WHERE email = %s", 
                (cust_data["email"],)
            )
            
            if existing:
                print(f"  - Customer '{cust_data['full_name']}' already exists.")
                created_customers.append(existing)
            else:
                customer = customer_model.create_customer(
                    full_name=cust_data["full_name"],
                    email=cust_data["email"],
                    phone=cust_data["phone"],
                    address=cust_data["address"]
                )
                print(f"  - Created customer: {customer['full_name']}")
                created_customers.append(customer)
        
        # Add stock for products
        print("\nAdding stock for products...")
        stock_model = Stock(db)
        
        for product in created_products:
            # Check if stock entry already exists
            existing = db.fetch_one(
                "SELECT * FROM stock WHERE product_id = %s", 
                (product["product_id"],)
            )
            
            if existing:
                print(f"  - Stock for '{product['name']}' already exists ({existing['quantity']} units).")
            else:
                # Add random stock between 10 and 100 units
                quantity = random.randint(10, 100)
                
                try:
                    stock = stock_model.update_stock_quantity(
                        product_id=product["product_id"],
                        quantity_change=quantity,
                        reason="Initial stock"
                    )
                    print(f"  - Added {quantity} units of {product['name']}")
                except Exception as e:
                    print(f"  - Error adding stock for {product['name']}: {str(e)}")
        
        print("\nTest data creation completed successfully!")
        return True
        
    except Exception as e:
        print(f"\nError creating test data: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)