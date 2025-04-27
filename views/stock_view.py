"""
Stock view for POS application.
Handles inventory management.
"""

import tkinter as tk
from tkinter import ttk
import datetime
import csv
import os

from views.base_view import BaseView
from views.components.message_box import MessageBox
from utils.currency_formatter import format_currency


class StockView(BaseView):
    """View for inventory management."""
    
    def __init__(self, parent, stock_controller, product_controller):
        """Initialize stock view.
        
        Args:
            parent: Parent widget
            stock_controller: Controller for stock operations
            product_controller: Controller for product operations
        """
        super().__init__(parent)
        self.parent = parent
        self.stock_controller = stock_controller
        self.product_controller = product_controller
        
        # Current product
        self.current_product = None
        
        # Variables
        self.product_search_var = tk.StringVar()
        self.show_all_var = tk.BooleanVar(value=False)
        self.show_inactive_var = tk.BooleanVar(value=False)
        self.adjustment_amount_var = tk.StringVar(value="0")
        self.adjustment_reason_var = tk.StringVar()
        
        # Create UI components
        self._create_widgets()
        
        # Initial data load
        self._refresh_stock()
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with two panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel 1: Stock list
        self.stock_list_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.stock_list_frame, weight=2)
        
        # Panel 2: Stock details and adjustments
        self.stock_detail_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.stock_detail_frame, weight=1)
        
        # Set up stock list panel
        self._create_stock_list_panel()
        
        # Set up stock details panel
        self._create_stock_detail_panel()
    
    def _create_stock_list_panel(self):
        """Create and populate the stock list panel."""
        # Header
        header_label = ttk.Label(
            self.stock_list_frame, 
            text="Inventory", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Search and filters
        filters_frame = ttk.LabelFrame(self.stock_list_frame, text="Search & Filters", padding=10)
        filters_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Search field
        search_frame = ttk.Frame(filters_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(search_frame, textvariable=self.product_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        search_button = ttk.Button(
            search_frame, 
            text="Search", 
            command=self._refresh_stock
        )
        search_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Checkboxes for filters
        check_frame = ttk.Frame(filters_frame)
        check_frame.pack(fill=tk.X, pady=5)
        
        show_all_check = ttk.Checkbutton(
            check_frame, 
            text="Show all products (including non-stocked)", 
            variable=self.show_all_var,
            command=self._refresh_stock
        )
        show_all_check.pack(side=tk.LEFT, padx=(0, 10))
        
        show_inactive_check = ttk.Checkbutton(
            check_frame, 
            text="Show inactive products", 
            variable=self.show_inactive_var,
            command=self._refresh_stock
        )
        show_inactive_check.pack(side=tk.LEFT)
        
        # Buttons frame
        button_frame = ttk.Frame(filters_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        refresh_button = ttk.Button(
            button_frame, 
            text="Refresh", 
            command=self._refresh_stock
        )
        refresh_button.pack(side=tk.LEFT)
        
        export_button = ttk.Button(
            button_frame, 
            text="Export to CSV", 
            command=self._export_stock_to_csv
        )
        export_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Stock list
        list_frame = ttk.Frame(self.stock_list_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the stock list
        self.stock_tree = ttk.Treeview(
            list_frame, 
            columns=("sku", "name", "on_hand", "min_level", "status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.stock_tree.heading("sku", text="SKU")
        self.stock_tree.heading("name", text="Product Name")
        self.stock_tree.heading("on_hand", text="On Hand")
        self.stock_tree.heading("min_level", text="Min Level")
        self.stock_tree.heading("status", text="Status")
        
        self.stock_tree.column("sku", width=100)
        self.stock_tree.column("name", width=250)
        self.stock_tree.column("on_hand", width=80, anchor=tk.E)
        self.stock_tree.column("min_level", width=80, anchor=tk.E)
        self.stock_tree.column("status", width=100, anchor=tk.CENTER)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.stock_tree.yview)
        self.stock_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.stock_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.stock_tree.bind("<<TreeviewSelect>>", self._on_stock_selected)
        
        # Summary frame
        summary_frame = ttk.Frame(self.stock_list_frame)
        summary_frame.pack(fill=tk.X, pady=5)
        
        self.low_stock_label = ttk.Label(
            summary_frame, 
            text="Low Stock Items: 0", 
            foreground="red"
        )
        self.low_stock_label.pack(side=tk.LEFT)
        
        self.total_items_label = ttk.Label(
            summary_frame, 
            text="Total Items: 0"
        )
        self.total_items_label.pack(side=tk.RIGHT)
    
    def _create_stock_detail_panel(self):
        """Create and populate the stock detail panel."""
        # Header
        self.detail_header = ttk.Label(
            self.stock_detail_frame, 
            text="Stock Details", 
            style="Header.TLabel"
        )
        self.detail_header.pack(fill=tk.X, pady=(0, 10))
        
        # Product details frame
        details_frame = ttk.LabelFrame(self.stock_detail_frame, text="Product Information", padding=10)
        details_frame.pack(fill=tk.X, pady=5)
        
        # Create detail grid
        details_grid = ttk.Frame(details_frame)
        details_grid.pack(fill=tk.X, padx=5, pady=5)
        
        row = 0
        
        # Product ID/SKU
        ttk.Label(details_grid, text="Product ID:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.product_id_label = ttk.Label(details_grid, text="-")
        self.product_id_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # SKU
        ttk.Label(details_grid, text="SKU:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.sku_label = ttk.Label(details_grid, text="-")
        self.sku_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Name
        ttk.Label(details_grid, text="Name:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.name_label = ttk.Label(details_grid, text="-")
        self.name_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Category
        ttk.Label(details_grid, text="Category:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.category_label = ttk.Label(details_grid, text="-")
        self.category_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Stock level
        ttk.Label(details_grid, text="Current Stock:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.stock_level_label = ttk.Label(details_grid, text="-")
        self.stock_level_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Min stock level
        ttk.Label(details_grid, text="Min Stock Level:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.min_stock_label = ttk.Label(details_grid, text="-")
        self.min_stock_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Status
        ttk.Label(details_grid, text="Status:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.status_label = ttk.Label(details_grid, text="-")
        self.status_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Stock adjustment frame
        adjustment_frame = ttk.LabelFrame(self.stock_detail_frame, text="Stock Adjustment", padding=10)
        adjustment_frame.pack(fill=tk.X, pady=5)
        
        # Adjustment amount
        amount_frame = ttk.Frame(adjustment_frame)
        amount_frame.pack(fill=tk.X, pady=5)
        
        amount_label = ttk.Label(amount_frame, text="Amount:")
        amount_label.pack(side=tk.LEFT, padx=(0, 5))
        
        amount_entry = ttk.Entry(amount_frame, textvariable=self.adjustment_amount_var, width=10)
        amount_entry.pack(side=tk.LEFT)
        
        # Adjustment reason
        reason_frame = ttk.Frame(adjustment_frame)
        reason_frame.pack(fill=tk.X, pady=5)
        
        reason_label = ttk.Label(reason_frame, text="Reason:")
        reason_label.pack(side=tk.LEFT, padx=(0, 5))
        
        reason_entry = ttk.Entry(reason_frame, textvariable=self.adjustment_reason_var)
        reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Adjustment buttons
        buttons_frame = ttk.Frame(adjustment_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        add_button = ttk.Button(
            buttons_frame, 
            text="Add Stock", 
            command=self._add_stock,
            style="Success.TButton"
        )
        add_button.pack(side=tk.LEFT, padx=(0, 5))
        
        remove_button = ttk.Button(
            buttons_frame, 
            text="Remove Stock", 
            command=self._remove_stock,
            style="Danger.TButton"
        )
        remove_button.pack(side=tk.LEFT)
        
        # Stock movement history frame
        history_frame = ttk.LabelFrame(self.stock_detail_frame, text="Stock Movement History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        history_list_frame = ttk.Frame(history_frame)
        history_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the history
        self.history_tree = ttk.Treeview(
            history_list_frame, 
            columns=("date", "type", "amount", "stock_after", "reason"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("type", text="Type")
        self.history_tree.heading("amount", text="Amount")
        self.history_tree.heading("stock_after", text="Stock After")
        self.history_tree.heading("reason", text="Reason")
        
        self.history_tree.column("date", width=100)
        self.history_tree.column("type", width=80)
        self.history_tree.column("amount", width=60, anchor=tk.E)
        self.history_tree.column("stock_after", width=60, anchor=tk.E)
        self.history_tree.column("reason", width=150)
        
        # Add vertical scrollbar
        history_scrollbar = ttk.Scrollbar(history_list_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _refresh_stock(self):
        """Refresh the stock list based on filters."""
        # Clear existing items
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        try:
            # Get filter values
            search_term = self.product_search_var.get().strip()
            show_all = self.show_all_var.get()
            show_inactive = self.show_inactive_var.get()
            
            # Get stock levels for all products or filtered products
            products = self.product_controller.search_products(
                search_term=search_term if search_term else None,
                is_active=None if show_inactive else True
            )
            
            # Add to treeview
            low_stock_count = 0
            
            for product in products:
                # Get stock level
                try:
                    stock_level = self.stock_controller.get_stock_level(product["product_id"])
                except Exception:
                    stock_level = 0
                
                # If not showing all products, skip those with no stock (unless showing low stock)
                if not show_all and stock_level == 0 and not product.get("is_stocked", True):
                    continue
                
                # SKU
                sku = product.get("sku", "-")
                
                # Min stock level
                min_stock = product.get("min_stock_level", 0)
                
                # Determine stock status
                if stock_level <= 0:
                    status = "Out of Stock"
                    status_color = "red"
                    low_stock_count += 1
                elif stock_level < min_stock:
                    status = "Low Stock"
                    status_color = "orange"
                    low_stock_count += 1
                else:
                    status = "In Stock"
                    status_color = "green"
                
                # If product is inactive, override status
                if not product.get("is_active", True):
                    status = "Inactive"
                    status_color = "gray"
                
                item_id = self.stock_tree.insert(
                    "", 
                    "end", 
                    values=(sku, product["name"], stock_level, min_stock, status),
                    iid=product["product_id"]
                )
                
                # Set tag for color
                self.stock_tree.item(item_id, tags=(status_color,))
            
            # Configure tags for colors
            self.stock_tree.tag_configure("red", foreground="red")
            self.stock_tree.tag_configure("orange", foreground="orange")
            self.stock_tree.tag_configure("green", foreground="green")
            self.stock_tree.tag_configure("gray", foreground="gray")
            
            # Update summary
            total_items = len(self.stock_tree.get_children())
            self.total_items_label.config(text=f"Total Items: {total_items}")
            self.low_stock_label.config(text=f"Low Stock Items: {low_stock_count}")
            
            # Clear details panel
            self._clear_details()
            
        except Exception as e:
            self.show_error(f"Error loading stock: {str(e)}")
    
    def _on_stock_selected(self, event=None):
        """Handle stock selection in the treeview."""
        selected_items = self.stock_tree.selection()
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
            self.detail_header.config(text=f"Stock Details: {product['name']}")
            
            # Update product details
            self.product_id_label.config(text=product["product_id"])
            self.sku_label.config(text=product.get("sku", "-"))
            self.name_label.config(text=product["name"])
            self.category_label.config(text=product.get("category_name", "-"))
            
            # Get stock level
            try:
                stock_level = self.stock_controller.get_stock_level(product["product_id"])
                self.stock_level_label.config(text=str(stock_level))
            except Exception:
                self.stock_level_label.config(text="0")
            
            # Min stock level
            min_stock = product.get("min_stock_level", 0)
            self.min_stock_label.config(text=str(min_stock))
            
            # Status
            is_active = product.get("is_active", True)
            status = "Active" if is_active else "Inactive"
            self.status_label.config(text=status)
            
            # Load stock history
            self._load_stock_history(product_id)
            
        except Exception as e:
            self.show_error(f"Error loading product details: {str(e)}")
    
    def _load_stock_history(self, product_id):
        """Load stock movement history for the product."""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        try:
            # Get stock history
            history = self.stock_controller.get_stock_movements(product_id, limit=100)
            
            # Add to treeview
            for movement in history:
                # Format date
                date_str = movement["created_at"].strftime("%Y-%m-%d %H:%M") if movement["created_at"] else "-"
                
                # Movement type
                movement_type = movement["movement_type"].replace("_", " ").title() if movement["movement_type"] else "-"
                
                # Format amount with sign
                amount = movement["quantity"]
                if amount > 0:
                    amount_str = f"+{amount}"
                else:
                    amount_str = str(amount)
                
                # Stock level after
                stock_after = movement["stock_after"] if "stock_after" in movement else "-"
                
                # Reason
                reason = movement.get("reason", "-")
                
                self.history_tree.insert(
                    "", 
                    0,  # Insert at the top (most recent first)
                    values=(date_str, movement_type, amount_str, stock_after, reason)
                )
                
        except Exception as e:
            self.show_error(f"Error loading stock history: {str(e)}")
    
    def _clear_details(self):
        """Clear all details in the detail panel."""
        # Update header
        self.detail_header.config(text="Stock Details")
        
        # Clear product details
        self.product_id_label.config(text="-")
        self.sku_label.config(text="-")
        self.name_label.config(text="-")
        self.category_label.config(text="-")
        self.stock_level_label.config(text="-")
        self.min_stock_label.config(text="-")
        self.status_label.config(text="-")
        
        # Clear adjustment fields
        self.adjustment_amount_var.set("0")
        self.adjustment_reason_var.set("")
        
        # Clear history
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Clear current product
        self.current_product = None
    
    def _add_stock(self):
        """Add stock to the current product."""
        if not self.current_product:
            self.show_warning("No product selected")
            return
        
        try:
            # Validate amount
            try:
                amount = int(self.adjustment_amount_var.get())
                if amount <= 0:
                    self.show_warning("Amount must be a positive number")
                    return
            except ValueError:
                self.show_warning("Please enter a valid number")
                return
            
            # Get reason
            reason = self.adjustment_reason_var.get().strip() or "Manual stock addition"
            
            # Add stock
            result = self.stock_controller.adjust_stock(
                self.current_product["product_id"],
                amount,
                reason
            )
            
            # Refresh stock level
            self._on_stock_selected()
            
            # Clear adjustment fields
            self.adjustment_amount_var.set("0")
            self.adjustment_reason_var.set("")
            
            # Show success message
            self.show_success(f"Added {amount} units to stock")
            
            # Refresh main stock list
            self._refresh_stock()
            
            # Re-select the product
            self.stock_tree.selection_set([self.current_product["product_id"]])
            
        except Exception as e:
            self.show_error(f"Error adding stock: {str(e)}")
    
    def _remove_stock(self):
        """Remove stock from the current product."""
        if not self.current_product:
            self.show_warning("No product selected")
            return
        
        try:
            # Validate amount
            try:
                amount = int(self.adjustment_amount_var.get())
                if amount <= 0:
                    self.show_warning("Amount must be a positive number")
                    return
            except ValueError:
                self.show_warning("Please enter a valid number")
                return
            
            # Get current stock level
            current_stock = int(self.stock_level_label.cget("text") or 0)
            
            # Check if removing more than available
            if amount > current_stock:
                confirm = self.show_confirmation(
                    f"You are trying to remove {amount} units but only {current_stock} units are in stock. This will result in negative stock. Continue?"
                )
                if not confirm:
                    return
            
            # Get reason
            reason = self.adjustment_reason_var.get().strip() or "Manual stock removal"
            
            # Remove stock (negative adjustment)
            result = self.stock_controller.adjust_stock(
                self.current_product["product_id"],
                -amount,
                reason
            )
            
            # Refresh stock level
            self._on_stock_selected()
            
            # Clear adjustment fields
            self.adjustment_amount_var.set("0")
            self.adjustment_reason_var.set("")
            
            # Show success message
            self.show_success(f"Removed {amount} units from stock")
            
            # Refresh main stock list
            self._refresh_stock()
            
            # Re-select the product
            self.stock_tree.selection_set([self.current_product["product_id"]])
            
        except Exception as e:
            self.show_error(f"Error removing stock: {str(e)}")
    
    def _export_stock_to_csv(self):
        """Export stock data to CSV file."""
        try:
            # Get all products with stock levels
            is_active = None if self.show_inactive_var.get() else True
            products = self.product_controller.search_products(is_active=is_active)
            
            # Get stock levels
            stock_data = []
            for product in products:
                try:
                    stock_level = self.stock_controller.get_stock_level(product["product_id"])
                except Exception:
                    stock_level = 0
                
                # Skip if only stocked items and this has no stock (and isn't showing all)
                if not self.show_all_var.get() and stock_level == 0 and not product.get("is_stocked", True):
                    continue
                
                # Get min stock level
                min_stock = product.get("min_stock_level", 0)
                
                # Determine stock status
                if stock_level <= 0:
                    status = "Out of Stock"
                elif stock_level < min_stock:
                    status = "Low Stock"
                else:
                    status = "In Stock"
                
                # If product is inactive, override status
                if not product.get("is_active", True):
                    status = "Inactive"
                
                # Add to data
                stock_data.append({
                    "Product ID": product["product_id"],
                    "SKU": product.get("sku", ""),
                    "Name": product["name"],
                    "Category": product.get("category_name", ""),
                    "Current Stock": stock_level,
                    "Min Stock Level": min_stock,
                    "Status": status
                })
            
            # Get file path
            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stock_export_{now}.csv"
            
            # Ensure exports directory exists
            export_dir = os.path.join(os.getcwd(), "exports")
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            # Full file path
            filepath = os.path.join(export_dir, filename)
            
            # Write CSV file
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["Product ID", "SKU", "Name", "Category", "Current Stock", "Min Stock Level", "Status"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for item in stock_data:
                    writer.writerow(item)
            
            # Show success message
            self.show_success(f"Stock data exported to {filepath}")
            
        except Exception as e:
            self.show_error(f"Error exporting stock data: {str(e)}")