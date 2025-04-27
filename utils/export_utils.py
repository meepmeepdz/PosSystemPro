"""
Export utilities for the POS application.
Handles PDF and Excel exports for various reports and data.
"""

import os
import pandas as pd
import xlsxwriter
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

# Directory for exports
EXPORT_DIR = "exports"

def ensure_export_dir():
    """Create export directory if it doesn't exist."""
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

def export_to_excel(data, filename, sheet_name="Data", headers=None):
    """
    Export data to Excel file.
    
    Args:
        data (list): List of dictionaries or list of lists
        filename (str): Output filename (without extension)
        sheet_name (str, optional): Excel sheet name
        headers (list, optional): Column headers
        
    Returns:
        str: Path to the created file
    """
    ensure_export_dir()
    
    # Format filename
    if not filename.endswith('.xlsx'):
        filename += '.xlsx'
    
    filepath = os.path.join(EXPORT_DIR, filename)
    
    # Convert data to DataFrame
    if data and isinstance(data[0], dict):
        df = pd.DataFrame(data)
        if headers:
            df = df.reindex(columns=headers)
    else:
        df = pd.DataFrame(data)
        if headers:
            df.columns = headers
    
    # Create Excel file with XlsxWriter as the engine
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Get workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # Add formats
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'bg_color': '#D7E4BC',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'border': 1
    })
    
    # Apply formats to header and cells
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
    
    # Auto-adjust column width
    for i, col in enumerate(df.columns):
        max_len = max([df[col].astype(str).str.len().max(), len(str(col)) + 2])
        worksheet.set_column(i, i, max_len)
    
    # Save the workbook
    writer.close()
    
    return filepath

def export_to_pdf(data, filename, title="Report", headers=None, orientation='portrait'):
    """
    Export data to PDF file.
    
    Args:
        data (list): List of dictionaries or list of lists
        filename (str): Output filename (without extension)
        title (str, optional): PDF title
        headers (list, optional): Column headers
        orientation (str, optional): Page orientation ('portrait' or 'landscape')
        
    Returns:
        str: Path to the created file
    """
    ensure_export_dir()
    
    # Format filename
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    
    filepath = os.path.join(EXPORT_DIR, filename)
    
    # Set up PDF document
    pagesize = landscape(A4) if orientation == 'landscape' else A4
    doc = SimpleDocTemplate(
        filepath,
        pagesize=pagesize,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Set up styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Date style
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.gray
    )
    
    # Create document content
    content = []
    
    # Add title
    content.append(Paragraph(title, title_style))
    content.append(Spacer(1, 0.5 * cm))
    
    # Add date
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content.append(Paragraph(f"Generated on: {date_str}", date_style))
    content.append(Spacer(1, 0.5 * cm))
    
    # Prepare table data
    table_data = []
    
    # Process data
    if data and isinstance(data[0], dict):
        # If data is a list of dictionaries
        if not headers:
            headers = list(data[0].keys())
        
        table_data.append(headers)
        for item in data:
            row = [item.get(h, '') for h in headers]
            table_data.append(row)
    else:
        # If data is a list of lists
        if headers:
            table_data.append(headers)
        table_data.extend(data)
    
    # Create table
    if table_data:
        table = Table(table_data)
        
        # Style the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        # Apply style to table
        table.setStyle(style)
        
        # Add table to content
        content.append(table)
    
    # Build PDF
    doc.build(content)
    
    return filepath

# Function to format currency values for display
def format_currency(value):
    """Format a value as Algerian Dinar currency string.
    
    Args:
        value (float): Value to format
        
    Returns:
        str: Formatted currency string
    """
    if value is None:
        return "0,00 DA"
    
    # Format with thousand separator and 2 decimal places
    return f"{value:,.2f} DA".replace(",", " ").replace(".", ",")

