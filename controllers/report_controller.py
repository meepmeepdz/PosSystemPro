"""
Report controller for POS application.
Handles report generation operations.
"""

from datetime import datetime, timedelta


class ReportController:
    """Controller for report operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        
    def get_sales_summary(self, date_from=None, date_to=None, user_id=None):
        """Get a sales summary report.
        
        Args:
            date_from (str or datetime, optional): Start date
            date_to (str or datetime, optional): End date
            user_id (str, optional): Filter by user ID
            
        Returns:
            dict: Sales summary data with daily/weekly/monthly breakdowns
        """
        # Convert datetime objects to ISO format strings if needed
        if hasattr(date_from, 'isoformat'):
            date_from = date_from.isoformat()
        if hasattr(date_to, 'isoformat'):
            date_to = date_to.isoformat()
            
        # Query to get daily sales
        daily_query = """
            SELECT 
                DATE_TRUNC('day', i.created_at)::date as period,
                COUNT(i.invoice_id) as invoice_count,
                SUM(i.total_amount) as total_amount
            FROM invoices i
            WHERE i.status = 'COMPLETED'
        """
        params = []
        
        # Add date filters
        if date_from:
            daily_query += " AND i.created_at >= %s"
            params.append(date_from)
        
        if date_to:
            daily_query += " AND i.created_at <= %s"
            params.append(date_to)
        
        # Add user filter
        if user_id:
            daily_query += " AND i.user_id = %s"
            params.append(user_id)
        
        # Group and order
        daily_query += " GROUP BY period ORDER BY period"
        
        # Execute query
        daily_data = self.db.fetch_all(daily_query, tuple(params))
        
        # Get summary totals
        summary_query = """
            SELECT 
                COUNT(i.invoice_id) as total_invoices,
                SUM(i.total_amount) as total_sales,
                ROUND(AVG(i.total_amount), 2) as average_sale,
                COUNT(DISTINCT i.customer_id) as unique_customers,
                COUNT(DISTINCT i.user_id) as unique_sellers,
                MAX(i.total_amount) as highest_sale,
                MIN(i.total_amount) as lowest_sale
            FROM invoices i
            WHERE i.status = 'COMPLETED'
        """
        
        # Add the same filters
        summary_params = []
        
        if date_from:
            summary_query += " AND i.created_at >= %s"
            summary_params.append(date_from)
        
        if date_to:
            summary_query += " AND i.created_at <= %s"
            summary_params.append(date_to)
        
        if user_id:
            summary_query += " AND i.user_id = %s"
            summary_params.append(user_id)
        
        # Execute summary query
        summary = self.db.fetch_one(summary_query, tuple(summary_params))
        
        # Return combined results
        return {
            "data": daily_data,
            "summary": summary or {}
        }
    
    def get_sales_report(self, date_from=None, date_to=None, user_id=None, customer_id=None):
        """Get a sales report for a period.
        
        Args:
            date_from (str, optional): Start date (ISO format)
            date_to (str, optional): End date (ISO format)
            user_id (str, optional): Filter by user (seller)
            customer_id (str, optional): Filter by customer
            
        Returns:
            dict: Sales report data
        """
        # Base query for sales
        query = """
            SELECT 
                i.invoice_id,
                i.invoice_number,
                i.created_at as sale_date,
                i.total_amount,
                i.status,
                u.username as seller_name,
                c.full_name as customer_name,
                COALESCE(p.total_paid, 0) as amount_paid,
                (CASE WHEN i.total_amount <= COALESCE(p.total_paid, 0) 
                     THEN true ELSE false END) as is_fully_paid
            FROM invoices i
            JOIN users u ON i.user_id = u.user_id
            LEFT JOIN customers c ON i.customer_id = c.customer_id
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) as total_paid
                FROM payments
                GROUP BY invoice_id
            ) p ON i.invoice_id = p.invoice_id
            WHERE i.status = 'COMPLETED'
        """
        params = []
        
        # Add date filters
        if date_from:
            query += " AND i.created_at >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND i.created_at <= %s"
            params.append(date_to)
        
        # Add user filter
        if user_id:
            query += " AND i.user_id = %s"
            params.append(user_id)
        
        # Add customer filter
        if customer_id:
            query += " AND i.customer_id = %s"
            params.append(customer_id)
        
        # Add ORDER BY clause
        query += " ORDER BY i.created_at DESC"
        
        # Execute query
        sales = self.db.fetch_all(query, tuple(params))
        
        # Get summary data
        summary_query = """
            SELECT 
                COUNT(i.invoice_id) as total_invoices,
                SUM(i.total_amount) as total_sales,
                AVG(i.total_amount) as average_sale,
                COUNT(DISTINCT i.customer_id) as unique_customers,
                COUNT(DISTINCT i.user_id) as unique_sellers
            FROM invoices i
            WHERE i.status = 'COMPLETED'
        """
        summary_params = []
        
        # Add date filters
        if date_from:
            summary_query += " AND i.created_at >= %s"
            summary_params.append(date_from)
        
        if date_to:
            summary_query += " AND i.created_at <= %s"
            summary_params.append(date_to)
        
        # Add user filter
        if user_id:
            summary_query += " AND i.user_id = %s"
            summary_params.append(user_id)
        
        # Add customer filter
        if customer_id:
            summary_query += " AND i.customer_id = %s"
            summary_params.append(customer_id)
        
        # Execute summary query
        summary = self.db.fetch_one(summary_query, tuple(summary_params))
        
        # Combine results
        return {
            "sales": sales,
            "summary": summary
        }
    
    def get_inventory_report(self, category_id=None, low_stock_only=False):
        """Get an inventory report.
        
        Args:
            category_id (str, optional): Filter by category
            low_stock_only (bool, optional): Only include low stock items
            
        Returns:
            dict: Inventory report data
        """
        query = """
            SELECT 
                p.product_id,
                p.name,
                p.sku,
                p.barcode,
                c.name as category_name,
                p.purchase_price,
                p.selling_price,
                COALESCE(s.quantity, 0) as stock_quantity,
                p.low_stock_threshold,
                (COALESCE(s.quantity, 0) < p.low_stock_threshold) as is_low_stock,
                (p.selling_price - p.purchase_price) as profit_margin,
                (COALESCE(s.quantity, 0) * p.purchase_price) as stock_value
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN stock s ON p.product_id = s.product_id
            WHERE p.is_active = true
        """
        params = []
        
        # Add category filter
        if category_id:
            query += " AND p.category_id = %s"
            params.append(category_id)
        
        # Add low stock filter
        if low_stock_only:
            query += " AND COALESCE(s.quantity, 0) < p.low_stock_threshold"
        
        # Add ORDER BY clause
        query += " ORDER BY p.name"
        
        # Execute query
        inventory = self.db.fetch_all(query, tuple(params))
        
        # Get summary data
        summary_query = """
            SELECT 
                COUNT(p.product_id) as total_products,
                SUM(COALESCE(s.quantity, 0)) as total_units,
                SUM(COALESCE(s.quantity, 0) * p.purchase_price) as total_value,
                COUNT(CASE WHEN COALESCE(s.quantity, 0) < p.low_stock_threshold THEN 1 END) as low_stock_count,
                COUNT(CASE WHEN COALESCE(s.quantity, 0) = 0 THEN 1 END) as out_of_stock_count,
                AVG(p.selling_price - p.purchase_price) as average_margin
            FROM products p
            LEFT JOIN stock s ON p.product_id = s.product_id
            WHERE p.is_active = true
        """
        summary_params = []
        
        # Add category filter
        if category_id:
            summary_query += " AND p.category_id = %s"
            summary_params.append(category_id)
        
        # Execute summary query
        summary = self.db.fetch_one(summary_query, tuple(summary_params))
        
        # Combine results
        return {
            "inventory": inventory,
            "summary": summary
        }
    
    def get_financial_report(self, date_from=None, date_to=None):
        """Get a financial report for a period.
        
        Args:
            date_from (str, optional): Start date (ISO format)
            date_to (str, optional): End date (ISO format)
            
        Returns:
            dict: Financial report data
        """
        # Set default date range if not provided
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).isoformat()
        
        if not date_to:
            date_to = datetime.now().isoformat()
        
        # Get sales data
        sales_query = """
            SELECT 
                DATE_TRUNC('day', i.created_at) as date,
                COUNT(i.invoice_id) as invoice_count,
                SUM(i.total_amount) as total_sales
            FROM invoices i
            WHERE i.status = 'COMPLETED'
              AND i.created_at BETWEEN %s AND %s
            GROUP BY DATE_TRUNC('day', i.created_at)
            ORDER BY date
        """
        daily_sales = self.db.fetch_all(sales_query, (date_from, date_to))
        
        # Get payment method breakdown
        payment_query = """
            SELECT 
                p.payment_method,
                COUNT(p.payment_id) as count,
                SUM(p.amount) as total
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.invoice_id
            WHERE i.status = 'COMPLETED'
              AND p.payment_date BETWEEN %s AND %s
            GROUP BY p.payment_method
            ORDER BY total DESC
        """
        payment_methods = self.db.fetch_all(payment_query, (date_from, date_to))
        
        # Get cost and profit data
        profit_query = """
            SELECT 
                SUM(ii.quantity * p.purchase_price) as total_cost,
                SUM(ii.subtotal) as total_revenue,
                SUM(ii.subtotal - (ii.quantity * p.purchase_price)) as gross_profit
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.product_id
            JOIN invoices i ON ii.invoice_id = i.invoice_id
            WHERE i.status = 'COMPLETED'
              AND i.created_at BETWEEN %s AND %s
        """
        profit_data = self.db.fetch_one(profit_query, (date_from, date_to))
        
        # Get top selling products
        top_products_query = """
            SELECT 
                p.product_id,
                p.name,
                p.sku,
                SUM(ii.quantity) as quantity_sold,
                SUM(ii.subtotal) as total_sales,
                SUM(ii.subtotal - (ii.quantity * p.purchase_price)) as profit
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.product_id
            JOIN invoices i ON ii.invoice_id = i.invoice_id
            WHERE i.status = 'COMPLETED'
              AND i.created_at BETWEEN %s AND %s
            GROUP BY p.product_id, p.name, p.sku
            ORDER BY quantity_sold DESC
            LIMIT 10
        """
        top_products = self.db.fetch_all(top_products_query, (date_from, date_to))
        
        # Get overall summary
        summary_query = """
            SELECT 
                COUNT(i.invoice_id) as total_invoices,
                SUM(i.total_amount) as total_sales,
                COUNT(DISTINCT i.customer_id) as unique_customers,
                AVG(i.total_amount) as average_sale,
                (SELECT COUNT(*) FROM invoices 
                 WHERE status = 'COMPLETED' AND created_at BETWEEN %s AND %s
                 AND total_amount > (SELECT AVG(total_amount) FROM invoices 
                                    WHERE status = 'COMPLETED' 
                                    AND created_at BETWEEN %s AND %s)) as above_average_sales
            FROM invoices i
            WHERE i.status = 'COMPLETED'
              AND i.created_at BETWEEN %s AND %s
        """
        summary = self.db.fetch_one(summary_query, (date_from, date_to, date_from, date_to, date_from, date_to))
        
        # Combine results
        return {
            "daily_sales": daily_sales,
            "payment_methods": payment_methods,
            "profit_data": profit_data,
            "top_products": top_products,
            "summary": summary,
            "date_range": {
                "from": date_from,
                "to": date_to
            }
        }
    
    def get_debt_report(self):
        """Get a report on customer debts.
        
        Returns:
            dict: Debt report data
        """
        # Get debts by customer
        customer_query = """
            SELECT 
                c.customer_id,
                c.full_name,
                c.phone,
                COUNT(cd.debt_id) as debt_count,
                SUM(cd.amount - cd.amount_paid) as total_outstanding,
                MAX(cd.created_at) as latest_debt_date,
                MIN(cd.created_at) as oldest_debt_date,
                EXTRACT(DAY FROM NOW() - MIN(cd.created_at)) as max_days_outstanding
            FROM customer_debts cd
            JOIN customers c ON cd.customer_id = c.customer_id
            WHERE cd.is_paid = false
            GROUP BY c.customer_id, c.full_name, c.phone
            ORDER BY total_outstanding DESC
        """
        customers_with_debt = self.db.fetch_all(customer_query)
        
        # Get debts by age
        age_query = """
            SELECT 
                COUNT(*) as total_debts,
                SUM(amount - amount_paid) as total_amount,
                COUNT(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) <= 30 THEN 1 END) as debts_0_30_days,
                SUM(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) <= 30 THEN (amount - amount_paid) ELSE 0 END) as amount_0_30_days,
                COUNT(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) BETWEEN 31 AND 60 THEN 1 END) as debts_31_60_days,
                SUM(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) BETWEEN 31 AND 60 THEN (amount - amount_paid) ELSE 0 END) as amount_31_60_days,
                COUNT(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) BETWEEN 61 AND 90 THEN 1 END) as debts_61_90_days,
                SUM(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) BETWEEN 61 AND 90 THEN (amount - amount_paid) ELSE 0 END) as amount_61_90_days,
                COUNT(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) > 90 THEN 1 END) as debts_over_90_days,
                SUM(CASE WHEN EXTRACT(DAY FROM (NOW() - created_at)) > 90 THEN (amount - amount_paid) ELSE 0 END) as amount_over_90_days
            FROM customer_debts
            WHERE is_paid = false
        """
        debt_age_summary = self.db.fetch_one(age_query)
        
        # Recent debt payments
        payments_query = """
            SELECT 
                cd.debt_id,
                c.full_name as customer_name,
                cd.amount,
                cd.amount_paid,
                (cd.amount - cd.amount_paid) as remaining,
                cd.created_at as debt_date,
                cd.last_payment_date,
                u.username as created_by_name
            FROM customer_debts cd
            JOIN customers c ON cd.customer_id = c.customer_id
            LEFT JOIN users u ON cd.created_by = u.user_id
            WHERE cd.is_paid = false
              AND cd.amount_paid > 0
            ORDER BY cd.last_payment_date DESC
            LIMIT 10
        """
        recent_payments = self.db.fetch_all(payments_query)
        
        # Overall debt summary
        summary_query = """
            SELECT 
                COUNT(*) as total_debts,
                COUNT(DISTINCT customer_id) as total_customers_with_debt,
                SUM(amount) as total_debt_value,
                SUM(amount_paid) as total_amount_paid,
                SUM(amount - amount_paid) as total_outstanding,
                AVG(amount - amount_paid) as average_debt_amount,
                MAX(amount - amount_paid) as largest_debt
            FROM customer_debts
            WHERE is_paid = false
        """
        summary = self.db.fetch_one(summary_query)
        
        # Combine results
        return {
            "customers_with_debt": customers_with_debt,
            "debt_age_summary": debt_age_summary,
            "recent_payments": recent_payments,
            "summary": summary
        }
    
    def get_user_performance_report(self, date_from=None, date_to=None):
        """Get a report on user sales performance.
        
        Args:
            date_from (str, optional): Start date (ISO format)
            date_to (str, optional): End date (ISO format)
            
        Returns:
            dict: User performance report data
        """
        # Set default date range if not provided
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).isoformat()
        
        if not date_to:
            date_to = datetime.now().isoformat()
        
        # Get user sales data
        user_query = """
            SELECT 
                u.user_id,
                u.username,
                u.full_name,
                COUNT(i.invoice_id) as total_sales,
                SUM(i.total_amount) as total_amount,
                AVG(i.total_amount) as average_sale,
                COUNT(DISTINCT i.customer_id) as unique_customers,
                (SELECT COUNT(*) FROM invoices 
                 WHERE user_id = u.user_id AND status = 'COMPLETED'
                 AND created_at BETWEEN %s AND %s
                 AND total_amount > (SELECT AVG(total_amount) FROM invoices 
                                    WHERE status = 'COMPLETED'
                                    AND created_at BETWEEN %s AND %s)) as above_average_sales
            FROM users u
            LEFT JOIN invoices i ON u.user_id = i.user_id
                               AND i.status = 'COMPLETED'
                               AND i.created_at BETWEEN %s AND %s
            GROUP BY u.user_id, u.username, u.full_name
            ORDER BY total_amount DESC NULLS LAST
        """
        users = self.db.fetch_all(user_query, (date_from, date_to, date_from, date_to, date_from, date_to))
        
        # Get sales by day of week
        day_of_week_query = """
            SELECT 
                u.username,
                EXTRACT(DOW FROM i.created_at) as day_of_week,
                COUNT(i.invoice_id) as sales_count,
                SUM(i.total_amount) as total_amount
            FROM invoices i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.status = 'COMPLETED'
              AND i.created_at BETWEEN %s AND %s
            GROUP BY u.username, EXTRACT(DOW FROM i.created_at)
            ORDER BY u.username, day_of_week
        """
        day_of_week_data = self.db.fetch_all(day_of_week_query, (date_from, date_to))
        
        # Get sales by hour of day
        hour_query = """
            SELECT 
                u.username,
                EXTRACT(HOUR FROM i.created_at) as hour_of_day,
                COUNT(i.invoice_id) as sales_count,
                SUM(i.total_amount) as total_amount
            FROM invoices i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.status = 'COMPLETED'
              AND i.created_at BETWEEN %s AND %s
            GROUP BY u.username, EXTRACT(HOUR FROM i.created_at)
            ORDER BY u.username, hour_of_day
        """
        hour_of_day_data = self.db.fetch_all(hour_query, (date_from, date_to))
        
        # Get top selling products by user
        top_products_query = """
            SELECT 
                u.username,
                p.name as product_name,
                SUM(ii.quantity) as quantity_sold,
                SUM(ii.subtotal) as total_sales
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.product_id
            JOIN invoices i ON ii.invoice_id = i.invoice_id
            JOIN users u ON i.user_id = u.user_id
            WHERE i.status = 'COMPLETED'
              AND i.created_at BETWEEN %s AND %s
            GROUP BY u.username, p.name
            ORDER BY u.username, quantity_sold DESC
        """
        top_products = self.db.fetch_all(top_products_query, (date_from, date_to))
        
        # Structure the top products by user
        user_products = {}
        for row in top_products:
            username = row["username"]
            if username not in user_products:
                user_products[username] = []
            
            if len(user_products[username]) < 5:  # Limit to 5 top products per user
                user_products[username].append(row)
        
        # Combine results
        return {
            "users": users,
            "day_of_week_data": day_of_week_data,
            "hour_of_day_data": hour_of_day_data,
            "user_products": user_products,
            "date_range": {
                "from": date_from,
                "to": date_to
            }
        }
