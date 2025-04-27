"""
Debt view for POS application.
Handles customer debt management.
"""

import tkinter as tk
from tkinter import ttk
import datetime

from views.base_view import BaseView
from views.components.message_box import MessageBox
from utils.currency_formatter import format_currency


class DebtView(BaseView):
    """View for customer debt management."""
    
    def __init__(self, parent, debt_controller, customer_controller, payment_controller, user):
        """Initialize debt view.
        
        Args:
            parent: Parent widget
            debt_controller: Controller for debt operations
            customer_controller: Controller for customer operations
            payment_controller: Controller for payment operations
            user: Current user information
        """
        super().__init__(parent)
        self.parent = parent
        self.debt_controller = debt_controller
        self.customer_controller = customer_controller
        self.payment_controller = payment_controller
        self.user = user
        
        # Current debt
        self.current_debt = None
        
        # Variables
        self.customer_filter_var = tk.StringVar(value="All Customers")
        self.status_filter_var = tk.StringVar(value="All")
        self.payment_amount_var = tk.StringVar(value="0.00")
        self.payment_method_var = tk.StringVar(value="CASH")
        
        # Create UI components
        self._create_widgets()
        
        # Initial data load
        self._load_customers()
        self._refresh_debts()
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with two panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel 1: Filters and list
        self.debts_list_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.debts_list_frame, weight=2)
        
        # Panel 2: Debt details and payment
        self.debt_detail_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.debt_detail_frame, weight=1)
        
        # Set up debts list panel
        self._create_debts_list_panel()
        
        # Set up debt details panel
        self._create_debt_detail_panel()
    
    def _create_debts_list_panel(self):
        """Create and populate the debts list panel."""
        # Header
        header_label = ttk.Label(
            self.debts_list_frame, 
            text="Customer Debts", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Filters frame
        filters_frame = ttk.LabelFrame(self.debts_list_frame, text="Filters", padding=10)
        filters_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Customer filter
        customer_frame = ttk.Frame(filters_frame)
        customer_frame.pack(fill=tk.X, pady=5)
        
        customer_label = ttk.Label(customer_frame, text="Customer:")
        customer_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.customer_combobox = ttk.Combobox(
            customer_frame, 
            textvariable=self.customer_filter_var,
            state="readonly"
        )
        self.customer_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status filter
        status_frame = ttk.Frame(filters_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        status_label = ttk.Label(status_frame, text="Status:")
        status_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.status_combobox = ttk.Combobox(
            status_frame, 
            textvariable=self.status_filter_var,
            values=["All", "Outstanding", "Paid"],
            state="readonly"
        )
        self.status_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_combobox.current(0)
        
        # Filter buttons
        button_frame = ttk.Frame(filters_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        apply_button = ttk.Button(
            button_frame, 
            text="Apply Filters", 
            command=self._refresh_debts,
            style="Primary.TButton"
        )
        apply_button.pack(side=tk.LEFT)
        
        reset_button = ttk.Button(
            button_frame, 
            text="Reset Filters", 
            command=self._reset_filters
        )
        reset_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Debts list
        list_frame = ttk.Frame(self.debts_list_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the debts list
        self.debts_tree = ttk.Treeview(
            list_frame, 
            columns=("customer", "date", "description", "amount", "remaining", "status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.debts_tree.heading("customer", text="Customer")
        self.debts_tree.heading("date", text="Date")
        self.debts_tree.heading("description", text="Description")
        self.debts_tree.heading("amount", text="Original")
        self.debts_tree.heading("remaining", text="Remaining")
        self.debts_tree.heading("status", text="Status")
        
        self.debts_tree.column("customer", width=150)
        self.debts_tree.column("date", width=100)
        self.debts_tree.column("description", width=200)
        self.debts_tree.column("amount", width=80, anchor=tk.E)
        self.debts_tree.column("remaining", width=80, anchor=tk.E)
        self.debts_tree.column("status", width=100, anchor=tk.CENTER)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.debts_tree.yview)
        self.debts_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.debts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.debts_tree.bind("<<TreeviewSelect>>", self._on_debt_selected)
        
        # Summary frame
        summary_frame = ttk.Frame(self.debts_list_frame)
        summary_frame.pack(fill=tk.X, pady=5)
        
        self.total_label = ttk.Label(
            summary_frame, 
            text=f"Total Outstanding: {format_currency(0)}", 
            font=("", 12, "bold")
        )
        self.total_label.pack(side=tk.RIGHT)
        
        self.count_label = ttk.Label(
            summary_frame, 
            text="Count: 0"
        )
        self.count_label.pack(side=tk.LEFT)
    
    def _create_debt_detail_panel(self):
        """Create and populate the debt detail panel."""
        # Header
        self.detail_header = ttk.Label(
            self.debt_detail_frame, 
            text="Debt Details", 
            style="Header.TLabel"
        )
        self.detail_header.pack(fill=tk.X, pady=(0, 10))
        
        # Details frame
        details_frame = ttk.LabelFrame(self.debt_detail_frame, text="Details", padding=10)
        details_frame.pack(fill=tk.X, pady=5)
        
        # Create detail grid
        details_grid = ttk.Frame(details_frame)
        details_grid.pack(fill=tk.X, padx=5, pady=5)
        
        row = 0
        
        # Debt ID
        ttk.Label(details_grid, text="Debt ID:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.debt_id_label = ttk.Label(details_grid, text="-")
        self.debt_id_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Customer
        ttk.Label(details_grid, text="Customer:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.customer_label = ttk.Label(details_grid, text="-")
        self.customer_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Date
        ttk.Label(details_grid, text="Date:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.date_label = ttk.Label(details_grid, text="-")
        self.date_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Description
        ttk.Label(details_grid, text="Description:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.description_label = ttk.Label(details_grid, text="-", wraplength=300)
        self.description_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Original Amount
        ttk.Label(details_grid, text="Original Amount:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.original_amount_label = ttk.Label(details_grid, text="-")
        self.original_amount_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Remaining Amount
        ttk.Label(details_grid, text="Remaining:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.remaining_amount_label = ttk.Label(details_grid, text="-")
        self.remaining_amount_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Status
        ttk.Label(details_grid, text="Status:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.status_label = ttk.Label(details_grid, text="-")
        self.status_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Invoice Reference
        ttk.Label(details_grid, text="Invoice Ref:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.invoice_label = ttk.Label(details_grid, text="-")
        self.invoice_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Created By
        ttk.Label(details_grid, text="Created By:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.created_by_label = ttk.Label(details_grid, text="-")
        self.created_by_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Payment History frame
        payments_frame = ttk.LabelFrame(self.debt_detail_frame, text="Payment History", padding=10)
        payments_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        payments_list_frame = ttk.Frame(payments_frame)
        payments_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the payments
        self.payments_tree = ttk.Treeview(
            payments_list_frame, 
            columns=("date", "amount", "method", "user"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.payments_tree.heading("date", text="Date")
        self.payments_tree.heading("amount", text="Amount")
        self.payments_tree.heading("method", text="Method")
        self.payments_tree.heading("user", text="User")
        
        self.payments_tree.column("date", width=100)
        self.payments_tree.column("amount", width=80, anchor=tk.E)
        self.payments_tree.column("method", width=100)
        self.payments_tree.column("user", width=100)
        
        # Add vertical scrollbar
        payments_scrollbar = ttk.Scrollbar(payments_list_frame, orient=tk.VERTICAL, command=self.payments_tree.yview)
        self.payments_tree.configure(yscrollcommand=payments_scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.payments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        payments_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Make a payment frame
        payment_frame = ttk.LabelFrame(self.debt_detail_frame, text="Make a Payment", padding=10)
        payment_frame.pack(fill=tk.X, pady=5)
        
        # Payment amount field
        amount_frame = ttk.Frame(payment_frame)
        amount_frame.pack(fill=tk.X, pady=5)
        
        amount_label = ttk.Label(amount_frame, text="Amount:")
        amount_label.pack(side=tk.LEFT, padx=(0, 5))
        
        amount_entry = ttk.Entry(amount_frame, textvariable=self.payment_amount_var, width=15)
        amount_entry.pack(side=tk.LEFT)
        
        # Payment method field
        method_frame = ttk.Frame(payment_frame)
        method_frame.pack(fill=tk.X, pady=5)
        
        method_label = ttk.Label(method_frame, text="Method:")
        method_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Get payment methods from config
        from config import PAYMENT_TYPES
        
        method_combobox = ttk.Combobox(
            method_frame, 
            textvariable=self.payment_method_var,
            values=PAYMENT_TYPES,
            state="readonly"
        )
        method_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        method_combobox.current(0)  # Default to first method
        
        # Full payment button
        full_payment_button = ttk.Button(
            payment_frame, 
            text="Pay Full Amount", 
            command=self._pay_full_amount
        )
        full_payment_button.pack(fill=tk.X, pady=5)
        
        # Payment button
        make_payment_button = ttk.Button(
            payment_frame, 
            text="Make Payment", 
            command=self._make_payment,
            style="Primary.TButton"
        )
        make_payment_button.pack(fill=tk.X, pady=5)
    
    def _load_customers(self):
        """Load customers for dropdown filter."""
        try:
            # Get all active customers
            customers = self.customer_controller.get_all_customers()
            
            # Prepare for dropdown
            customer_list = ["All Customers"]
            customer_list.extend([f"{c['full_name']} ({c['email']})" for c in customers])
            
            # Store customer data for reference
            self.customers = [None] + customers
            
            # Update combobox
            self.customer_combobox["values"] = customer_list
            self.customer_combobox.current(0)
            
        except Exception as e:
            self.show_error(f"Error loading customers: {str(e)}")
    
    def _refresh_debts(self):
        """Refresh the list of debts based on filters."""
        # Clear existing items
        for item in self.debts_tree.get_children():
            self.debts_tree.delete(item)
        
        try:
            # Get filter values
            customer_filter = self.customer_filter_var.get()
            status_filter = self.status_filter_var.get()
            
            # Get customer ID if specific customer selected
            customer_id = None
            if customer_filter != "All Customers" and self.customers:
                for i, customer in enumerate(self.customers):
                    if customer and f"{customer['full_name']} ({customer['email']})" == customer_filter:
                        customer_id = customer["customer_id"]
                        break
            
            # Get status boolean filter
            is_paid = None
            if status_filter == "Paid":
                is_paid = True
            elif status_filter == "Outstanding":
                is_paid = False
            
            # Get debts based on filters
            debts = self.debt_controller.search_debts(
                customer_id=customer_id,
                is_paid=is_paid,
                limit=1000
            )
            
            # Add to treeview
            total_outstanding = 0
            
            for debt in debts:
                # Format date
                date_str = debt["created_at"].strftime("%Y-%m-%d") if debt["created_at"] else "-"
                
                # Format amounts
                original_amount = debt["original_amount"] or 0
                remaining_amount = debt["remaining_amount"] or 0
                
                original_str = format_currency(original_amount)
                remaining_str = format_currency(remaining_amount)
                
                # Add to outstanding total if not paid
                if remaining_amount > 0:
                    total_outstanding += remaining_amount
                
                # Status text
                status = "Paid" if remaining_amount == 0 else "Outstanding"
                
                # Customer name
                customer_name = debt.get("customer_name", "-")
                
                # Description
                description = debt.get("description", "-")
                
                self.debts_tree.insert(
                    "", 
                    "end", 
                    values=(customer_name, date_str, description, original_str, remaining_str, status),
                    iid=debt["debt_id"]
                )
            
            # Update summary
            debt_count = len(debts)
            self.count_label.config(text=f"Count: {debt_count}")
            self.total_label.config(text=f"Total Outstanding: {format_currency(total_outstanding)}")
            
            # Clear details panel if no debts
            if debt_count == 0:
                self._clear_details()
            
        except Exception as e:
            self.show_error(f"Error loading debts: {str(e)}")
    
    def _reset_filters(self):
        """Reset filters to default values."""
        self.customer_filter_var.set("All Customers")
        self.status_filter_var.set("All")
        self._refresh_debts()
    
    def _on_debt_selected(self, event=None):
        """Handle debt selection in the treeview."""
        selected_items = self.debts_tree.selection()
        if not selected_items:
            return
        
        # Get the first selected item
        debt_id = selected_items[0]
        
        try:
            # Get debt details
            debt = self.debt_controller.get_debt_by_id(debt_id)
            if not debt:
                return
            
            # Store current debt
            self.current_debt = debt
            
            # Update header
            self.detail_header.config(text=f"Debt Details: {debt['debt_id']}")
            
            # Update debt details
            self.debt_id_label.config(text=debt["debt_id"])
            self.customer_label.config(text=debt.get("customer_name", "-"))
            
            # Format date
            date_str = debt["created_at"].strftime("%Y-%m-%d") if debt["created_at"] else "-"
            self.date_label.config(text=date_str)
            
            # Description
            self.description_label.config(text=debt.get("description", "-"))
            
            # Format amounts
            original_amount = debt["original_amount"] or 0
            remaining_amount = debt["remaining_amount"] or 0
            
            self.original_amount_label.config(text=format_currency(original_amount))
            self.remaining_amount_label.config(text=format_currency(remaining_amount))
            
            # Status
            status = "Paid" if remaining_amount == 0 else "Outstanding"
            self.status_label.config(text=status)
            
            # Invoice reference
            invoice_ref = debt.get("invoice_number", "-")
            self.invoice_label.config(text=invoice_ref)
            
            # Created by
            self.created_by_label.config(text=debt.get("created_by_name", "-"))
            
            # Set default payment amount to remaining amount
            self.payment_amount_var.set(f"{remaining_amount:.2f}")
            
            # Load payment history
            self._load_payment_history(debt_id)
            
        except Exception as e:
            self.show_error(f"Error loading debt details: {str(e)}")
    
    def _load_payment_history(self, debt_id):
        """Load payment history for the debt."""
        # Clear existing items
        for item in self.payments_tree.get_children():
            self.payments_tree.delete(item)
        
        try:
            # Get payments for this debt
            payments = self.debt_controller.get_debt_payments(debt_id)
            
            # Add to treeview
            for payment in payments:
                # Format date
                date_str = payment["payment_date"].strftime("%Y-%m-%d %H:%M") if payment["payment_date"] else "-"
                
                # Format amount
                amount_str = format_currency(payment["amount"]) if payment["amount"] is not None else "-"
                
                # Method
                method = payment["payment_method"].replace("_", " ").title() if payment["payment_method"] else "-"
                
                # User
                username = payment.get("user_name", "-")
                
                self.payments_tree.insert(
                    "", 
                    0,  # Insert at the top (most recent first)
                    values=(date_str, amount_str, method, username),
                    iid=payment["payment_id"]
                )
                
        except Exception as e:
            self.show_error(f"Error loading payment history: {str(e)}")
    
    def _clear_details(self):
        """Clear all details."""
        # Update header
        self.detail_header.config(text="Debt Details")
        
        # Clear debt details
        self.debt_id_label.config(text="-")
        self.customer_label.config(text="-")
        self.date_label.config(text="-")
        self.description_label.config(text="-")
        self.original_amount_label.config(text="-")
        self.remaining_amount_label.config(text="-")
        self.status_label.config(text="-")
        self.invoice_label.config(text="-")
        self.created_by_label.config(text="-")
        
        # Clear payment amount
        self.payment_amount_var.set("0.00")
        
        # Clear payment history
        for item in self.payments_tree.get_children():
            self.payments_tree.delete(item)
        
        # Clear current debt
        self.current_debt = None
    
    def _pay_full_amount(self):
        """Set the payment amount to the full remaining debt amount."""
        if not self.current_debt:
            self.show_warning("No debt selected")
            return
        
        # Set payment amount to remaining amount
        remaining_amount = self.current_debt["remaining_amount"] or 0
        self.payment_amount_var.set(f"{remaining_amount:.2f}")
    
    def _make_payment(self):
        """Make a payment on the current debt."""
        if not self.current_debt:
            self.show_warning("No debt selected")
            return
        
        # Check if debt is already paid
        if self.current_debt["remaining_amount"] == 0:
            self.show_warning("This debt is already fully paid")
            return
        
        try:
            # Validate payment amount
            try:
                payment_amount = float(self.payment_amount_var.get())
                if payment_amount <= 0:
                    self.show_warning("Payment amount must be positive")
                    return
                
                remaining_amount = self.current_debt["remaining_amount"] or 0
                if payment_amount > remaining_amount:
                    # Ask for confirmation for overpayment
                    confirm = self.show_confirmation(
                        f"The payment amount {format_currency(payment_amount)} is greater than the remaining debt {format_currency(remaining_amount)}. Proceed anyway?"
                    )
                    if not confirm:
                        return
            except ValueError:
                self.show_warning("Please enter a valid payment amount")
                return
            
            # Get payment method
            payment_method = self.payment_method_var.get()
            
            # Make the payment
            payment = self.debt_controller.add_debt_payment(
                self.current_debt["debt_id"],
                payment_amount,
                payment_method,
                self.user["user_id"]
            )
            
            # Refresh debt details and payments
            self._refresh_debts()
            self._on_debt_selected()
            
            self.show_success(f"Payment of {format_currency(payment_amount)} recorded successfully")
            
        except Exception as e:
            self.show_error(f"Error making payment: {str(e)}")