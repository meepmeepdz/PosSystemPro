#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
POS Application Entry Point
This is the main entry point for the Point of Sale application.
It initializes the database connection, sets up the main window,
and starts the application loop.
"""

import sys
import traceback
import os

# Import database initialization
from models.database import Database

# Check if we're running in a graphical environment
HAS_DISPLAY = os.environ.get('DISPLAY') or (sys.platform == 'win32') or (sys.platform == 'darwin')

# Non-GUI mode flag - check if this is explicitly requested or if we're in a headless environment
NON_GUI_MODE = os.environ.get('POS_NON_GUI', 'false').lower() in ('true', '1', 't') or not HAS_DISPLAY

# Import controllers
from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.customer_controller import CustomerController
from controllers.stock_controller import StockController
from controllers.invoice_controller import InvoiceController
from controllers.cash_register_controller import CashRegisterController
from controllers.payment_controller import PaymentController
from controllers.debt_controller import DebtController
from controllers.report_controller import ReportController
from controllers.backup_controller import BackupController


def setup_database():
    """Initialize database connection and return db instance."""
    try:
        db = Database()
        db.initialize()
        return db
    except Exception as e:
        print(f"Database Error: Failed to connect to the database.\n\nError: {str(e)}")
        sys.exit(1)


def run_cli_mode():
    """Run the application in command-line interface mode."""
    print("Running POS System in non-GUI mode (Command Line Interface)")
    print("This mode is intended for server environments without a display.")
    
    # Initialize database
    db = setup_database()
    
    # Initialize controllers
    auth_controller = AuthController(db)
    user_controller = UserController(db)
    product_controller = ProductController(db)
    category_controller = CategoryController(db)
    customer_controller = CustomerController(db)
    stock_controller = StockController(db)
    invoice_controller = InvoiceController(db)
    cash_register_controller = CashRegisterController(db)
    payment_controller = PaymentController(db)
    debt_controller = DebtController(db)
    report_controller = ReportController(db)
    backup_controller = BackupController(db)
    
    controllers = {
        'auth': auth_controller,
        'user': user_controller,
        'product': product_controller,
        'category': category_controller,
        'customer': customer_controller,
        'stock': stock_controller,
        'invoice': invoice_controller,
        'cash_register': cash_register_controller,
        'payment': payment_controller,
        'debt': debt_controller,
        'report': report_controller,
        'backup': backup_controller
    }
    
    # Print information about the database
    print("\nDatabase Information:")
    print("- Host:", os.environ.get("PGHOST", "localhost"))
    print("- Database:", os.environ.get("PGDATABASE", "pos_db"))
    
    # Show available user accounts
    users = user_controller.get_all_users()
    print("\nAvailable User Accounts:")
    for i, user in enumerate(users, 1):
        print(f"{i}. Username: {user['username']} | Role: {user['role']} | Name: {user['full_name']}")
    
    # Show some basic stats
    product_count = product_controller.count_products()
    customer_count = customer_controller.count_customers()
    invoice_count = invoice_controller.count_invoices()
    
    print("\nSystem Statistics:")
    print(f"- Products: {product_count}")
    print(f"- Customers: {customer_count}")
    print(f"- Invoices: {invoice_count}")
    
    print("\nSystem is ready. Use API endpoints or scripts to interact with the system.")
    print("Press Ctrl+C to exit.")
    
    try:
        # Keep the application running
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        db.close()


def run_gui_mode():
    """Run the application in graphical user interface mode."""
    import tkinter as tk
    from tkinter import messagebox
    
    # Import configuration
    from config import APP_TITLE, APP_SIZE, DEFAULT_FONT
    
    # Import views
    from views.login_view import LoginView
    
    class POSApplication:
        """Main application class for the POS system."""
        
        def __init__(self):
            """Initialize the application."""
            self.root = tk.Tk()
            self.root.title(APP_TITLE)
            self.root.geometry(f"{APP_SIZE[0]}x{APP_SIZE[1]}")
            self.root.minsize(800, 600)
            
            # Configure default font
            self.root.option_add("*Font", DEFAULT_FONT)
            
            # Initialize database
            try:
                self.db = Database()
                self.db.initialize()
            except Exception as e:
                messagebox.showerror("Database Error", 
                                    f"Failed to connect to the database.\n\nError: {str(e)}")
                sys.exit(1)
            
            # Initialize controllers
            self.auth_controller = AuthController(self.db)
            
            # Set up exception handling
            self._setup_exception_handler()
            
            # Start with login view
            self.current_view = None
            self.show_login()
        
        def show_login(self):
            """Show the login view."""
            if self.current_view:
                self.current_view.destroy()
            
            self.current_view = LoginView(self.root, self.auth_controller, self.on_successful_login)
            self.current_view.pack(fill=tk.BOTH, expand=True)
        
        def on_successful_login(self, user):
            """Handle successful login by showing the main application."""
            from views.main_view import MainView
            
            # Initialize all controllers
            user_controller = UserController(self.db)
            product_controller = ProductController(self.db)
            category_controller = CategoryController(self.db)
            customer_controller = CustomerController(self.db)
            stock_controller = StockController(self.db)
            invoice_controller = InvoiceController(self.db)
            cash_register_controller = CashRegisterController(self.db)
            payment_controller = PaymentController(self.db)
            debt_controller = DebtController(self.db)
            report_controller = ReportController(self.db)
            backup_controller = BackupController(self.db)
            
            # Dictionary of controllers to pass to the main view
            controllers = {
                'auth': self.auth_controller,
                'user': user_controller,
                'product': product_controller,
                'category': category_controller,
                'customer': customer_controller,
                'stock': stock_controller,
                'invoice': invoice_controller,
                'cash_register': cash_register_controller,
                'payment': payment_controller,
                'debt': debt_controller,
                'report': report_controller,
                'backup': backup_controller
            }
            
            if self.current_view:
                self.current_view.destroy()
            
            self.current_view = MainView(self.root, controllers, user, self.show_login)
            self.current_view.pack(fill=tk.BOTH, expand=True)
        
        def _setup_exception_handler(self):
            """Set up global exception handler to catch unhandled exceptions."""
            def handle_exception(exc_type, exc_value, exc_traceback):
                if issubclass(exc_type, KeyboardInterrupt):
                    # Handle keyboard interrupt differently
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return
                
                # Log the error
                error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                print(f"Unhandled exception:\n{error_msg}", file=sys.stderr)
                
                # Show error to user
                messagebox.showerror("Application Error", 
                                    f"An unexpected error occurred:\n\n{str(exc_value)}\n\nPlease contact support.")
            
            sys.excepthook = handle_exception
        
        def run(self):
            """Run the application main loop."""
            self.root.mainloop()
            
            # Clean up database connection when app closes
            if hasattr(self, 'db'):
                self.db.close()
    
    # Create and run the GUI application
    app = POSApplication()
    app.run()


if __name__ == "__main__":
    try:
        # Choose the appropriate mode based on environment
        if NON_GUI_MODE:
            run_cli_mode()
        else:
            run_gui_mode()
    except Exception as e:
        print(f"Application startup error: {str(e)}")
        traceback.print_exc()
