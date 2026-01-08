

PRODUCT_COLUMNS = """
        product_code,
        product_name,
        quantity,
        cost,
        wholesale_price,
        retail_price,
        min_stock_level,
        date_replenished
        """

class FetchSummary:
    def __init__(self, conn):
        self.conn = conn

    def fetch_low_stock_count(self):
        """Returns the number of products where quantity is less
        or equal to min stock level."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM products
                    WHERE quantity <= min_stock_level AND is_active = 1;
                """)
                result = cursor.fetchone()
                return result["count"], None
        except Exception as e:
            return None, f"Error fetching low stock count: {str(e)}."

    def fetch_low_stock_products(self):
        """Returns Items Fallen or equal to min stock level."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute(f"""
                    SELECT {PRODUCT_COLUMNS}
                    FROM products
                    WHERE quantity <= min_stock_level AND is_active = 1
                    ORDER BY quantity ASC;
                """)
                return cursor.fetchall(), None
        except Exception as e:
            return None, f"Error Fetching Low Stock Items: {str(e)}."

    def fetch_low_stock_warning_count(self):
        """Counts product where quantity is > min stock level
        and <= min stock level * 1.5"""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM products
                    WHERE quantity > min_stock_level AND is_active = 1
                        AND quantity <= (min_stock_level * 1.5);
                """)
                result = cursor.fetchone()
                return result["count"], None
        except Exception as e:
            return None, f"Error Fetching Stock Warning: {str(e)}."

    def fetch_low_stock_warning_products(self):
        """Returns products where quantity is > min stock level
        and <= min stock level * 1.5"""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute(f"""
                    SELECT {PRODUCT_COLUMNS} FROM products
                    WHERE quantity > min_stock_level AND is_active = 1
                        AND quantity <= (min_stock_level * 1.5);
                """)
                result = cursor.fetchall()
                return result, None
        except Exception as e:
            return None, f"Error Fetching Stock Warning Products: {str(e)}."


    def fetch_total_products(self):
        """Returns Total number of products in stock."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM products
                    WHERE quantity > 0;
                """)
                result = cursor.fetchone()
                return result["count"], None
        except Exception as e:
            return None, f"Error Fetching Total Products: {str(e)}."

    def fetch_out_of_stock_count(self):
        """Returns number of Products with zero Quantity."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM products
                    WHERE quantity = 0 AND is_active = 1;
                """)
                result = cursor.fetchone()
                return result["count"], None
        except Exception as e:
            return None, f"Error Fetching Out of Stock Counts: {str(e)}."

    def fetch_out_of_stock_products(self):
        """Returns Products with zero Quantity."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute(f"""
                    SELECT {PRODUCT_COLUMNS} FROM products
                    WHERE quantity = 0 AND is_active = 1
                    ORDER BY product_name;
                """)
                result = cursor.fetchall()
                return result, None
        except Exception as e:
            return None, f"Error Fetching Out of Stock Products: {str(e)}."

    def fetch_inactive_products_count(self):
        """Returns number of Inactive products."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM products
                    WHERE is_active = 0;
                """)
                result = cursor.fetchone()
                return result["count"], None
        except Exception as e:
            return None, f"Error Fetching Inactive Products: {str(e)}."

    def fetch_total_inventory_value(self):
        """Returns Total inventory value (quantity * cost)."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT SUM(quantity * cost) AS total_value
                    FROM products
                    WHERE is_active = 1;
                """)
                result = cursor.fetchone()
                return result["total_value"] or 0, None
        except Exception as e:
            return None, f"Error Fetching Stock Value: {str(e)}."

    def fetch_all_stock_products(self):
        """Returns All Products with Above zero Quantity."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute(f"""
                    SELECT {PRODUCT_COLUMNS} FROM products
                    WHERE quantity > 0
                    ORDER BY product_name;
                """)
                result = cursor.fetchall()
                return result, None
        except Exception as e:
            return None, f"Error Fetching All Stock Products: {str(e)}."

    def fetch_unsold_product_count(self, year=None, month=None):
        """Counts product that have Not Been sold.
        Year & month Optional filters."""
        try:
            query = """
                SELECT COUNT(*) AS count
                FROM products p
                WHERE is_active = 1 AND NOT EXISTS (
                    SELECT 1
                    FROM sale_items s
                    WHERE s.product_code = p.product_code
            """
            params = []
            # Optional filters inside sale_items
            if year is not None:
                query += " AND YEAR(s.date) = %s"
                params.append(year)
            if month is not None:
                query += " AND MONTH(s.date) = %s"
                params.append(month)
            query += ")"

            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result["count"], None
        except Exception as e:
            return None, f"Error Fetching Unsold Products: {str(e)}."

    def fetch_unsold_products(self, year=None, month=None):
        """
        Products that have Not Been sold. Year & month Optional filters.
        """
        try:
            query = f"""
                SELECT {PRODUCT_COLUMNS}
                FROM products p
                WHERE is_active = 1 AND NOT EXISTS (
                    SELECT 1
                    FROM sale_items s
                    WHERE s.product_code = p.product_code
            """
            params = []
            # Optional filters inside sale_items
            if year is not None:
                query += " AND YEAR(s.date) = %s"
                params.append(year)
            if month is not None:
                query += " AND MONTH(s.date) = %s"
                params.append(month)
            query += ") ORDER BY p.product_name"

            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
                return result, None
        except Exception as e:
            return None, f"Error Fetching Unsold Products: {str(e)}."

    def fetch_disabled_user_count(self):
        """Returns number of disabled users."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM logins
                    WHERE status = "disabled";
                """)
                result = cursor.fetchone()
                return result["count"], None
        except Exception as e:
            return None, f"Error Fetching Disabled Users No.: {str(e)}."

    def fetch_disabled_users(self):
        """Returns users that are disabled from accessing system."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                SELECT e.name, e.username, e.department, e.designation,
                    e.phone, e.email, l.user_code, l.status
                FROM employees e
                JOIN logins l ON e.username = l.username
                WHERE l.status = 'disabled'
                ORDER BY l.user_code ASC;
                """)
                result = cursor.fetchall()
                return result, None
        except Exception as e:
            return None, f"Error Fetching Disabled Users: {str(e)}."

    def fetch_active_users_count(self):
        """Returns number of disabled users."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM logins
                    WHERE status = "Active";
                """)
                result = cursor.fetchone()
                return result["count"], None
        except Exception as e:
            return None, f"Error Fetching Active Users No.: {str(e)}."

    def fetch_active_users(self):
        """Returns users that are disabled from accessing system."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                SELECT e.name, e.username, e.department, e.designation,
                    e.phone, e.email, l.user_code, l.status
                FROM employees e
                JOIN logins l ON e.username = l.username
                WHERE l.status = 'Active'
                ORDER BY l.user_code ASC;
                """)
                result = cursor.fetchall()
                return result, None
        except Exception as e:
            return None, f"Error Fetching Active Users: {str(e)}."

    def fetch_pending_orders_count(self):
        """Returns number of disabled users."""
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM orders
                    WHERE status = "Pending";
                """)
                result = cursor.fetchone()
                return result["count"], None
        except Exception as e:
            return None, f"Error Fetching Pending Orders Count: {str(e)}."



if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    summary = FetchSummary(conn)
    orders, error = summary.fetch_pending_orders_count()
    if not error:
        print(orders)
        # for i, user in enumerate(users, start=1):
        #     print(i, user)
    else:
        print(error)