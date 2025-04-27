"""
Message box module for POS application.
Provides standard message dialogs.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class MessageBox:
    """Utility class for showing message boxes."""
    
    @staticmethod
    def show_info(parent, message):
        """Show an information message.
        
        Args:
            parent: Parent widget
            message (str): Message to display
            
        Returns:
            str: "ok"
        """
        return messagebox.showinfo("Information", message, parent=parent)
    
    @staticmethod
    def show_warning(parent, message):
        """Show a warning message.
        
        Args:
            parent: Parent widget
            message (str): Warning message to display
            
        Returns:
            str: "ok"
        """
        return messagebox.showwarning("Warning", message, parent=parent)
    
    @staticmethod
    def show_error(parent, message):
        """Show an error message.
        
        Args:
            parent: Parent widget
            message (str): Error message to display
            
        Returns:
            str: "ok"
        """
        return messagebox.showerror("Error", message, parent=parent)
    
    @staticmethod
    def show_confirmation(parent, message):
        """Show a confirmation dialog.
        
        Args:
            parent: Parent widget
            message (str): Confirmation message to display
            
        Returns:
            bool: True if confirmed, False otherwise
        """
        return messagebox.askyesno("Confirmation", message, parent=parent)
    
    @staticmethod
    def show_question(parent, message):
        """Show a question dialog.
        
        Args:
            parent: Parent widget
            message (str): Question to display
            
        Returns:
            bool: True if yes, False if no
        """
        return messagebox.askyesno("Question", message, parent=parent)
    
    @staticmethod
    def show_input(parent, title, prompt, initialvalue=None):
        """Show an input dialog.
        
        Args:
            parent: Parent widget
            title (str): Dialog title
            prompt (str): Input prompt
            initialvalue (str, optional): Initial value
            
        Returns:
            str: Input value or None if canceled
        """
        # Using a simple dialog window instead of simpledialog
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() - width) // 2
        y = (dialog.winfo_screenheight() - height) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Set up dialog widgets
        ttk_frame = tk.Frame(dialog, padx=20, pady=20)
        ttk_frame.pack(fill=tk.BOTH, expand=True)
        
        # Prompt label
        prompt_label = tk.Label(ttk_frame, text=prompt)
        prompt_label.pack(pady=(0, 10), anchor=tk.W)
        
        # Entry widget
        result = tk.StringVar()
        if initialvalue:
            result.set(initialvalue)
        
        entry = tk.Entry(ttk_frame, textvariable=result, width=30)
        entry.pack(fill=tk.X, pady=(0, 15))
        entry.focus_set()
        
        # Store the result - initialize as a dictionary with a mutable value
        # This avoids the type error when assigning a value later
        return_value = {}
        return_value["value"] = None
        
        # OK/Cancel buttons
        def on_ok():
            # Store the string result
            return_value["value"] = result.get()
            dialog.destroy()
            
        def on_cancel():
            dialog.destroy()
        
        button_frame = tk.Frame(ttk_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ok_button = tk.Button(button_frame, text="OK", width=10, command=on_ok)
        ok_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_button = tk.Button(button_frame, text="Cancel", width=10, command=on_cancel)
        cancel_button.pack(side=tk.RIGHT)
        
        # Handle Enter key
        entry.bind("<Return>", lambda event: on_ok())
        
        # Handle Escape key
        dialog.bind("<Escape>", lambda event: on_cancel())
        
        # Wait for dialog to close
        parent.wait_window(dialog)
        
        return return_value["value"]
    
    @staticmethod
    def show_success(parent, message):
        """Show a success message.
        
        Args:
            parent: Parent widget
            message (str): Success message to display
            
        Returns:
            str: "ok"
        """
        return messagebox.showinfo("Success", message, parent=parent)