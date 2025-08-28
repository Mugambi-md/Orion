from connect_to_db import connect_db
from datetime import datetime, date
from decimal import Decimal
class SalesManager:
    def __init__(self, conn):
        self.conn = conn
    def record_sale(self, user, sale_items, payment_method, amount_paid):
        if not self.conn:
            return False, "Database connection failed."
        try:
            with self.conn.cursor() as cursor:
                # Get user code from logins table
                cursor.execute("SELECT user_code FROM logins WHERE username = %s", (user,))
                result = cursor.fetchone()
                if not result:
                    return False, f"User '{user}' not found in logins table."
                user_code = result[0]
                # Generate receipt no: <user_code><YYYYMMDD><HHMMSS>
                now = datetime.now()
                receipt_no = f"{user_code}{now.strftime('%y%m%d%H%M%S')}"
                sale_date = now.date()
                sale_time = now.time().replace(microsecond=0)
                # 1. Calculate total amount
                total_amount = sum(item['quantity'] * item['unit_price'] for item in sale_items)
                # Insert into sales table with sale_date = today
                cursor.execute("""INSERT INTO sales (receipt_no, sale_date, sale_time, total_amount, user)
                                VALUES (%s, %s, %s, %s, %s)
                                """, (receipt_no, sale_date, sale_time, total_amount, user))
                # Insert each sale item into sale_items table
                for item in sale_items:
                    cursor.execute("""
                    INSERT INTO sale_items (date, time, receipt_no, product_code, product_name, quantity,
                            unit_price, user)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        sale_date,
                        sale_time,
                        receipt_no,
                        item['product_code'],
                        item['product_name'],
                        item['quantity'],
                        item['unit_price'],
                        user
                    ))
                    # Reduce quantity in product and replenishments table
                    cursor.execute("""
                            UPDATE products
                            SET quantity = quantity - %s
                            WHERE product_code=%s
                            """, (item['quantity'], item['product_code']))
                    cursor.execute("""
                        UPDATE replenishments
                        SET quantity = quantity - %s
                        WHERE product_code = %s
                        """, (item['quantity'], item['product_code']))
                    # Insert into product_control logs
                    description= f"Sale Receipt no.-{receipt_no}"
                    cursor.execute("""
                        INSERT INTO product_control_logs (log_date, product_code, product_name, description, quantity, total, user)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                        sale_date,
                        item['product_code'],
                        item['product_name'],
                        description,
                        item['quantity'],
                        item['quantity'] * item['unit_price'],
                        user
                    ))
                # Record payment in payments
                cursor.execute("""
                        INSERT INTO payments (user, receipt_no, payment_date, amount_paid, payment_method)
                        VALUES (%s, %s, %s, %s, %s)
                        """, (user, receipt_no, sale_date, amount_paid, payment_method))
                status = insert_to_sale_control(self.conn, receipt_no, user, total_amount, "Sale")
                if "error" in status.lower():
                    self.conn.rollback()
                    return False, status
            self.conn.commit()
            return True, receipt_no
        except Exception as e:
            self.conn.rollback()
            return False, f"Error recording sale: {e}"


