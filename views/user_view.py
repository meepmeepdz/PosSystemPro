"""
User view for POS application.
Handles user management.
"""

import tkinter as tk
from tkinter import ttk

from views.base_view import BaseView
from views.components.message_box import MessageBox


class UserView(BaseView):
    """View for user management."""
    
    def __init__(self, parent, user_controller, auth_controller, current_user):
        """Initialize user view.
        
        Args:
            parent: Parent widget
            user_controller: Controller for user operations
            auth_controller: Controller for authentication operations
            current_user: Current logged-in user information
        """
        super().__init__(parent)
        self.parent = parent
        self.user_controller = user_controller
        self.auth_controller = auth_controller
        self.current_user = current_user
        
        # Selected user
        self.selected_user = None
        
        # Variables
        self.username_var = tk.StringVar()
        self.full_name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.is_active_var = tk.BooleanVar(value=True)
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.change_password_var = tk.BooleanVar(value=False)
        self.show_inactive_var = tk.BooleanVar(value=False)
        
        # Create UI components
        self._create_widgets()
        
        # Initial data load
        self._refresh_users()
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with two panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel 1: User list
        self.user_list_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.user_list_frame, weight=1)
        
        # Panel 2: User details/edit
        self.user_detail_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.user_detail_frame, weight=1)
        
        # Set up user list panel
        self._create_user_list_panel()
        
        # Set up user details panel
        self._create_user_detail_panel()
    
    def _create_user_list_panel(self):
        """Create and populate the user list panel."""
        # Header
        header_label = ttk.Label(
            self.user_list_frame, 
            text="Users", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Show inactive users checkbox
        check_frame = ttk.Frame(self.user_list_frame)
        check_frame.pack(fill=tk.X, pady=5)
        
        show_inactive_check = ttk.Checkbutton(
            check_frame, 
            text="Show inactive users", 
            variable=self.show_inactive_var,
            command=self._refresh_users
        )
        show_inactive_check.pack(side=tk.LEFT)
        
        refresh_button = ttk.Button(
            check_frame, 
            text="Refresh", 
            command=self._refresh_users
        )
        refresh_button.pack(side=tk.RIGHT)
        
        # User list
        list_frame = ttk.Frame(self.user_list_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the user list
        self.user_tree = ttk.Treeview(
            list_frame, 
            columns=("username", "full_name", "role", "status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.user_tree.heading("username", text="Username")
        self.user_tree.heading("full_name", text="Full Name")
        self.user_tree.heading("role", text="Role")
        self.user_tree.heading("status", text="Status")
        
        self.user_tree.column("username", width=100)
        self.user_tree.column("full_name", width=150)
        self.user_tree.column("role", width=100)
        self.user_tree.column("status", width=80, anchor=tk.CENTER)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.user_tree.bind("<<TreeviewSelect>>", self._on_user_selected)
        
        # Action buttons below the list
        action_frame = ttk.Frame(self.user_list_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        new_button = ttk.Button(
            action_frame, 
            text="New User", 
            command=self._create_new_user,
            style="Primary.TButton"
        )
        new_button.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_button = ttk.Button(
            action_frame, 
            text="Delete", 
            command=self._delete_selected_user,
            style="Danger.TButton"
        )
        delete_button.pack(side=tk.LEFT)
    
    def _create_user_detail_panel(self):
        """Create and populate the user detail panel."""
        # Header
        self.detail_header = ttk.Label(
            self.user_detail_frame, 
            text="User Details", 
            style="Header.TLabel"
        )
        self.detail_header.pack(fill=tk.X, pady=(0, 10))
        
        # Form frame
        form_frame = ttk.Frame(self.user_detail_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Basic information section
        ttk.Label(form_frame, text="Basic Information", font=("", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Username field
        username_frame = ttk.Frame(form_frame)
        username_frame.pack(fill=tk.X, pady=5)
        
        username_label = ttk.Label(username_frame, text="Username:", width=15)
        username_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        username_entry = ttk.Entry(username_frame, textvariable=self.username_var)
        username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Full name field
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        name_label = ttk.Label(name_frame, text="Full Name:", width=15)
        name_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        name_entry = ttk.Entry(name_frame, textvariable=self.full_name_var)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Email field
        email_frame = ttk.Frame(form_frame)
        email_frame.pack(fill=tk.X, pady=5)
        
        email_label = ttk.Label(email_frame, text="Email:", width=15)
        email_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        email_entry = ttk.Entry(email_frame, textvariable=self.email_var)
        email_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Role field
        role_frame = ttk.Frame(form_frame)
        role_frame.pack(fill=tk.X, pady=5)
        
        role_label = ttk.Label(role_frame, text="Role:", width=15)
        role_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        role_combobox = ttk.Combobox(
            role_frame, 
            textvariable=self.role_var,
            values=["admin", "manager", "cashier"],
            state="readonly"
        )
        role_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status field
        status_frame = ttk.Frame(form_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        status_label = ttk.Label(status_frame, text="Active:", width=15)
        status_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        status_check = ttk.Checkbutton(status_frame, variable=self.is_active_var)
        status_check.pack(side=tk.LEFT)
        
        # Password section
        ttk.Label(form_frame, text="Password", font=("", 11, "bold")).pack(anchor=tk.W, pady=(10, 5))
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Change password checkbox (only for editing)
        self.change_password_frame = ttk.Frame(form_frame)
        self.change_password_frame.pack(fill=tk.X, pady=5)
        
        change_password_check = ttk.Checkbutton(
            self.change_password_frame, 
            text="Change password", 
            variable=self.change_password_var,
            command=self._toggle_password_fields
        )
        change_password_check.pack(anchor=tk.W)
        
        # Password fields
        self.password_fields_frame = ttk.Frame(form_frame)
        self.password_fields_frame.pack(fill=tk.X, pady=5)
        
        # Password field
        password_frame = ttk.Frame(self.password_fields_frame)
        password_frame.pack(fill=tk.X, pady=5)
        
        password_label = ttk.Label(password_frame, text="Password:", width=15)
        password_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        password_entry = ttk.Entry(password_frame, textvariable=self.password_var, show="*")
        password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Confirm password field
        confirm_frame = ttk.Frame(self.password_fields_frame)
        confirm_frame.pack(fill=tk.X, pady=5)
        
        confirm_label = ttk.Label(confirm_frame, text="Confirm:", width=15)
        confirm_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        confirm_entry = ttk.Entry(confirm_frame, textvariable=self.confirm_password_var, show="*")
        confirm_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Password requirements
        req_label = ttk.Label(
            self.password_fields_frame, 
            text="Password must be at least 8 characters long",
            font=("", 9),
            foreground="gray"
        )
        req_label.pack(anchor=tk.W, padx=(15, 0))
        
        # Button frame at the bottom
        button_frame = ttk.Frame(self.user_detail_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        save_button = ttk.Button(
            button_frame, 
            text="Save Changes", 
            command=self._save_user,
            style="Primary.TButton"
        )
        save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self._cancel_edit
        )
        cancel_button.pack(side=tk.LEFT)
        
        # Initially hide password fields for editing
        self._toggle_password_fields()
    
    def _toggle_password_fields(self):
        """Show or hide password fields based on change_password checkbox."""
        if self.selected_user:
            # Editing existing user
            if self.change_password_var.get():
                self.password_fields_frame.pack(fill=tk.X, pady=5)
            else:
                self.password_fields_frame.pack_forget()
                # Clear password fields
                self.password_var.set("")
                self.confirm_password_var.set("")
        else:
            # New user, always show password fields
            self.password_fields_frame.pack(fill=tk.X, pady=5)
            # Hide change password checkbox
            self.change_password_frame.pack_forget()
    
    def _refresh_users(self):
        """Refresh the list of users."""
        # Clear existing items
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        try:
            # Get all users
            include_inactive = self.show_inactive_var.get()
            users = self.user_controller.get_all_users(include_inactive=include_inactive)
            
            # Add to treeview
            for user in users:
                # Status text
                status = "Active" if user.get("is_active", True) else "Inactive"
                
                # Role text
                role = user.get("role", "").title()
                
                self.user_tree.insert(
                    "", 
                    "end", 
                    values=(user["username"], user.get("full_name", ""), role, status),
                    iid=user["user_id"]
                )
                
        except Exception as e:
            self.show_error(f"Error loading users: {str(e)}")
    
    def _on_user_selected(self, event=None):
        """Handle user selection in the treeview."""
        selected_items = self.user_tree.selection()
        if not selected_items:
            return
        
        # Get the first selected item
        user_id = selected_items[0]
        
        try:
            # Get user details
            user = self.user_controller.get_user_by_id(user_id)
            if not user:
                return
            
            # Check if trying to edit self
            is_self = user["user_id"] == self.current_user["user_id"]
            
            # Store selected user
            self.selected_user = user
            
            # Update header
            self.detail_header.config(text=f"Edit User: {user['username']}")
            
            # Update form fields
            self.username_var.set(user["username"])
            self.full_name_var.set(user.get("full_name", ""))
            self.email_var.set(user.get("email", ""))
            self.role_var.set(user.get("role", "cashier"))
            self.is_active_var.set(user.get("is_active", True))
            
            # Reset password fields
            self.password_var.set("")
            self.confirm_password_var.set("")
            self.change_password_var.set(False)
            
            # Show change password checkbox
            self.change_password_frame.pack(fill=tk.X, pady=5)
            
            # Toggle password fields
            self._toggle_password_fields()
            
            # If editing self, disable role and status changes
            if is_self:
                role_combobox = self.user_detail_frame.winfo_children()[1].winfo_children()[9].winfo_children()[1]
                status_check = self.user_detail_frame.winfo_children()[1].winfo_children()[11].winfo_children()[1]
                
                role_combobox.config(state="disabled")
                status_check.config(state="disabled")
            else:
                role_combobox = self.user_detail_frame.winfo_children()[1].winfo_children()[9].winfo_children()[1]
                status_check = self.user_detail_frame.winfo_children()[1].winfo_children()[11].winfo_children()[1]
                
                role_combobox.config(state="readonly")
                status_check.config(state="normal")
            
        except Exception as e:
            self.show_error(f"Error loading user details: {str(e)}")
    
    def _create_new_user(self):
        """Create a new user."""
        # Clear current selection
        self.user_tree.selection_set([])
        
        # Clear form fields
        self.selected_user = None
        self.username_var.set("")
        self.full_name_var.set("")
        self.email_var.set("")
        self.role_var.set("cashier")
        self.is_active_var.set(True)
        self.password_var.set("")
        self.confirm_password_var.set("")
        
        # Update header
        self.detail_header.config(text="New User")
        
        # Hide change password checkbox, always show password fields for new users
        self.change_password_frame.pack_forget()
        self.password_fields_frame.pack(fill=tk.X, pady=5)
        
        # Enable all fields
        role_combobox = self.user_detail_frame.winfo_children()[1].winfo_children()[9].winfo_children()[1]
        status_check = self.user_detail_frame.winfo_children()[1].winfo_children()[11].winfo_children()[1]
        
        role_combobox.config(state="readonly")
        status_check.config(state="normal")
    
    def _save_user(self):
        """Save the current user."""
        try:
            # Get form data
            username = self.username_var.get().strip()
            full_name = self.full_name_var.get().strip()
            email = self.email_var.get().strip()
            role = self.role_var.get()
            is_active = self.is_active_var.get()
            
            # Validate
            if not username:
                self.show_warning("Username is required")
                return
            
            # If editing self, don't allow role or status changes
            if self.selected_user and self.selected_user["user_id"] == self.current_user["user_id"]:
                role = self.selected_user["role"]
                is_active = True
            
            # Prepare user data
            user_data = {
                "username": username,
                "full_name": full_name,
                "email": email,
                "role": role,
                "is_active": is_active
            }
            
            # Handle password
            need_password = False
            if not self.selected_user:
                # New user needs password
                need_password = True
            elif self.change_password_var.get():
                # Existing user with change password checked
                need_password = True
            
            if need_password:
                password = self.password_var.get()
                confirm_password = self.confirm_password_var.get()
                
                # Validate password
                if not password:
                    self.show_warning("Password is required")
                    return
                
                if password != confirm_password:
                    self.show_warning("Passwords do not match")
                    return
                
                # Check password length
                if len(password) < 8:
                    self.show_warning("Password must be at least 8 characters long")
                    return
                
                # Add password to user data
                user_data["password"] = password
            
            if self.selected_user:
                # Update existing user
                result = self.user_controller.update_user(
                    self.selected_user["user_id"],
                    user_data
                )
                success_message = "User updated successfully"
            else:
                # Create new user
                result = self.user_controller.create_user(user_data)
                success_message = "User created successfully"
            
            # Refresh list and show success message
            self._refresh_users()
            self.show_success(success_message)
            
            # Select the updated/created user if available
            if result and "user_id" in result:
                self.user_tree.selection_set([result["user_id"]])
                self._on_user_selected()
            
        except Exception as e:
            self.show_error(f"Error saving user: {str(e)}")
    
    def _cancel_edit(self):
        """Cancel the current edit operation."""
        # Revert to selected user or clear if none
        selected_items = self.user_tree.selection()
        if selected_items:
            self._on_user_selected()
        else:
            self._create_new_user()
    
    def _delete_selected_user(self):
        """Delete the selected user."""
        selected_items = self.user_tree.selection()
        if not selected_items:
            self.show_warning("Please select a user to delete")
            return
        
        user_id = selected_items[0]
        
        # Prevent deleting self
        if user_id == self.current_user["user_id"]:
            self.show_warning("You cannot delete your own account")
            return
        
        # Get the name for confirmation
        user_values = self.user_tree.item(user_id, "values")
        username = user_values[0]
        
        # Confirm deletion
        confirm = self.show_confirmation(
            f"Are you sure you want to delete user '{username}'? This action cannot be undone."
        )
        
        if not confirm:
            return
        
        try:
            # Try to delete
            result = self.user_controller.delete_user(user_id)
            
            # Refresh and show message
            self._refresh_users()
            self._create_new_user()
            
            self.show_success("User deleted successfully")
            
        except Exception as e:
            self.show_error(f"Error deleting user: {str(e)}")