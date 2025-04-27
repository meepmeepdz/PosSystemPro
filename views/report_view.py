"""
Report view for POS application.
Handles report generation and visualization.
"""

import tkinter as tk
from tkinter import ttk
import datetime
import csv
import os
import io
from tkinter.filedialog import asksaveasfilename

from views.base_view import BaseView
from views.components.message_box import MessageBox


class ReportView(BaseView):
    """View for report generation and visualization."""
    
    def __init__(self, parent, report_controller, user_controller, product_controller, customer_controller):
        """Initialize report view.
        
        Args:
            parent: Parent widget
            report_controller: Controller for report operations
            user_controller: Controller for user operations
            product_controller: Controller for product operations
            customer_controller: Controller for customer operations
        """
        super().__init__(parent)
        self.parent = parent
        self.report_controller = report_controller
        self.user_controller = user_controller
        self.product_controller = product_controller
        self.customer_controller = customer_controller
        
        # Variables
        self.date_from_var = tk.StringVar()
        self.date_to_var = tk.StringVar()
        self.user_filter_var = tk.StringVar(value="All Users")
        self.selected_report_var = tk.StringVar(value="Sales Summary")
        
        # Create UI components
        self._create_widgets()
        
        # Set default date range (last 30 days)
        self._set_default_date_range()
        
        # Load users for filter
        self._load_users()
    
    def _set_default_date_range(self):
        """Set default date range to last 30 days."""
        today = datetime.date.today()
        month_ago = today - datetime.timedelta(days=30)
        
        self.date_from_var.set(month_ago.strftime("%Y-%m-%d"))
        self.date_to_var.set(today.strftime("%Y-%m-%d"))
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Report selection panel
        selection_frame = ttk.LabelFrame(main_frame, text="Report Selection", padding=10)
        selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Report type selection
        report_type_frame = ttk.Frame(selection_frame)
        report_type_frame.pack(fill=tk.X, pady=5)
        
        report_type_label = ttk.Label(report_type_frame, text="Report Type:")
        report_type_label.pack(side=tk.LEFT, padx=(0, 5))
        
        report_types = [
            "Sales Summary",
            "Sales by Product",
            "Sales by Category",
            "Sales by Customer",
            "Sales by User",
            "Inventory Status",
            "Low Stock Report",
            "Product Performance"
        ]
        
        report_type_combobox = ttk.Combobox(
            report_type_frame, 
            textvariable=self.selected_report_var,
            values=report_types,
            state="readonly",
            width=30
        )
        report_type_combobox.pack(side=tk.LEFT)
        report_type_combobox.current(0)
        
        # Date range selection
        date_frame = ttk.Frame(selection_frame)
        date_frame.pack(fill=tk.X, pady=5)
        
        from_label = ttk.Label(date_frame, text="From:")
        from_label.pack(side=tk.LEFT, padx=(0, 5))
        
        from_entry = ttk.Entry(date_frame, textvariable=self.date_from_var, width=12)
        from_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        to_label = ttk.Label(date_frame, text="To:")
        to_label.pack(side=tk.LEFT, padx=(0, 5))
        
        to_entry = ttk.Entry(date_frame, textvariable=self.date_to_var, width=12)
        to_entry.pack(side=tk.LEFT)
        
        # Additional filters frame
        filter_frame = ttk.Frame(selection_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        # User filter
        user_label = ttk.Label(filter_frame, text="User:")
        user_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.user_combobox = ttk.Combobox(
            filter_frame, 
            textvariable=self.user_filter_var,
            state="readonly",
            width=20
        )
        self.user_combobox.pack(side=tk.LEFT)
        
        # Generate button
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        generate_button = ttk.Button(
            button_frame, 
            text="Generate Report", 
            command=self._generate_report,
            style="Primary.TButton"
        )
        generate_button.pack(side=tk.LEFT)
        
        export_button = ttk.Button(
            button_frame, 
            text="Export to CSV", 
            command=self._export_to_csv
        )
        export_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Report content frame
        self.report_frame = ttk.LabelFrame(main_frame, text="Report Results", padding=10)
        self.report_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Report header
        self.report_header = ttk.Label(
            self.report_frame, 
            text="", 
            font=("", 12, "bold")
        )
        self.report_header.pack(fill=tk.X, pady=(0, 10))
        
        # Create report content area with scrollbar
        content_frame = ttk.Frame(self.report_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a treeview for the report data
        self.report_tree = ttk.Treeview(
            content_frame,
            show="headings",
            selectmode="browse"
        )
        
        # Add vertical scrollbar
        y_scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=y_scrollbar.set)
        
        # Add horizontal scrollbar
        x_scrollbar = ttk.Scrollbar(content_frame, orient=tk.HORIZONTAL, command=self.report_tree.xview)
        self.report_tree.configure(xscrollcommand=x_scrollbar.set)
        
        # Pack the treeview and scrollbars
        self.report_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Summary frame
        self.summary_frame = ttk.Frame(self.report_frame)
        self.summary_frame.pack(fill=tk.X, pady=10)
        
        # Status bar at the bottom
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def _load_users(self):
        """Load users for filter dropdown."""
        try:
            users = self.user_controller.get_all_users()
            
            # Prepare for dropdown
            user_list = ["All Users"]
            user_list.extend([f"{u['username']} ({u['role']})" for u in users])
            
            # Update combobox
            self.user_combobox["values"] = user_list
            self.user_combobox.current(0)
            
        except Exception as e:
            self.show_error(f"Error loading users: {str(e)}")
    
    def _convert_date_range(self):
        """Convert date range strings to date objects."""
        try:
            from_date = datetime.datetime.strptime(self.date_from_var.get(), "%Y-%m-%d").date()
            to_date = datetime.datetime.strptime(self.date_to_var.get(), "%Y-%m-%d").date()
            
            # Validate date range
            if from_date > to_date:
                self.show_warning("From date cannot be after To date")
                return None, None
            
            return from_date, to_date
            
        except ValueError:
            self.show_warning("Invalid date format. Please use YYYY-MM-DD")
            return None, None
    
    def _generate_report(self):
        """Generate the selected report."""
        report_type = self.selected_report_var.get()
        
        # Convert date range
        from_date, to_date = self._convert_date_range()
        if from_date is None or to_date is None:
            return
        
        # Get user filter
        user_filter = self.user_filter_var.get()
        user_id = None
        if user_filter != "All Users":
            # Extract username from the format "username (role)"
            username = user_filter.split(" (")[0]
            try:
                user = self.user_controller.get_user_by_username(username)
                if user:
                    user_id = user["user_id"]
            except:
                pass
        
        # Update status
        self.status_var.set(f"Generating {report_type} report...")
        
        # Clear previous report
        self._clear_report()
        
        try:
            # Call appropriate report method based on selection
            if report_type == "Sales Summary":
                self._generate_sales_summary(from_date, to_date, user_id)
            elif report_type == "Sales by Product":
                self._generate_sales_by_product(from_date, to_date, user_id)
            elif report_type == "Sales by Category":
                self._generate_sales_by_category(from_date, to_date, user_id)
            elif report_type == "Sales by Customer":
                self._generate_sales_by_customer(from_date, to_date, user_id)
            elif report_type == "Sales by User":
                self._generate_sales_by_user(from_date, to_date)
            elif report_type == "Inventory Status":
                self._generate_inventory_status()
            elif report_type == "Low Stock Report":
                self._generate_low_stock_report()
            elif report_type == "Product Performance":
                self._generate_product_performance(from_date, to_date)
            else:
                self.show_warning(f"Report type '{report_type}' not implemented")
                return
                
            # Update status
            self.status_var.set(f"{report_type} report generated successfully")
            
        except Exception as e:
            self.show_error(f"Error generating report: {str(e)}")
            self.status_var.set("Error generating report")
    
    def _clear_report(self):
        """Clear the report display."""
        # Clear header
        self.report_header.config(text="")
        
        # Clear tree columns and data
        for column in self.report_tree["columns"]:
            self.report_tree.heading(column, text="")
        
        self.report_tree["columns"] = ()
        
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        
        # Clear summary
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
    
    def _configure_tree_columns(self, columns, widths=None):
        """Configure the treeview columns.
        
        Args:
            columns (list): List of column names
            widths (list, optional): List of column widths
        """
        self.report_tree["columns"] = tuple(columns)
        
        for i, col in enumerate(columns):
            # Set heading text
            display_name = col.replace("_", " ").title()
            self.report_tree.heading(col, text=display_name)
            
            # Set width if provided
            if widths and i < len(widths):
                self.report_tree.column(col, width=widths[i])
                
            # Set anchor for numeric columns
            if any(numeric in col.lower() for numeric in ["amount", "price", "total", "count", "qty", "quantity"]):
                self.report_tree.column(col, anchor=tk.E)
    
    def _add_summary_line(self, label_text, value_text):
        """Add a summary line to the summary frame."""
        frame = ttk.Frame(self.summary_frame)
        frame.pack(fill=tk.X, pady=2)
        
        label = ttk.Label(frame, text=label_text, font=("", 10, "bold"))
        label.pack(side=tk.LEFT, padx=(0, 5))
        
        value = ttk.Label(frame, text=value_text)
        value.pack(side=tk.RIGHT)
    
    def _generate_sales_summary(self, from_date, to_date, user_id=None):
        """Generate a sales summary report."""
        # Update header
        date_range = f"{from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"
        self.report_header.config(text=f"Sales Summary Report ({date_range})")
        
        # Get data from the controller
        try:
            report_data = self.report_controller.get_sales_summary(from_date, to_date, user_id)
            
            # Configure columns for the summary data
            columns = ["period", "invoice_count", "total_amount"]
            self._configure_tree_columns(columns, [150, 100, 100])
            
            # Add data to treeview
            for row in report_data["data"]:
                self.report_tree.insert(
                    "", 
                    "end",
                    values=(row["period"], row["invoice_count"], f"${row['total_amount']:.2f}")
                )
            
            # Add summary information
            totals = report_data["summary"]
            self._add_summary_line("Total Invoices:", str(totals["total_invoices"]))
            self._add_summary_line("Total Sales:", f"${totals['total_sales']:.2f}")
            self._add_summary_line("Average Invoice Value:", f"${totals['average_invoice']:.2f}")
            
        except Exception as e:
            self.show_error(f"Error generating sales summary report: {str(e)}")
    
    def _generate_sales_by_product(self, from_date, to_date, user_id=None):
        """Generate a sales by product report."""
        # Update header
        date_range = f"{from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"
        self.report_header.config(text=f"Sales by Product Report ({date_range})")
        
        # Get data from the controller
        try:
            report_data = self.report_controller.get_sales_by_product(from_date, to_date, user_id)
            
            # Configure columns for the summary data
            columns = ["product_name", "sku", "quantity_sold", "total_amount", "percentage"]
            self._configure_tree_columns(columns, [200, 100, 100, 100, 100])
            
            # Add data to treeview
            for row in report_data["data"]:
                self.report_tree.insert(
                    "", 
                    "end",
                    values=(
                        row["product_name"],
                        row["sku"],
                        row["quantity_sold"],
                        f"${row['total_amount']:.2f}",
                        f"{row['percentage']:.2f}%"
                    )
                )
            
            # Add summary information
            totals = report_data["summary"]
            self._add_summary_line("Total Products Sold:", str(totals["total_products"]))
            self._add_summary_line("Total Sales:", f"${totals['total_sales']:.2f}")
            self._add_summary_line("Top Product:", totals["top_product"])
            
        except Exception as e:
            self.show_error(f"Error generating sales by product report: {str(e)}")
    
    def _generate_sales_by_category(self, from_date, to_date, user_id=None):
        """Generate a sales by category report."""
        # Update header
        date_range = f"{from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"
        self.report_header.config(text=f"Sales by Category Report ({date_range})")
        
        # Get data from the controller
        try:
            report_data = self.report_controller.get_sales_by_category(from_date, to_date, user_id)
            
            # Configure columns for the summary data
            columns = ["category_name", "product_count", "quantity_sold", "total_amount", "percentage"]
            self._configure_tree_columns(columns, [200, 100, 100, 100, 100])
            
            # Add data to treeview
            for row in report_data["data"]:
                self.report_tree.insert(
                    "", 
                    "end",
                    values=(
                        row["category_name"],
                        row["product_count"],
                        row["quantity_sold"],
                        f"${row['total_amount']:.2f}",
                        f"{row['percentage']:.2f}%"
                    )
                )
            
            # Add summary information
            totals = report_data["summary"]
            self._add_summary_line("Total Categories:", str(totals["total_categories"]))
            self._add_summary_line("Total Sales:", f"${totals['total_sales']:.2f}")
            self._add_summary_line("Top Category:", totals["top_category"])
            
        except Exception as e:
            self.show_error(f"Error generating sales by category report: {str(e)}")
    
    def _generate_sales_by_customer(self, from_date, to_date, user_id=None):
        """Generate a sales by customer report."""
        # Update header
        date_range = f"{from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"
        self.report_header.config(text=f"Sales by Customer Report ({date_range})")
        
        # Get data from the controller
        try:
            report_data = self.report_controller.get_sales_by_customer(from_date, to_date, user_id)
            
            # Configure columns for the summary data
            columns = ["customer_name", "invoice_count", "total_amount", "percentage", "last_purchase"]
            self._configure_tree_columns(columns, [200, 100, 100, 100, 150])
            
            # Add data to treeview
            for row in report_data["data"]:
                # Format last purchase date
                last_purchase = row.get("last_purchase", "")
                if last_purchase:
                    last_purchase = datetime.datetime.strptime(last_purchase, "%Y-%m-%d").strftime("%Y-%m-%d")
                
                self.report_tree.insert(
                    "", 
                    "end",
                    values=(
                        row["customer_name"],
                        row["invoice_count"],
                        f"${row['total_amount']:.2f}",
                        f"{row['percentage']:.2f}%",
                        last_purchase
                    )
                )
            
            # Add summary information
            totals = report_data["summary"]
            self._add_summary_line("Total Customers:", str(totals["total_customers"]))
            self._add_summary_line("Total Sales:", f"${totals['total_sales']:.2f}")
            self._add_summary_line("Top Customer:", totals["top_customer"])
            
        except Exception as e:
            self.show_error(f"Error generating sales by customer report: {str(e)}")
    
    def _generate_sales_by_user(self, from_date, to_date):
        """Generate a sales by user report."""
        # Update header
        date_range = f"{from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"
        self.report_header.config(text=f"Sales by User Report ({date_range})")
        
        # Get data from the controller
        try:
            report_data = self.report_controller.get_sales_by_user(from_date, to_date)
            
            # Configure columns for the summary data
            columns = ["username", "invoice_count", "total_amount", "percentage", "average_invoice"]
            self._configure_tree_columns(columns, [150, 100, 100, 100, 100])
            
            # Add data to treeview
            for row in report_data["data"]:
                self.report_tree.insert(
                    "", 
                    "end",
                    values=(
                        row["username"],
                        row["invoice_count"],
                        f"${row['total_amount']:.2f}",
                        f"{row['percentage']:.2f}%",
                        f"${row['average_invoice']:.2f}"
                    )
                )
            
            # Add summary information
            totals = report_data["summary"]
            self._add_summary_line("Total Users:", str(totals["total_users"]))
            self._add_summary_line("Total Sales:", f"${totals['total_sales']:.2f}")
            self._add_summary_line("Top User:", totals["top_user"])
            
        except Exception as e:
            self.show_error(f"Error generating sales by user report: {str(e)}")
    
    def _generate_inventory_status(self):
        """Generate an inventory status report."""
        # Update header
        self.report_header.config(text=f"Inventory Status Report (Current)")
        
        # Get data from the controller
        try:
            report_data = self.report_controller.get_inventory_status()
            
            # Configure columns for the summary data
            columns = ["product_name", "sku", "current_stock", "min_stock", "status", "last_updated"]
            self._configure_tree_columns(columns, [200, 100, 100, 100, 100, 150])
            
            # Add data to treeview
            for row in report_data["data"]:
                # Format last updated date
                last_updated = row.get("last_updated", "")
                if last_updated:
                    last_updated = datetime.datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
                
                self.report_tree.insert(
                    "", 
                    "end",
                    values=(
                        row["product_name"],
                        row["sku"],
                        row["current_stock"],
                        row["min_stock"],
                        row["status"],
                        last_updated
                    )
                )
                
                # Set tag for color based on status
                if row["status"] == "Out of Stock":
                    self.report_tree.item(self.report_tree.get_children()[-1], tags=("out_of_stock",))
                elif row["status"] == "Low Stock":
                    self.report_tree.item(self.report_tree.get_children()[-1], tags=("low_stock",))
                elif row["status"] == "In Stock":
                    self.report_tree.item(self.report_tree.get_children()[-1], tags=("in_stock",))
            
            # Configure tags for colors
            self.report_tree.tag_configure("out_of_stock", foreground="red")
            self.report_tree.tag_configure("low_stock", foreground="orange")
            self.report_tree.tag_configure("in_stock", foreground="green")
            
            # Add summary information
            totals = report_data["summary"]
            self._add_summary_line("Total Products:", str(totals["total_products"]))
            self._add_summary_line("Out of Stock:", str(totals["out_of_stock_count"]))
            self._add_summary_line("Low Stock:", str(totals["low_stock_count"]))
            self._add_summary_line("In Stock:", str(totals["in_stock_count"]))
            
        except Exception as e:
            self.show_error(f"Error generating inventory status report: {str(e)}")
    
    def _generate_low_stock_report(self):
        """Generate a low stock report."""
        # Update header
        self.report_header.config(text=f"Low Stock Report (Current)")
        
        # Get data from the controller
        try:
            report_data = self.report_controller.get_low_stock_report()
            
            # Configure columns for the summary data
            columns = ["product_name", "sku", "current_stock", "min_stock", "reorder_quantity", "last_sold"]
            self._configure_tree_columns(columns, [200, 100, 100, 100, 100, 150])
            
            # Add data to treeview
            for row in report_data["data"]:
                # Format last sold date
                last_sold = row.get("last_sold", "")
                if last_sold:
                    last_sold = datetime.datetime.strptime(last_sold, "%Y-%m-%d").strftime("%Y-%m-%d")
                
                self.report_tree.insert(
                    "", 
                    "end",
                    values=(
                        row["product_name"],
                        row["sku"],
                        row["current_stock"],
                        row["min_stock"],
                        row["reorder_quantity"],
                        last_sold
                    )
                )
                
                # Set tag for color based on stock level
                if row["current_stock"] == 0:
                    self.report_tree.item(self.report_tree.get_children()[-1], tags=("out_of_stock",))
                else:
                    self.report_tree.item(self.report_tree.get_children()[-1], tags=("low_stock",))
            
            # Configure tags for colors
            self.report_tree.tag_configure("out_of_stock", foreground="red")
            self.report_tree.tag_configure("low_stock", foreground="orange")
            
            # Add summary information
            totals = report_data["summary"]
            self._add_summary_line("Low Stock Items:", str(totals["low_stock_count"]))
            self._add_summary_line("Out of Stock Items:", str(totals["out_of_stock_count"]))
            self._add_summary_line("Total Reorder Quantity:", str(totals["total_reorder_quantity"]))
            
        except Exception as e:
            self.show_error(f"Error generating low stock report: {str(e)}")
    
    def _generate_product_performance(self, from_date, to_date):
        """Generate a product performance report."""
        # Update header
        date_range = f"{from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"
        self.report_header.config(text=f"Product Performance Report ({date_range})")
        
        # Get data from the controller
        try:
            report_data = self.report_controller.get_product_performance(from_date, to_date)
            
            # Configure columns for the summary data
            columns = ["product_name", "sku", "quantity_sold", "revenue", "profit", "profit_margin"]
            self._configure_tree_columns(columns, [200, 100, 100, 100, 100, 100])
            
            # Add data to treeview
            for row in report_data["data"]:
                self.report_tree.insert(
                    "", 
                    "end",
                    values=(
                        row["product_name"],
                        row["sku"],
                        row["quantity_sold"],
                        f"${row['revenue']:.2f}",
                        f"${row['profit']:.2f}",
                        f"{row['profit_margin']:.2f}%"
                    )
                )
            
            # Add summary information
            totals = report_data["summary"]
            self._add_summary_line("Total Revenue:", f"${totals['total_revenue']:.2f}")
            self._add_summary_line("Total Profit:", f"${totals['total_profit']:.2f}")
            self._add_summary_line("Average Profit Margin:", f"{totals['average_profit_margin']:.2f}%")
            self._add_summary_line("Best Performing Product:", totals["best_performing_product"])
            
        except Exception as e:
            self.show_error(f"Error generating product performance report: {str(e)}")
    
    def _export_to_csv(self):
        """Export the current report to CSV."""
        # Check if there's data to export
        if not self.report_tree["columns"]:
            self.show_warning("No report data to export")
            return
        
        try:
            # Get report type
            report_type = self.selected_report_var.get()
            
            # Create a default filename
            date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"{report_type.lower().replace(' ', '_')}_{date_str}.csv"
            
            # Get file path from user
            filepath = asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if not filepath:
                # User cancelled
                return
                
            # Create CSV file
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                # Get column headers from treeview
                columns = self.report_tree["columns"]
                column_headers = [self.report_tree.heading(col)["text"] for col in columns]
                
                writer = csv.writer(csvfile)
                
                # Write headers
                writer.writerow(column_headers)
                
                # Write data
                for item_id in self.report_tree.get_children():
                    # Get values for this row
                    values = self.report_tree.item(item_id)["values"]
                    
                    # Clean values (remove $ signs, % signs, etc.)
                    clean_values = []
                    for val in values:
                        if isinstance(val, str):
                            # Remove currency and percentage symbols
                            if val.startswith("$"):
                                val = val[1:]
                            if val.endswith("%"):
                                val = val[:-1]
                        clean_values.append(val)
                    
                    writer.writerow(clean_values)
            
            # Show success message
            self.show_success(f"Report exported to {filepath}")
            self.status_var.set(f"Report exported successfully")
            
        except Exception as e:
            self.show_error(f"Error exporting report: {str(e)}")
            self.status_var.set("Error exporting report")