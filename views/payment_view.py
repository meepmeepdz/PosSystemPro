"""
Payment view for POS application.
Handles payment management.
"""

import tkinter as tk
from tkinter import ttk
import datetime

from views.base_view import BaseView
from views.components.message_box import MessageBox
from utils.currency_formatter import format_currency


class PaymentView(BaseView):
    """View for payment management."""
    
    def __init__(self, parent, payment_controller, invoice_controller):
        """Initialize payment view.
        
        Args:
            parent: Parent widget
            payment_controller: Controller for payment operations
            invoice_controller: Controller for invoice operations
        """
        super().__init__(parent)
        self.parent = parent
        self.payment_controller = payment_controller
        self.invoice_controller = invoice_controller
        
        # Current payment
        self.current_payment = None
        
        # Variables
        self.date_from_var = tk.StringVar()
        self.date_to_var = tk.StringVar()
        self.payment_method_var = tk.StringVar(value="All")
        
        # Create UI components
        self._create_widgets()
        
        # Set default date range (last 7 days)
        self._set_default_date_range()
        
        # Initial data load
        self._refresh_payments()
    
    def _set_default_date_range(self):
        """Set default date range to last 7 days."""
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)
        
        self.date_from_var.set(week_ago.strftime("%Y-%m-%d"))
        self.date_to_var.set(today.strftime("%Y-%m-%d"))
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with two panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel 1: Filters and list
        self.payments_list_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.payments_list_frame, weight=2)
        
        # Panel 2: Payment details
        self.payment_detail_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.payment_detail_frame, weight=1)
        
        # Set up payments list panel
        self._create_payments_list_panel()
        
        # Set up payment details panel
        self._create_payment_detail_panel()
    
    def _create_payments_list_panel(self):
        """Create and populate the payments list panel."""
        # Header
        header_label = ttk.Label(
            self.payments_list_frame, 
            text="Payments", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Filters frame
        filters_frame = ttk.LabelFrame(self.payments_list_frame, text="Filters", padding=10)
        filters_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Date range filter
        date_frame = ttk.Frame(filters_frame)
        date_frame.pack(fill=tk.X, pady=5)
        
        from_label = ttk.Label(date_frame, text="From:")
        from_label.pack(side=tk.LEFT, padx=(0, 5))
        
        from_entry = ttk.Entry(date_frame, textvariable=self.date_from_var, width=12)
        from_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        to_label = ttk.Label(date_frame, text="To:")
        to_label.pack(side=tk.LEFT, padx=(0, 5))
        
        to_entry = ttk.Entry(date_frame, textvariable=self.date_to_var, width=12)
        to_entry.pack(side=tk.LEFT)
        
        # Payment method filter
        method_frame = ttk.Frame(filters_frame)
        method_frame.pack(fill=tk.X, pady=5)
        
        method_label = ttk.Label(method_frame, text="Payment Method:")
        method_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Get payment methods from config
        from config import PAYMENT_TYPES
        payment_methods = ["All"] + PAYMENT_TYPES
        
        method_combobox = ttk.Combobox(
            method_frame, 
            textvariable=self.payment_method_var,
            values=payment_methods,
            state="readonly"
        )
        method_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Filter/Refresh button
        button_frame = ttk.Frame(filters_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        refresh_button = ttk.Button(
            button_frame, 
            text="Apply Filters", 
            command=self._refresh_payments,
            style="Primary.TButton"
        )
        refresh_button.pack(side=tk.LEFT)
        
        reset_button = ttk.Button(
            button_frame, 
            text="Reset Filters", 
            command=self._reset_filters
        )
        reset_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Payments list
        list_frame = ttk.Frame(self.payments_list_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the payments list
        self.payments_tree = ttk.Treeview(
            list_frame, 
            columns=("date", "invoice", "amount", "method", "user"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.payments_tree.heading("date", text="Date")
        self.payments_tree.heading("invoice", text="Invoice #")
        self.payments_tree.heading("amount", text="Amount")
        self.payments_tree.heading("method", text="Method")
        self.payments_tree.heading("user", text="User")
        
        self.payments_tree.column("date", width=150)
        self.payments_tree.column("invoice", width=100)
        self.payments_tree.column("amount", width=100, anchor=tk.E)
        self.payments_tree.column("method", width=120)
        self.payments_tree.column("user", width=120)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.payments_tree.yview)
        self.payments_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.payments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.payments_tree.bind("<<TreeviewSelect>>", self._on_payment_selected)
        
        # Summary frame
        summary_frame = ttk.Frame(self.payments_list_frame)
        summary_frame.pack(fill=tk.X, pady=5)
        
        self.total_label = ttk.Label(
            summary_frame, 
            text=f"Total: {format_currency(0)}", 
            font=("", 12, "bold")
        )
        self.total_label.pack(side=tk.RIGHT)
        
        self.count_label = ttk.Label(
            summary_frame, 
            text="Count: 0"
        )
        self.count_label.pack(side=tk.LEFT)
    
    def _create_payment_detail_panel(self):
        """Create and populate the payment detail panel."""
        # Header
        self.detail_header = ttk.Label(
            self.payment_detail_frame, 
            text="Payment Details", 
            style="Header.TLabel"
        )
        self.detail_header.pack(fill=tk.X, pady=(0, 10))
        
        # Details frame
        details_frame = ttk.LabelFrame(self.payment_detail_frame, text="Details", padding=10)
        details_frame.pack(fill=tk.X, pady=5)
        
        # Create detail grid
        details_grid = ttk.Frame(details_frame)
        details_grid.pack(fill=tk.X, padx=5, pady=5)
        
        row = 0
        
        # Payment ID
        ttk.Label(details_grid, text="Payment ID:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.payment_id_label = ttk.Label(details_grid, text="-")
        self.payment_id_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Date/Time
        ttk.Label(details_grid, text="Date/Time:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.payment_date_label = ttk.Label(details_grid, text="-")
        self.payment_date_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Amount
        ttk.Label(details_grid, text="Amount:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.payment_amount_label = ttk.Label(details_grid, text="-")
        self.payment_amount_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Method
        ttk.Label(details_grid, text="Method:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.payment_method_label = ttk.Label(details_grid, text="-")
        self.payment_method_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Processed By
        ttk.Label(details_grid, text="Processed By:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.payment_user_label = ttk.Label(details_grid, text="-")
        self.payment_user_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Reference Number
        ttk.Label(details_grid, text="Reference:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.payment_reference_label = ttk.Label(details_grid, text="-")
        self.payment_reference_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Notes
        ttk.Label(details_grid, text="Notes:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.payment_notes_label = ttk.Label(details_grid, text="-", wraplength=300)
        self.payment_notes_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Related invoice frame
        invoice_frame = ttk.LabelFrame(self.payment_detail_frame, text="Related Invoice", padding=10)
        invoice_frame.pack(fill=tk.X, pady=5)
        
        # Invoice grid
        invoice_grid = ttk.Frame(invoice_frame)
        invoice_grid.pack(fill=tk.X, padx=5, pady=5)
        
        row = 0
        
        # Invoice Number
        ttk.Label(invoice_grid, text="Invoice #:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.invoice_number_label = ttk.Label(invoice_grid, text="-")
        self.invoice_number_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Invoice Date
        ttk.Label(invoice_grid, text="Date:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.invoice_date_label = ttk.Label(invoice_grid, text="-")
        self.invoice_date_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Invoice Total
        ttk.Label(invoice_grid, text="Total:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.invoice_total_label = ttk.Label(invoice_grid, text="-")
        self.invoice_total_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Invoice Status
        ttk.Label(invoice_grid, text="Status:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.invoice_status_label = ttk.Label(invoice_grid, text="-")
        self.invoice_status_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Invoice Customer
        ttk.Label(invoice_grid, text="Customer:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.invoice_customer_label = ttk.Label(invoice_grid, text="-")
        self.invoice_customer_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # View invoice button
        button_frame = ttk.Frame(invoice_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        view_invoice_button = ttk.Button(
            button_frame, 
            text="View Invoice Details", 
            command=self._view_invoice
        )
        view_invoice_button.pack(side=tk.LEFT)
        
        print_receipt_button = ttk.Button(
            button_frame, 
            text="Print Receipt", 
            command=self._print_receipt
        )
        print_receipt_button.pack(side=tk.RIGHT)
    
    def _refresh_payments(self):
        """Refresh the list of payments based on filters."""
        # Clear existing items
        for item in self.payments_tree.get_children():
            self.payments_tree.delete(item)
        
        try:
            # Get filter values
            date_from = self.date_from_var.get().strip()
            date_to = self.date_to_var.get().strip()
            payment_method = self.payment_method_var.get()
            
            # Convert dates
            from_date = None
            to_date = None
            
            if date_from:
                try:
                    from_date = datetime.datetime.strptime(date_from, "%Y-%m-%d").date()
                except ValueError:
                    self.show_warning("Invalid 'From' date format. Use YYYY-MM-DD")
                    return
            
            if date_to:
                try:
                    to_date = datetime.datetime.strptime(date_to, "%Y-%m-%d").date()
                except ValueError:
                    self.show_warning("Invalid 'To' date format. Use YYYY-MM-DD")
                    return
            
            # Validate dates
            if from_date and to_date and from_date > to_date:
                self.show_warning("'From' date cannot be after 'To' date")
                return
            
            # Get method filter
            method_filter = None if payment_method == "All" else payment_method
            
            # Get payments based on filters
            payments = self.payment_controller.search_payments(
                date_from=from_date,
                date_to=to_date,
                payment_method=method_filter,
                limit=1000
            )
            
            # Add to treeview
            total_amount = 0
            
            for payment in payments:
                # Format date
                date_str = payment["payment_date"].strftime("%Y-%m-%d %H:%M") if payment["payment_date"] else "-"
                
                # Format amount
                amount = payment["amount"] or 0
                amount_str = format_currency(amount)
                total_amount += amount
                
                # Format method
                method = payment["payment_method"].replace("_", " ").title() if payment["payment_method"] else "-"
                
                # Get invoice number
                invoice_number = payment.get("invoice_number", "-")
                
                # Get username
                username = payment.get("user_name", "-")
                
                self.payments_tree.insert(
                    "", 
                    "end", 
                    values=(date_str, invoice_number, amount_str, method, username),
                    iid=payment["payment_id"]
                )
            
            # Update summary
            payment_count = len(payments)
            self.count_label.config(text=f"Count: {payment_count}")
            self.total_label.config(text=f"Total: {format_currency(total_amount)}")
            
            # Clear details panel if no payments
            if payment_count == 0:
                self._clear_details()
            
        except Exception as e:
            self.show_error(f"Error loading payments: {str(e)}")
    
    def _reset_filters(self):
        """Reset filters to default values."""
        self._set_default_date_range()
        self.payment_method_var.set("All")
        self._refresh_payments()
    
    def _on_payment_selected(self, event=None):
        """Handle payment selection in the treeview."""
        selected_items = self.payments_tree.selection()
        if not selected_items:
            return
        
        # Get the first selected item
        payment_id = selected_items[0]
        
        try:
            # Get payment details
            payment = self.payment_controller.get_payment_by_id(payment_id)
            if not payment:
                return
            
            # Store current payment
            self.current_payment = payment
            
            # Update header
            self.detail_header.config(text=f"Payment Details: {payment['payment_id']}")
            
            # Update payment details
            self.payment_id_label.config(text=payment["payment_id"])
            
            # Format date
            date_str = payment["payment_date"].strftime("%Y-%m-%d %H:%M:%S") if payment["payment_date"] else "-"
            self.payment_date_label.config(text=date_str)
            
            # Format amount
            amount_str = format_currency(payment["amount"]) if payment["amount"] is not None else "-"
            self.payment_amount_label.config(text=amount_str)
            
            # Format method
            method = payment["payment_method"].replace("_", " ").title() if payment["payment_method"] else "-"
            self.payment_method_label.config(text=method)
            
            # User
            self.payment_user_label.config(text=payment.get("user_name", "-"))
            
            # Reference
            self.payment_reference_label.config(text=payment.get("reference", "-"))
            
            # Notes
            self.payment_notes_label.config(text=payment.get("notes", "-"))
            
            # Get related invoice if available
            if payment.get("invoice_id"):
                try:
                    invoice = self.invoice_controller.get_invoice_by_id(payment["invoice_id"])
                    if invoice:
                        # Invoice number
                        self.invoice_number_label.config(text=invoice["invoice_number"])
                        
                        # Invoice date
                        invoice_date = invoice["created_at"].strftime("%Y-%m-%d") if invoice["created_at"] else "-"
                        self.invoice_date_label.config(text=invoice_date)
                        
                        # Invoice total
                        invoice_total = format_currency(invoice["total_amount"]) if invoice["total_amount"] is not None else "-"
                        self.invoice_total_label.config(text=invoice_total)
                        
                        # Invoice status
                        self.invoice_status_label.config(text=invoice["status"])
                        
                        # Customer
                        self.invoice_customer_label.config(text=invoice.get("customer_name", "-"))
                    else:
                        self._clear_invoice_details()
                except Exception as e:
                    self.show_error(f"Error loading invoice details: {str(e)}")
                    self._clear_invoice_details()
            else:
                self._clear_invoice_details()
            
        except Exception as e:
            self.show_error(f"Error loading payment details: {str(e)}")
    
    def _clear_details(self):
        """Clear all details."""
        # Update header
        self.detail_header.config(text="Payment Details")
        
        # Clear payment details
        self.payment_id_label.config(text="-")
        self.payment_date_label.config(text="-")
        self.payment_amount_label.config(text="-")
        self.payment_method_label.config(text="-")
        self.payment_user_label.config(text="-")
        self.payment_reference_label.config(text="-")
        self.payment_notes_label.config(text="-")
        
        # Clear invoice details
        self._clear_invoice_details()
        
        # Clear current payment
        self.current_payment = None
    
    def _clear_invoice_details(self):
        """Clear invoice details."""
        self.invoice_number_label.config(text="-")
        self.invoice_date_label.config(text="-")
        self.invoice_total_label.config(text="-")
        self.invoice_status_label.config(text="-")
        self.invoice_customer_label.config(text="-")
    
    def _view_invoice(self):
        """View the related invoice details."""
        if not self.current_payment or not self.current_payment.get("invoice_id"):
            self.show_warning("No invoice associated with this payment")
            return
        
        # Show a message that this would normally navigate to the invoice view
        self.show_info(
            f"In a full implementation, this would open the invoice view for invoice ID: {self.current_payment['invoice_id']}"
        )
    
    def _print_receipt(self):
        """Print a receipt for the payment."""
        if not self.current_payment:
            self.show_warning("No payment selected")
            return
        
        if not self.current_payment.get("invoice_id"):
            self.show_warning("No invoice associated with this payment")
            return
        
        # Show a message that this would normally print a receipt
        self.show_info(
            f"In a full implementation, this would print a receipt for invoice ID: {self.current_payment['invoice_id']}"
        )