# Specialized export functions for specific reports
def export_sales_report_to_pdf(data, date_from, date_to, filename=None):
    """
    Export sales report to PDF.
    
    Args:
        data (dict): Sales report data
        date_from (str): Start date
        date_to (str): End date
        filename (str, optional): Output filename
        
    Returns:
        str: Path to the created file
    """
    if not filename:
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Ensure dates are strings to avoid NoneType formatting errors
    from_str = str(date_from) if date_from is not None else "All time"
    to_str = str(date_to) if date_to is not None else "Present"
    title = f"Sales Report: {from_str} to {to_str}"
    
    # Format data for PDF
    pdf_data = []
    
    # Add headers
    headers = ["Invoice #", "Date", "Customer", "Items", "Total", "Status"]
    pdf_data.append(headers)
    
    # Add sales data
    for sale in data.get('sales', []):
        pdf_data.append([
            sale.get('invoice_number', ''),
            sale.get('date', ''),
            sale.get('customer_name', 'Walk-in Customer'),
            str(sale.get('item_count', 0)),
            format_currency(sale.get('total', 0)),
            sale.get('status', '')
        ])
    
    # Export to PDF
    return export_to_pdf(
        pdf_data, 
        filename,
        title=title,
        orientation='landscape'
    )

def export_sales_report_to_excel(data, date_from, date_to, filename=None):
    """
    Export sales report to Excel.
    
    Args:
        data (dict): Sales report data
        date_from (str): Start date
        date_to (str): End date
        filename (str, optional): Output filename
        
    Returns:
        str: Path to the created file
    """
    if not filename:
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Format data for Excel
    excel_data = []
    
    # Add sales data
    for sale in data.get('sales', []):
        excel_data.append({
            'Invoice #': sale.get('invoice_number', ''),
            'Date': sale.get('date', ''),
            'Customer': sale.get('customer_name', 'Walk-in Customer'),
            'Items': sale.get('item_count', 0),
            'Total': sale.get('total', 0),
            'Status': sale.get('status', ''),
            'Paid': sale.get('paid', 0),
            'Balance': sale.get('balance', 0),
            'User': sale.get('user_name', '')
        })
    
    # Export to Excel
    return export_to_excel(
        excel_data,
        filename,
        sheet_name=f"Sales {str(date_from) if date_from is not None else 'All time'} to {str(date_to) if date_to is not None else 'Present'}"
    )

def export_inventory_report_to_pdf(data, filename=None):
    """
    Export inventory report to PDF.
    
    Args:
        data (dict): Inventory report data
        filename (str, optional): Output filename
        
    Returns:
        str: Path to the created file
    """
    if not filename:
        filename = f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    title = "Inventory Report"
    
    # Format data for PDF
    pdf_data = []
    
    # Add headers
    headers = ["SKU", "Product", "Category", "Stock", "Min. Stock", "Unit Price", "Value"]
    pdf_data.append(headers)
    
    # Add inventory data
    for item in data.get('inventory', []):
        pdf_data.append([
            item.get('sku', ''),
            item.get('name', ''),
            item.get('category_name', ''),
            str(item.get('stock', 0)),
            str(item.get('min_stock', 0)),
            format_currency(item.get('unit_price', 0)),
            format_currency(item.get('value', 0))
        ])
    
    # Export to PDF
    return export_to_pdf(
        pdf_data, 
        filename,
        title=title,
        orientation='landscape'
    )

def export_inventory_report_to_excel(data, filename=None):
    """
    Export inventory report to Excel.
    
    Args:
        data (dict): Inventory report data
        filename (str, optional): Output filename
        
    Returns:
        str: Path to the created file
    """
    if not filename:
        filename = f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Format data for Excel
    excel_data = []
    
    # Add inventory data
    for item in data.get('inventory', []):
        excel_data.append({
            'SKU': item.get('sku', ''),
            'Product': item.get('name', ''),
            'Category': item.get('category_name', ''),
            'Stock': item.get('stock', 0),
            'Min. Stock': item.get('min_stock', 0),
            'Unit Price': item.get('unit_price', 0),
            'Value': item.get('value', 0),
            'Last Updated': item.get('last_updated', '')
        })
    
    # Export to Excel
    return export_to_excel(
        excel_data,
        filename,
        sheet_name="Inventory Report"
    )

