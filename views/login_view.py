"""
Login view for POS application.
Handles user authentication UI.
"""

import tkinter as tk
from tkinter import ttk

from views.base_view import BaseView
from views.components.form_widgets import LabelInput
from config import COLORS, APP_TITLE, COMPANY_NAME


class LoginView(BaseView):
    """Login view for user authentication."""
    
    def __init__(self, parent, auth_controller, on_login_success):
        """Initialize login view.
        
        Args:
            parent: Parent widget
            auth_controller: Authentication controller
            on_login_success: Callback function for successful login
        """
        super().__init__(parent)
        self.parent = parent
        self.auth_controller = auth_controller
        self.on_login_success = on_login_success
        
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.status_var = tk.StringVar()
        
        self._create_widgets()
        self._create_bindings()
    
    def _create_widgets(self):
        """Create and layout login widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Company name and app title
        company_label = ttk.Label(
            main_frame, 
            text=COMPANY_NAME,
            font=("", 16, "bold"),
            foreground=COLORS["primary"]
        )
        company_label.pack(pady=(0, 5))
        
        title_label = ttk.Label(
            main_frame, 
            text=APP_TITLE,
            font=("", 20, "bold"),
            foreground=COLORS["dark"]
        )
        title_label.pack(pady=(0, 30))
        
        # Login frame
        login_frame = ttk.Frame(main_frame, padding=20)
        login_frame.pack(fill=tk.BOTH, expand=False)
        
        # Login header
        login_header = ttk.Label(
            login_frame,
            text="Login to Your Account",
            style="Header.TLabel"
        )
        login_header.pack(pady=(0, 20))
        
        # Username field
        self.username_field = LabelInput(
            login_frame,
            "Username:",
            input_class=ttk.Entry,
            input_var=self.username_var,
            input_args={"width": 30}
        )
        self.username_field.pack(fill=tk.X, pady=5)
        
        # Password field
        self.password_field = LabelInput(
            login_frame,
            "Password:",
            input_class=ttk.Entry,
            input_var=self.password_var,
            input_args={"width": 30, "show": "•"}
        )
        self.password_field.pack(fill=tk.X, pady=5)
        
        # Login button
        login_button = ttk.Button(
            login_frame,
            text="Login",
            style="Primary.TButton",
            command=self._on_login
        )
        login_button.pack(pady=15, fill=tk.X)
        
        # Status message
        status_label = ttk.Label(
            login_frame,
            textvariable=self.status_var,
            foreground=COLORS["danger"]
        )
        status_label.pack(pady=10)
    
    def _create_bindings(self):
        """Create event bindings."""
        # Bind Enter key to login button
        self.password_field.input.bind("<Return>", lambda event: self._on_login())
        self.username_field.input.bind("<Return>", lambda event: self._on_login())
    
    def _on_login(self):
        """Handle login button click."""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        # Basic validation
        if not username:
            self.status_var.set("Username is required")
            self.username_field.input.focus_set()
            return
        
        if not password:
            self.status_var.set("Password is required")
            self.password_field.input.focus_set()
            return
        
        # Clear status
        self.status_var.set("")
        
        # Attempt to authenticate
        try:
            user = self.auth_controller.login(username, password)
            
            if user:
                # Call success callback with the user
                self.on_login_success(user)
            else:
                self.status_var.set("Invalid username or password")
                self.password_var.set("")  # Clear password field
                self.password_field.input.focus_set()
        
        except Exception as e:
            self.status_var.set(f"Login error: {str(e)}")
