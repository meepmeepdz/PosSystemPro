"""
Invoice view for POS application.
Handles sales and invoice management.
"""

import tkinter as tk
from tkinter import ttk
import datetime
import decimal

from views.base_view import BaseView
from views.components.message_box import MessageBox
from views.components.form_widgets import LabelInput, FormFrame
from utils.currency_formatter import format_currency


class InvoiceView(BaseView):
    """View for sales and invoice management."""
    
    def __init__(self, parent, invoice_controller, product_controller, 
                 customer_controller, payment_controller, cash_register_controller,
                 stock_controller, debt_controller, user, category_controller=None):
        """Initialize invoice view.
        
        Args:
            parent: Parent widget
            invoice_controller: Controller for invoice operations
            product_controller: Controller for product operations
            customer_controller: Controller for customer operations
            payment_controller: Controller for payment operations
            cash_register_controller: Controller for cash register operations
            stock_controller: Controller for stock operations
            debt_controller: Controller for debt operations
            user: Current user information
            category_controller: Controller for category operations (optional)
        """
        super().__init__(parent)
        self.parent = parent
        self.invoice_controller = invoice_controller
        self.product_controller = product_controller
        self.customer_controller = customer_controller
        self.payment_controller = payment_controller
        self.cash_register_controller = cash_register_controller
        self.stock_controller = stock_controller
        self.debt_controller = debt_controller
        self.user = user
        self.category_controller = category_controller
        
        # Current invoice
        self.current_invoice = None
        
        # Variables
        self.invoice_search_var = tk.StringVar()
        self.selected_customer_var = tk.StringVar()
        self.barcode_var = tk.StringVar()
        self.discount_var = tk.StringVar(value="0.00")
        self.payment_amount_var = tk.StringVar(value="0.00")
        self.payment_method_var = tk.StringVar(value="CASH")
        
        # Create UI components
        self._create_widgets()
        self._create_bindings()
        
        # Initial data population
        self._refresh_invoice_list()
        self._check_cash_register()
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with three panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel 1: Invoice list
        self.invoice_list_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.invoice_list_frame, weight=1)
        
        # Panel 2: Active invoice details
        self.invoice_detail_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.invoice_detail_frame, weight=2)
        
        # Panel 3: Checkout
        self.checkout_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.checkout_frame, weight=1)
        
        # Set up invoice list panel
        self._create_invoice_list_panel()
        
        # Set up active invoice panel
        self._create_invoice_detail_panel()
        
        # Set up checkout panel
        self._create_checkout_panel()
    
    def _create_invoice_list_panel(self):
        """Create and populate the invoice list panel."""
        # Header
        header_label = ttk.Label(
            self.invoice_list_frame, 
            text="Open Invoices", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Search and refresh toolbar
        toolbar_frame = ttk.Frame(self.invoice_list_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        search_label = ttk.Label(toolbar_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.invoice_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        search_button = ttk.Button(
            toolbar_frame, 
            text="Search", 
            command=self._refresh_invoice_list
        )
        search_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = ttk.Button(
            toolbar_frame, 
            text="Refresh", 
            command=self._refresh_invoice_list
        )
        refresh_button.pack(side=tk.LEFT)
        
        # Invoice list
        list_frame = ttk.Frame(self.invoice_list_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the invoice list
        self.invoice_tree = ttk.Treeview(
            list_frame, 
            columns=("invoice_number", "date", "customer", "amount", "status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.invoice_tree.heading("invoice_number", text="Invoice #")
        self.invoice_tree.heading("date", text="Date")
        self.invoice_tree.heading("customer", text="Customer")
        self.invoice_tree.heading("amount", text="Amount")
        self.invoice_tree.heading("status", text="Status")
        
        self.invoice_tree.column("invoice_number", width=100)
        self.invoice_tree.column("date", width=100)
        self.invoice_tree.column("customer", width=150)
        self.invoice_tree.column("amount", width=80, anchor=tk.E)
        self.invoice_tree.column("status", width=80)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.invoice_tree.yview)
        self.invoice_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.invoice_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons below the list
        action_frame = ttk.Frame(self.invoice_list_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        new_button = ttk.Button(
            action_frame, 
            text="New Invoice", 
            command=self._create_new_invoice,
            style="Primary.TButton"
        )
        new_button.pack(side=tk.LEFT, padx=(0, 5))
        
        open_button = ttk.Button(
            action_frame, 
            text="Open Selected", 
            command=self._open_selected_invoice
        )
        open_button.pack(side=tk.LEFT, padx=5)
        
        void_button = ttk.Button(
            action_frame, 
            text="Void", 
            command=self._void_selected_invoice,
            style="Danger.TButton"
        )
        void_button.pack(side=tk.LEFT, padx=5)
    
    def _create_invoice_detail_panel(self):
        """Create and populate the invoice detail panel."""
        # Header with invoice number and date
        header_frame = ttk.Frame(self.invoice_detail_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.invoice_title_label = ttk.Label(
            header_frame, 
            text="No Invoice Selected", 
            style="Header.TLabel"
        )
        self.invoice_title_label.pack(side=tk.LEFT)
        
        self.invoice_date_label = ttk.Label(
            header_frame, 
            text="", 
            style="Subheader.TLabel"
        )
        self.invoice_date_label.pack(side=tk.RIGHT)
        
        # Customer selection and note
        customer_frame = ttk.Frame(self.invoice_detail_frame)
        customer_frame.pack(fill=tk.X, pady=(0, 10))
        
        customer_label = ttk.Label(customer_frame, text="Customer:")
        customer_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.customer_combobox = ttk.Combobox(
            customer_frame, 
            textvariable=self.selected_customer_var,
            state="readonly"
        )
        self.customer_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Notes field
        notes_frame = ttk.Frame(self.invoice_detail_frame)
        notes_frame.pack(fill=tk.X, pady=(0, 10))
        
        notes_label = ttk.Label(notes_frame, text="Notes:")
        notes_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.notes_entry = ttk.Entry(notes_frame)
        self.notes_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        update_notes_button = ttk.Button(
            notes_frame, 
            text="Update", 
            command=self._update_invoice_notes
        )
        update_notes_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Product entry
        product_frame = ttk.Frame(self.invoice_detail_frame)
        product_frame.pack(fill=tk.X, pady=(0, 10))
        
        barcode_label = ttk.Label(product_frame, text="Barcode/SKU:")
        barcode_label.pack(side=tk.LEFT, padx=(0, 5))
        
        barcode_entry = ttk.Entry(product_frame, textvariable=self.barcode_var)
        barcode_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        add_button = ttk.Button(
            product_frame, 
            text="Add", 
            command=self._add_product_to_invoice,
            style="Primary.TButton"
        )
        add_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Product browser button
        browse_button = ttk.Button(
            product_frame, 
            text="Browse Products", 
            command=self._open_product_browser
        )
        browse_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Items list
        items_frame = ttk.Frame(self.invoice_detail_frame)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Items treeview
        self.items_tree = ttk.Treeview(
            items_frame, 
            columns=("product", "sku", "quantity", "price", "discount", "total"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.items_tree.heading("product", text="Product")
        self.items_tree.heading("sku", text="SKU")
        self.items_tree.heading("quantity", text="Quantity")
        self.items_tree.heading("price", text="Price")
        self.items_tree.heading("discount", text="Discount")
        self.items_tree.heading("total", text="Total")
        
        self.items_tree.column("product", width=200)
        self.items_tree.column("sku", width=80)
        self.items_tree.column("quantity", width=80, anchor=tk.E)
        self.items_tree.column("price", width=80, anchor=tk.E)
        self.items_tree.column("discount", width=80, anchor=tk.E)
        self.items_tree.column("total", width=80, anchor=tk.E)
        
        # Scrollbar for items
        items_scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Item actions
        item_actions_frame = ttk.Frame(self.invoice_detail_frame)
        item_actions_frame.pack(fill=tk.X, pady=5)
        
        remove_button = ttk.Button(
            item_actions_frame, 
            text="Remove Item", 
            command=self._remove_selected_item,
            style="Danger.TButton"
        )
        remove_button.pack(side=tk.LEFT, padx=(0, 5))
        
        edit_quantity_button = ttk.Button(
            item_actions_frame, 
            text="Edit Quantity", 
            command=self._edit_item_quantity
        )
        edit_quantity_button.pack(side=tk.LEFT, padx=5)
        
        edit_discount_button = ttk.Button(
            item_actions_frame, 
            text="Edit Discount", 
            command=self._edit_item_discount
        )
        edit_discount_button.pack(side=tk.LEFT, padx=5)
        
        # Total display
        total_frame = ttk.Frame(self.invoice_detail_frame)
        total_frame.pack(fill=tk.X, pady=5)
        
        self.total_label = ttk.Label(
            total_frame, 
            text="Total: $0.00", 
            font=("", 14, "bold")
        )
        self.total_label.pack(side=tk.RIGHT)
    
    def _create_checkout_panel(self):
        """Create and populate the checkout panel."""
        # Header
        header_label = ttk.Label(
            self.checkout_frame, 
            text="Checkout", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Payment section
        payment_frame = ttk.Frame(self.checkout_frame)
        payment_frame.pack(fill=tk.X, pady=5)
        
        # Payment amount
        amount_frame = ttk.Frame(payment_frame)
        amount_frame.pack(fill=tk.X, pady=5)
        
        amount_label = ttk.Label(amount_frame, text="Payment Amount:")
        amount_label.pack(side=tk.LEFT, padx=(0, 5))
        
        amount_entry = ttk.Entry(amount_frame, textvariable=self.payment_amount_var)
        amount_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Payment method
        method_frame = ttk.Frame(payment_frame)
        method_frame.pack(fill=tk.X, pady=5)
        
        method_label = ttk.Label(method_frame, text="Payment Method:")
        method_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create a combobox for payment methods
        self.payment_method_combobox = ttk.Combobox(
            method_frame, 
            textvariable=self.payment_method_var,
            state="readonly",
            values=["CASH", "CREDIT_CARD", "DEBIT_CARD", "BANK_TRANSFER", "CHEQUE", "OTHER"]
        )
        self.payment_method_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Complete payment button
        pay_button = ttk.Button(
            payment_frame, 
            text="Complete Payment", 
            command=self._complete_payment,
            style="Success.TButton"
        )
        pay_button.pack(fill=tk.X, pady=10)
        
        # Save as debt button
        debt_button = ttk.Button(
            payment_frame, 
            text="Save as Debt", 
            command=self._save_as_debt
        )
        debt_button.pack(fill=tk.X, pady=(0, 10))
        
        # Divider
        ttk.Separator(payment_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Register status
        register_frame = ttk.Frame(payment_frame)
        register_frame.pack(fill=tk.X, pady=5)
        
        self.register_status_label = ttk.Label(
            register_frame, 
            text="Cash Register: Not Open", 
            foreground="red"
        )
        self.register_status_label.pack(side=tk.LEFT)
        
        open_register_button = ttk.Button(
            register_frame, 
            text="Open Register", 
            command=self._open_cash_register
        )
        open_register_button.pack(side=tk.RIGHT)
        
        # Recent payments list
        payments_label = ttk.Label(
            self.checkout_frame, 
            text="Recent Payments", 
            style="Subheader.TLabel"
        )
        payments_label.pack(fill=tk.X, pady=(10, 5))
        
        # Payments treeview
        payments_frame = ttk.Frame(self.checkout_frame)
        payments_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.payments_tree = ttk.Treeview(
            payments_frame, 
            columns=("date", "amount", "method", "status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.payments_tree.heading("date", text="Date")
        self.payments_tree.heading("amount", text="Amount")
        self.payments_tree.heading("method", text="Method")
        self.payments_tree.heading("status", text="Status")
        
        self.payments_tree.column("date", width=100)
        self.payments_tree.column("amount", width=80, anchor=tk.E)
        self.payments_tree.column("method", width=100)
        self.payments_tree.column("status", width=80)
        
        # Scrollbar for payments
        payments_scrollbar = ttk.Scrollbar(payments_frame, orient=tk.VERTICAL, command=self.payments_tree.yview)
        self.payments_tree.configure(yscrollcommand=payments_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.payments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        payments_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_bindings(self):
        """Create event bindings."""
        # Invoice list selection
        self.invoice_tree.bind("<<TreeviewSelect>>", self._on_invoice_selected)
        
        # Product entry by barcode
        # Return key in barcode entry adds product to invoice
        self.barcode_var.trace_add("write", self._on_barcode_changed)
        
        # Double-click on an item to edit quantity
        self.items_tree.bind("<Double-1>", self._on_item_double_click)
        
        # Payments tree binding for viewing or printing receipt
        self.payments_tree.bind("<Double-1>", self._on_payment_double_click)
    
    def _refresh_invoice_list(self):
        """Refresh the list of invoices."""
        # Clear existing items
        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)
        
        try:
            # Get all draft invoices
            search_term = self.invoice_search_var.get().strip()
            invoices = self.invoice_controller.search_invoices(
                search_term=search_term if search_term else None,
                status="DRAFT",
                limit=50
            )
            
            # Add to treeview
            for invoice in invoices:
                # Format date
                date_str = invoice["created_at"].strftime("%Y-%m-%d") if invoice["created_at"] else ""
                
                # Get customer name
                customer_name = invoice.get("customer_name", "")
                
                # Format amount
                amount_str = format_currency(invoice['total_amount']) if invoice["total_amount"] is not None else format_currency(0)
                
                # Add to tree
                self.invoice_tree.insert(
                    "", 
                    "end", 
                    values=(invoice["invoice_number"], date_str, customer_name, amount_str, invoice["status"]),
                    iid=invoice["invoice_id"]
                )
                
        except Exception as e:
            self.show_error(f"Error loading invoices: {str(e)}")
    
    def _refresh_customers_list(self):
        """Refresh the list of customers for the dropdown."""
        try:
            # Get all customers
            customers = self.customer_controller.get_all_customers()
            
            # Update combobox
            customer_list = [f"{c['full_name']} ({c['email']})" for c in customers]
            self.customer_combobox["values"] = ["No Customer"] + customer_list
            
            # Store customer data for lookup
            self.customers = [None] + customers
            
        except Exception as e:
            self.show_error(f"Error loading customers: {str(e)}")
    
    def _check_cash_register(self):
        """Check if the cash register is open."""
        try:
            register = self.cash_register_controller.get_current_register()
            if register:
                self.register_status_label.config(
                    text=f"Cash Register: Open - Balance: {format_currency(register['current_amount'])}",
                    foreground="green"
                )
            else:
                self.register_status_label.config(
                    text="Cash Register: Not Open",
                    foreground="red"
                )
        except Exception as e:
            self.show_error(f"Error checking cash register: {str(e)}")
    
    def _create_new_invoice(self):
        """Create a new draft invoice."""
        try:
            # Create new invoice
            new_invoice = self.invoice_controller.create_invoice(self.user["user_id"])
            
            # Refresh list and select new invoice
            self._refresh_invoice_list()
            self.invoice_tree.selection_set(new_invoice["invoice_id"])
            self._on_invoice_selected()
            
            # Also refresh customer list
            self._refresh_customers_list()
            
            self.show_success("New invoice created")
            
        except Exception as e:
            self.show_error(f"Error creating invoice: {str(e)}")
    
    def _open_selected_invoice(self):
        """Open the selected invoice from the list."""
        selected_items = self.invoice_tree.selection()
        if not selected_items:
            self.show_warning("Please select an invoice")
            return
        
        # Get the first selected item
        invoice_id = selected_items[0]
        self.invoice_tree.see(invoice_id)
        self._load_invoice_details(invoice_id)
    
    def _on_invoice_selected(self, event=None):
        """Handle invoice selection in the treeview."""
        selected_items = self.invoice_tree.selection()
        if not selected_items:
            return
        
        # Get the first selected item
        invoice_id = selected_items[0]
        self._load_invoice_details(invoice_id)
    
    def _load_invoice_details(self, invoice_id):
        """Load and display the details of an invoice."""
        try:
            # Get invoice with items
            invoice = self.invoice_controller.get_invoice_with_items(invoice_id)
            if not invoice:
                self.show_error("Invoice not found")
                return
            
            # Store current invoice
            self.current_invoice = invoice
            
            # Update header
            self.invoice_title_label.config(text=f"Invoice #{invoice['invoice_number']}")
            
            # Format date
            if invoice["created_at"]:
                date_str = invoice["created_at"].strftime("%Y-%m-%d %H:%M")
                self.invoice_date_label.config(text=date_str)
            else:
                self.invoice_date_label.config(text="")
            
            # Update notes
            self.notes_entry.delete(0, tk.END)
            if invoice["notes"]:
                self.notes_entry.insert(0, invoice["notes"])
            
            # Update customer selection
            if not hasattr(self, "customers"):
                self._refresh_customers_list()
            
            if invoice["customer_id"]:
                # Find customer in the list
                for i, customer in enumerate(self.customers):
                    if customer and customer["customer_id"] == invoice["customer_id"]:
                        self.customer_combobox.current(i)
                        break
            else:
                # Select "No Customer"
                self.customer_combobox.current(0)
            
            # Clear items list
            for item in self.items_tree.get_children():
                self.items_tree.delete(item)
            
            # Add items to the tree
            if "items" in invoice and invoice["items"]:
                for item in invoice["items"]:
                    # Format values
                    sku = item["sku"] or ""
                    price = format_currency(item['unit_price']) if item["unit_price"] is not None else format_currency(0)
                    discount = format_currency(item['discount_price']) if item["discount_price"] is not None else "None"
                    total = format_currency(item['subtotal']) if item["subtotal"] is not None else format_currency(0)
                    
                    # Add to tree
                    self.items_tree.insert(
                        "", 
                        "end", 
                        values=(item["product_name"], sku, item["quantity"], price, discount, total),
                        iid=item["invoice_item_id"]
                    )
            
            # Update total
            self._update_total_display()
            
            # Clear barcode field
            self.barcode_var.set("")
            
            # Load payments
            self._refresh_payment_list()
            
        except Exception as e:
            self.show_error(f"Error loading invoice details: {str(e)}")
    
    def _update_total_display(self):
        """Update the total amount display."""
        if self.current_invoice:
            total = self.current_invoice["total_amount"] or 0
            self.total_label.config(text=f"Total: {format_currency(total)}")
            
            # Also update payment amount
            self.payment_amount_var.set(f"{total:.2f}")
    
    def _on_barcode_changed(self, *args):
        """Handle barcode field changes."""
        # We could implement auto-add functionality here
        pass
    
    def _add_product_to_invoice(self):
        """Add a product to the current invoice using barcode or SKU."""
        if not self.current_invoice:
            self.show_warning("Please select or create an invoice first")
            return
        
        barcode_or_sku = self.barcode_var.get().strip()
        if not barcode_or_sku:
            self.show_warning("Please enter a barcode or SKU")
            return
        
        try:
            # First try to find by barcode
            product = self.product_controller.get_product_by_barcode(barcode_or_sku)
            
            # If not found, try by SKU
            if not product:
                product = self.product_controller.get_product_by_sku(barcode_or_sku)
            
            if not product:
                self.show_warning(f"Product not found with barcode or SKU: {barcode_or_sku}")
                return
            
            # Check if product is active
            if not product["is_active"]:
                self.show_warning(f"Product '{product['name']}' is inactive and cannot be added")
                return
            
            # Get quantity from user
            quantity = MessageBox.show_input(
                self, 
                "Enter Quantity", 
                f"Enter quantity for {product['name']}:", 
                "1"
            )
            
            if not quantity:
                return  # Cancelled
            
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")
            except ValueError:
                self.show_warning("Please enter a valid quantity (positive number)")
                return
            
            # Add to invoice
            item = self.invoice_controller.add_item_to_invoice(
                self.current_invoice["invoice_id"],
                product["product_id"],
                quantity
            )
            
            # Reload invoice to refresh items
            self._load_invoice_details(self.current_invoice["invoice_id"])
            
            # Clear barcode field
            self.barcode_var.set("")
            
            self.show_success(f"Added {quantity} x {product['name']} to invoice")
            
        except Exception as e:
            self.show_error(f"Error adding product: {str(e)}")
    
    def _open_product_browser(self):
        """Open a product browser to select products."""
        if not self.current_invoice:
            self.show_warning("Please select or create an invoice first")
            return
        
        # Create a top-level window for the product browser
        browser = tk.Toplevel(self)
        browser.title("Product Browser")
        browser.geometry("800x600")
        browser.transient(self.winfo_toplevel())  # Make it transient to the root window
        browser.grab_set()
        
        # Center on screen
        self.center_window(browser)
        
        # Add product browser content
        ProductBrowserView(browser, self.product_controller, self.category_controller, 
                          self._on_product_selected, self.current_invoice["invoice_id"])
    
    def _on_product_selected(self, product, invoice_id):
        """Callback when a product is selected from the browser."""
        try:
            # Get quantity from user
            quantity = MessageBox.show_input(
                self, 
                "Enter Quantity", 
                f"Enter quantity for {product['name']}:", 
                "1"
            )
            
            if not quantity:
                return  # Cancelled
            
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")
            except ValueError:
                self.show_warning("Please enter a valid quantity (positive number)")
                return
            
            # Add to invoice
            item = self.invoice_controller.add_item_to_invoice(
                invoice_id,
                product["product_id"],
                quantity
            )
            
            # Reload invoice to refresh items
            self._load_invoice_details(invoice_id)
            
            self.show_success(f"Added {quantity} x {product['name']} to invoice")
            
        except Exception as e:
            self.show_error(f"Error adding product: {str(e)}")
    
    def _on_item_double_click(self, event):
        """Handle double-click on an invoice item."""
        # Get the selected item
        selection = self.items_tree.selection()
        if not selection:
            return
        
        # Edit quantity by default
        self._edit_item_quantity()
    
    def _remove_selected_item(self):
        """Remove the selected item from the invoice."""
        # Get the selected item
        selection = self.items_tree.selection()
        if not selection:
            self.show_warning("Please select an item to remove")
            return
        
        item_id = selection[0]
        
        # Confirm removal
        confirm = self.show_confirmation("Are you sure you want to remove this item?")
        if not confirm:
            return
        
        try:
            if not self.current_invoice:
                self.show_error("No invoice selected")
                return
                
            # Remove the item
            result = self.invoice_controller.remove_item_from_invoice(item_id)
            
            # Reload invoice to refresh items
            self._load_invoice_details(self.current_invoice["invoice_id"])
            
            self.show_success("Item removed successfully")
            
        except Exception as e:
            self.show_error(f"Error removing item: {str(e)}")
    
    def _edit_item_quantity(self):
        """Edit the quantity of the selected item."""
        # Get the selected item
        selection = self.items_tree.selection()
        if not selection:
            self.show_warning("Please select an item to edit")
            return
        
        item_id = selection[0]
        
        # Get current quantity
        item_values = self.items_tree.item(item_id, "values")
        current_quantity = item_values[2]  # Assuming quantity is the third column
        
        # Get new quantity from user
        new_quantity = MessageBox.show_input(
            self, 
            "Edit Quantity", 
            f"Enter new quantity for {item_values[0]}:", 
            current_quantity
        )
        
        if not new_quantity:
            return  # Cancelled
        
        try:
            if not self.current_invoice:
                self.show_error("No invoice selected")
                return
                
            quantity = int(new_quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
                
            # Update the item
            result = self.invoice_controller.update_item_quantity(item_id, quantity)
            
            # Reload invoice to refresh items
            self._load_invoice_details(self.current_invoice["invoice_id"])
            
            self.show_success("Quantity updated successfully")
            
        except ValueError:
            self.show_warning("Please enter a valid quantity (positive number)")
        except Exception as e:
            self.show_error(f"Error updating quantity: {str(e)}")
    
    def _edit_item_discount(self):
        """Edit the discount of the selected item."""
        # Get the selected item
        selection = self.items_tree.selection()
        if not selection:
            self.show_warning("Please select an item to discount")
            return
        
        item_id = selection[0]
        
        # Get item details
        item_values = self.items_tree.item(item_id, "values")
        product_name = item_values[0]
        current_price = item_values[3]  # Assuming price is the fourth column
        current_discount = item_values[4]  # Assuming discount is the fifth column
        
        # Strip currency symbol and convert to float
        try:
            # Extract numeric value from price string (e.g., "1 234,56 DA" to 1234.56)
            current_price_str = current_price.replace(" ", "").replace(",", ".").replace("DA", "").strip()
            current_price = float(current_price_str)
            
            # Handle discount
            if current_discount == "None" or current_discount == "-":
                current_discount = ""
            else:
                current_discount_str = current_discount.replace(" ", "").replace(",", ".").replace("DA", "").strip()
                current_discount = float(current_discount_str)
        except (ValueError, AttributeError, TypeError):
            # In case of any conversion error, default to empty discount
            current_discount = ""
        
        # Get new discount from user
        new_discount = MessageBox.show_input(
            self, 
            "Edit Discount", 
            f"Enter discount price for {product_name} (regular price: {format_currency(current_price)}):", 
            current_discount
        )
        
        if new_discount is None:
            return  # Cancelled
        
        try:
            if not self.current_invoice:
                self.show_error("No invoice selected")
                return
                
            # Handle empty string (no discount)
            if not new_discount.strip():
                discount_price = None
            else:
                # Handle both decimal separators (point or comma)
                # Convert comma to point for float conversion
                new_discount_normalized = new_discount.replace(",", ".").replace(" ", "")
                discount_price = float(new_discount_normalized)
                if discount_price < 0:
                    raise ValueError("Discount cannot be negative")
                # Safe comparison with correct types
                if isinstance(discount_price, (int, float)) and isinstance(current_price, (int, float)):
                    if discount_price > current_price:
                        raise ValueError("Discount cannot be greater than the price")
                
            # Update the item
            result = self.invoice_controller.update_item_discount(item_id, discount_price)
            
            # Reload invoice to refresh items
            self._load_invoice_details(self.current_invoice["invoice_id"])
            
            self.show_success("Discount updated successfully")
            
        except ValueError as e:
            self.show_warning(f"Invalid discount: {str(e)}")
        except Exception as e:
            self.show_error(f"Error updating discount: {str(e)}")
    
    def _update_invoice_notes(self):
        """Update the notes for the current invoice."""
        if not self.current_invoice:
            self.show_warning("Please select or create an invoice first")
            return
        
        notes = self.notes_entry.get()
        
        try:
            # Update invoice notes
            result = self.invoice_controller.update_invoice(
                self.current_invoice["invoice_id"], 
                {"notes": notes}
            )
            
            # Reload invoice
            self._load_invoice_details(self.current_invoice["invoice_id"])
            
            self.show_success("Notes updated successfully")
            
        except Exception as e:
            self.show_error(f"Error updating notes: {str(e)}")
    
    def _void_selected_invoice(self):
        """Void the selected invoice."""
        selected_items = self.invoice_tree.selection()
        if not selected_items:
            self.show_warning("Please select an invoice to void")
            return
        
        # Get the first selected item
        invoice_id = selected_items[0]
        
        # Confirm voiding
        confirm = self.show_confirmation(
            "Are you sure you want to void this invoice? This action cannot be undone."
        )
        if not confirm:
            return
        
        # Get reason for voiding
        reason = MessageBox.show_input(
            self, 
            "Void Reason", 
            "Enter reason for voiding this invoice:"
        )
        
        if reason is None:
            return  # Cancelled
        
        try:
            # Void the invoice
            result = self.invoice_controller.void_invoice(invoice_id, reason)
            
            # Refresh the invoice list
            self._refresh_invoice_list()
            
            # Clear current invoice
            self.current_invoice = None
            self.invoice_title_label.config(text="No Invoice Selected")
            self.invoice_date_label.config(text="")
            self.notes_entry.delete(0, tk.END)
            
            # Clear items
            for item in self.items_tree.get_children():
                self.items_tree.delete(item)
            
            self.show_success("Invoice voided successfully")
            
        except Exception as e:
            self.show_error(f"Error voiding invoice: {str(e)}")
    
    def _open_cash_register(self):
        """Open the cash register."""
        # Check if already open
        register = self.cash_register_controller.get_current_register()
        if register:
            self.show_info("Cash register is already open")
            return
        
        # Get initial amount from user
        initial_amount = MessageBox.show_input(
            self, 
            "Open Cash Register", 
            "Enter initial cash amount:"
        )
        
        if initial_amount is None:
            return  # Cancelled
        
        try:
            amount = float(initial_amount)
            if amount < 0:
                raise ValueError("Amount cannot be negative")
                
            # Open the register
            result = self.cash_register_controller.open_register(
                self.user["user_id"],
                amount
            )
            
            # Update status
            self._check_cash_register()
            
            self.show_success("Cash register opened successfully")
            
        except ValueError:
            self.show_warning("Please enter a valid amount (positive number)")
        except Exception as e:
            self.show_error(f"Error opening cash register: {str(e)}")
    
    def _complete_payment(self):
        """Complete payment for the current invoice."""
        if not self.current_invoice:
            self.show_warning("Please select or create an invoice first")
            return
        
        # Check if the invoice has items
        if not self.current_invoice.get("items"):
            self.show_warning("Cannot process payment for an empty invoice")
            return
        
        # Get payment details
        try:
            payment_amount = float(self.payment_amount_var.get())
            payment_method = self.payment_method_var.get()
            
            if payment_amount <= 0:
                self.show_warning("Payment amount must be positive")
                return
                
        except ValueError:
            self.show_warning("Please enter a valid payment amount")
            return
        
        # Check if cash register is open for cash payments
        if payment_method == "CASH":
            register = self.cash_register_controller.get_current_register()
            if not register:
                confirm = self.show_confirmation(
                    "Cash register is not open. Do you want to open it now?"
                )
                if confirm:
                    self._open_cash_register()
                    # Check again after opening
                    register = self.cash_register_controller.get_current_register()
                    if not register:
                        return  # Register not opened
                else:
                    return  # Cancelled
        
        # Finalize the invoice (update stock)
        try:
            # Complete the invoice
            self.invoice_controller.finalize_invoice(self.current_invoice["invoice_id"])
            
            # Record the payment
            payment = self.payment_controller.create_payment(
                self.current_invoice["invoice_id"],
                self.user["user_id"],
                payment_amount,
                payment_method
            )
            
            # Refresh the invoice
            self._load_invoice_details(self.current_invoice["invoice_id"])
            
            # Show success
            self.show_success("Payment processed successfully")
            
            # Check if fully paid
            if self.current_invoice["total_amount"] <= payment_amount:
                # Ask if user wants to print receipt
                confirm = self.show_confirmation("Do you want to print a receipt?")
                if confirm:
                    self._print_receipt(self.current_invoice["invoice_id"])
            
        except Exception as e:
            self.show_error(f"Error processing payment: {str(e)}")
    
    def _save_as_debt(self):
        """Save the current invoice as a customer debt."""
        if not self.current_invoice:
            self.show_warning("Please select or create an invoice first")
            return
        
        # Check if the invoice has items
        if not self.current_invoice.get("items"):
            self.show_warning("Cannot create debt for an empty invoice")
            return
        
        # Check if a customer is selected
        if not self.current_invoice["customer_id"]:
            self.show_warning("A customer must be selected to create a debt")
            return
        
        # Confirm action
        confirm = self.show_confirmation(
            "Are you sure you want to save this invoice as a customer debt?"
        )
        if not confirm:
            return
        
        try:
            # Finalize the invoice (update stock)
            finalized_invoice = self.invoice_controller.finalize_invoice(
                self.current_invoice["invoice_id"]
            )
            
            # Create the debt record
            debt = self.debt_controller.create_debt(
                self.current_invoice["customer_id"],
                self.current_invoice["invoice_id"],
                self.current_invoice["total_amount"],
                self.user["user_id"],
                f"Invoice #{self.current_invoice['invoice_number']}"
            )
            
            # Refresh the invoice
            self._load_invoice_details(self.current_invoice["invoice_id"])
            
            self.show_success("Invoice saved as customer debt")
            
        except Exception as e:
            self.show_error(f"Error saving as debt: {str(e)}")
    
    def _refresh_payment_list(self):
        """Refresh the list of payments for the current invoice."""
        if not self.current_invoice:
            return
        
        # Clear existing items
        for item in self.payments_tree.get_children():
            self.payments_tree.delete(item)
        
        try:
            # Get payments for this invoice
            if "payments" in self.current_invoice and self.current_invoice["payments"]:
                for payment in self.current_invoice["payments"]:
                    # Format date
                    date_str = payment["payment_date"].strftime("%Y-%m-%d %H:%M") if payment["payment_date"] else ""
                    
                    # Format amount
                    amount_str = format_currency(payment['amount']) if payment["amount"] is not None else format_currency(0)
                    
                    # Format method
                    method = payment["payment_method"].replace("_", " ").title()
                    
                    # Add to tree
                    self.payments_tree.insert(
                        "", 
                        "end", 
                        values=(date_str, amount_str, method, "Completed"),
                        iid=payment["payment_id"]
                    )
                    
        except Exception as e:
            self.show_error(f"Error loading payments: {str(e)}")
    
    def _on_payment_double_click(self, event):
        """Handle double-click on a payment."""
        # Get the selected payment
        selection = self.payments_tree.selection()
        if not selection:
            return
            
        # Check if we have a current invoice
        if not self.current_invoice:
            self.show_error("No invoice selected")
            return
        
        # Print receipt for this payment
        self._print_receipt(self.current_invoice["invoice_id"])
    
    def _print_receipt(self, invoice_id):
        """Print a receipt for an invoice."""
        if not invoice_id:
            self.show_error("Invalid invoice ID")
            return
            
        try:
            # Get the invoice with all details
            invoice = self.invoice_controller.get_invoice_with_items(invoice_id)
            if not invoice:
                self.show_error("Invoice not found")
                return
            
            # Display receipt preview
            receipt_window = tk.Toplevel(self)
            receipt_window.title(f"Receipt - Invoice #{invoice['invoice_number']}")
            receipt_window.geometry("400x600")
            receipt_window.transient(self.winfo_toplevel())
            
            # Center on screen
            self.center_window(receipt_window)
            
            # Create receipt content
            receipt_frame = ttk.Frame(receipt_window, padding=20)
            receipt_frame.pack(fill=tk.BOTH, expand=True)
            
            # Add company header
            from config import COMPANY_NAME, COMPANY_ADDRESS, COMPANY_PHONE, COMPANY_TAX_ID
            
            header_label = ttk.Label(
                receipt_frame, 
                text=COMPANY_NAME,
                font=("", 16, "bold"),
                justify=tk.CENTER
            )
            header_label.pack(fill=tk.X)
            
            address_label = ttk.Label(
                receipt_frame, 
                text=COMPANY_ADDRESS,
                justify=tk.CENTER
            )
            address_label.pack(fill=tk.X)
            
            phone_label = ttk.Label(
                receipt_frame, 
                text=f"Phone: {COMPANY_PHONE}",
                justify=tk.CENTER
            )
            phone_label.pack(fill=tk.X)
            
            if COMPANY_TAX_ID:
                tax_label = ttk.Label(
                    receipt_frame, 
                    text=f"Tax ID: {COMPANY_TAX_ID}",
                    justify=tk.CENTER
                )
                tax_label.pack(fill=tk.X)
            
            # Separator
            ttk.Separator(receipt_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
            
            # Invoice details
            invoice_label = ttk.Label(
                receipt_frame, 
                text=f"Invoice: #{invoice['invoice_number']}",
                font=("", 12, "bold")
            )
            invoice_label.pack(anchor=tk.W)
            
            date_str = invoice["created_at"].strftime("%Y-%m-%d %H:%M") if invoice["created_at"] else ""
            date_label = ttk.Label(
                receipt_frame, 
                text=f"Date: {date_str}"
            )
            date_label.pack(anchor=tk.W)
            
            if invoice["customer_name"]:
                customer_label = ttk.Label(
                    receipt_frame, 
                    text=f"Customer: {invoice['customer_name']}"
                )
                customer_label.pack(anchor=tk.W)
            
            # Separator
            ttk.Separator(receipt_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
            
            # Items header
            items_header_frame = ttk.Frame(receipt_frame)
            items_header_frame.pack(fill=tk.X)
            
            ttk.Label(items_header_frame, text="Item", width=20).pack(side=tk.LEFT)
            ttk.Label(items_header_frame, text="Qty", width=5).pack(side=tk.LEFT)
            ttk.Label(items_header_frame, text="Price", width=10).pack(side=tk.LEFT)
            ttk.Label(items_header_frame, text="Total", width=10).pack(side=tk.LEFT)
            
            # Separator
            ttk.Separator(receipt_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
            
            # Items
            if "items" in invoice and invoice["items"]:
                for item in invoice["items"]:
                    item_frame = ttk.Frame(receipt_frame)
                    item_frame.pack(fill=tk.X)
                    
                    # Format values
                    price = item["discount_price"] if item["discount_price"] is not None else item["unit_price"]
                    price_str = format_currency(price) if price is not None else format_currency(0)
                    total = format_currency(item['subtotal']) if item["subtotal"] is not None else format_currency(0)
                    
                    ttk.Label(item_frame, text=item["product_name"], width=20).pack(side=tk.LEFT)
                    ttk.Label(item_frame, text=str(item["quantity"]), width=5).pack(side=tk.LEFT)
                    ttk.Label(item_frame, text=price_str, width=10).pack(side=tk.LEFT)
                    ttk.Label(item_frame, text=total, width=10).pack(side=tk.LEFT)
            
            # Separator
            ttk.Separator(receipt_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
            
            # Total
            total_frame = ttk.Frame(receipt_frame)
            total_frame.pack(fill=tk.X)
            
            ttk.Label(total_frame, text="Total:").pack(side=tk.LEFT)
            total_str = format_currency(invoice['total_amount']) if invoice["total_amount"] is not None else format_currency(0)
            ttk.Label(total_frame, text=total_str, font=("", 12, "bold")).pack(side=tk.RIGHT)
            
            # Payments
            if "payments" in invoice and invoice["payments"]:
                # Separator
                ttk.Separator(receipt_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
                
                # Payments header
                ttk.Label(receipt_frame, text="Payments:").pack(anchor=tk.W)
                
                for payment in invoice["payments"]:
                    payment_frame = ttk.Frame(receipt_frame)
                    payment_frame.pack(fill=tk.X)
                    
                    # Format values
                    date_str = payment["payment_date"].strftime("%Y-%m-%d") if payment["payment_date"] else ""
                    method = payment["payment_method"].replace("_", " ").title()
                    amount_str = format_currency(payment['amount']) if payment["amount"] is not None else format_currency(0)
                    
                    ttk.Label(payment_frame, text=f"{date_str} - {method}").pack(side=tk.LEFT)
                    ttk.Label(payment_frame, text=amount_str).pack(side=tk.RIGHT)
            
            # Separator
            ttk.Separator(receipt_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
            
            # Footer
            footer_label = ttk.Label(
                receipt_frame, 
                text="Thank you for your business!",
                font=("", 10, "bold"),
                justify=tk.CENTER
            )
            footer_label.pack(fill=tk.X)
            
            # Print and Export buttons in a frame
            button_frame = ttk.Frame(receipt_frame)
            button_frame.pack(pady=10, fill=tk.X)
            
            # Print button
            print_button = ttk.Button(
                button_frame, 
                text="Print", 
                command=lambda: self._print_receipt_to_printer(receipt_window)
            )
            print_button.pack(side=tk.LEFT, padx=(0, 5), expand=True, fill=tk.X)
            
            # Export to PDF button
            export_button = ttk.Button(
                button_frame, 
                text="Export to PDF", 
                command=lambda: self._export_receipt_to_pdf(invoice_id)
            )
            export_button.pack(side=tk.RIGHT, padx=(5, 0), expand=True, fill=tk.X)
            
        except Exception as e:
            self.show_error(f"Error printing receipt: {str(e)}")
    
    def _print_receipt_to_printer(self, receipt_window):
        """Print the receipt to a printer."""
        try:
            # This would normally use the OS print dialog or a direct printer API
            # For now, we'll export to PDF and show a message
            if self.show_confirmation("Would you like to export the receipt to PDF before printing?"):
                # Check if current_invoice is None before accessing it
                if self.current_invoice is None:
                    self.show_error("No invoice selected")
                    return
                    
                invoice_id = self.current_invoice.get("invoice_id")
                if not invoice_id:
                    self.show_error("Invalid invoice ID")
                    return
                    
                pdf_path = self._export_receipt_to_pdf(invoice_id)
                if pdf_path:
                    self.show_success(f"Receipt exported to {pdf_path}\nYou can now print it using your PDF viewer.")
            else:
                self.show_info("Direct printing functionality will be implemented based on your printer requirements")
        except Exception as e:
            self.show_error(f"Error printing receipt: {str(e)}")
            
    def _export_receipt_to_pdf(self, invoice_id):
        """Export the receipt to a PDF file.
        
        Args:
            invoice_id: The ID of the invoice to export
            
        Returns:
            str: The path to the exported PDF file, or None if export failed
        """
        try:
            # Get the invoice with all details
            invoice = self.invoice_controller.get_invoice_with_items(invoice_id)
            if not invoice:
                self.show_error("Invoice not found")
                return None
                
            # Import necessary modules for PDF generation
            try:
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.lib.units import cm, mm
                REPORTLAB_AVAILABLE = True
            except ImportError:
                REPORTLAB_AVAILABLE = False
                print("Warning: reportlab modules not available, PDF generation functionality will be limited")
            
            # Import company details
            from config import COMPANY_NAME, COMPANY_ADDRESS, COMPANY_PHONE, COMPANY_TAX_ID
            
            # Import currency formatter
            from utils.currency_formatter import format_currency
            
            # Create the exports directory if it doesn't exist
            from utils.export_utils import ensure_export_dir, EXPORT_DIR
            ensure_export_dir()
            
            # Generate filename
            import os
            from datetime import datetime
            filename = f"invoice_{invoice['invoice_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(EXPORT_DIR, filename)
            
            # Check if reportlab is available
            if not REPORTLAB_AVAILABLE:
                import csv
                
                # Fallback to CSV if reportlab is not available
                filename = filename.replace('.pdf', '.csv')
                filepath = os.path.join(EXPORT_DIR, filename)
                
                with open(filepath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header information
                    writer.writerow([COMPANY_NAME])
                    writer.writerow([COMPANY_ADDRESS])
                    writer.writerow([f"Phone: {COMPANY_PHONE}"])
                    writer.writerow([f"Tax ID: {COMPANY_TAX_ID}"])
                    writer.writerow([])
                    
                    # Write invoice details
                    writer.writerow([f"Invoice #{invoice['invoice_number']}"])
                    date_str = invoice["created_at"].strftime("%Y-%m-%d %H:%M") if invoice["created_at"] else "N/A"
                    writer.writerow([f"Date: {date_str}"])
                    
                    if invoice["customer_name"]:
                        writer.writerow([f"Customer: {invoice['customer_name']}"])
                    
                    writer.writerow([])
                    
                    # Write items
                    if "items" in invoice and invoice["items"]:
                        writer.writerow(["Item", "Qty", "Price", "Total"])
                        
                        for item in invoice["items"]:
                            price = item["discount_price"] if item["discount_price"] is not None else item["unit_price"]
                            price_str = format_currency(price) if price is not None else format_currency(0)
                            total = format_currency(item['subtotal']) if item["subtotal"] is not None else format_currency(0)
                            
                            writer.writerow([
                                item["product_name"],
                                str(item["quantity"]),
                                price_str,
                                total
                            ])
                    
                    writer.writerow([])
                    
                    # Write total
                    total_str = format_currency(invoice['total_amount']) if invoice["total_amount"] is not None else format_currency(0)
                    writer.writerow(["Total:", total_str])
                    
                    # Write payments
                    if "payments" in invoice and invoice["payments"]:
                        writer.writerow([])
                        writer.writerow(["Payments:"])
                        writer.writerow(["Date", "Method", "Amount"])
                        
                        for payment in invoice["payments"]:
                            date_str = payment["payment_date"].strftime("%Y-%m-%d") if payment["payment_date"] else "N/A"
                            method = payment["payment_method"].replace("_", " ").title()
                            amount_str = format_currency(payment['amount']) if payment["amount"] is not None else format_currency(0)
                            
                            writer.writerow([date_str, method, amount_str])
                    
                    writer.writerow([])
                    writer.writerow(["Thank you for your business!"])
                
                self.show_success(f"Receipt exported to CSV (PDF generation not available): {filepath}")
                return filepath
            
            # If reportlab is available, create the PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            subtitle_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Content elements
            elements = []
            
            # Add company header
            elements.append(Paragraph(COMPANY_NAME, title_style))
            elements.append(Paragraph(COMPANY_ADDRESS, normal_style))
            elements.append(Paragraph(f"Phone: {COMPANY_PHONE}", normal_style))
            elements.append(Paragraph(f"Tax ID: {COMPANY_TAX_ID}", normal_style))
            elements.append(Spacer(1, 0.5 * cm))
            
            # Add invoice details
            elements.append(Paragraph(f"Invoice #{invoice['invoice_number']}", subtitle_style))
            
            # Format the date
            date_str = invoice["created_at"].strftime("%Y-%m-%d %H:%M") if invoice["created_at"] else "N/A"
            elements.append(Paragraph(f"Date: {date_str}", normal_style))
            
            # Add customer details if available
            if invoice["customer_name"]:
                elements.append(Paragraph(f"Customer: {invoice['customer_name']}", normal_style))
            
            elements.append(Spacer(1, 0.5 * cm))
            
            # Items table
            if "items" in invoice and invoice["items"]:
                # Table header
                data = [["Item", "Qty", "Price", "Total"]]
                
                # Table rows
                for item in invoice["items"]:
                    price = item["discount_price"] if item["discount_price"] is not None else item["unit_price"]
                    price_str = format_currency(price) if price is not None else format_currency(0)
                    total = format_currency(item['subtotal']) if item["subtotal"] is not None else format_currency(0)
                    
                    data.append([
                        item["product_name"],
                        str(item["quantity"]),
                        price_str,
                        total
                    ])
                
                # Create table
                table = Table(data, colWidths=[doc.width * 0.5, doc.width * 0.1, doc.width * 0.2, doc.width * 0.2])
                
                # Style the table
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                    ('ALIGN', (2, 1), (3, -1), 'RIGHT'),
                ]))
                
                elements.append(table)
            
            elements.append(Spacer(1, 0.5 * cm))
            
            # Total
            total_str = format_currency(invoice['total_amount']) if invoice["total_amount"] is not None else format_currency(0)
            total_data = [["Total:", total_str]]
            total_table = Table(total_data, colWidths=[doc.width * 0.8, doc.width * 0.2])
            total_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ]))
            elements.append(total_table)
            
            # Add payments if available
            if "payments" in invoice and invoice["payments"]:
                elements.append(Spacer(1, 0.5 * cm))
                elements.append(Paragraph("Payments:", subtitle_style))
                
                payments_data = [["Date", "Method", "Amount"]]
                
                for payment in invoice["payments"]:
                    date_str = payment["payment_date"].strftime("%Y-%m-%d") if payment["payment_date"] else "N/A"
                    method = payment["payment_method"].replace("_", " ").title()
                    amount_str = format_currency(payment['amount']) if payment["amount"] is not None else format_currency(0)
                    
                    payments_data.append([date_str, method, amount_str])
                
                payments_table = Table(payments_data, colWidths=[doc.width * 0.3, doc.width * 0.4, doc.width * 0.3])
                payments_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ]))
                
                elements.append(payments_table)
            
            # Footer
            elements.append(Spacer(1, 1 * cm))
            elements.append(Paragraph("Thank you for your business!", subtitle_style))
            
            # Build PDF
            doc.build(elements)
            
            self.show_success(f"Receipt exported to {filepath}")
            return filepath
            
        except Exception as e:
            self.show_error(f"Error exporting receipt to PDF: {str(e)}")
            return None


class ProductBrowserView(BaseView):
    """Product browser view for selecting products."""
    
    def __init__(self, parent, product_controller, category_controller, on_product_selected, invoice_id):
        """Initialize product browser view.
        
        Args:
            parent: Parent widget
            product_controller: Controller for product operations
            category_controller: Controller for category operations
            on_product_selected: Callback when a product is selected
            invoice_id: Current invoice ID
        """
        super().__init__(parent)
        self.parent = parent
        self.product_controller = product_controller
        self.category_controller = category_controller
        self.on_product_selected = on_product_selected
        self.invoice_id = invoice_id
        
        # Variables
        self.search_var = tk.StringVar()
        self.selected_category_var = tk.StringVar()
        
        # Create UI components
        self._create_widgets()
        
        # Load initial data
        self._load_categories()
        self._load_products()
        
        # Pack the main frame
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Top toolbar
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Search field
        search_label = ttk.Label(toolbar_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        search_button = ttk.Button(
            toolbar_frame, 
            text="Search", 
            command=self._load_products
        )
        search_button.pack(side=tk.LEFT, padx=5)
        
        # Category dropdown
        category_label = ttk.Label(toolbar_frame, text="Category:")
        category_label.pack(side=tk.LEFT, padx=(10, 5))
        
        self.category_combobox = ttk.Combobox(
            toolbar_frame, 
            textvariable=self.selected_category_var,
            state="readonly"
        )
        self.category_combobox.pack(side=tk.LEFT, padx=(0, 5))
        
        # Product list
        product_frame = ttk.Frame(self)
        product_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a treeview for the product list
        self.product_tree = ttk.Treeview(
            product_frame, 
            columns=("name", "sku", "price", "stock"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.product_tree.heading("name", text="Product Name")
        self.product_tree.heading("sku", text="SKU")
        self.product_tree.heading("price", text="Price")
        self.product_tree.heading("stock", text="In Stock")
        
        self.product_tree.column("name", width=250)
        self.product_tree.column("sku", width=100)
        self.product_tree.column("price", width=80, anchor=tk.E)
        self.product_tree.column("stock", width=80, anchor=tk.E)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(product_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame at the bottom
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        select_button = ttk.Button(
            button_frame, 
            text="Select Product", 
            command=self._on_select_product,
            style="Primary.TButton"
        )
        select_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self.parent.destroy
        )
        cancel_button.pack(side=tk.RIGHT)
        
        # Double-click to select
        self.product_tree.bind("<Double-1>", lambda e: self._on_select_product())
        
        # Category change handler
        self.category_combobox.bind("<<ComboboxSelected>>", lambda e: self._load_products())
    
    def _load_categories(self):
        """Load categories into the combobox."""
        try:
            # Get all categories
            categories = self.category_controller.get_all_categories()
            
            # Update combobox
            category_list = [c["name"] for c in categories]
            self.category_combobox["values"] = ["All Categories"] + category_list
            
            # Set default selection
            self.category_combobox.current(0)
            
            # Store category data for lookup
            self.categories = [None] + categories
            
        except Exception as e:
            self.show_error(f"Error loading categories: {str(e)}")
    
    def _load_products(self):
        """Load products based on search criteria and selected category."""
        # Clear existing items
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        try:
            # Get search term
            search_term = self.search_var.get().strip()
            
            # Get selected category
            selected_category = self.selected_category_var.get()
            category_id = None
            
            if selected_category and selected_category != "All Categories":
                # Find category ID
                for category in self.categories:
                    if category and category["name"] == selected_category:
                        category_id = category["category_id"]
                        break
            
            # Get products
            products = self.product_controller.search_products(
                search_term=search_term if search_term else None,
                category_id=category_id,
                include_inactive=False,
                limit=100
            )
            
            # Add to treeview
            for product in products:
                # Format values
                price = format_currency(product['selling_price']) if product["selling_price"] is not None else format_currency(0)
                stock = str(product.get("stock_quantity", "N/A"))
                
                self.product_tree.insert(
                    "", 
                    "end", 
                    values=(product["name"], product["sku"], price, stock),
                    iid=product["product_id"]
                )
                
        except Exception as e:
            self.show_error(f"Error loading products: {str(e)}")
    
    def _on_select_product(self):
        """Handle product selection."""
        selection = self.product_tree.selection()
        if not selection:
            self.show_warning("Please select a product")
            return
        
        product_id = selection[0]
        
        try:
            # Get product details
            product = self.product_controller.get_product_by_id(product_id)
            if not product:
                self.show_error("Product not found")
                return
            
            # Call the callback
            self.on_product_selected(product, self.invoice_id)
            
        except Exception as e:
            self.show_error(f"Error selecting product: {str(e)}")