"""
Backup view for POS application.
Handles database backup and restore operations.
"""

import tkinter as tk
from tkinter import ttk
import datetime
from tkinter.filedialog import askopenfilename
import os

from views.base_view import BaseView
from views.components.message_box import MessageBox


class BackupView(BaseView):
    """View for database backup and restore operations."""
    
    def __init__(self, parent, backup_controller):
        """Initialize backup view.
        
        Args:
            parent: Parent widget
            backup_controller: Controller for backup operations
        """
        super().__init__(parent)
        self.parent = parent
        self.backup_controller = backup_controller
        
        # Current backup
        self.current_backup = None
        
        # Variables
        self.backup_description_var = tk.StringVar()
        self.compress_var = tk.BooleanVar(value=True)
        self.auto_backup_var = tk.BooleanVar(value=False)
        self.auto_backup_interval_var = tk.StringVar(value="24")
        
        # Create UI components
        self._create_widgets()
        
        # Initial data load
        self._refresh_backups()
        self._check_auto_backup_status()
    
    def _create_widgets(self):
        """Create and layout widgets."""
        # Main container with two panels
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel 1: Backup list
        self.backup_list_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.backup_list_frame, weight=2)
        
        # Panel 2: Backup details and operations
        self.backup_detail_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.backup_detail_frame, weight=1)
        
        # Set up backup list panel
        self._create_backup_list_panel()
        
        # Set up backup details panel
        self._create_backup_detail_panel()
    
    def _create_backup_list_panel(self):
        """Create and populate the backup list panel."""
        # Header
        header_label = ttk.Label(
            self.backup_list_frame, 
            text="Database Backups", 
            style="Header.TLabel"
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Toolbar frame
        toolbar_frame = ttk.Frame(self.backup_list_frame)
        toolbar_frame.pack(fill=tk.X, pady=5)
        
        refresh_button = ttk.Button(
            toolbar_frame, 
            text="Refresh", 
            command=self._refresh_backups
        )
        refresh_button.pack(side=tk.RIGHT)
        
        # Backups list
        list_frame = ttk.Frame(self.backup_list_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a treeview for the backup list
        self.backup_tree = ttk.Treeview(
            list_frame, 
            columns=("date", "size", "description"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.backup_tree.heading("date", text="Date/Time")
        self.backup_tree.heading("size", text="Size")
        self.backup_tree.heading("description", text="Description")
        
        self.backup_tree.column("date", width=150)
        self.backup_tree.column("size", width=100, anchor=tk.E)
        self.backup_tree.column("description", width=300)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.backup_tree.bind("<<TreeviewSelect>>", self._on_backup_selected)
    
    def _create_backup_detail_panel(self):
        """Create and populate the backup detail panel."""
        # Create backup frame
        create_frame = ttk.LabelFrame(self.backup_detail_frame, text="Create Backup", padding=10)
        create_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Description field
        desc_frame = ttk.Frame(create_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        
        desc_label = ttk.Label(desc_frame, text="Description:")
        desc_label.pack(side=tk.LEFT, padx=(0, 5))
        
        desc_entry = ttk.Entry(desc_frame, textvariable=self.backup_description_var)
        desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Compress checkbox
        compress_check = ttk.Checkbutton(
            create_frame, 
            text="Compress backup (recommended)", 
            variable=self.compress_var
        )
        compress_check.pack(anchor=tk.W, pady=5)
        
        # Create button
        create_button = ttk.Button(
            create_frame, 
            text="Create Backup Now", 
            command=self._create_backup,
            style="Primary.TButton"
        )
        create_button.pack(fill=tk.X, pady=5)
        
        # Auto backup frame
        auto_frame = ttk.LabelFrame(self.backup_detail_frame, text="Automatic Backups", padding=10)
        auto_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Auto backup checkbox
        auto_check = ttk.Checkbutton(
            auto_frame, 
            text="Enable automatic backups", 
            variable=self.auto_backup_var,
            command=self._toggle_auto_backup
        )
        auto_check.pack(anchor=tk.W, pady=5)
        
        # Interval field
        interval_frame = ttk.Frame(auto_frame)
        interval_frame.pack(fill=tk.X, pady=5)
        
        interval_label = ttk.Label(interval_frame, text="Interval (hours):")
        interval_label.pack(side=tk.LEFT, padx=(0, 5))
        
        interval_entry = ttk.Entry(interval_frame, textvariable=self.auto_backup_interval_var, width=5)
        interval_entry.pack(side=tk.LEFT)
        
        # Update button
        update_button = ttk.Button(
            auto_frame, 
            text="Update Auto Backup Settings", 
            command=self._update_auto_backup
        )
        update_button.pack(fill=tk.X, pady=5)
        
        # Status label
        self.auto_backup_status_label = ttk.Label(
            auto_frame, 
            text="Auto backup status: Not running",
            foreground="red"
        )
        self.auto_backup_status_label.pack(anchor=tk.W, pady=5)
        
        # Backup details frame
        details_frame = ttk.LabelFrame(self.backup_detail_frame, text="Backup Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create details grid
        details_grid = ttk.Frame(details_frame)
        details_grid.pack(fill=tk.X, padx=5, pady=5)
        
        row = 0
        
        # Backup ID
        ttk.Label(details_grid, text="Backup ID:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.backup_id_label = ttk.Label(details_grid, text="-")
        self.backup_id_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Date/Time
        ttk.Label(details_grid, text="Date/Time:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.backup_date_label = ttk.Label(details_grid, text="-")
        self.backup_date_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Size
        ttk.Label(details_grid, text="Size:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.backup_size_label = ttk.Label(details_grid, text="-")
        self.backup_size_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Compressed
        ttk.Label(details_grid, text="Compressed:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.backup_compressed_label = ttk.Label(details_grid, text="-")
        self.backup_compressed_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # File Path
        ttk.Label(details_grid, text="File Path:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.backup_path_label = ttk.Label(details_grid, text="-", wraplength=250)
        self.backup_path_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Description
        ttk.Label(details_grid, text="Description:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.backup_desc_label = ttk.Label(details_grid, text="-", wraplength=250)
        self.backup_desc_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Action buttons
        action_frame = ttk.Frame(details_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        restore_button = ttk.Button(
            action_frame, 
            text="Restore This Backup", 
            command=self._restore_backup,
            style="Primary.TButton"
        )
        restore_button.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_button = ttk.Button(
            action_frame, 
            text="Delete", 
            command=self._delete_backup,
            style="Danger.TButton"
        )
        delete_button.pack(side=tk.LEFT)
        
        # Restore from file frame
        restore_file_frame = ttk.LabelFrame(self.backup_detail_frame, text="Restore from File", padding=10)
        restore_file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Browse button
        browse_button = ttk.Button(
            restore_file_frame, 
            text="Browse for Backup File", 
            command=self._browse_backup_file
        )
        browse_button.pack(fill=tk.X, pady=5)
        
        # Warning label
        warning_label = ttk.Label(
            restore_file_frame, 
            text="Warning: Restoring will overwrite all current data. Make sure to backup first!",
            foreground="red",
            wraplength=250
        )
        warning_label.pack(pady=5)
    
    def _refresh_backups(self):
        """Refresh the list of backups."""
        # Clear existing items
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        try:
            # Get all backups
            backups = self.backup_controller.list_backups()
            
            # Add to treeview (sorted by date, newest first)
            for backup in reversed(backups):
                # Format date
                date_str = backup["created_at"].strftime("%Y-%m-%d %H:%M") if backup["created_at"] else "-"
                
                # Format size
                size_bytes = backup.get("file_size", 0)
                if size_bytes >= 1024 * 1024:
                    size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
                elif size_bytes >= 1024:
                    size_str = f"{size_bytes / 1024:.2f} KB"
                else:
                    size_str = f"{size_bytes} B"
                
                # Description
                description = backup.get("description", "")
                
                self.backup_tree.insert(
                    "", 
                    "end", 
                    values=(date_str, size_str, description),
                    iid=backup["backup_id"]
                )
                
        except Exception as e:
            self.show_error(f"Error loading backups: {str(e)}")
    
    def _check_auto_backup_status(self):
        """Check the status of auto backup."""
        try:
            status = self.backup_controller.get_backup_status()
            
            if status.get("running", False):
                self.auto_backup_var.set(True)
                self.auto_backup_interval_var.set(str(status.get("interval_hours", 24)))
                self.auto_backup_status_label.config(
                    text=f"Auto backup status: Running (every {status.get('interval_hours', 24)} hours)",
                    foreground="green"
                )
            else:
                self.auto_backup_var.set(False)
                self.auto_backup_status_label.config(
                    text="Auto backup status: Not running",
                    foreground="red"
                )
                
        except Exception as e:
            self.show_error(f"Error checking auto backup status: {str(e)}")
    
    def _on_backup_selected(self, event=None):
        """Handle backup selection in the treeview."""
        selected_items = self.backup_tree.selection()
        if not selected_items:
            return
        
        # Get the first selected item
        backup_id = selected_items[0]
        
        try:
            # Get backup details
            backup = self.backup_controller.get_backup_by_id(backup_id)
            if not backup:
                return
            
            # Store current backup
            self.current_backup = backup
            
            # Update backup details
            self.backup_id_label.config(text=backup["backup_id"])
            
            # Format date
            date_str = backup["created_at"].strftime("%Y-%m-%d %H:%M:%S") if backup["created_at"] else "-"
            self.backup_date_label.config(text=date_str)
            
            # Format size
            size_bytes = backup.get("file_size", 0)
            if size_bytes >= 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            elif size_bytes >= 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{size_bytes} B"
            self.backup_size_label.config(text=size_str)
            
            # Compressed status
            compressed = "Yes" if backup.get("compressed", False) else "No"
            self.backup_compressed_label.config(text=compressed)
            
            # File path
            self.backup_path_label.config(text=backup.get("file_path", "-"))
            
            # Description
            self.backup_desc_label.config(text=backup.get("description", "-"))
            
        except Exception as e:
            self.show_error(f"Error loading backup details: {str(e)}")
    
    def _create_backup(self):
        """Create a new database backup."""
        try:
            # Get description and compress flag
            description = self.backup_description_var.get().strip()
            compress = self.compress_var.get()
            
            # Create the backup
            result = self.backup_controller.create_backup(
                compress=compress,
                description=description or None
            )
            
            if result.get("success", False):
                # Refresh the list
                self._refresh_backups()
                
                # Clear description
                self.backup_description_var.set("")
                
                # Show success message
                self.show_success("Backup created successfully")
                
                # Select the new backup
                if "backup_id" in result:
                    self.backup_tree.selection_set([result["backup_id"]])
                    self._on_backup_selected()
            else:
                self.show_error(f"Error creating backup: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            self.show_error(f"Error creating backup: {str(e)}")
    
    def _toggle_auto_backup(self):
        """Toggle automatic backup."""
        try:
            if self.auto_backup_var.get():
                # Enable auto backup
                try:
                    interval = int(self.auto_backup_interval_var.get())
                    if interval <= 0:
                        self.show_warning("Interval must be a positive number")
                        self.auto_backup_var.set(False)
                        return
                except ValueError:
                    self.show_warning("Please enter a valid interval")
                    self.auto_backup_var.set(False)
                    return
                
                # Start auto backup
                result = self.backup_controller.start_auto_backup(interval_hours=interval)
                
                if result:
                    self.auto_backup_status_label.config(
                        text=f"Auto backup status: Running (every {interval} hours)",
                        foreground="green"
                    )
                else:
                    self.show_error("Error starting automatic backup")
                    self.auto_backup_var.set(False)
            else:
                # Disable auto backup
                self.backup_controller.stop_auto_backup_thread()
                
                self.auto_backup_status_label.config(
                    text="Auto backup status: Not running",
                    foreground="red"
                )
                
        except Exception as e:
            self.show_error(f"Error toggling automatic backup: {str(e)}")
            # Reset checkbox state
            self.auto_backup_var.set(False)
    
    def _update_auto_backup(self):
        """Update automatic backup settings."""
        try:
            # Stop current auto backup if running
            self.backup_controller.stop_auto_backup_thread()
            
            # Check if auto backup should be enabled
            if self.auto_backup_var.get():
                # Get interval
                try:
                    interval = int(self.auto_backup_interval_var.get())
                    if interval <= 0:
                        self.show_warning("Interval must be a positive number")
                        return
                except ValueError:
                    self.show_warning("Please enter a valid interval")
                    return
                
                # Start auto backup with new settings
                result = self.backup_controller.start_auto_backup(interval_hours=interval)
                
                if result:
                    self.auto_backup_status_label.config(
                        text=f"Auto backup status: Running (every {interval} hours)",
                        foreground="green"
                    )
                    self.show_success("Automatic backup settings updated")
                else:
                    self.show_error("Error updating automatic backup settings")
            else:
                self.auto_backup_status_label.config(
                    text="Auto backup status: Not running",
                    foreground="red"
                )
                self.show_success("Automatic backup disabled")
                
        except Exception as e:
            self.show_error(f"Error updating automatic backup settings: {str(e)}")
    
    def _restore_backup(self):
        """Restore from the selected backup."""
        if not self.current_backup:
            self.show_warning("No backup selected")
            return
        
        # Confirm restore
        confirm = self.show_confirmation(
            "Warning: Restoring will overwrite all current data. This cannot be undone. "
            "Are you sure you want to restore this backup?"
        )
        
        if not confirm:
            return
        
        try:
            # Show a message that this is happening
            self.show_info("Restoring backup... This may take a moment")
            
            # Force update the UI
            self.update_idletasks()
            
            # Restore the backup
            result = self.backup_controller.restore_backup(
                backup_id=self.current_backup["backup_id"]
            )
            
            if result.get("success", False):
                self.show_success("Backup restored successfully. You may need to restart the application.")
            else:
                self.show_error(f"Error restoring backup: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            self.show_error(f"Error restoring backup: {str(e)}")
    
    def _delete_backup(self):
        """Delete the selected backup."""
        if not self.current_backup:
            self.show_warning("No backup selected")
            return
        
        # Confirm deletion
        confirm = self.show_confirmation(
            f"Are you sure you want to delete this backup from {self.backup_date_label.cget('text')}? "
            "This action cannot be undone."
        )
        
        if not confirm:
            return
        
        try:
            # Delete the backup
            result = self.backup_controller.delete_backup(self.current_backup["backup_id"])
            
            # Refresh the list
            self._refresh_backups()
            
            # Clear selection
            self.current_backup = None
            self.backup_id_label.config(text="-")
            self.backup_date_label.config(text="-")
            self.backup_size_label.config(text="-")
            self.backup_compressed_label.config(text="-")
            self.backup_path_label.config(text="-")
            self.backup_desc_label.config(text="-")
            
            self.show_success("Backup deleted successfully")
            
        except Exception as e:
            self.show_error(f"Error deleting backup: {str(e)}")
    
    def _browse_backup_file(self):
        """Browse for a backup file to restore."""
        # Get file path from user
        filepath = askopenfilename(
            filetypes=[
                ("SQL Backup Files", "*.sql"),
                ("Compressed SQL Files", "*.sql.gz"),
                ("All files", "*.*")
            ]
        )
        
        if not filepath:
            # User cancelled
            return
        
        # Validate file exists
        if not os.path.isfile(filepath):
            self.show_error("Selected file does not exist")
            return
        
        # Confirm restore
        confirm = self.show_confirmation(
            "Warning: Restoring will overwrite all current data. This cannot be undone. "
            f"Are you sure you want to restore from file:\n{filepath}?"
        )
        
        if not confirm:
            return
        
        try:
            # Show a message that this is happening
            self.show_info("Restoring from file... This may take a moment")
            
            # Force update the UI
            self.update_idletasks()
            
            # Restore from file
            result = self.backup_controller.restore_backup(
                backup_path=filepath
            )
            
            if result.get("success", False):
                self.show_success("Backup restored successfully. You may need to restart the application.")
            else:
                self.show_error(f"Error restoring backup: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            self.show_error(f"Error restoring from file: {str(e)}")