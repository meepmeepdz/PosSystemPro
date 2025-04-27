"""
Base view class for POS application.
Provides common functionality for all views.
"""

import tkinter as tk
from tkinter import ttk

from config import COLORS


class BaseView(ttk.Frame):
    """Base view class to be inherited by all views."""
    
    def __init__(self, parent, *args, **kwargs):
        """Initialize a new base view.
        
        Args:
            parent: Parent widget
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        
        # Apply default styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._setup_styles()
    
    def _setup_styles(self):
        """Set up custom styles for widgets."""
        # Primary button style
        self.style.configure(
            "Primary.TButton",
            background=COLORS["primary"],
            foreground=COLORS["text_light"],
            font=("", 10, "bold"),
            padding=5
        )
        
        # Secondary button style
        self.style.configure(
            "Secondary.TButton",
            background=COLORS["secondary"],
            foreground=COLORS["text_light"],
            font=("", 10),
            padding=5
        )
        
        # Danger button style
        self.style.configure(
            "Danger.TButton",
            background=COLORS["danger"],
            foreground=COLORS["text_light"],
            font=("", 10, "bold"),
            padding=5
        )
        
        # Success button style
        self.style.configure(
            "Success.TButton",
            background=COLORS["success"],
            foreground=COLORS["text_light"],
            font=("", 10, "bold"),
            padding=5
        )
        
        # Primary header style
        self.style.configure(
            "Header.TLabel",
            font=("", 14, "bold"),
            padding=10
        )
        
        # Subheader style
        self.style.configure(
            "Subheader.TLabel",
            font=("", 12, "bold"),
            padding=5
        )
    
    def show_success(self, message):
        """Show a success message to the user.
        
        Args:
            message (str): Message to display
        """
        from views.components.message_box import MessageBox
        MessageBox.show_success(self, message)
    
    def show_error(self, message):
        """Show an error message to the user.
        
        Args:
            message (str): Error message to display
        """
        from views.components.message_box import MessageBox
        MessageBox.show_error(self, message)
    
    def show_warning(self, message):
        """Show a warning message to the user.
        
        Args:
            message (str): Warning message to display
        """
        from views.components.message_box import MessageBox
        MessageBox.show_warning(self, message)
    
    def show_info(self, message):
        """Show an info message to the user.
        
        Args:
            message (str): Info message to display
        """
        from views.components.message_box import MessageBox
        MessageBox.show_info(self, message)
    
    def show_confirmation(self, message):
        """Show a confirmation dialog to the user.
        
        Args:
            message (str): Confirmation message to display
            
        Returns:
            bool: True if confirmed, False otherwise
        """
        from views.components.message_box import MessageBox
        return MessageBox.show_confirmation(self, message)
    
    def center_window(self, window, width=None, height=None):
        """Center a window on the screen.
        
        Args:
            window: Window to center
            width (int, optional): Window width
            height (int, optional): Window height
        """
        if width and height:
            window.geometry(f"{width}x{height}")
        
        window.update_idletasks()
        
        # Get window dimensions and position
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set position
        window.geometry(f"+{x}+{y}")
    
    def create_scrolled_frame(self, parent, **kwargs):
        """Create a scrollable frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for the frame
            
        Returns:
            tuple: (container_frame, scrollable_frame)
        """
        # Create a canvas with scrollbar
        container = ttk.Frame(parent)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(container, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        
        # Create canvas
        canvas = tk.Canvas(container, yscrollcommand=scrollbar.set, **kwargs)
        canvas.pack(side="left", fill="both", expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=canvas.yview)
        
        # Create scrollable frame
        scrollable_frame = ttk.Frame(canvas)
        
        # Add scrollable frame to canvas
        frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Update canvas scroll region when frame size changes
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Resize the canvas window when scrollable_frame width changes
        def _on_canvas_configure(event):
            canvas.itemconfig(frame_id, width=event.width)
        
        scrollable_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        
        # Bind mouse wheel to scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Bind the mousewheel to the canvas and all child widgets
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        return container, scrollable_frame
    
    def clear_frame(self, frame):
        """Clear all widgets from a frame.
        
        Args:
            frame: Frame to clear
        """
        for widget in frame.winfo_children():
            widget.destroy()
