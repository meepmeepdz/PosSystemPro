"""
Product view for POS application.
Handles product management.
"""

import tkinter as tk
from tkinter import ttk
import decimal

from views.base_view import BaseView
from views.components.message_box import MessageBox
from views.components.form_widgets import LabelInput, FormFrame


class ProductView(BaseView):
    """View for product management."""
    
    def __init__(self, parent, product_controller, category_controller, stock_controller):
        """Initialize product view.
        
        Args:
            parent: Parent widget
            product_controller: Controller for product operations
            category_controller: Controller for category operations
            stock_controller: Controller for stock operations
        """
        super().__init__(parent)
        self.parent = parent
        self.product_controller = product_controller
        self.category_controller = category_controller
        self.stock_controller = stock_controller
        
        # Current product
        self.current_product = None
        
        # Variables
        self.product_search_var = tk.StringVar()
        self.category_filter_var = tk.StringVar(value="All Categories")
        self.show_inactive_var = tk.BooleanVar(value=False)
        
        # Form variables
        self.name_var = tk.StringVar()
        self.sku_var = tk.StringVar()
        self.barcode_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.cost_price_var = tk.StringVar(value="0.00")
        self.selling_price_var = tk.StringVar(value="0.00")
        self.min_stock_var = tk.StringVar(value="0")
        self.is_active_var = tk.BooleanVar(value=True)
        
        # Cache for categories
        self.categories = []
        
        # Create UI components
        self._create_widgets()
        
        # Initial data population
        self._load_categories()
        self._refresh_product_list()
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with two panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel 1: Product list
        self.product_list_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.product_list_frame, weight=1)
        
        # Panel 2: Product details/edit
        self.product_detail_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.product_detail_frame, weight=1)
        
        # Set up product list panel
        self._create_product_list_panel()
        
        # Set up product details panel
        self._create_product_detail_panel()
    
    def _create_product_list_panel(self):
        """Create and populate the product list panel."""
        # Header
        header_label = ttk.Label(
            self.product_list_frame, 
            text="Products", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Search and filter toolbar
        toolbar_frame = ttk.Frame(self.product_list_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        search_label = ttk.Label(toolbar_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.product_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        search_button = ttk.Button(
            toolbar_frame, 
            text="Search", 
            command=self._refresh_product_list
        )
        search_button.pack(side=tk.LEFT, padx=5)
        
        # Category filter
        filter_frame = ttk.Frame(self.product_list_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        category_label = ttk.Label(filter_frame, text="Category:")
        category_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.category_combobox = ttk.Combobox(
            filter_frame, 
            textvariable=self.category_filter_var,
            state="readonly"
        )
        self.category_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Show inactive checkbox
        show_inactive_check = ttk.Checkbutton(
            filter_frame, 
            text="Show inactive", 
            variable=self.show_inactive_var,
            command=self._refresh_product_list
        )
        show_inactive_check.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Refresh button
        refresh_button = ttk.Button(
            filter_frame, 
            text="Refresh", 
            command=self._refresh_product_list
        )
        refresh_button.pack(side=tk.RIGHT)
        
        # Product list
        list_frame = ttk.Frame(self.product_list_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the product list
        self.product_tree = ttk.Treeview(
            list_frame, 
            columns=("name", "sku", "price", "stock", "status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.product_tree.heading("name", text="Product Name")
        self.product_tree.heading("sku", text="SKU")
        self.product_tree.heading("price", text="Price")
        self.product_tree.heading("stock", text="In Stock")
        self.product_tree.heading("status", text="Status")
        
        self.product_tree.column("name", width=200)
        self.product_tree.column("sku", width=100)
        self.product_tree.column("price", width=80, anchor=tk.E)
        self.product_tree.column("stock", width=80, anchor=tk.E)
        self.product_tree.column("status", width=80, anchor=tk.CENTER)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.product_tree.bind("<<TreeviewSelect>>", self._on_product_selected)
        
        # Action buttons below the list
        action_frame = ttk.Frame(self.product_list_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        new_button = ttk.Button(
            action_frame, 
            text="New Product", 
            command=self._create_new_product,
            style="Primary.TButton"
        )
        new_button.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_button = ttk.Button(
            action_frame, 
            text="Delete", 
            command=self._delete_selected_product,
            style="Danger.TButton"
        )
        delete_button.pack(side=tk.LEFT)
    
    def _create_product_detail_panel(self):
        """Create and populate the product detail panel."""
        # Header
        self.detail_header = ttk.Label(
            self.product_detail_frame, 
            text="Product Details", 
            style="Header.TLabel"
        )
        self.detail_header.pack(fill=tk.X, pady=(0, 10))
        
        # Create a scrollable frame for the form
        container, scrollable_frame = self.create_scrolled_frame(self.product_detail_frame)
        container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Form frame
        form_frame = FormFrame(scrollable_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Basic information section
        form_frame.add_section_header("Basic Information")
        
        # Name field
        form_frame.add_field("Name:", self.name_var, input_args={"width": 40})
        
        # SKU field
        form_frame.add_field("SKU:", self.sku_var, input_args={"width": 20})
        
        # Barcode field
        form_frame.add_field("Barcode:", self.barcode_var, input_args={"width": 20})
        
        # Description field
        desc_label = ttk.Label(form_frame, text="Description:")
        desc_label.pack(anchor=tk.W, pady=(5, 0))
        
        desc_frame = ttk.Frame(form_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.description_text = tk.Text(desc_frame, height=4, width=40)
        self.description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        desc_scrollbar = ttk.Scrollbar(desc_frame, orient=tk.VERTICAL, command=self.description_text.yview)
        self.description_text.configure(yscrollcommand=desc_scrollbar.set)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Category
        category_frame = ttk.Frame(form_frame)
        category_frame.pack(fill=tk.X, pady=(0, 10))
        
        category_label = ttk.Label(category_frame, text="Category:")
        category_label.pack(side=tk.LEFT, padx=(0, 5), width=100, anchor=tk.W)
        
        self.product_category_combobox = ttk.Combobox(
            category_frame, 
            textvariable=self.category_var,
            state="readonly"
        )
        self.product_category_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Pricing section
        form_frame.add_section_header("Pricing")
        
        # Cost price field
        form_frame.add_field("Cost Price:", self.cost_price_var, input_args={"width": 15})
        
        # Selling price field
        form_frame.add_field("Selling Price:", self.selling_price_var, input_args={"width": 15})
        
        # Stock section
        form_frame.add_section_header("Inventory")
        
        # Min stock level field
        form_frame.add_field("Min Stock Level:", self.min_stock_var, input_args={"width": 10})
        
        # Current stock level
        self.stock_label = ttk.Label(form_frame, text="Current Stock: 0")
        self.stock_label.pack(anchor=tk.W, pady=5)
        
        # Stock adjustment button
        adjust_stock_button = ttk.Button(
            form_frame, 
            text="Adjust Stock", 
            command=self._adjust_stock
        )
        adjust_stock_button.pack(anchor=tk.W, pady=(0, 10))
        
        # Status section
        form_frame.add_section_header("Status")
        
        # Is active field
        is_active_frame = ttk.Frame(form_frame)
        is_active_frame.pack(fill=tk.X, pady=5)
        
        is_active_label = ttk.Label(is_active_frame, text="Active:")
        is_active_label.pack(side=tk.LEFT, padx=(0, 5), width=100, anchor=tk.W)
        
        is_active_check = ttk.Checkbutton(is_active_frame, variable=self.is_active_var)
        is_active_check.pack(side=tk.LEFT)
        
        # Button frame
        button_frame = ttk.Frame(self.product_detail_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        save_button = ttk.Button(
            button_frame, 
            text="Save Changes", 
            command=self._save_product,
            style="Primary.TButton"
        )
        save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self._cancel_edit
        )
        cancel_button.pack(side=tk.LEFT)
    
    def _load_categories(self):
        """Load categories for dropdowns."""
        try:
            # Get all categories
            self.categories = self.category_controller.get_all_categories(include_inactive=False)
            
            # Prepare lists for dropdowns
            category_names = [c["name"] for c in self.categories]
            
            # Update filter combobox
            self.category_combobox["values"] = ["All Categories"] + category_names
            self.category_combobox.current(0)  # Set to "All Categories"
            
            # Update product form combobox
            self.product_category_combobox["values"] = category_names
            if category_names:
                self.product_category_combobox.current(0)
                
        except Exception as e:
            self.show_error(f"Error loading categories: {str(e)}")
    
    def _refresh_product_list(self):
        """Refresh the list of products."""
        # Clear existing items
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        try:
            # Get search and filter values
            search_term = self.product_search_var.get().strip()
            category = self.category_filter_var.get()
            include_inactive = self.show_inactive_var.get()
            
            # Get category ID if a specific category is selected
            category_id = None
            if category != "All Categories":
                for c in self.categories:
                    if c["name"] == category:
                        category_id = c["category_id"]
                        break
            
            # Get products based on search and filters
            products = self.product_controller.search_products(
                search_term=search_term if search_term else None,
                category_id=category_id,
                include_inactive=include_inactive
            )
            
            # Get stock levels
            stock_levels = {}
            try:
                for product in products:
                    stock = self.stock_controller.get_stock_level(product["product_id"])
                    stock_levels[product["product_id"]] = stock
            except Exception:
                # If not implemented, use zeros
                pass
            
            # Add to treeview
            for product in products:
                # Get stock level
                stock_level = stock_levels.get(product["product_id"], 0)
                
                # Format price
                price = f"${product['selling_price']:.2f}" if product["selling_price"] is not None else "-"
                
                # Status text
                status = "Active" if product.get("is_active", True) else "Inactive"
                
                self.product_tree.insert(
                    "", 
                    "end", 
                    values=(product["name"], product["sku"], price, stock_level, status),
                    iid=product["product_id"]
                )
                
        except Exception as e:
            self.show_error(f"Error loading products: {str(e)}")
    
    def _on_product_selected(self, event=None):
        """Handle product selection in the treeview."""
        selected_items = self.product_tree.selection()
        if not selected_items:
            return
        
        # Get the first selected item
        product_id = selected_items[0]
        
        try:
            # Get product details
            product = self.product_controller.get_product_by_id(product_id)
            if not product:
                return
            
            # Store current product
            self.current_product = product
            
            # Update header
            self.detail_header.config(text=f"Edit Product: {product['name']}")
            
            # Update form fields
            self.name_var.set(product["name"])
            self.sku_var.set(product["sku"] or "")
            self.barcode_var.set(product["barcode"] or "")
            
            # Update description in text widget
            self.description_text.delete(1.0, tk.END)
            if product.get("description"):
                self.description_text.insert(1.0, product["description"])
            
            # Update category dropdown
            if product.get("category_id"):
                for i, category in enumerate(self.categories):
                    if category["category_id"] == product["category_id"]:
                        if len(self.categories) > 0:
                            self.product_category_combobox.current(i)
                        break
            
            # Update prices
            self.cost_price_var.set(f"{product.get('cost_price', 0):.2f}")
            self.selling_price_var.set(f"{product.get('selling_price', 0):.2f}")
            
            # Update stock info
            self.min_stock_var.set(str(product.get("min_stock_level", 0)))
            
            try:
                stock_level = self.stock_controller.get_stock_level(product_id)
                self.stock_label.config(text=f"Current Stock: {stock_level}")
            except Exception:
                self.stock_label.config(text="Current Stock: Unknown")
            
            # Update status
            self.is_active_var.set(product.get("is_active", True))
            
        except Exception as e:
            self.show_error(f"Error loading product details: {str(e)}")
    
    def _create_new_product(self):
        """Create a new product."""
        # Clear current selection
        self.product_tree.selection_set([])
        
        # Clear form fields
        self.current_product = None
        self.name_var.set("")
        self.sku_var.set("")
        self.barcode_var.set("")
        self.description_text.delete(1.0, tk.END)
        
        # Set default category if available
        if len(self.categories) > 0:
            self.product_category_combobox.current(0)
        
        # Reset prices
        self.cost_price_var.set("0.00")
        self.selling_price_var.set("0.00")
        
        # Reset stock info
        self.min_stock_var.set("0")
        self.stock_label.config(text="Current Stock: 0")
        
        # Set active
        self.is_active_var.set(True)
        
        # Update header
        self.detail_header.config(text="New Product")
    
    def _save_product(self):
        """Save the current product."""
        try:
            # Get form data
            name = self.name_var.get().strip()
            sku = self.sku_var.get().strip() or None
            barcode = self.barcode_var.get().strip() or None
            description = self.description_text.get(1.0, tk.END).strip() or None
            
            # Get category
            category_id = None
            category_name = self.category_var.get()
            for category in self.categories:
                if category["name"] == category_name:
                    category_id = category["category_id"]
                    break
            
            # Get prices
            try:
                cost_price = decimal.Decimal(self.cost_price_var.get())
                selling_price = decimal.Decimal(self.selling_price_var.get())
            except (ValueError, decimal.InvalidOperation):
                self.show_warning("Please enter valid prices")
                return
            
            # Get min stock level
            try:
                min_stock = int(self.min_stock_var.get())
                if min_stock < 0:
                    self.show_warning("Minimum stock level cannot be negative")
                    return
            except ValueError:
                self.show_warning("Please enter a valid minimum stock level")
                return
            
            # Get active status
            is_active = self.is_active_var.get()
            
            # Validate
            if not name:
                self.show_warning("Product name is required")
                return
            
            product_data = {
                "name": name,
                "sku": sku,
                "barcode": barcode,
                "description": description,
                "category_id": category_id,
                "cost_price": float(cost_price),
                "selling_price": float(selling_price),
                "min_stock_level": min_stock,
                "is_active": is_active
            }
            
            if self.current_product:
                # Update existing product
                result = self.product_controller.update_product(
                    self.current_product["product_id"],
                    product_data
                )
                success_message = "Product updated successfully"
            else:
                # Create new product
                result = self.product_controller.create_product(product_data)
                success_message = "Product created successfully"
                
                # Set initial stock level to 0 if it's a new product
                if result and "product_id" in result:
                    try:
                        self.stock_controller.set_initial_stock(result["product_id"], 0)
                    except Exception:
                        # If not implemented, just ignore
                        pass
            
            # Refresh list and show success message
            self._refresh_product_list()
            self.show_success(success_message)
            
            # Select the updated/created product if available
            if result and "product_id" in result:
                self.product_tree.selection_set([result["product_id"]])
                self._on_product_selected()
            
        except Exception as e:
            self.show_error(f"Error saving product: {str(e)}")
    
    def _cancel_edit(self):
        """Cancel the current edit operation."""
        # Revert to selected product or clear if none
        selected_items = self.product_tree.selection()
        if selected_items:
            self._on_product_selected()
        else:
            self._create_new_product()
    
    def _delete_selected_product(self):
        """Delete the selected product."""
        selected_items = self.product_tree.selection()
        if not selected_items:
            self.show_warning("Please select a product to delete")
            return
        
        product_id = selected_items[0]
        
        # Get the name for confirmation
        product_values = self.product_tree.item(product_id, "values")
        product_name = product_values[0]
        
        # Confirm deletion
        confirm = self.show_confirmation(
            f"Are you sure you want to delete product '{product_name}'? This will remove all stock and sales data for this product."
        )
        
        if not confirm:
            return
        
        try:
            # Try to delete
            result = self.product_controller.delete_product(product_id)
            
            # Refresh and show message
            self._refresh_product_list()
            self._create_new_product()
            
            self.show_success("Product deleted successfully")
            
        except Exception as e:
            self.show_error(f"Error deleting product: {str(e)}")
    
    def _adjust_stock(self):
        """Adjust stock for the current product."""
        if not self.current_product:
            self.show_warning("Please select a product first")
            return
        
        # Create a dialog window
        dialog = tk.Toplevel(self)
        dialog.title(f"Adjust Stock: {self.current_product['name']}")
        dialog.transient(self.winfo_toplevel())  # Make dialog modal
        dialog.grab_set()
        
        # Center on screen
        self.center_window(dialog, 300, 200)
        
        # Dialog content
        content_frame = ttk.Frame(dialog, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current stock label
        try:
            current_stock = self.stock_controller.get_stock_level(self.current_product["product_id"])
        except Exception:
            current_stock = 0
            
        stock_label = ttk.Label(
            content_frame, 
            text=f"Current Stock: {current_stock}",
            font=("", 12)
        )
        stock_label.pack(pady=(0, 20))
        
        # Adjustment field
        adj_frame = ttk.Frame(content_frame)
        adj_frame.pack(fill=tk.X, pady=5)
        
        adj_label = ttk.Label(adj_frame, text="Adjustment:")
        adj_label.pack(side=tk.LEFT, padx=(0, 5))
        
        adj_var = tk.StringVar(value="0")
        adj_entry = ttk.Entry(adj_frame, textvariable=adj_var, width=10)
        adj_entry.pack(side=tk.LEFT, padx=5)
        adj_entry.focus_set()
        
        # Radio buttons for adjustment type
        type_var = tk.StringVar(value="add")
        
        add_radio = ttk.Radiobutton(
            content_frame, 
            text="Add to stock", 
            variable=type_var, 
            value="add"
        )
        add_radio.pack(anchor=tk.W, pady=2)
        
        set_radio = ttk.Radiobutton(
            content_frame, 
            text="Set to value", 
            variable=type_var, 
            value="set"
        )
        set_radio.pack(anchor=tk.W, pady=2)
        
        # Reason field
        reason_frame = ttk.Frame(content_frame)
        reason_frame.pack(fill=tk.X, pady=10)
        
        reason_label = ttk.Label(reason_frame, text="Reason:")
        reason_label.pack(side=tk.LEFT, padx=(0, 5))
        
        reason_var = tk.StringVar()
        reason_entry = ttk.Entry(reason_frame, textvariable=reason_var, width=20)
        reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Function to handle adjustment
        def apply_adjustment():
            try:
                # Validate input
                try:
                    amount = int(adj_var.get())
                except ValueError:
                    self.show_warning("Please enter a valid number")
                    return
                
                reason = reason_var.get().strip() or "Manual adjustment"
                adj_type = type_var.get()
                
                if adj_type == "add":
                    # Add to current stock
                    result = self.stock_controller.adjust_stock(
                        self.current_product["product_id"],
                        amount,
                        reason
                    )
                    
                    success_message = f"Added {amount} to stock"
                else:
                    # Set to value
                    if amount < 0:
                        self.show_warning("Stock level cannot be negative")
                        return
                    
                    # Calculate adjustment amount
                    adjustment = amount - current_stock
                    
                    result = self.stock_controller.adjust_stock(
                        self.current_product["product_id"],
                        adjustment,
                        reason
                    )
                    
                    success_message = f"Stock level set to {amount}"
                
                # Close dialog
                dialog.destroy()
                
                # Refresh product and show success message
                self._on_product_selected()
                self.show_success(success_message)
                
            except Exception as e:
                self.show_error(f"Error adjusting stock: {str(e)}")
        
        apply_button = ttk.Button(
            button_frame, 
            text="Apply", 
            command=apply_adjustment,
            style="Primary.TButton"
        )
        apply_button.pack(side=tk.RIGHT)