def export_customer_report_to_pdf(data, filename=None):
    """
    Export customer report to PDF.
    
    Args:
        data (list): Customer data
        filename (str, optional): Output filename
        
    Returns:
        str: Path to the created file
    """
    if not filename:
        filename = f"customer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    title = "Customer Report"
    
    # Format data for PDF
    pdf_data = []
    
    # Add headers
    headers = ["ID", "Name", "Phone", "Email", "Total Purchases", "Balance"]
    pdf_data.append(headers)
    
    # Add customer data
    for customer in data:
        pdf_data.append([
            customer.get('customer_id', ''),
            customer.get('name', ''),
            customer.get('phone', ''),
            customer.get('email', ''),
            format_currency(customer.get('total_purchases', 0)),
            format_currency(customer.get('balance', 0))
        ])
    
    # Export to PDF
    return export_to_pdf(
        pdf_data, 
        filename,
        title=title
    )

def export_customer_report_to_excel(data, filename=None):
    """
    Export customer report to Excel.
    
    Args:
        data (list): Customer data
        filename (str, optional): Output filename
        
    Returns:
        str: Path to the created file
    """
    if not filename:
        filename = f"customer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Format data for Excel
    excel_data = []
    
    # Add customer data
    for customer in data:
        excel_data.append({
            'ID': customer.get('customer_id', ''),
            'Name': customer.get('name', ''),
            'Phone': customer.get('phone', ''),
            'Email': customer.get('email', ''),
            'Address': customer.get('address', ''),
            'Total Purchases': customer.get('total_purchases', 0),
            'Balance': customer.get('balance', 0),
            'Last Purchase': customer.get('last_purchase_date', '')
        })
    
    # Export to Excel
    return export_to_excel(
        excel_data,
        filename,
        sheet_name="Customer Report"
    )

def export_financial_report_to_pdf(data, date_from, date_to, filename=None):
    """
    Export financial report to PDF.
    
    Args:
        data (dict): Financial report data
        date_from (str): Start date
        date_to (str): End date
        filename (str, optional): Output filename
        
    Returns:
        str: Path to the created file
    """
    if not filename:
        filename = f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Ensure dates are strings to avoid NoneType formatting errors
    from_str = str(date_from) if date_from is not None else "All time"
    to_str = str(date_to) if date_to is not None else "Present"
    title = f"Financial Report: {from_str} to {to_str}"
    
    # Set up PDF document
    ensure_export_dir()
    filepath = os.path.join(EXPORT_DIR, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Set up styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create document content
    content = []
    
    # Add title
    content.append(Paragraph(title, title_style))
    content.append(Spacer(1, 0.5 * cm))
    
    # Add date
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content.append(Paragraph(f"Generated on: {date_str}", normal_style))
    content.append(Spacer(1, 1 * cm))
    
    # Summary section
    content.append(Paragraph("Summary", subtitle_style))
    content.append(Spacer(1, 0.5 * cm))
    
    summary_data = [
        ["Total Sales", format_currency(data.get('total_sales', 0))],
        ["Total Cost", format_currency(data.get('total_cost', 0))],
        ["Gross Profit", format_currency(data.get('gross_profit', 0))],
        ["Profit Margin", f"{data.get('profit_margin', 0):.2f}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 150])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    content.append(summary_table)
    content.append(Spacer(1, 1 * cm))
    
    # Daily sales section
    content.append(Paragraph("Daily Sales", subtitle_style))
    content.append(Spacer(1, 0.5 * cm))
    
    daily_headers = ["Date", "Sales", "Items Sold", "Invoices"]
    daily_data = [daily_headers]
    
    for day in data.get('daily_sales', []):
        daily_data.append([
            day.get('date', ''),
            format_currency(day.get('total', 0)),
            str(day.get('items', 0)),
            str(day.get('invoices', 0))
        ])
    
    daily_table = Table(daily_data, colWidths=[120, 120, 80, 80])
    daily_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 1), (3, -1), 'CENTER'),
    ]))
    
    content.append(daily_table)
    
    # Build PDF
    doc.build(content)
    
    return filepath

