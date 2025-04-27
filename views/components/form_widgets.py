"""
Form widgets for POS application.
Contains reusable form components.
"""

import tkinter as tk
from tkinter import ttk


class LabelInput(ttk.Frame):
    """A widget that combines a label and input together."""
    
    def __init__(self, parent, label, input_class, input_var, input_args=None, 
                 label_args=None, **kwargs):
        """Create a label-input pair.
        
        Args:
            parent: The parent widget
            label (str): The label text
            input_class: The input widget class to use
            input_var: The input variable
            input_args (dict, optional): Additional arguments for the input widget
            label_args (dict, optional): Additional arguments for the label widget
            **kwargs: Additional keyword arguments for the frame
        """
        super().__init__(parent, **kwargs)
        
        input_args = input_args or {}
        label_args = label_args or {}
        
        # Create the label
        self.label = ttk.Label(self, text=label, **label_args)
        self.label.grid(row=0, column=0, sticky=tk.W)
        
        # Create the input
        self.input = input_class(self, textvariable=input_var, **input_args)
        self.input.grid(row=1, column=0, sticky=tk.W + tk.E)
        
        # Variables
        self.variable = input_var
        
        # Configure grid to expand with window
        self.columnconfigure(0, weight=1)
    
    def grid(self, sticky=(tk.W + tk.E), **kwargs):
        """Override grid to add default sticky attribute."""
        super().grid(sticky=sticky, **kwargs)


class FormFrame(ttk.Frame):
    """A frame that holds form fields with automatic layout."""
    
    def __init__(self, parent, **kwargs):
        """Create a form frame.
        
        Args:
            parent: The parent widget
            **kwargs: Additional keyword arguments for the frame
        """
        super().__init__(parent, **kwargs)
        
        # Configure grid to expand with window
        self.columnconfigure(0, weight=1)
    
    def add_section_header(self, text):
        """Add a section header to the form.
        
        Args:
            text (str): The header text
        """
        header_label = ttk.Label(self, text=text, font=("", 11, "bold"))
        header_label.pack(anchor=tk.W, pady=(10, 5))
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        return header_label
    
    def add_field(self, label_text, variable, input_class=ttk.Entry, input_args=None, label_args=None):
        """Add a field to the form.
        
        Args:
            label_text (str): The label text
            variable: The variable to bind to the input
            input_class: The input widget class (default: ttk.Entry)
            input_args (dict, optional): Additional arguments for the input widget
            label_args (dict, optional): Additional arguments for the label widget
            
        Returns:
            tuple: The frame, label, and input widgets
        """
        # Create a frame for the field
        field_frame = ttk.Frame(self)
        field_frame.pack(fill=tk.X, pady=5)
        
        # Create the label
        label = ttk.Label(field_frame, text=label_text, width=15, anchor=tk.W)
        label.pack(side=tk.LEFT, padx=5)
        
        # Set default input arguments
        input_args = input_args or {}
        
        # Create the input
        input_widget = input_class(field_frame, textvariable=variable, **input_args)
        input_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        return field_frame, label, input_widget