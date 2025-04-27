"""
Category view for POS application.
Handles category management.
"""

import tkinter as tk
from tkinter import ttk

from views.base_view import BaseView
from views.components.message_box import MessageBox


class CategoryView(BaseView):
    """View for category management."""
    
    def __init__(self, parent, category_controller):
        """Initialize category view.
        
        Args:
            parent: Parent widget
            category_controller: Controller for category operations
        """
        super().__init__(parent)
        self.parent = parent
        self.category_controller = category_controller
        
        # Current category
        self.current_category = None
        
        # Variables
        self.category_search_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.is_active_var = tk.BooleanVar(value=True)
        
        # Create UI components
        self._create_widgets()
        
        # Initial data population
        self._refresh_category_list()
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with two panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel 1: Category list
        self.category_list_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.category_list_frame, weight=1)
        
        # Panel 2: Category details/edit
        self.category_detail_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.category_detail_frame, weight=1)
        
        # Set up category list panel
        self._create_category_list_panel()
        
        # Set up category details panel
        self._create_category_detail_panel()
    
    def _create_category_list_panel(self):
        """Create and populate the category list panel."""
        # Header
        header_label = ttk.Label(
            self.category_list_frame, 
            text="Categories", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Search and refresh toolbar
        toolbar_frame = ttk.Frame(self.category_list_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        search_label = ttk.Label(toolbar_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.category_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        search_button = ttk.Button(
            toolbar_frame, 
            text="Search", 
            command=self._refresh_category_list
        )
        search_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = ttk.Button(
            toolbar_frame, 
            text="Refresh", 
            command=self._refresh_category_list
        )
        refresh_button.pack(side=tk.LEFT)
        
        # Category list
        list_frame = ttk.Frame(self.category_list_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the category list
        self.category_tree = ttk.Treeview(
            list_frame, 
            columns=("name", "product_count", "status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.category_tree.heading("name", text="Category Name")
        self.category_tree.heading("product_count", text="Products")
        self.category_tree.heading("status", text="Status")
        
        self.category_tree.column("name", width=200)
        self.category_tree.column("product_count", width=80, anchor=tk.CENTER)
        self.category_tree.column("status", width=80, anchor=tk.CENTER)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.category_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.category_tree.bind("<<TreeviewSelect>>", self._on_category_selected)
        
        # Action buttons below the list
        action_frame = ttk.Frame(self.category_list_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        new_button = ttk.Button(
            action_frame, 
            text="New Category", 
            command=self._create_new_category,
            style="Primary.TButton"
        )
        new_button.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_button = ttk.Button(
            action_frame, 
            text="Delete", 
            command=self._delete_selected_category,
            style="Danger.TButton"
        )
        delete_button.pack(side=tk.LEFT)
    
    def _create_category_detail_panel(self):
        """Create and populate the category detail panel."""
        # Header
        self.detail_header = ttk.Label(
            self.category_detail_frame, 
            text="Category Details", 
            style="Header.TLabel"
        )
        self.detail_header.pack(fill=tk.X, pady=(0, 10))
        
        # Form fields
        form_frame = ttk.Frame(self.category_detail_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Name field
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        name_label = ttk.Label(name_frame, text="Name:", width=15)
        name_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Description field
        desc_frame = ttk.Frame(form_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        
        desc_label = ttk.Label(desc_frame, text="Description:", width=15)
        desc_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        # Create a text widget for description with scrollbar
        desc_container = ttk.Frame(desc_frame)
        desc_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.description_text = tk.Text(desc_container, height=5, width=30, wrap=tk.WORD)
        self.description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        desc_scrollbar = ttk.Scrollbar(desc_container, orient=tk.VERTICAL, command=self.description_text.yview)
        self.description_text.configure(yscrollcommand=desc_scrollbar.set)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status field
        status_frame = ttk.Frame(form_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        status_label = ttk.Label(status_frame, text="Active:", width=15)
        status_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        status_check = ttk.Checkbutton(status_frame, variable=self.is_active_var)
        status_check.pack(side=tk.LEFT)
        
        # Button frame
        button_frame = ttk.Frame(self.category_detail_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        save_button = ttk.Button(
            button_frame, 
            text="Save Changes", 
            command=self._save_category,
            style="Primary.TButton"
        )
        save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self._cancel_edit
        )
        cancel_button.pack(side=tk.LEFT)
    
    def _refresh_category_list(self):
        """Refresh the list of categories."""
        # Clear existing items
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
        
        try:
            # Get categories based on search
            search_term = self.category_search_var.get().strip()
            categories = self.category_controller.search_categories(
                search_term=search_term if search_term else None,
                include_inactive=True
            )
            
            # Get product counts for each category
            product_counts = {}
            try:
                for category in categories:
                    # Get count from controller if available
                    count = self.category_controller.get_product_count(category["category_id"])
                    product_counts[category["category_id"]] = count
            except Exception:
                # If not implemented, just use 0
                pass
            
            # Add to treeview
            for category in categories:
                # Get product count
                product_count = product_counts.get(category["category_id"], 0)
                
                # Status text
                status = "Active" if category.get("is_active", True) else "Inactive"
                
                self.category_tree.insert(
                    "", 
                    "end", 
                    values=(category["name"], product_count, status),
                    iid=category["category_id"]
                )
                
        except Exception as e:
            self.show_error(f"Error loading categories: {str(e)}")
    
    def _on_category_selected(self, event=None):
        """Handle category selection in the treeview."""
        selected_items = self.category_tree.selection()
        if not selected_items:
            return
        
        # Get the first selected item
        category_id = selected_items[0]
        
        try:
            # Get category details
            category = self.category_controller.get_category_by_id(category_id)
            if not category:
                return
            
            # Store current category
            self.current_category = category
            
            # Update header
            self.detail_header.config(text=f"Edit Category: {category['name']}")
            
            # Update form fields
            self.name_var.set(category["name"])
            
            # Update description in text widget
            self.description_text.delete(1.0, tk.END)
            if category.get("description"):
                self.description_text.insert(1.0, category["description"])
            
            # Update status
            self.is_active_var.set(category.get("is_active", True))
            
        except Exception as e:
            self.show_error(f"Error loading category details: {str(e)}")
    
    def _create_new_category(self):
        """Create a new category."""
        # Clear current selection
        self.category_tree.selection_set([])
        
        # Clear form fields
        self.current_category = None
        self.name_var.set("")
        self.description_text.delete(1.0, tk.END)
        self.is_active_var.set(True)
        
        # Update header
        self.detail_header.config(text="New Category")
    
    def _save_category(self):
        """Save the current category."""
        try:
            # Get form data
            name = self.name_var.get().strip()
            description = self.description_text.get(1.0, tk.END).strip()
            is_active = self.is_active_var.get()
            
            # Validate
            if not name:
                self.show_warning("Category name is required")
                return
            
            category_data = {
                "name": name,
                "description": description,
                "is_active": is_active
            }
            
            if self.current_category:
                # Update existing category
                result = self.category_controller.update_category(
                    self.current_category["category_id"],
                    category_data
                )
                success_message = "Category updated successfully"
            else:
                # Create new category
                result = self.category_controller.create_category(category_data)
                success_message = "Category created successfully"
            
            # Refresh list and show success message
            self._refresh_category_list()
            self.show_success(success_message)
            
            # Select the updated/created category if available
            if result and "category_id" in result:
                self.category_tree.selection_set([result["category_id"]])
                self._on_category_selected()
            
        except Exception as e:
            self.show_error(f"Error saving category: {str(e)}")
    
    def _cancel_edit(self):
        """Cancel the current edit operation."""
        # Revert to selected category or clear if none
        selected_items = self.category_tree.selection()
        if selected_items:
            self._on_category_selected()
        else:
            self._create_new_category()
    
    def _delete_selected_category(self):
        """Delete the selected category."""
        selected_items = self.category_tree.selection()
        if not selected_items:
            self.show_warning("Please select a category to delete")
            return
        
        category_id = selected_items[0]
        
        # Get the name for confirmation
        category_values = self.category_tree.item(category_id, "values")
        category_name = category_values[0]
        
        # Confirm deletion
        confirm = self.show_confirmation(
            f"Are you sure you want to delete category '{category_name}'? This may affect products assigned to this category."
        )
        
        if not confirm:
            return
        
        try:
            # Try to delete
            result = self.category_controller.delete_category(category_id)
            
            # Refresh and show message
            self._refresh_category_list()
            self._create_new_category()
            
            self.show_success("Category deleted successfully")
            
        except Exception as e:
            self.show_error(f"Error deleting category: {str(e)}")