"""
Currency formatting utilities for POS application.
"""

from config import (
    CURRENCY_SYMBOL, 
    CURRENCY_POSITION, 
    DECIMAL_PLACES, 
    THOUSANDS_SEPARATOR, 
    DECIMAL_SEPARATOR
)

def format_currency(amount, include_symbol=True):
    """Format a number as currency.
    
    Args:
        amount (float): The amount to format
        include_symbol (bool): Whether to include the currency symbol
        
    Returns:
        str: Formatted currency string
    """
    if amount is None:
        amount = 0
    
    # Format with decimal places
    amount_str = f"{float(amount):.{DECIMAL_PLACES}f}"
    
    # Handle decimal separator
    if DECIMAL_SEPARATOR != ".":
        amount_str = amount_str.replace(".", DECIMAL_SEPARATOR)
    
    # Add thousands separator if needed
    if THOUSANDS_SEPARATOR:
        int_part, dec_part = amount_str.split(DECIMAL_SEPARATOR)
        
        # Format integer part with thousands separator
        groups = []
        while int_part:
            groups.append(int_part[-3:])
            int_part = int_part[:-3]
        
        int_part = THOUSANDS_SEPARATOR.join(reversed(groups))
        amount_str = f"{int_part}{DECIMAL_SEPARATOR}{dec_part}"
    
    # Add currency symbol
    if include_symbol:
        if CURRENCY_POSITION == "before":
            return f"{CURRENCY_SYMBOL}{amount_str}"
        else:
            return f"{amount_str} {CURRENCY_SYMBOL}"
    else:
        return amount_str

def parse_currency(amount_str):
    """Parse a currency string into a float.
    
    Args:
        amount_str (str): The currency string to parse
        
    Returns:
        float: Parsed amount as a float
    """
    if not amount_str:
        return 0.0
    
    # Remove currency symbol
    amount_str = amount_str.replace(CURRENCY_SYMBOL, "")
    
    # Remove thousands separator
    if THOUSANDS_SEPARATOR:
        amount_str = amount_str.replace(THOUSANDS_SEPARATOR, "")
    
    # Handle decimal separator
    if DECIMAL_SEPARATOR != ".":
        amount_str = amount_str.replace(DECIMAL_SEPARATOR, ".")
    
    # Convert to float
    try:
        return float(amount_str.strip())
    except ValueError:
        return 0.0