def export_financial_report_to_excel(data, date_from, date_to, filename=None):
    """
    Export financial report to Excel.
    
    Args:
        data (dict): Financial report data
        date_from (str): Start date
        date_to (str): End date
        filename (str, optional): Output filename
        
    Returns:
        str: Path to the created file
    """
    if not filename:
        filename = f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    ensure_export_dir()
    filepath = os.path.join(EXPORT_DIR, filename)
    
    # Create Excel workbook
    workbook = xlsxwriter.Workbook(filepath)
    
    # Add formats
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14
    })
    
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D7E4BC',
        'border': 1,
        'align': 'center'
    })
    
    money_format = workbook.add_format({
        'num_format': '# ##0,00 "DA"',
        'border': 1
    })
    
    percent_format = workbook.add_format({
        'num_format': '0.00%',
        'border': 1
    })
    
    date_format = workbook.add_format({
        'num_format': 'yyyy-mm-dd',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'border': 1
    })
    
    # Summary worksheet
    summary_sheet = workbook.add_worksheet('Summary')
    
    # Add title
    # Use the same string formatting as in the title to avoid NoneType errors
    from_str = str(date_from) if date_from is not None else "All time"
    to_str = str(date_to) if date_to is not None else "Present"
    summary_sheet.write(0, 0, f"Financial Report: {from_str} to {to_str}", title_format)
    summary_sheet.write(1, 0, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Summary section
    summary_sheet.write(3, 0, "Summary", title_format)
    summary_sheet.write(4, 0, "Total Sales")
    summary_sheet.write(5, 0, "Total Cost")
    summary_sheet.write(6, 0, "Gross Profit")
    summary_sheet.write(7, 0, "Profit Margin")
    
    summary_sheet.write_number(4, 1, data.get('total_sales', 0), money_format)
    summary_sheet.write_number(5, 1, data.get('total_cost', 0), money_format)
    summary_sheet.write_number(6, 1, data.get('gross_profit', 0), money_format)
    summary_sheet.write_number(7, 1, data.get('profit_margin', 0)/100, percent_format)
    
    # Daily sales
    summary_sheet.write(9, 0, "Daily Sales", title_format)
    
    # Add headers
    headers = ["Date", "Sales", "Items Sold", "Invoices"]
    for i, header in enumerate(headers):
        summary_sheet.write(10, i, header, header_format)
    
    # Add data
    row = 11
    for day in data.get('daily_sales', []):
        summary_sheet.write(row, 0, day.get('date', ''), date_format)
        summary_sheet.write_number(row, 1, day.get('total', 0), money_format)
        summary_sheet.write_number(row, 2, day.get('items', 0), cell_format)
        summary_sheet.write_number(row, 3, day.get('invoices', 0), cell_format)
        row += 1
    
    # Product sales worksheet
    if 'product_sales' in data:
        product_sheet = workbook.add_worksheet('Product Sales')
        
        # Headers
        product_headers = ["Product", "SKU", "Quantity", "Total Sales", "Profit"]
        for i, header in enumerate(product_headers):
            product_sheet.write(0, i, header, header_format)
        
        # Data
        for i, product in enumerate(data.get('product_sales', [])):
            row = i + 1
            product_sheet.write(row, 0, product.get('name', ''), cell_format)
            product_sheet.write(row, 1, product.get('sku', ''), cell_format)
            product_sheet.write_number(row, 2, product.get('quantity', 0), cell_format)
            product_sheet.write_number(row, 3, product.get('sales', 0), money_format)
            product_sheet.write_number(row, 4, product.get('profit', 0), money_format)
    
    # Category sales worksheet
    if 'category_sales' in data:
        category_sheet = workbook.add_worksheet('Category Sales')
        
        # Headers
        category_headers = ["Category", "Products Sold", "Total Sales", "Profit"]
        for i, header in enumerate(category_headers):
            category_sheet.write(0, i, header, header_format)
        
        # Data
        for i, category in enumerate(data.get('category_sales', [])):
            row = i + 1
            category_sheet.write(row, 0, category.get('name', ''), cell_format)
            category_sheet.write_number(row, 1, category.get('quantity', 0), cell_format)
            category_sheet.write_number(row, 2, category.get('sales', 0), money_format)
            category_sheet.write_number(row, 3, category.get('profit', 0), money_format)
    
    # Auto-fit columns
    for sheet in workbook.worksheets():
        for i in range(10):  # Adjust first 10 columns
            sheet.set_column(i, i, 15)
    
    # Close the workbook
    workbook.close()
    
    return filepath