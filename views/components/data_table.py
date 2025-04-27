"""
Data table module for POS application.
Provides a reusable data table component.
"""

import tkinter as tk
from tkinter import ttk


class DataTable(ttk.Frame):
    """A widget that displays tabular data with sorting and selection."""
    
    def __init__(self, parent, columns, data=None, on_select=None, on_double_click=None, 
                 sortable=True, selection_mode="browse", **kwargs):
        """Create a data table.
        
        Args:
            parent: The parent widget
            columns (list): List of column definitions with keys: name, width, label
            data (list, optional): Initial data (list of dictionaries)
            on_select (callable, optional): Function to call when a row is selected
            on_double_click (callable, optional): Function to call when a row is double-clicked
            sortable (bool, optional): Whether the table is sortable by column
            selection_mode (str, optional): Treeview selection mode
            **kwargs: Additional keyword arguments for the frame
        """
        super().__init__(parent, **kwargs)
        
        self.columns = columns
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.sortable = sortable
        self.data = data or []
        self.sort_column = None
        self.sort_reverse = False
        
        self._create_widgets(selection_mode)
        
        if data:
            self.set_data(data)
    
    def _create_widgets(self, selection_mode):
        """Create and layout the widgets.
        
        Args:
            selection_mode (str): Treeview selection mode
        """
        # Create a frame for the treeview and scrollbar
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=[col["name"] for col in self.columns],
            show="headings",
            selectmode=selection_mode
        )
        
        # Configure columns
        for col in self.columns:
            self.tree.heading(
                col["name"], 
                text=col.get("label", col["name"]),
                command=lambda c=col["name"]: self._sort_by_column(c) if self.sortable else None
            )
            self.tree.column(
                col["name"],
                width=col.get("width", 100),
                minwidth=col.get("minwidth", 50),
                anchor=col.get("anchor", "w")
            )
        
        # Create vertical scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        # Create horizontal scrollbar
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=hsb.set)
        
        # Layout widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind events
        if self.on_select:
            self.tree.bind("<<TreeviewSelect>>", self.on_select)
        if self.on_double_click:
            self.tree.bind("<Double-1>", self.on_double_click)
    
    def _sort_by_column(self, column):
        """Sort data by the specified column.
        
        Args:
            column (str): Column name to sort by
        """
        if not self.sortable:
            return
        
        # If already sorted by this column, reverse the order
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Sort the data
        self.data.sort(
            key=lambda x: (x.get(column) is None, x.get(column, "")),
            reverse=self.sort_reverse
        )
        
        # Update the display
        self._populate_tree()
    
    def _populate_tree(self):
        """Populate the treeview with current data."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add data rows
        for item in self.data:
            values = [item.get(col["name"], "") for col in self.columns]
            self.tree.insert("", "end", values=values, iid=item.get("id"))
    
    def set_data(self, data):
        """Set the table data.
        
        Args:
            data (list): List of dictionaries with row data
        """
        self.data = data
        self._populate_tree()
    
    def add_row(self, row_data):
        """Add a single row to the table.
        
        Args:
            row_data (dict): Dictionary with row data
        """
        self.data.append(row_data)
        values = [row_data.get(col["name"], "") for col in self.columns]
        self.tree.insert("", "end", values=values, iid=row_data.get("id"))
    
    def update_row(self, row_id, row_data):
        """Update a row in the table.
        
        Args:
            row_id: ID of the row to update
            row_data (dict): New row data
        """
        # Update in data list
        for i, item in enumerate(self.data):
            if item.get("id") == row_id:
                self.data[i] = row_data
                break
        
        # Update in treeview
        for item in self.tree.get_children():
            if self.tree.item(item, "iid") == row_id:
                values = [row_data.get(col["name"], "") for col in self.columns]
                self.tree.item(item, values=values)
                break
    
    def delete_row(self, row_id):
        """Delete a row from the table.
        
        Args:
            row_id: ID of the row to delete
        """
        # Remove from data list
        self.data = [item for item in self.data if item.get("id") != row_id]
        
        # Remove from treeview
        for item in self.tree.get_children():
            if self.tree.item(item, "iid") == row_id:
                self.tree.delete(item)
                break
    
    def get_selected_item(self):
        """Get the currently selected item.
        
        Returns:
            dict: Selected item data or None if no selection
        """
        selected_items = self.tree.selection()
        if not selected_items:
            return None
        
        selected_values = self.tree.item(selected_items[0], "values")
        for item in self.data:
            match = True
            for i, col in enumerate(self.columns):
                if str(item.get(col["name"], "")) != str(selected_values[i]):
                    match = False
                    break
            if match:
                return item
        
        return None
    
    def get_selected_items(self):
        """Get all selected items.
        
        Returns:
            list: List of selected item data
        """
        selected_items = []
        for selected in self.tree.selection():
            selected_values = self.tree.item(selected, "values")
            for item in self.data:
                match = True
                for i, col in enumerate(self.columns):
                    if str(item.get(col["name"], "")) != str(selected_values[i]):
                        match = False
                        break
                if match:
                    selected_items.append(item)
                    break
        
        return selected_items
    
    def clear(self):
        """Clear all data from the table."""
        self.data = []
        for item in self.tree.get_children():
            self.tree.delete(item)