def fetch_sales_product(product_code):
    """Fetch product details by product code."""
    try:
        conn = connect_db()
        cursor =conn.cursor()
        cursor.execute("""SELECT product_code, product_name, quantity, wholesale_price, retail_price
                       FROM products
                       WHERE product_code=%s
                       """, (product_code,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result
        else:
            return f"No Product found with code: {product_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def search_products(conn, field, keyword):
    """Search products by field (e.g., 'product_name' or 'product_code')
    using like %keyword%."""
    pattern = f"%{keyword}%"
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"""
            SELECT product_code, product_name, quantity, wholesale_price, retail_price
            FROM products
            WHERE {field} LIKE %s
            ORDER BY {field}
            LIMIT 15
            """, (pattern,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Error searching products: {e}")
        return []
def search_product(conn, field, keyword):
    """Search products by field (e.g., 'product_name' or 'product_code') using like %keyword%."""
    pattern = f"{keyword}%"
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"""
            SELECT product_code, product_name
            FROM products
            WHERE {field} LIKE %s
            ORDER BY {field}
            LIMIT 15
            """, (pattern,))
            return cursor.fetchall()
    except Exception as e:
        return f"Error searching: {str(e)}" or None

def insert_to_sale_control(conn, receipt_no, user, amount, description="Sale"):
    today = date.today()
    first_day = today.replace(day=1)
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Remove previous "Balance brought down"
            amount = Decimal(str(amount))
            cursor.execute("""
                DELETE FROM sales_control
                WHERE description = 'Balance Brought Down' AND date BETWEEN %s AND %s
                """, (first_day, today))
            # Fetch last cumulative total
            cursor.execute("""
                    SELECT cumulative_total FROM sales_control
                    WHERE date BETWEEN %s AND %s
                    ORDER BY id DESC LIMIT 1
                    """, (first_day, today))
            last = cursor.fetchone()
            # If no previous record this month, insert balance carried down
            if not last:
                cursor.execute("""
                    INSERT INTO sales_control (date, receipt_no, description, user, amount, cumulative_total)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, (first_day, None, "Balance Carried Down", "System", 0, 0))
                previous_total = 0
            else:
                previous_total =last["cumulative_total"]
            # Compute new cumulative total
            if description.lower() == "sale":
                new_total = previous_total + amount
            elif description.lower() == "sale reversal":
                new_total = previous_total - amount
            else:
                new_total = previous_total # Fall back
            # Insert sale or reversal
            cursor.execute("""
                INSERT INTO sales_control (date, receipt_no, description, user, amount, cumulative_total)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (today, receipt_no, description, user, amount, new_total))
            # Insert balance brought Down
            cursor.execute("""INSERT INTO sales_control (date, receipt_no, description, user, amount, cumulative_total)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """, (today, None, "Balance Brought Down", "System", 0, new_total))
            conn.commit()
            return "Sale control updates successfully."
    except Exception as e:
        conn.rollback()
        return f"Error updating to sales control: {e}"

def fetch_sales_control_by_month(conn, year, month):
    try:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""SELECT date, receipt_no, description, user, amount, cumulative_total
                    FROM sales_control
                    WHERE date >= %s AND date < %s
                    ORDER BY date ASC, id ASC
                    """, (start_date, end_date))
            return cursor.fetchall()
    except Exception as e:
        return [], f"{e}"

def fetch_sales_last_24_hours(conn, username):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT sale_date, sale_time, receipt_no, total_amount, user
                FROM sales 
                WHERE CONCAT(sale_date, ' ', sale_time) >= NOW()- INTERVAL 1 DAY AND user = %s
                ORDER BY sale_date DESC, sale_time DESC
                """, (username,))
            return cursor.fetchall(), None
    except Exception as e:
        return [], str(e)
def fetch_sales_by_month_and_user(conn, year, month, username):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                    SELECT date, receipt_no, description, amount
                    FROM sales_control
                    WHERE YEAR(date) = %s AND MONTH(date) = %s AND user = %s
                    ORDER BY date ASC
                    """, (year, month, username))
            return cursor.fetchall(), None
    except Exception as e:
        return None, f"Error fetching data: {str(e)}"

def fetch_all_sales_users(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT user FROM sales ORDER BY user ASC")
            rows = cursor.fetchall()
            return [row[0] for row in rows if row[0]]
    except Exception as e:
        return [], f"{e}"

def fetch_receipt_data(conn, receipt_no):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM sales WHERE receipt_no=%s", (receipt_no,))
            sale = cursor.fetchone()
            if not sale:
                return None, []
            # Fetch sale items
            cursor.execute("""
                    SELECT date, time, product_code, product_name, quantity, unit_price, total_amount
                    FROM sale_items WHERE receipt_no=%s
                    """, (receipt_no,))
            items = cursor.fetchall()
            return sale, items
    except Exception as e:
        raise e

def fetch_sales_by_year(conn, year, month=None, product_name=None, user=None):
    """Fetch sales data for a given year, with option to filter by month,
    user and product name."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT
                    user,
                    date,
                    receipt_no,
                    product_code,
                    product_name,
                    quantity,
                    unit_price,
                    total_amount
                FROM sale_items
                WHERE YEAR(date) = %s
            """
            params = [year]
            # Optional filters
            if month:
                query += " AND MONTH(date) = %s"
                params.append(month)
            if product_name:
                query += " AND product_name = %s"
                params.append(product_name)
            if user:
                query += " AND user = %s"
                params.append(user)
            query += " ORDER BY date ASC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return rows, None
    except Exception as e:
        return [], str(e)

def fetch_filter_values(conn):
    """Fetch distinct product names and users from sales table."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT product_name
                FROM sale_items
                ORDER BY product_name
            """)
            product_names = [row[0] for row in cursor.fetchall()]
            cursor.execute("""
                SELECT DISTINCT user
                FROM sale_items
                ORDER BY user
            """)
            users = [row[0] for row in cursor.fetchall()]
            # Fetch years from date column
            cursor.execute("""
                SELECT DISTINCT YEAR(date) AS year
                FROM sale_items
                ORDER BY year DESC
            """)
            years = [row[0] for row in cursor.fetchall()]
        return product_names, users, years, None
    except Exception as e:
        return [], [], [], str(e)
