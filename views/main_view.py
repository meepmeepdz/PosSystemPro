"""
Main view for POS application.
Serves as the container for all other views.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time

from views.base_view import BaseView
from views.user_view import UserView
from views.product_view import ProductView
from views.category_view import CategoryView
from views.customer_view import CustomerView
from views.stock_view import StockView
from views.invoice_view import InvoiceView
from views.cash_register_view import CashRegisterView
from views.payment_view import PaymentView
from views.debt_view import DebtView
from views.report_view import ReportView
from views.backup_view import BackupView
from views.components.message_box import MessageBox

from config import COLORS, APP_TITLE, COMPANY_NAME, SESSION_TIMEOUT


class MainView(BaseView):
    """Main view that contains all other views."""
    
    def __init__(self, parent, controllers, user, on_logout):
        """Initialize main view.
        
        Args:
            parent: Parent widget
            controllers (dict): Dictionary of controllers
            user (dict): Current user information
            on_logout: Callback for logout
        """
        super().__init__(parent)
        self.parent = parent
        self.controllers = controllers
        self.user = user
        self.on_logout = on_logout
        
        # Track active view
        self.active_view = None
        self.active_view_name = None
        
        # Session tracking
        self.last_activity_time = time.time()
        self.session_timeout = SESSION_TIMEOUT
        self.session_timer = None
        
        # Create user interface
        self._create_widgets()
        self._create_bindings()
        
        # Start session timer
        self._start_session_timer()
        
        # Show initial view (default to sales)
        self.show_view("sales")
        
        # Reset session timer on startup
        self._reset_session_timer()
    
    def _create_widgets(self):
        """Create and layout main widgets."""
        # Main container with border
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self._create_header()
        
        # Create sidebar menu
        self._create_sidebar()
        
        # Create content area
        self.content_frame = ttk.Frame(self.main_container, padding=10)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Status bar at the bottom
        self._create_status_bar()
    
    def _create_header(self):
        """Create the header section."""
        header_frame = ttk.Frame(self.main_container, padding=5, style="Header.TFrame")
        header_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Add company and app title
        title_label = ttk.Label(
            header_frame, 
            text=f"{COMPANY_NAME} - {APP_TITLE}",
            font=("", 14, "bold"),
            foreground=COLORS["primary"]
        )
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Add user info and logout button on the right
        user_frame = ttk.Frame(header_frame)
        user_frame.pack(side=tk.RIGHT, padx=10)
        
        user_label = ttk.Label(
            user_frame,
            text=f"Logged in as: {self.user['username']} ({self.user['role']})",
            font=("", 10)
        )
        user_label.pack(side=tk.LEFT, padx=10)
        
        logout_button = ttk.Button(
            user_frame,
            text="Logout",
            command=self._handle_logout,
            style="Secondary.TButton"
        )
        logout_button.pack(side=tk.RIGHT)
    
    def _create_sidebar(self):
        """Create the sidebar menu."""
        sidebar_frame = ttk.Frame(self.main_container, width=200, padding=10)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        sidebar_frame.pack_propagate(False)  # Prevent shrinking
        
        # Style for menu buttons
        self.style.configure(
            "Menu.TButton",
            font=("", 11),
            padding=10,
            anchor="w",  # Align text to the left
            width=20
        )
        
        # Create menu items
        self._create_menu_button(sidebar_frame, "Sales", "sales", True)
        self._create_menu_button(sidebar_frame, "Products", "products", True)
        self._create_menu_button(sidebar_frame, "Categories", "categories", True)
        self._create_menu_button(sidebar_frame, "Customers", "customers", True)
        self._create_menu_button(sidebar_frame, "Inventory", "inventory", True)
        
        # Add separator
        ttk.Separator(sidebar_frame, orient="horizontal").pack(fill=tk.X, pady=10)
        
        self._create_menu_button(sidebar_frame, "Cash Register", "cash_register", True)
        self._create_menu_button(sidebar_frame, "Payments", "payments", True)
        self._create_menu_button(sidebar_frame, "Customer Debts", "debts", True)
        
        # Add separator
        ttk.Separator(sidebar_frame, orient="horizontal").pack(fill=tk.X, pady=10)
        
        self._create_menu_button(sidebar_frame, "Reports", "reports", True)
        self._create_menu_button(sidebar_frame, "Users", "users", 
                                self.controllers["auth"].is_manager_or_admin())
        self._create_menu_button(sidebar_frame, "Backup & Restore", "backup", 
                                self.controllers["auth"].is_admin())
    
    def _create_menu_button(self, parent, text, view_name, show=True):
        """Create a menu button in the sidebar.
        
        Args:
            parent: Parent widget
            text (str): Button text
            view_name (str): View to show when clicked
            show (bool): Whether to show the button
        """
        if not show:
            return
        
        button = ttk.Button(
            parent,
            text=text,
            style="Menu.TButton",
            command=lambda: self.show_view(view_name)
        )
        button.pack(fill=tk.X, pady=2)
    
    def _create_status_bar(self):
        """Create the status bar at the bottom."""
        status_frame = ttk.Frame(self, padding=2, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status message on the left
        self.status_message = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_message)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Session timer info on the right
        self.session_info = tk.StringVar()
        session_label = ttk.Label(status_frame, textvariable=self.session_info)
        session_label.pack(side=tk.RIGHT, padx=5)
    
    def _create_bindings(self):
        """Set up event bindings."""
        # Bind activity tracking to various events
        self.bind_all("<Button>", self._reset_session_timer)
        self.bind_all("<KeyPress>", self._reset_session_timer)
        self.bind_all("<MouseWheel>", self._reset_session_timer)
    
    def show_view(self, view_name):
        """Show a specific view in the content area.
        
        Args:
            view_name (str): Name of the view to show
        """
        # Clear current view
        if self.active_view:
            self.active_view.pack_forget()
            self.active_view.destroy()
        
        # Create and show new view
        self.active_view_name = view_name
        
        try:
            if view_name == "sales":
                self.active_view = InvoiceView(
                    self.content_frame, 
                    self.controllers["invoice"],
                    self.controllers["product"],
                    self.controllers["customer"],
                    self.controllers["payment"],
                    self.controllers["cash_register"],
                    self.controllers["stock"],
                    self.controllers["debt"],
                    self.user
                )
            elif view_name == "products":
                self.active_view = ProductView(
                    self.content_frame, 
                    self.controllers["product"],
                    self.controllers["category"],
                    self.controllers["stock"]
                )
            elif view_name == "categories":
                self.active_view = CategoryView(
                    self.content_frame, 
                    self.controllers["category"]
                )
            elif view_name == "customers":
                self.active_view = CustomerView(
                    self.content_frame, 
                    self.controllers["customer"],
                    self.controllers["invoice"],
                    self.controllers["debt"]
                )
            elif view_name == "inventory":
                self.active_view = StockView(
                    self.content_frame, 
                    self.controllers["stock"],
                    self.controllers["product"]
                )
            elif view_name == "cash_register":
                self.active_view = CashRegisterView(
                    self.content_frame, 
                    self.controllers["cash_register"],
                    self.user
                )
            elif view_name == "payments":
                self.active_view = PaymentView(
                    self.content_frame, 
                    self.controllers["payment"],
                    self.controllers["invoice"]
                )
            elif view_name == "debts":
                self.active_view = DebtView(
                    self.content_frame, 
                    self.controllers["debt"],
                    self.controllers["customer"],
                    self.controllers["payment"],
                    self.user
                )
            elif view_name == "reports":
                self.active_view = ReportView(
                    self.content_frame, 
                    self.controllers["report"],
                    self.controllers["user"],
                    self.controllers["product"],
                    self.controllers["customer"]
                )
            elif view_name == "users":
                self.active_view = UserView(
                    self.content_frame, 
                    self.controllers["user"],
                    self.controllers["auth"],
                    self.user
                )
            elif view_name == "backup":
                self.active_view = BackupView(
                    self.content_frame, 
                    self.controllers["backup"]
                )
            else:
                raise ValueError(f"Unknown view: {view_name}")
            
            # Show the view
            self.active_view.pack(fill=tk.BOTH, expand=True)
            
            # Update status message
            view_titles = {
                "sales": "Sales & Invoicing",
                "products": "Product Management",
                "categories": "Category Management",
                "customers": "Customer Management",
                "inventory": "Inventory Management",
                "cash_register": "Cash Register",
                "payments": "Payment Management",
                "debts": "Customer Debts",
                "reports": "Reports",
                "users": "User Management",
                "backup": "Backup & Restore"
            }
            
            self.status_message.set(f"Current view: {view_titles.get(view_name, 'Unknown')}")
            
        except Exception as e:
            MessageBox.show_error(self, f"Error loading view: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _handle_logout(self):
        """Handle user logout."""
        # Stop session timer
        if self.session_timer:
            self.after_cancel(self.session_timer)
        
        # Clear user and call logout callback
        self.controllers["auth"].logout()
        self.on_logout()
    
    def _start_session_timer(self):
        """Start the session timeout timer."""
        self._update_session_timer()
    
    def _update_session_timer(self):
        """Update the session timer display and check for timeout."""
        current_time = time.time()
        elapsed = current_time - self.last_activity_time
        remaining = max(0, self.session_timeout - elapsed)
        
        # Format time remaining
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        self.session_info.set(f"Session timeout: {minutes:02d}:{seconds:02d}")
        
        # Check for timeout
        if remaining <= 0:
            self.session_info.set("Session expired")
            self._handle_session_timeout()
            return
        
        # Schedule next update
        self.session_timer = self.after(1000, self._update_session_timer)
    
    def _reset_session_timer(self, event=None):
        """Reset the session timer on user activity."""
        self.last_activity_time = time.time()
    
    def _handle_session_timeout(self):
        """Handle session timeout by logging out."""
        MessageBox.show_warning(self, "Your session has timed out due to inactivity.")
        self._handle_logout()
