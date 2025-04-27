"""
User view for POS application.
Handles user management UI.
"""

import tkinter as tk
from tkinter import ttk, simpledialog
import re
from datetime import datetime

from views.base_view import BaseView
from views.components.data_table import DataTable
from views.components.form_widgets import LabelInput, FormFrame


class UserView(BaseView):
    """User management view."""
    
    def __init__(self, parent, user_controller, auth_controller, current_user):
        """Initialize user view.
        
        Args:
            parent: Parent widget
            user_controller: User controller instance
            auth_controller: Authentication controller instance
            current_user: Current logged-in user
        """
        super().__init__(parent)
        self.parent = parent
        self.user_controller = user_controller
        self.auth_controller = auth_controller
        self.current_user = current_user
        
        # Variables for form fields
        self.user_vars = {
            'username': tk.StringVar(),
            'password': tk.StringVar(),
            'confirm_password': tk.StringVar(),
            'full_name': tk.StringVar(),
            'role': tk.StringVar(),
            'email': tk.StringVar(),
            'phone': tk.StringVar(),
            'active': tk.BooleanVar(value=True)
        }
        
        # For editing mode
        self.current_user_id = None
        self.editing_mode = False
        
        self._create_widgets()
        self._load_users()
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with two panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Users list panel
        self.users_frame = ttk.Frame(self.main_container, padding=5)
        self.main_container.add(self.users_frame, weight=2)
        
        # User form panel
        self.user_form_frame = ttk.Frame(self.main_container, padding=10)
        self.main_container.add(self.user_form_frame, weight=1)
        
        # Create users list
        self._create_users_list()
        
        # Create user form
        self._create_user_form()
    
    def _create_users_list(self):
        """Create the users list with DataTable."""
        # Frame for the title and actions
        header_frame = ttk.Frame(self.users_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Title
        title_label = ttk.Label(
            header_frame, 
            text="User Management",
            style="Header.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        # New user button
        new_button = ttk.Button(
            header_frame,
            text="New User",
            command=self._new_user,
            style="Primary.TButton"
        )
        new_button.pack(side=tk.RIGHT)
        
        # Refresh button
        refresh_button = ttk.Button(
            header_frame,
            text="Refresh",
            command=self._load_users,
            style="Secondary.TButton"
        )
        refresh_button.pack(side=tk.RIGHT, padx=5)
        
        # User data table
        columns = [
            {"name": "username", "width": 100, "label": "Username"},
            {"name": "full_name", "width": 150, "label": "Full Name"},
            {"name": "role", "width": 100, "label": "Role"},
            {"name": "email", "width": 150, "label": "Email"},
            {"name": "active", "width": 70, "label": "Active"},
            {"name": "last_login", "width": 150, "label": "Last Login"}
        ]
        
        self.users_table = DataTable(
            self.users_frame,
            columns=columns,
            on_select=self._on_user_select,
            on_double_click=self._on_user_double_click,
            sortable=True
        )
        self.users_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _create_user_form(self):
        """Create user form for add/edit."""
        # Frame for the title
        title_frame = ttk.Frame(self.user_form_frame)
        title_frame.pack(fill=tk.X, pady=5)
        
        self.form_title_var = tk.StringVar(value="New User")
        title_label = ttk.Label(
            title_frame, 
            textvariable=self.form_title_var,
            style="Subheader.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        # Create scrollable form
        form_container, form_frame = self.create_scrolled_frame(self.user_form_frame)
        form_container.pack(fill=tk.BOTH, expand=True)
        
        # Create form fields
        self.user_form = FormFrame(form_frame)
        self.user_form.pack(fill=tk.X, padx=5, pady=5)
        
        # Username field
        LabelInput(
            self.user_form, "Username:", 
            input_class=ttk.Entry,
            input_var=self.user_vars['username'],
            input_args={"width": 30}
        ).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Password fields
        LabelInput(
            self.user_form, "Password:", 
            input_class=ttk.Entry,
            input_var=self.user_vars['password'],
            input_args={"width": 30, "show": "•"}
        ).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        LabelInput(
            self.user_form, "Confirm Password:", 
            input_class=ttk.Entry,
            input_var=self.user_vars['confirm_password'],
            input_args={"width": 30, "show": "•"}
        ).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Full name field
        LabelInput(
            self.user_form, "Full Name:", 
            input_class=ttk.Entry,
            input_var=self.user_vars['full_name'],
            input_args={"width": 30}
        ).grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Role field (combobox)
        roles = self.user_controller.set_valid_roles()
        LabelInput(
            self.user_form, "Role:", 
            input_class=ttk.Combobox,
            input_var=self.user_vars['role'],
            input_args={"values": roles, "state": "readonly", "width": 28}
        ).grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Email field
        LabelInput(
            self.user_form, "Email:", 
            input_class=ttk.Entry,
            input_var=self.user_vars['email'],
            input_args={"width": 30}
        ).grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Phone field
        LabelInput(
            self.user_form, "Phone:", 
            input_class=ttk.Entry,
            input_var=self.user_vars['phone'],
            input_args={"width": 30}
        ).grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Active checkbox
        active_frame = ttk.Frame(self.user_form)
        active_frame.grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
        
        active_label = ttk.Label(active_frame, text="Active:")
        active_label.pack(side=tk.LEFT)
        
        active_check = ttk.Checkbutton(
            active_frame,
            variable=self.user_vars['active'],
            onvalue=True,
            offvalue=False
        )
        active_check.pack(side=tk.LEFT, padx=5)
        
        # Buttons frame
        button_frame = ttk.Frame(self.user_form_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.save_button = ttk.Button(
            button_frame,
            text="Save",
            command=self._save_user,
            style="Primary.TButton"
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel_edit,
            style="Secondary.TButton"
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Only show the delete button for existing users
        self.delete_button = ttk.Button(
            button_frame,
            text="Delete",
            command=self._delete_user,
            style="Danger.TButton"
        )
        # Don't pack initially - will be shown when editing
        
        # Add button for changing password when in edit mode
        self.change_password_button = ttk.Button(
            button_frame,
            text="Change Password",
            command=self._change_password,
            style="Secondary.TButton"
        )
        # Don't pack initially - will be shown when editing
    
    def _load_users(self):
        """Load users into the data table."""
        try:
            users = self.user_controller.get_all_users(active_only=False)
            
            # Format data for display
            formatted_users = []
            for user in users:
                # Format last_login
                last_login = "Never"
                if user.get("last_login"):
                    try:
                        last_login_dt = datetime.fromisoformat(user["last_login"].replace("Z", "+00:00"))
                        last_login = last_login_dt.strftime("%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        pass
                
                formatted_user = {
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "role": user["role"],
                    "email": user.get("email", ""),
                    "active": "Yes" if user.get("active", True) else "No",
                    "last_login": last_login
                }
                formatted_users.append(formatted_user)
            
            # Update table data
            self.users_table.set_data(formatted_users)
            
        except Exception as e:
            self.show_error(f"Error loading users: {str(e)}")
    
    def _new_user(self):
        """Prepare form for a new user."""
        # Clear form fields
        for var in self.user_vars.values():
            if isinstance(var, tk.BooleanVar):
                var.set(True)
            else:
                var.set("")
        
        # Set default role if empty
        if not self.user_vars["role"].get():
            self.user_vars["role"].set("SELLER")
        
        # Update form state
        self.form_title_var.set("New User")
        self.current_user_id = None
        self.editing_mode = False
        
        # Show appropriate buttons
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.delete_button.pack_forget()
        self.change_password_button.pack_forget()
    
    def _on_user_select(self, event=None):
        """Handle user selection in the table."""
        selected_item = self.users_table.get_selected_item()
        if selected_item:
            self._load_user_for_edit(selected_item["user_id"])
    
    def _on_user_double_click(self, event=None):
        """Handle double-click on user in the table."""
        selected_item = self.users_table.get_selected_item()
        if selected_item:
            self._load_user_for_edit(selected_item["user_id"])
    
    def _load_user_for_edit(self, user_id):
        """Load user data into the form for editing.
        
        Args:
            user_id (str): ID of the user to edit
        """
        try:
            # Get user data
            user = self.user_controller.get_user_by_id(user_id)
            if not user:
                self.show_error(f"User not found with ID: {user_id}")
                return
            
            # Update form fields
            self.user_vars["username"].set(user["username"])
            self.user_vars["full_name"].set(user["full_name"])
            self.user_vars["role"].set(user["role"])
            self.user_vars["email"].set(user.get("email", ""))
            self.user_vars["phone"].set(user.get("phone", ""))
            self.user_vars["active"].set(user.get("active", True))
            
            # Clear password fields
            self.user_vars["password"].set("")
            self.user_vars["confirm_password"].set("")
            
            # Update form state
            self.form_title_var.set(f"Edit User: {user['username']}")
            self.current_user_id = user_id
            self.editing_mode = True
            
            # Show appropriate buttons
            self.save_button.pack(side=tk.LEFT, padx=5)
            
            # Only show delete button for non-self users and if the current user has permission
            if (user_id != self.current_user["user_id"] and 
                self.auth_controller.is_admin()):
                self.delete_button.pack(side=tk.LEFT, padx=5)
            else:
                self.delete_button.pack_forget()
            
            # Show change password button for current user or if admin
            if (user_id == self.current_user["user_id"] or 
                self.auth_controller.is_admin()):
                self.change_password_button.pack(side=tk.RIGHT, padx=5)
            else:
                self.change_password_button.pack_forget()
            
        except Exception as e:
            self.show_error(f"Error loading user for edit: {str(e)}")
    
    def _save_user(self):
        """Save the current user form data."""
        try:
            # Get form data
            username = self.user_vars["username"].get().strip()
            password = self.user_vars["password"].get()
            confirm_password = self.user_vars["confirm_password"].get()
            full_name = self.user_vars["full_name"].get().strip()
            role = self.user_vars["role"].get()
            email = self.user_vars["email"].get().strip()
            phone = self.user_vars["phone"].get().strip()
            active = self.user_vars["active"].get()
            
            # Validate data
            if not username:
                self.show_error("Username is required")
                return
            
            if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
                self.show_error("Username must be 3-20 characters and contain only letters, numbers, and underscores")
                return
            
            if not full_name or len(full_name) < 2:
                self.show_error("Full name is required")
                return
            
            if not role:
                self.show_error("Role is required")
                return
            
            if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                self.show_error("Invalid email format")
                return
            
            # For new users, validate password
            if not self.editing_mode:
                if not password:
                    self.show_error("Password is required for new users")
                    return
                
                if len(password) < 8:
                    self.show_error("Password must be at least 8 characters long")
                    return
                
                if password != confirm_password:
                    self.show_error("Passwords do not match")
                    return
            
            # Create or update user
            if self.editing_mode:
                # Prepare update data
                update_data = {
                    "username": username,
                    "full_name": full_name,
                    "role": role,
                    "email": email or None,
                    "phone": phone or None,
                    "active": active
                }
                
                # Add password if provided
                if password:
                    if len(password) < 8:
                        self.show_error("Password must be at least 8 characters long")
                        return
                    
                    if password != confirm_password:
                        self.show_error("Passwords do not match")
                        return
                    
                    update_data["password"] = password
                
                # Update user
                user = self.user_controller.update_user(self.current_user_id, update_data)
                self.show_success(f"User '{username}' updated successfully")
            else:
                # Create new user
                user = self.user_controller.create_user(
                    username, password, full_name, role, email, phone
                )
                self.show_success(f"User '{username}' created successfully")
            
            # Reload users
            self._load_users()
            
            # Clear form
            self._new_user()
            
        except Exception as e:
            self.show_error(f"Error saving user: {str(e)}")
    
    def _cancel_edit(self):
        """Cancel editing and clear the form."""
        self._new_user()
    
    def _delete_user(self):
        """Delete the current user."""
        if not self.current_user_id:
            return
        
        # Get user data
        user = self.user_controller.get_user_by_id(self.current_user_id)
        if not user:
            self.show_error("User not found")
            return
        
        # Confirm deletion
        if not self.show_confirmation(f"Are you sure you want to deactivate user '{user['username']}'?"):
            return
        
        try:
            # Deactivate user instead of deleting
            self.user_controller.deactivate_user(self.current_user_id)
            self.show_success(f"User '{user['username']}' deactivated successfully")
            
            # Reload users and clear form
            self._load_users()
            self._new_user()
            
        except Exception as e:
            self.show_error(f"Error deactivating user: {str(e)}")
    
    def _change_password(self):
        """Change password for the current user."""
        if not self.current_user_id:
            return
        
        try:
            # For admin changing other users' passwords
            if (self.current_user_id != self.current_user["user_id"] and 
                self.auth_controller.is_admin()):
                
                # Get new password
                new_password = simpledialog.askstring(
                    "Change Password",
                    "Enter new password:",
                    show="•",
                    parent=self
                )
                
                if not new_password:
                    return
                
                if len(new_password) < 8:
                    self.show_error("Password must be at least 8 characters long")
                    return
                
                # Confirm new password
                confirm_password = simpledialog.askstring(
                    "Change Password",
                    "Confirm new password:",
                    show="•",
                    parent=self
                )
                
                if new_password != confirm_password:
                    self.show_error("Passwords do not match")
                    return
                
                # Update user with new password
                self.user_controller.update_user(self.current_user_id, {"password": new_password})
                self.show_success("Password changed successfully")
                
            else:  # User changing own password
                # Get current password
                current_password = simpledialog.askstring(
                    "Change Password",
                    "Enter current password:",
                    show="•",
                    parent=self
                )
                
                if not current_password:
                    return
                
                # Get new password
                new_password = simpledialog.askstring(
                    "Change Password",
                    "Enter new password:",
                    show="•",
                    parent=self
                )
                
                if not new_password:
                    return
                
                if len(new_password) < 8:
                    self.show_error("Password must be at least 8 characters long")
                    return
                
                # Confirm new password
                confirm_password = simpledialog.askstring(
                    "Change Password",
                    "Confirm new password:",
                    show="•",
                    parent=self
                )
                
                if new_password != confirm_password:
                    self.show_error("Passwords do not match")
                    return
                
                # Change password
                self.auth_controller.change_password(
                    self.current_user_id, current_password, new_password
                )
                self.show_success("Password changed successfully")
                
        except Exception as e:
            self.show_error(f"Error changing password: {str(e)}")
