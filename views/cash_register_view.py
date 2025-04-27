"""
Cash register view for POS application.
Handles cash register operations.
"""

import tkinter as tk
from tkinter import ttk
import datetime

from views.base_view import BaseView
from views.components.message_box import MessageBox


class CashRegisterView(BaseView):
    """View for cash register management."""
    
    def __init__(self, parent, cash_register_controller, user):
        """Initialize cash register view.
        
        Args:
            parent: Parent widget
            cash_register_controller: Controller for cash register operations
            user: Current user information
        """
        super().__init__(parent)
        self.parent = parent
        self.cash_register_controller = cash_register_controller
        self.user = user
        
        # Current register
        self.current_register = None
        
        # Variables
        self.amount_var = tk.StringVar(value="0.00")
        self.reason_var = tk.StringVar()
        
        # Create UI components
        self._create_widgets()
        
        # Initial data
        self._check_register_status()
        self._load_register_history()
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with two panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel 1: Register status and operations
        self.register_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.register_panel, weight=1)
        
        # Panel 2: Register history
        self.history_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.history_panel, weight=2)
        
        # Set up register status panel
        self._create_register_panel()
        
        # Set up history panel
        self._create_history_panel()
    
    def _create_register_panel(self):
        """Create the register status and operations panel."""
        # Header
        header_label = ttk.Label(
            self.register_panel, 
            text="Cash Register", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 20))
        
        # Status section
        status_frame = ttk.LabelFrame(self.register_panel, text="Register Status", padding=10)
        status_frame.pack(fill=tk.X, pady=10)
        
        # Status indicator
        self.status_label = ttk.Label(
            status_frame, 
            text="Closed", 
            font=("", 14, "bold"),
            foreground="red"
        )
        self.status_label.pack(pady=5)
        
        # Current balance
        self.balance_label = ttk.Label(
            status_frame, 
            text="Current Balance: $0.00", 
            font=("", 12)
        )
        self.balance_label.pack(pady=5)
        
        # Open time
        self.open_time_label = ttk.Label(
            status_frame, 
            text="", 
            font=("", 10)
        )
        self.open_time_label.pack(pady=5)
        
        # Opened by
        self.opened_by_label = ttk.Label(
            status_frame, 
            text="", 
            font=("", 10)
        )
        self.opened_by_label.pack(pady=5)
        
        # Operations section
        operations_frame = ttk.LabelFrame(self.register_panel, text="Operations", padding=10)
        operations_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Amount field
        amount_frame = ttk.Frame(operations_frame)
        amount_frame.pack(fill=tk.X, pady=5)
        
        amount_label = ttk.Label(amount_frame, text="Amount:")
        amount_label.pack(side=tk.LEFT, padx=(0, 5))
        
        amount_entry = ttk.Entry(amount_frame, textvariable=self.amount_var, width=15)
        amount_entry.pack(side=tk.LEFT, padx=5)
        
        # Reason field
        reason_frame = ttk.Frame(operations_frame)
        reason_frame.pack(fill=tk.X, pady=5)
        
        reason_label = ttk.Label(reason_frame, text="Reason:")
        reason_label.pack(side=tk.LEFT, padx=(0, 5))
        
        reason_entry = ttk.Entry(reason_frame, textvariable=self.reason_var)
        reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Action buttons
        self.action_buttons_frame = ttk.Frame(operations_frame)
        self.action_buttons_frame.pack(fill=tk.X, pady=10)
        
        # These buttons will be created/updated based on register state
        self.open_button = ttk.Button(
            self.action_buttons_frame, 
            text="Open Register", 
            command=self._open_register,
            style="Primary.TButton"
        )
        
        self.add_cash_button = ttk.Button(
            self.action_buttons_frame, 
            text="Add Cash", 
            command=lambda: self._adjust_cash("add"),
            style="Success.TButton"
        )
        
        self.remove_cash_button = ttk.Button(
            self.action_buttons_frame, 
            text="Remove Cash", 
            command=lambda: self._adjust_cash("remove"),
            style="Danger.TButton"
        )
        
        self.close_button = ttk.Button(
            self.action_buttons_frame, 
            text="Close Register", 
            command=self._close_register,
            style="Secondary.TButton"
        )
        
        # Refresh button
        refresh_frame = ttk.Frame(self.register_panel)
        refresh_frame.pack(fill=tk.X, pady=10)
        
        refresh_button = ttk.Button(
            refresh_frame, 
            text="Refresh Status", 
            command=self._check_register_status
        )
        refresh_button.pack(side=tk.RIGHT)
    
    def _create_history_panel(self):
        """Create the register history panel."""
        # Header
        header_label = ttk.Label(
            self.history_panel, 
            text="Register History", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Filter controls
        filter_frame = ttk.Frame(self.history_panel)
        filter_frame.pack(fill=tk.X, pady=5)
        
        refresh_button = ttk.Button(
            filter_frame, 
            text="Refresh History", 
            command=self._load_register_history
        )
        refresh_button.pack(side=tk.RIGHT)
        
        # History list
        list_frame = ttk.Frame(self.history_panel)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the history
        self.history_tree = ttk.Treeview(
            list_frame, 
            columns=("date", "type", "amount", "balance", "user", "note"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.history_tree.heading("date", text="Date/Time")
        self.history_tree.heading("type", text="Action")
        self.history_tree.heading("amount", text="Amount")
        self.history_tree.heading("balance", text="Balance")
        self.history_tree.heading("user", text="User")
        self.history_tree.heading("note", text="Note")
        
        self.history_tree.column("date", width=140)
        self.history_tree.column("type", width=100)
        self.history_tree.column("amount", width=80, anchor=tk.E)
        self.history_tree.column("balance", width=80, anchor=tk.E)
        self.history_tree.column("user", width=100)
        self.history_tree.column("note", width=200)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Details frame
        details_frame = ttk.LabelFrame(self.history_panel, text="Transaction Details", padding=10)
        details_frame.pack(fill=tk.X, pady=10)
        
        # Create labels for details
        details_grid = ttk.Frame(details_frame)
        details_grid.pack(fill=tk.X, padx=5, pady=5)
        
        row = 0
        
        # Transaction ID
        ttk.Label(details_grid, text="Transaction ID:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.detail_id_label = ttk.Label(details_grid, text="-")
        self.detail_id_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Date/Time
        ttk.Label(details_grid, text="Date/Time:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.detail_datetime_label = ttk.Label(details_grid, text="-")
        self.detail_datetime_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Type
        ttk.Label(details_grid, text="Type:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.detail_type_label = ttk.Label(details_grid, text="-")
        self.detail_type_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Amount
        ttk.Label(details_grid, text="Amount:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.detail_amount_label = ttk.Label(details_grid, text="-")
        self.detail_amount_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Balance
        ttk.Label(details_grid, text="Balance After:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.detail_balance_label = ttk.Label(details_grid, text="-")
        self.detail_balance_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # User
        ttk.Label(details_grid, text="User:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.detail_user_label = ttk.Label(details_grid, text="-")
        self.detail_user_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Note
        ttk.Label(details_grid, text="Note:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.detail_note_label = ttk.Label(details_grid, text="-", wraplength=400)
        self.detail_note_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Bind selection event
        self.history_tree.bind("<<TreeviewSelect>>", self._on_history_selected)
    
    def _check_register_status(self):
        """Check the current register status and update UI."""
        try:
            # Get current register status
            register = self.cash_register_controller.get_current_register()
            self.current_register = register
            
            # Update UI based on status
            if register:
                # Register is open
                self.status_label.config(text="Open", foreground="green")
                self.balance_label.config(text=f"Current Balance: ${register['current_balance']:.2f}")
                
                # Format open time
                open_time = register["opened_at"].strftime("%Y-%m-%d %H:%M:%S") if register["opened_at"] else "-"
                self.open_time_label.config(text=f"Opened at: {open_time}")
                
                # Show opened by
                self.opened_by_label.config(text=f"Opened by: {register.get('opened_by_username', '-')}")
                
                # Update buttons
                self._show_open_register_buttons()
            else:
                # Register is closed
                self.status_label.config(text="Closed", foreground="red")
                self.balance_label.config(text="Current Balance: $0.00")
                self.open_time_label.config(text="")
                self.opened_by_label.config(text="")
                
                # Update buttons
                self._show_closed_register_buttons()
                
        except Exception as e:
            self.show_error(f"Error checking register status: {str(e)}")
    
    def _show_closed_register_buttons(self):
        """Show buttons for closed register state."""
        # Clear all buttons
        for widget in self.action_buttons_frame.winfo_children():
            widget.pack_forget()
        
        # Show only open button
        self.open_button.pack(fill=tk.X, pady=5)
    
    def _show_open_register_buttons(self):
        """Show buttons for open register state."""
        # Clear all buttons
        for widget in self.action_buttons_frame.winfo_children():
            widget.pack_forget()
        
        # Show operation buttons
        self.add_cash_button.pack(fill=tk.X, pady=5)
        self.remove_cash_button.pack(fill=tk.X, pady=5)
        self.close_button.pack(fill=tk.X, pady=5)
    
    def _load_register_history(self):
        """Load and display register transaction history."""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        try:
            # Get transaction history
            transactions = self.cash_register_controller.get_register_transactions(limit=100)
            
            # Add to treeview
            for transaction in transactions:
                # Format date/time
                date_str = transaction["created_at"].strftime("%Y-%m-%d %H:%M") if transaction["created_at"] else "-"
                
                # Format amount with sign
                amount = transaction["amount"]
                if transaction["transaction_type"] in ["OPEN", "ADD"]:
                    amount_str = f"+${amount:.2f}" if amount is not None else "-"
                else:
                    amount_str = f"-${abs(amount):.2f}" if amount is not None else "-"
                
                # Format balance
                balance_str = f"${transaction['balance_after']:.2f}" if transaction["balance_after"] is not None else "-"
                
                # Format type
                type_str = transaction["transaction_type"].capitalize().replace("_", " ")
                
                # Get username
                username = transaction.get("username", "-")
                
                # Get note/reason
                note = transaction.get("note", "")
                
                self.history_tree.insert(
                    "", 
                    0,  # Insert at the top (most recent first)
                    values=(date_str, type_str, amount_str, balance_str, username, note),
                    iid=transaction["transaction_id"]
                )
                
        except Exception as e:
            self.show_error(f"Error loading register history: {str(e)}")
    
    def _on_history_selected(self, event=None):
        """Handle selection in the history treeview."""
        selected_items = self.history_tree.selection()
        if not selected_items:
            return
        
        # Get the selected item
        transaction_id = selected_items[0]
        
        try:
            # Get transaction details
            transaction = self.cash_register_controller.get_transaction_by_id(transaction_id)
            if not transaction:
                return
            
            # Update detail labels
            self.detail_id_label.config(text=transaction["transaction_id"])
            
            # Format date/time
            date_str = transaction["created_at"].strftime("%Y-%m-%d %H:%M:%S") if transaction["created_at"] else "-"
            self.detail_datetime_label.config(text=date_str)
            
            # Format type
            type_str = transaction["transaction_type"].capitalize().replace("_", " ")
            self.detail_type_label.config(text=type_str)
            
            # Format amount with sign
            amount = transaction["amount"]
            if transaction["transaction_type"] in ["OPEN", "ADD"]:
                amount_str = f"+${amount:.2f}" if amount is not None else "-"
            else:
                amount_str = f"-${abs(amount):.2f}" if amount is not None else "-"
            self.detail_amount_label.config(text=amount_str)
            
            # Format balance
            balance_str = f"${transaction['balance_after']:.2f}" if transaction["balance_after"] is not None else "-"
            self.detail_balance_label.config(text=balance_str)
            
            # Show username
            self.detail_user_label.config(text=transaction.get("username", "-"))
            
            # Show note
            self.detail_note_label.config(text=transaction.get("note", "-"))
            
        except Exception as e:
            self.show_error(f"Error loading transaction details: {str(e)}")
    
    def _open_register(self):
        """Open the cash register."""
        try:
            # Validate amount
            try:
                amount = float(self.amount_var.get())
                if amount < 0:
                    self.show_warning("Initial amount cannot be negative")
                    return
            except ValueError:
                self.show_warning("Please enter a valid amount")
                return
            
            # Get reason
            reason = self.reason_var.get().strip() or "Opening balance"
            
            # Open the register
            register = self.cash_register_controller.open_register(
                self.user["user_id"],
                amount,
                reason
            )
            
            # Update UI
            self._check_register_status()
            self._load_register_history()
            
            # Clear fields
            self.amount_var.set("0.00")
            self.reason_var.set("")
            
            self.show_success("Cash register opened successfully")
            
        except Exception as e:
            self.show_error(f"Error opening register: {str(e)}")
    
    def _adjust_cash(self, adjustment_type):
        """Add or remove cash from the register.
        
        Args:
            adjustment_type (str): "add" or "remove"
        """
        if not self.current_register:
            self.show_warning("Cash register is not open")
            return
        
        try:
            # Validate amount
            try:
                amount = float(self.amount_var.get())
                if amount <= 0:
                    self.show_warning("Amount must be positive")
                    return
            except ValueError:
                self.show_warning("Please enter a valid amount")
                return
            
            # Check if removing more than available (for remove only)
            if adjustment_type == "remove" and amount > self.current_register["current_balance"]:
                self.show_warning(
                    f"Cannot remove ${amount:.2f} - only ${self.current_register['current_balance']:.2f} available"
                )
                return
            
            # Get reason
            reason = self.reason_var.get().strip()
            if not reason:
                self.show_warning("Please enter a reason for this adjustment")
                return
            
            # Make the adjustment
            if adjustment_type == "add":
                transaction = self.cash_register_controller.add_cash(
                    self.current_register["register_id"],
                    amount,
                    reason
                )
                success_message = f"Added ${amount:.2f} to the register"
            else:  # remove
                transaction = self.cash_register_controller.remove_cash(
                    self.current_register["register_id"],
                    amount,
                    reason
                )
                success_message = f"Removed ${amount:.2f} from the register"
            
            # Update UI
            self._check_register_status()
            self._load_register_history()
            
            # Clear fields
            self.amount_var.set("0.00")
            self.reason_var.set("")
            
            self.show_success(success_message)
            
        except Exception as e:
            self.show_error(f"Error adjusting cash: {str(e)}")
    
    def _close_register(self):
        """Close the cash register."""
        if not self.current_register:
            self.show_warning("Cash register is not open")
            return
        
        # Confirm closing
        confirm = self.show_confirmation(
            f"Are you sure you want to close the register? Current balance: ${self.current_register['current_balance']:.2f}"
        )
        if not confirm:
            return
        
        try:
            # Close the register
            result = self.cash_register_controller.close_register(
                self.current_register["register_id"],
                self.user["user_id"],
                "End of day closing"  # Default reason
            )
            
            # Update UI
            self._check_register_status()
            self._load_register_history()
            
            self.show_success("Cash register closed successfully")
            
        except Exception as e:
            self.show_error(f"Error closing register: {str(e)}")