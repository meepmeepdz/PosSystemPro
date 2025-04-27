"""
Configuration settings for the POS application.
"""

import os
import platform

# Application settings
APP_TITLE = "POS System"
APP_VERSION = "1.0.0"
APP_SIZE = (1280, 800)  # Default window size (width, height)

# Database settings
DB_HOST = os.environ.get("PGHOST", "localhost")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE", "pos_db")
DB_USER = os.environ.get("PGUSER", "postgres")
DB_PASSWORD = os.environ.get("PGPASSWORD", "")
DB_URL = os.environ.get("DATABASE_URL", f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# UI settings
if platform.system() == "Windows":
    DEFAULT_FONT = ("Segoe UI", 10)
elif platform.system() == "Darwin":  # macOS
    DEFAULT_FONT = ("SF Pro Text", 12)
else:  # Linux and others
    DEFAULT_FONT = ("DejaVu Sans", 10)

TITLE_FONT = (DEFAULT_FONT[0], DEFAULT_FONT[1] + 4, "bold")
HEADER_FONT = (DEFAULT_FONT[0], DEFAULT_FONT[1] + 2, "bold")
LABEL_FONT = DEFAULT_FONT
BUTTON_FONT = (DEFAULT_FONT[0], DEFAULT_FONT[1], "bold")
SMALL_FONT = (DEFAULT_FONT[0], DEFAULT_FONT[1] - 2)

# Color scheme
COLORS = {
    "primary": "#4a6fa5",
    "secondary": "#6c757d",
    "success": "#28a745",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#17a2b8",
    "light": "#f8f9fa",
    "dark": "#343a40",
    "white": "#ffffff",
    "bg_light": "#f5f5f5",
    "bg_dark": "#212529",
    "text_light": "#f8f9fa",
    "text_dark": "#212529",
    "border": "#dee2e6"
}

# Business settings
COMPANY_NAME = "My Company"
COMPANY_ADDRESS = "123 Main Street, City, Country"
COMPANY_PHONE = "+123456789"
COMPANY_EMAIL = "contact@mycompany.com"
COMPANY_WEBSITE = "www.mycompany.com"
COMPANY_LOGO = None  # Path to logo if available

# Invoice settings
INVOICE_PREFIX = "INV"
RECEIPT_PREFIX = "RCP"

# Security settings
PASSWORD_MIN_LENGTH = 8
SESSION_TIMEOUT = 30 * 60  # 30 minutes in seconds

# Backup settings
BACKUP_DIR = "backups"
AUTO_BACKUP_INTERVAL = 24 * 60 * 60  # 24 hours in seconds

# Stock settings
LOW_STOCK_THRESHOLD = 10  # Default low stock threshold

# Payment types
PAYMENT_TYPES = ["CASH", "CARD", "CHECK", "CREDIT", "MOBILE"]
