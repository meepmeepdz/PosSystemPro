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