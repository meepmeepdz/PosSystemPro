"""
Customer view for POS application.
Handles customer management.
"""

import tkinter as tk
from tkinter import ttk

from views.base_view import BaseView
from views.components.message_box import MessageBox
from views.components.form_widgets import LabelInput, FormFrame


class CustomerView(BaseView):
    """View for customer management."""
    
    def __init__(self, parent, customer_controller, invoice_controller, debt_controller):
        """Initialize customer view.
        
        Args:
            parent: Parent widget
            customer_controller: Controller for customer operations
            invoice_controller: Controller for invoice operations
            debt_controller: Controller for debt operations
        """
        super().__init__(parent)
        self.parent = parent
        self.customer_controller = customer_controller
        self.invoice_controller = invoice_controller
        self.debt_controller = debt_controller
        
        # Current customer
        self.current_customer = None
        
        # Variables
        self.customer_search_var = tk.StringVar()
        self.show_inactive_var = tk.BooleanVar(value=False)
        
        # Form variables
        self.full_name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.city_var = tk.StringVar()
        self.postal_code_var = tk.StringVar()
        self.country_var = tk.StringVar()
        self.tax_id_var = tk.StringVar()
        self.notes_var = tk.StringVar()
        self.is_active_var = tk.BooleanVar(value=True)
        
        # Create UI components
        self._create_widgets()
        
        # Initial data population
        self._refresh_customer_list()
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with two panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel 1: Customer list
        self.customer_list_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.customer_list_frame, weight=1)
        
        # Panel 2: Customer details/edit and tabs for related info
        self.customer_detail_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.customer_detail_frame, weight=2)
        
        # Set up customer list panel
        self._create_customer_list_panel()
        
        # Set up customer details panel with tabs
        self._create_customer_detail_panel()
    
    def _create_customer_list_panel(self):
        """Create and populate the customer list panel."""
        # Header
        header_label = ttk.Label(
            self.customer_list_frame, 
            text="Customers", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Search and filter toolbar
        toolbar_frame = ttk.Frame(self.customer_list_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        search_label = ttk.Label(toolbar_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.customer_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        search_button = ttk.Button(
            toolbar_frame, 
            text="Search", 
            command=self._refresh_customer_list
        )
        search_button.pack(side=tk.LEFT, padx=5)
        
        # Show inactive checkbox
        show_inactive_check = ttk.Checkbutton(
            toolbar_frame, 
            text="Show inactive", 
            variable=self.show_inactive_var,
            command=self._refresh_customer_list
        )
        show_inactive_check.pack(side=tk.LEFT, padx=(10, 0))
        
        # Refresh button
        refresh_button = ttk.Button(
            toolbar_frame, 
            text="Refresh", 
            command=self._refresh_customer_list
        )
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Customer list
        list_frame = ttk.Frame(self.customer_list_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the customer list
        self.customer_tree = ttk.Treeview(
            list_frame, 
            columns=("name", "email", "phone", "status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.customer_tree.heading("name", text="Name")
        self.customer_tree.heading("email", text="Email")
        self.customer_tree.heading("phone", text="Phone")
        self.customer_tree.heading("status", text="Status")
        
        self.customer_tree.column("name", width=150)
        self.customer_tree.column("email", width=150)
        self.customer_tree.column("phone", width=100)
        self.customer_tree.column("status", width=80, anchor=tk.CENTER)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.customer_tree.yview)
        self.customer_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.customer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.customer_tree.bind("<<TreeviewSelect>>", self._on_customer_selected)
        
        # Action buttons below the list
        action_frame = ttk.Frame(self.customer_list_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        new_button = ttk.Button(
            action_frame, 
            text="New Customer", 
            command=self._create_new_customer,
            style="Primary.TButton"
        )
        new_button.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_button = ttk.Button(
            action_frame, 
            text="Delete", 
            command=self._delete_selected_customer,
            style="Danger.TButton"
        )
        delete_button.pack(side=tk.LEFT)
    
    def _create_customer_detail_panel(self):
        """Create and populate the customer detail panel with tabs."""
        # Header
        self.detail_header = ttk.Label(
            self.customer_detail_frame, 
            text="Customer Details", 
            style="Header.TLabel"
        )
        self.detail_header.pack(fill=tk.X, pady=(0, 10))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.customer_detail_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Customer info
        self.info_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.info_tab, text="Information")
        
        # Tab 2: Invoices
        self.invoices_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.invoices_tab, text="Invoices")
        
        # Tab 3: Debts
        self.debts_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.debts_tab, text="Debts")
        
        # Set up info tab with form
        self._create_info_tab()
        
        # Set up invoices tab
        self._create_invoices_tab()
        
        # Set up debts tab
        self._create_debts_tab()
        
        # Button frame at the bottom
        button_frame = ttk.Frame(self.customer_detail_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        save_button = ttk.Button(
            button_frame, 
            text="Save Changes", 
            command=self._save_customer,
            style="Primary.TButton"
        )
        save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self._cancel_edit
        )
        cancel_button.pack(side=tk.LEFT)
    
    def _create_info_tab(self):
        """Create the customer information tab."""
        try:
            # Create a scrollable frame for the form
            container, scrollable_frame = self.create_scrolled_frame(self.info_tab)
            if container and scrollable_frame:
                container.pack(fill=tk.BOTH, expand=True, pady=5)
                
                # Form frame
                form_frame = FormFrame(scrollable_frame)
                form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            else:
                self.show_error("Error creating scrollable frame")
                return
        except Exception as e:
            self.show_error(f"Error creating customer information tab: {str(e)}")
            return
        
        # Basic information section
        form_frame.add_section_header("Basic Information")
        
        # Full name field
        form_frame.add_field("Full Name:", self.full_name_var, input_args={"width": 40})
        
        # Email field
        form_frame.add_field("Email:", self.email_var, input_args={"width": 40})
        
        # Phone field
        form_frame.add_field("Phone:", self.phone_var, input_args={"width": 20})
        
        # Address section
        form_frame.add_section_header("Address")
        
        # Address field
        address_label = ttk.Label(form_frame, text="Address:")
        address_label.pack(anchor=tk.W, pady=(5, 0))
        
        address_frame = ttk.Frame(form_frame)
        address_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.address_text = tk.Text(address_frame, height=3, width=40)
        self.address_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        address_scrollbar = ttk.Scrollbar(address_frame, orient=tk.VERTICAL, command=self.address_text.yview)
        self.address_text.configure(yscrollcommand=address_scrollbar.set)
        address_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # City, postal code, country
        form_frame.add_field("City:", self.city_var, input_args={"width": 30})
        form_frame.add_field("Postal Code:", self.postal_code_var, input_args={"width": 15})
        form_frame.add_field("Country:", self.country_var, input_args={"width": 30})
        
        # Additional information section
        form_frame.add_section_header("Additional Information")
        
        # Tax ID field
        form_frame.add_field("Tax ID:", self.tax_id_var, input_args={"width": 20})
        
        # Notes field
        notes_label = ttk.Label(form_frame, text="Notes:")
        notes_label.pack(anchor=tk.W, pady=(5, 0))
        
        notes_frame = ttk.Frame(form_frame)
        notes_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.notes_text = tk.Text(notes_frame, height=3, width=40)
        self.notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        notes_scrollbar = ttk.Scrollbar(notes_frame, orient=tk.VERTICAL, command=self.notes_text.yview)
        self.notes_text.configure(yscrollcommand=notes_scrollbar.set)
        notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status section
        form_frame.add_section_header("Status")
        
        # Is active field
        is_active_frame = ttk.Frame(form_frame)
        is_active_frame.pack(fill=tk.X, pady=5)
        
        is_active_label = ttk.Label(is_active_frame, text="Active:", width=15)
        is_active_label.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W)
        
        is_active_check = ttk.Checkbutton(is_active_frame, variable=self.is_active_var)
        is_active_check.pack(side=tk.LEFT)
    
    def _create_invoices_tab(self):
        """Create the customer invoices tab."""
        try:
            # Header and controls
            header_frame = ttk.Frame(self.invoices_tab, padding=5)
            header_frame.pack(fill=tk.X)
            
            header_label = ttk.Label(
                header_frame, 
                text="Customer Invoices", 
                style="Subheader.TLabel"
            )
            header_label.pack(side=tk.LEFT)
            
            refresh_button = ttk.Button(
                header_frame, 
                text="Refresh", 
                command=self._refresh_invoices
            )
            refresh_button.pack(side=tk.RIGHT)
            
            # Invoices list
            list_frame = ttk.Frame(self.invoices_tab, padding=5)
            list_frame.pack(fill=tk.BOTH, expand=True)
            
            # Create a treeview for the invoices
            self.invoices_tree = ttk.Treeview(
                list_frame, 
                columns=("invoice_number", "date", "amount", "status"),
                show="headings",
                selectmode="browse"
            )
            
            # Configure columns
            self.invoices_tree.heading("invoice_number", text="Invoice #")
            self.invoices_tree.heading("date", text="Date")
            self.invoices_tree.heading("amount", text="Amount")
            self.invoices_tree.heading("status", text="Status")
            
            self.invoices_tree.column("invoice_number", width=100)
            self.invoices_tree.column("date", width=150)
            self.invoices_tree.column("amount", width=100, anchor=tk.E)
            self.invoices_tree.column("status", width=100, anchor=tk.CENTER)
            
            # Add vertical scrollbar
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.invoices_tree.yview)
            self.invoices_tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack the treeview and scrollbar
            self.invoices_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Info label for no customer selected
            self.invoices_info_label = ttk.Label(
                self.invoices_tab, 
                text="Select a customer to view their invoices", 
                padding=10
            )
            self.invoices_info_label.pack(fill=tk.X)
            
        except Exception as e:
            self.show_error(f"Error creating invoices tab: {str(e)}")
    
    def _create_debts_tab(self):
        """Create the customer debts tab."""
        try:
            # Header and controls
            header_frame = ttk.Frame(self.debts_tab, padding=5)
            header_frame.pack(fill=tk.X)
            
            header_label = ttk.Label(
                header_frame, 
                text="Customer Debts", 
                style="Subheader.TLabel"
            )
            header_label.pack(side=tk.LEFT)
            
            refresh_button = ttk.Button(
                header_frame, 
                text="Refresh", 
                command=self._refresh_debts
            )
            refresh_button.pack(side=tk.RIGHT)
            
            # Debts list
            list_frame = ttk.Frame(self.debts_tab, padding=5)
            list_frame.pack(fill=tk.BOTH, expand=True)
            
            # Create a treeview for the debts
            self.debts_tree = ttk.Treeview(
                list_frame, 
                columns=("date", "description", "amount", "remaining", "status"),
                show="headings",
                selectmode="browse"
            )
            
            # Configure columns
            self.debts_tree.heading("date", text="Date")
            self.debts_tree.heading("description", text="Description")
            self.debts_tree.heading("amount", text="Original Amount")
            self.debts_tree.heading("remaining", text="Remaining")
            self.debts_tree.heading("status", text="Status")
            
            self.debts_tree.column("date", width=100)
            self.debts_tree.column("description", width=200)
            self.debts_tree.column("amount", width=100, anchor=tk.E)
            self.debts_tree.column("remaining", width=100, anchor=tk.E)
            self.debts_tree.column("status", width=100, anchor=tk.CENTER)
            
            # Add vertical scrollbar
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.debts_tree.yview)
            self.debts_tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack the treeview and scrollbar
            self.debts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Summary frame
            summary_frame = ttk.Frame(self.debts_tab, padding=10)
            summary_frame.pack(fill=tk.X)
            
            self.total_debt_label = ttk.Label(
                summary_frame, 
                text="Total debt: $0.00", 
                font=("", 11, "bold")
            )
            self.total_debt_label.pack(side=tk.RIGHT)
            
            # Info label for no customer selected
            self.debts_info_label = ttk.Label(
                self.debts_tab, 
                text="Select a customer to view their debts", 
                padding=10
            )
            self.debts_info_label.pack(fill=tk.X)
            
        except Exception as e:
            self.show_error(f"Error creating debts tab: {str(e)}")
    
    def _refresh_customer_list(self):
        """Refresh the list of customers."""
        # Clear existing items
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        
        try:
            # Get search and filter values
            search_term = self.customer_search_var.get().strip()
            include_inactive = self.show_inactive_var.get()
            
            # Get customers based on search and filters
            customers = self.customer_controller.search_customers(
                search_term=search_term if search_term else None,
                include_inactive=include_inactive
            )
            
            # Add to treeview
            for customer in customers:
                # Status text
                status = "Active" if customer.get("is_active", True) else "Inactive"
                
                self.customer_tree.insert(
                    "", 
                    "end", 
                    values=(customer["full_name"], customer["email"], customer["phone"], status),
                    iid=customer["customer_id"]
                )
                
        except Exception as e:
            self.show_error(f"Error loading customers: {str(e)}")
    
    def _on_customer_selected(self, event=None):
        """Handle customer selection in the treeview."""
        try:
            selected_items = self.customer_tree.selection()
            if not selected_items:
                return
            
            # Get the first selected item
            customer_id = selected_items[0]
            if not customer_id:
                return
            
            try:
                # Get customer details
                customer = self.customer_controller.get_customer_by_id(customer_id)
                if not customer:
                    self.show_warning("Customer details could not be loaded")
                    return
                
                # Store current customer
                self.current_customer = customer
                
                # Update header
                self.detail_header.config(text=f"Edit Customer: {customer['full_name']}")
                
                # Update form fields
                self.full_name_var.set(customer["full_name"])
                self.email_var.set(customer["email"] or "")
                self.phone_var.set(customer["phone"] or "")
                
                # Update address in text widget
                self.address_text.delete(1.0, tk.END)
                if customer.get("address"):
                    self.address_text.insert(1.0, customer["address"])
                
                # Update city, postal code, country
                self.city_var.set(customer.get("city", ""))
                self.postal_code_var.set(customer.get("postal_code", ""))
                self.country_var.set(customer.get("country", ""))
                
                # Update tax ID
                self.tax_id_var.set(customer.get("tax_id", ""))
                
                # Update notes in text widget
                self.notes_text.delete(1.0, tk.END)
                if customer.get("notes"):
                    self.notes_text.insert(1.0, customer["notes"])
                
                # Update status
                self.is_active_var.set(customer.get("is_active", True))
                
                # Hide info labels
                self.invoices_info_label.pack_forget()
                self.debts_info_label.pack_forget()
                
                # Only refresh related data if we have a valid customer with ID
                if "customer_id" in customer and customer["customer_id"]:
                    self._refresh_invoices()
                    self._refresh_debts()
                
            except Exception as e:
                self.show_error(f"Error loading customer details: {str(e)}")
                
        except Exception as e:
            self.show_error(f"Error selecting customer: {str(e)}")
    
    def _create_new_customer(self):
        """Create a new customer."""
        try:
            # Clear current selection
            self.customer_tree.selection_set([])
            
            # Clear form fields
            self.current_customer = None
            self.full_name_var.set("")
            self.email_var.set("")
            self.phone_var.set("")
            self.address_text.delete(1.0, tk.END)
            self.city_var.set("")
            self.postal_code_var.set("")
            self.country_var.set("")
            self.tax_id_var.set("")
            self.notes_text.delete(1.0, tk.END)
            self.is_active_var.set(True)
            
            # Update header
            self.detail_header.config(text="New Customer")
            
            # Clear invoices and debts
            for item in self.invoices_tree.get_children():
                self.invoices_tree.delete(item)
            
            for item in self.debts_tree.get_children():
                self.debts_tree.delete(item)
            
            # Show info labels
            self.invoices_info_label.pack(fill=tk.X)
            self.debts_info_label.pack(fill=tk.X)
            
            # Reset total debt
            self.total_debt_label.config(text="Total debt: $0.00")
            
            # Switch to info tab
            self.notebook.select(0)
            
        except Exception as e:
            self.show_error(f"Error creating new customer form: {str(e)}")
    
    def _save_customer(self):
        """Save the current customer."""
        try:
            # Get form data
            full_name = self.full_name_var.get().strip()
            email = self.email_var.get().strip() or None
            phone = self.phone_var.get().strip() or None
            address = self.address_text.get(1.0, tk.END).strip() or None
            city = self.city_var.get().strip() or None
            postal_code = self.postal_code_var.get().strip() or None
            country = self.country_var.get().strip() or None
            tax_id = self.tax_id_var.get().strip() or None
            notes = self.notes_text.get(1.0, tk.END).strip() or None
            is_active = self.is_active_var.get()
            
            # Validate
            if not full_name:
                self.show_warning("Customer name is required")
                return
            
            customer_data = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "address": address,
                "city": city,
                "postal_code": postal_code,
                "country": country,
                "tax_id": tax_id,
                "notes": notes,
                "is_active": is_active
            }
            
            try:
                if self.current_customer:
                    # Update existing customer
                    result = self.customer_controller.update_customer(
                        self.current_customer["customer_id"],
                        customer_data
                    )
                    success_message = "Customer updated successfully"
                else:
                    # Create new customer
                    result = self.customer_controller.create_customer(
                        full_name=customer_data["full_name"],
                        email=customer_data.get("email"),
                        phone=customer_data.get("phone"),
                        address=customer_data.get("address"),
                        tax_id=customer_data.get("tax_id"),
                        notes=customer_data.get("notes")
                    )
                    success_message = "Customer created successfully"
                
                # Refresh list and show success message
                self._refresh_customer_list()
                self.show_success(success_message)
                
                # Select the updated/created customer if available
                if result and "customer_id" in result:
                    try:
                        # Set selection
                        self.customer_tree.selection_set([result["customer_id"]])
                        
                        # Update current customer with result to avoid race condition
                        self.current_customer = result
                        
                        # Call customer selected to update UI
                        self._on_customer_selected()
                    except Exception as e:
                        self.show_error(f"Error selecting saved customer: {str(e)}")
            
            except Exception as e:
                self.show_error(f"Error during customer save operation: {str(e)}")
            
        except Exception as e:
            self.show_error(f"Error saving customer: {str(e)}")
    
    def _cancel_edit(self):
        """Cancel the current edit operation."""
        try:
            # Revert to selected customer or clear if none
            selected_items = self.customer_tree.selection()
            if selected_items:
                self._on_customer_selected()
            else:
                self._create_new_customer()
        except Exception as e:
            self.show_error(f"Error canceling edit: {str(e)}")
    
    def _delete_selected_customer(self):
        """Delete the selected customer."""
        try:
            selected_items = self.customer_tree.selection()
            if not selected_items:
                self.show_warning("Please select a customer to delete")
                return
            
            customer_id = selected_items[0]
            
            # Get the name for confirmation
            customer_values = self.customer_tree.item(customer_id, "values")
            if not customer_values or len(customer_values) < 1:
                self.show_warning("Cannot retrieve customer information")
                return
                
            customer_name = customer_values[0]
            
            # Confirm deletion
            confirm = self.show_confirmation(
                f"Are you sure you want to delete customer '{customer_name}'? "
                "This will remove all their data, including invoices and debts."
            )
            
            if not confirm:
                return
            
            try:
                # Try to delete
                result = self.customer_controller.delete_customer(customer_id)
                
                # Refresh and show message
                self._refresh_customer_list()
                self._create_new_customer()
                
                self.show_success("Customer deleted successfully")
                
            except Exception as e:
                self.show_error(f"Error deleting customer: {str(e)}")
                
        except Exception as e:
            self.show_error(f"Error preparing customer deletion: {str(e)}")
    
    def _refresh_invoices(self):
        """Refresh the list of invoices for the current customer."""
        try:
            # Clear existing items
            for item in self.invoices_tree.get_children():
                self.invoices_tree.delete(item)
            
            if not self.current_customer:
                return
            
            try:
                # Get invoices for this customer
                invoices = self.invoice_controller.get_customer_invoices(
                    self.current_customer["customer_id"]
                )
                
                # Add to treeview
                for invoice in invoices:
                    try:
                        # Format date
                        date_str = invoice["created_at"].strftime("%Y-%m-%d %H:%M") if invoice["created_at"] else ""
                        
                        # Format amount with error handling
                        amount_str = "$0.00"
                        if "total_amount" in invoice and invoice["total_amount"] is not None:
                            amount_str = f"${invoice['total_amount']:.2f}"
                        
                        # Add to treeview with error handling
                        self.invoices_tree.insert(
                            "", 
                            "end", 
                            values=(
                                invoice.get("invoice_number", ""),
                                date_str,
                                amount_str,
                                invoice.get("status", "")
                            ),
                            iid=invoice.get("invoice_id", "")
                        )
                        
                    except Exception as e:
                        # Skip this invoice if there's an error, but log it
                        print(f"Error processing invoice: {str(e)}")
                        continue
                    
            except Exception as e:
                self.show_error(f"Error loading customer invoices: {str(e)}")
                
        except Exception as e:
            self.show_error(f"Error refreshing invoice list: {str(e)}")
    
    def _refresh_debts(self):
        """Refresh the list of debts for the current customer."""
        try:
            # Clear existing items
            for item in self.debts_tree.get_children():
                self.debts_tree.delete(item)
            
            if not self.current_customer:
                return
            
            try:
                # Get debts for this customer
                debts = self.debt_controller.get_customer_debts(
                    self.current_customer["customer_id"]
                )
                
                # Calculate total debt with error handling
                try:
                    total_debt = sum(debt.get("remaining_amount", 0) or 0 for debt in debts)
                    # Update total label
                    self.total_debt_label.config(text=f"Total debt: ${total_debt:.2f}")
                except Exception as e:
                    self.total_debt_label.config(text="Total debt: $0.00")
                    print(f"Error calculating total debt: {str(e)}")
                
                # Add to treeview
                for debt in debts:
                    try:
                        # Format date with error handling
                        date_str = ""
                        if "created_at" in debt and debt["created_at"]:
                            try:
                                date_str = debt["created_at"].strftime("%Y-%m-%d")
                            except:
                                date_str = str(debt["created_at"])
                        
                        # Format amounts with error handling
                        amount_str = "$0.00"
                        if "original_amount" in debt and debt["original_amount"] is not None:
                            amount_str = f"${debt['original_amount']:.2f}"
                            
                        remaining_str = "$0.00"
                        if "remaining_amount" in debt and debt["remaining_amount"] is not None:
                            remaining_str = f"${debt['remaining_amount']:.2f}"
                        
                        # Status text with error handling
                        status = "Unknown"
                        if "remaining_amount" in debt:
                            remaining = debt["remaining_amount"] or 0
                            status = "Paid" if remaining == 0 else "Outstanding"
                        
                        # Insert with error handling
                        self.debts_tree.insert(
                            "", 
                            "end", 
                            values=(
                                date_str, 
                                debt.get("description", ""), 
                                amount_str, 
                                remaining_str, 
                                status
                            ),
                            iid=debt.get("debt_id", "")
                        )
                    except Exception as e:
                        # Skip this debt if there's an error, but log it
                        print(f"Error processing debt: {str(e)}")
                        continue
                    
            except Exception as e:
                self.show_error(f"Error loading customer debts: {str(e)}")
                
        except Exception as e:
            self.show_error(f"Error refreshing debt list: {str(e)}")