from datetime import datetime
from working_on_stock import get_total_cost_by_codes
from working_on_accounting import SalesJournalRecorder

class SalesManager:
    def __init__(self, conn):
        self.conn = conn
        self.accounts = {
            "Sales Revenue": {"type": "Revenue",
                              "description": "Income from sales"},
            "Cash": {"type": "Asset", "description": "Cash In Hand"},
            "Inventory": {"type": "Asset", "description": "Stock Value"}
        }

    def finalize_sales(self, receipt_no, amount_paid, cost):
        """Finalize the sale by recording journal entries in the
        accounting system."""
        recorder = SalesJournalRecorder(self.conn)
        transaction_lines = [
            {"account_name": "Cash", "debit": float(amount_paid),
             "credit": 0, "description": "Cash Sales"},
            {"account_name": "Sales Revenue", "debit": 0,
             "credit": float(amount_paid), "description": "Sales."},
            {"account_name": "Inventory", "debit": 0,
             "credit": float(cost), "description": "Sales."}
        ]
        return recorder.record_sales(self.accounts, transaction_lines,
                                     receipt_no)

    def record_sale(self, user, sale_items, payment_method, amount_paid):
        """Record a complete sale transaction including: sales, sales items,
        stock updates, payment entry, cost of goods sold, journal entries."""
        if not self.conn:
            return False, "Database connection failed."
        try:
            with self.conn.cursor() as cursor:
                # Get user code from logins table
                cursor.execute("""
                SELECT user_code FROM logins WHERE username = %s;
                """, (user,))
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
                total_amount = sum(
                    item["quantity"] * item["unit_price"] for item in sale_items
                )
                # Insert into sales table with sale_date = today
                cursor.execute("""
                INSERT INTO sales (receipt_no, sale_date, sale_time,
                    total_amount, user)
                VALUES (%s, %s, %s, %s, %s)
                """, (receipt_no, sale_date, sale_time, total_amount, user))
                cogs_items = [] # List of product codes and quantity
                # Insert each sale item into sale_items table
                for item in sale_items:
                    cursor.execute("""
                    INSERT INTO sale_items (date, time, receipt_no,
                        product_code, product_name, quantity, unit_price,
                        user)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        sale_date,
                        sale_time,
                        receipt_no,
                        item["product_code"],
                        item["product_name"],
                        item["quantity"],
                        item["unit_price"],
                        user,
                    ))
                    # Reduce quantity in products
                    cursor.execute("""
                    UPDATE products
                    SET quantity = quantity - %s
                    WHERE product_code=%s
                    """, (item["quantity"], item["product_code"]))
                    # Insert into product_control logs
                    description = f"Sale Receipt no.-{receipt_no}"
                    cursor.execute("""
                    INSERT INTO product_control_logs (log_date, product_code,
                        product_name, description, quantity, total, user)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        sale_date,
                        item["product_code"],
                        item["product_name"],
                        description,
                        item["quantity"],
                        item["quantity"] * item["unit_price"],
                        user
                    ))
                    cogs_items.append({
                        "product_code": item["product_code"],
                        "quantity": item["quantity"]
                    })
                # Record payment in payments
                cursor.execute("""
                INSERT INTO payments (user, receipt_no, payment_date,
                    amount_paid, payment_method)
                VALUES (%s, %s, %s, %s, %s)
                """, (
                    user, receipt_no, sale_date, amount_paid, payment_method
                ))

            cost, error = get_total_cost_by_codes(self.conn, cogs_items)
            if error:
                self.conn.rollback()
                return False, f"Error Calculating Cost: {error}"
            # Record Journal entries
            success, err = self.finalize_sales(receipt_no, amount_paid, cost)
            if success:
                self.conn.commit()
                return True, receipt_no
            else:
                self.conn.rollback()
                return False, f"Error Recording Books of Accounts: {err}"
        except Exception as e:
            self.conn.rollback()
            return False, f"Error recording sale: {e!s}"


def fetch_sales_product(conn, product_code):
    """Fetch product details by product code."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
            SELECT product_code, product_name, quantity, wholesale_price,
                retail_price
            FROM products
            WHERE product_code=%s AND is_active = 1;
            """,
                (product_code,),
            )
            result = cursor.fetchone()
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
            cursor.execute(
                f"""
            SELECT product_code, product_name, quantity, wholesale_price, retail_price
            FROM products
            WHERE {field} LIKE %s AND is_active = 1
            ORDER BY {field}
            LIMIT 15
            """,
                (pattern,),
            )
            return cursor.fetchall()
    except Exception as e:
        print(f"Error searching products: {e}")
        return []


def search_product(conn, field, keyword):
    """Search products by field (e.g., 'product_name' or 'product_code') using like %keyword%."""
    pattern = f"{keyword}%"
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                f"""
            SELECT product_code, product_name
            FROM products
            WHERE {field} LIKE %s AND is_active = 1
            ORDER BY {field}
            LIMIT 15
            """,
                (pattern,),
            )
            return cursor.fetchall()
    except Exception as e:
        return f"Error searching: {str(e)}" or None


def fetch_sales_last_24_hours(conn, username):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT sale_date, sale_time, receipt_no, total_amount, user
                FROM sales 
                WHERE CONCAT(sale_date, ' ', sale_time) >= NOW()- INTERVAL 1 DAY AND user = %s
                ORDER BY sale_date DESC, sale_time DESC
                """,
                (username,),
            )
            return cursor.fetchall(), None
    except Exception as e:
        return [], str(e)


def fetch_sales_by_month_and_user(conn, year, month, user=None):
    """Fetch total sales grouped by day for given month/ year.
    Optionally filter by user."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT
                    sale_date,
                    SUM(total_amount) AS daily_total
                FROM sales
                WHERE YEAR(sale_date) = %s
                    AND MONTH(sale_date) = %s
                """
            params = [year, month]
            # Optional filter
            if user:
                query += " AND user = %s"
                params.append(user)
            query += " GROUP BY sale_date ORDER BY sale_date ASC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return rows, None
    except Exception as e:
        return [], str(e)


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
            cursor.execute(
                """
                    SELECT date, time, product_code, product_name, quantity, unit_price, total_amount
                    FROM sale_items WHERE receipt_no=%s
                    """,
                (receipt_no,),
            )
            items = cursor.fetchall()
            return sale, items
    except Exception as e:
        raise e


def fetch_sale_by_year(conn, year, month=None, user=None):
    """Fetch sales data for a given year, with option to filter by month and
    user."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT
                    sale_date,
                    receipt_no,
                    user,
                    total_amount
                FROM sales
                WHERE YEAR(sale_date) = %s
            """
            params = [year]
            # Optional filters
            if month:
                query += " AND MONTH(sale_date) = %s"
                params.append(month)
            if user:
                query += " AND user = %s"
                params.append(user)
            query += " ORDER BY sale_date ASC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return rows, None
    except Exception as e:
        return [], str(e)


def fetch_filter_values(conn):
    """Fetch distinct product names and users from sales table."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT user
                FROM sale_items
                ORDER BY user
            """
            )
            users = [row[0] for row in cursor.fetchall()]
            # Fetch years from date column
            cursor.execute(
                """
                SELECT DISTINCT YEAR(date) AS year
                FROM sale_items
                ORDER BY year DESC
            """
            )
            years = [row[0] for row in cursor.fetchall()]
        return users, years, None
    except Exception as e:
        return [], [], str(e)


def fetch_sales_summary_by_year(conn, year, month=None, user=None):
    """Fetch sales summary data for a given year, with option to filter
    by month and user. Group by product_code and product_name. Return
    total quantity, unit cost and total amount for each product."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT
                    si.product_code,
                    si.product_name,
                    SUM(si.quantity) AS total_quantity,
                    SUM(si.total_amount) AS total_amount,
                    p.cost AS unit_cost
                FROM sale_items si
                JOIN products p ON si.product_code = p.product_code
                WHERE YEAR(date) = %s
            """
            params = [year]
            # Optional filters
            if month:
                query += " AND MONTH(si.date) = %s"
                params.append(month)
            if user:
                query += " AND si.user = %s"
                params.append(user)
            query += """
                GROUP BY si.product_code, si.product_name, p.cost
                ORDER BY total_amount DESC"""
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return rows, None
    except Exception as e:
        return [], str(e)


def fetch_sales_items(conn, year, month=None, day=None, user=None):
    """Fetch sales items details by year with filters for: month, day
    and user. Returns a list of dicts."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT
                    date,
                    user,
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
            if month:
                query += " AND MONTH(date) = %s"
                params.append(month)
            if day:
                query += " AND DAY(date) = %s"
                params.append(day)
            if user:
                query += " AND user = %s"
                params.append(user)
            query += " ORDER BY date DESC, time DESC"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return rows, None
    except Exception as e:
        return [], str(e)


def insert_to_sale_control(conn, entries):
    try:
        now = datetime.now()
        s_date = now.date()
        s_time = now.time().strftime("%H:%M:%S")  # Time as HH:MM:SS
        # Normalize to list
        if isinstance(entries, dict):
            entries = [entries]
        values = [
            (
                s_date,
                s_time,
                e["product_code"],
                e["receipt_no"],
                e["description"],
                e["user"],
            )
            for e in entries
        ]
        with conn.cursor(dictionary=True) as cursor:
            cursor.executemany(
                """
            INSERT INTO sales_control (date, time, product_code, receipt_no,
                    description, user)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
                values,
            )
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)


def tag_reversal(conn, receipt, code, name, price, quantity, refund, user):
    try:
        s_date = datetime.today().date()
        with conn.cursor() as cursor:
            cursor.execute(
                """
            INSERT INTO sales_reversal (date, receipt_no, product_code,
                    product_name, unit_price, quantity, refund, tag)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (s_date, receipt, code, name, price, quantity, refund, user),
            )
            entry = {
                "product_code": code,
                "receipt_no": receipt,
                "description": "Tagged Reversal",
                "user": user,
            }
            success, err = insert_to_sale_control(conn, entry)
            if success:
                conn.commit()
                return True, "Reversal Tagged Successfully."
            else:
                conn.rollback()
                return False, f"Error Tagging Reversal: {str(err)}"
    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"


def authorize_reversal(conn, receipt_no, product_code, username):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE sales_reversal
                SET authorized = %s
                WHERE receipt_no = %s AND product_code = %s
            """, (username, receipt_no, product_code))

            entry = {
                "product_code": product_code,
                "receipt_no": receipt_no,
                "description": "Authorized reversal.",
                "user": username,
            }
            success, err = insert_to_sale_control(conn, entry)
            if success:
                conn.commit()
                return True, "Reversal authorized successfully."
            else:
                conn.rollback()
                return False, f"Error Authorizing Reversal: {str(err)}"
    except Exception as e:
        conn.rollback()
        return False, f"Error authorizing reversal: {str(e)}"


def reject_tagged_reversal(conn, receipt_no, product_code, username):
    """Reject tagged reversal instead of Authorizing it."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE sales_reversal
                SET authorized = %s, posted = %s
                WHERE receipt_no = %s AND product_code = %s
                    And tag IS NOT NULL;
            """, ("Rejected", "Rejected", receipt_no, product_code))
            if cursor.rowcount == 0:
                return False, "No Tagged Reversal Found to Reject."

            entry = {
                "product_code": product_code,
                "receipt_no": receipt_no,
                "description": "Rejected tagged reversal.",
                "user": username,
            }
            success, err = insert_to_sale_control(conn, entry)
            if success:
                conn.commit()
                return True, "Reversal Rejected Successfully."
            else:
                conn.rollback()
                return False, f"Error Rejecting Reversal: {str(err)}"
    except Exception as e:
        conn.rollback()
        return False, f"Error Rejecting Reversal: {str(e)}"


def delete_rejected_reversal(conn, receipt_no, product_code, username):
    """Delete a specific reversal where authorized = 'Rejected' using receipt,
    product code and user."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            DELETE FROM sales_reversal
            WHERE receipt_no = %s AND product_code = %s AND authorized =%s;
            """, (receipt_no, product_code, "Rejected"))

            if cursor.rowcount == 0:
                return False, "No matching rejected reversal found to Delete."

            entry = {
                "product_code": product_code,
                "receipt_no": receipt_no,
                "description": "Deleted Rejected Reversal.",
                "user": username,
            }
            success, err = insert_to_sale_control(conn, entry)
            if success:
                conn.commit()
                return True, "Rejected Reversal Deleted Successfully."
            else:
                conn.rollback()
                return False, f"Error Deleting rejected Reversal: {str(err)}"
    except Exception as e:
        conn.rollback()
        return False, f"Error Deleting Reversal: {str(e)}"


def post_reversal(conn, receipt, code, user, qty, price):
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Check if tag and authorized are filled
            cursor.execute("""
                SELECT tag, authorized, posted
                FROM sales_reversal
                WHERE receipt_no = %s AND product_code = %s
            """, (receipt, code))
            record = cursor.fetchone()
            if not record:
                return False, "Reversal Record not Found."
            if not record["tag"] or not record["authorized"]:
                return False, "Reversal Must be Tagged and Authorized for posting."
            if record["posted"]:
                return False, "Reversal Already posted."
            # Update sale item and related tables
            success, err = update_sale_item(conn, receipt, code, qty, price)
            if not success:
                conn.rollback()
                return False, f"Failed to update sale item: {err}"
            # Update posted column
            cursor.execute("""
                UPDATE sales_reversal
                SET posted = %s
                WHERE receipt_no = %s AND product_code = %s
            """, (user, receipt, code))

            entry = {
                "product_code": code,
                "receipt_no": receipt,
                "description": "Posted Sale Reversal.",
                "user": user,
            }
            success, err = insert_to_sale_control(conn, entry)
            if success:
                conn.commit()
                return True, "Reversal Posted successfully."
            else:
                conn.rollback()
                return False, f"Error Posting Reversal: {str(err)}"
    except Exception as e:
        conn.rollback()
        return False, f"Error Posting reversal: {str(e)}"


def update_sale_item(conn, receipt_no, product_code, quantity, unit_price):
    """Updates product quantity after reversal, reducing quantity sold,
    total sale amount and increasing available quantity."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Update the sale items record
            cursor.execute("""
                UPDATE sale_items
                SET quantity = GREATEST(quantity - %s, 0),
                    unit_price = %s
                WHERE receipt_no = %s AND product_code = %s
            """, (quantity, unit_price, receipt_no, product_code))
            # Reduce total amount in sales table using receipt number
            total_cost = quantity * unit_price
            cursor.execute("""
                UPDATE sales
                SET total_amount = GREATEST(total_amount - %s, 0)
                WHERE receipt_no = %s
            """, (total_cost, receipt_no))
            # Increase quantity in products table
            cursor.execute("""
                UPDATE products
                SET quantity = quantity + %s
                WHERE product_code = %s
            """, (quantity, product_code))
        recorder = SalesJournalRecorder(conn)
        accounts = {
            "Sales Revenue": {"type": "Revenue",
                              "description": "Income from sales"},
            "Cash": {"type": "Asset", "description": "Cash In Hand"},
            "Inventory": {"type": "Asset", "description": "Stock Value"}
        }
        lines = [
            {"account_name": "Cash", "debit": 0, "credit": total_cost,
             "description": "Sales Reversal"},
            {"account_name": "Sales Revenue", "debit": total_cost, "credit": 0,
             "description": "Sales Reversal."},
            {"account_name": "Inventory", "debit": total_cost, "credit": 0,
             "description": "Sales Reversal."}
        ]
        success, error =recorder.record_sales(accounts, lines, receipt_no)
        if not success:
            conn.rollback()
            return False, str(error)
        else:
            conn.commit()
            return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)


def get_retail_price(conn, product_code):
    """Fetch product details by product code."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT retail_price
            FROM products
            WHERE product_code=%s AND is_active = 1;
            """, (product_code,))
            result = cursor.fetchone()
            if result:
                return float(result[0])
            else:
                return None
    except Exception as e:
        return f"Error: {str(e)}"


def fetch_pending_reversals(conn, view_filter="Tagged"):
    """
    Fetch reversals based on filter:
        "Tagged" -> tagged is not null, authorized = null, posted = null
        "Authorized" -> tagged is not null, authorized is not null & not rejected
        "Rejected" -> fetch only where authorized = "Rejected" & posted= 'Rejected'
    """
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT date, receipt_no, product_code, product_name,
                    unit_price, quantity, refund, tag, authorized, posted
                FROM sales_reversal
                WHERE 1=1
                """
            params = []
            if view_filter == "Tagged":
                query += (
                    " AND tag is NOT NULL AND authorized is NULL AND posted IS NULL"
                )
            elif view_filter == "Authorized":
                query += """ AND tag IS NOT NULL AND authorized IS NOT NULL AND 
                authorized <> %s AND posted IS NULL"""
                params.append("Rejected")
            elif view_filter == "Rejected":
                query += " AND authorized = %s AND posted = %s"
                params.extend(["Rejected", "Rejected"])

            cursor.execute(query, params)
            return cursor.fetchall(), None
    except Exception as e:
        return None, str(e)

def fetch_reversals_by_month(conn, year, month):
    """Fetch all reversals from sales reversals for a given year and month."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT date, receipt_no, product_code, product_name, unit_price,
                quantity, refund, tag, authorized, posted
            FROM sales_reversal
            WHERE YEAR(date) = %s AND MONTH(date) = %s
            ORDER BY date DESC;
            """, (year, month))
            return cursor.fetchall(), None
    except Exception as e:
        return None, str(e)

def fetch_distinct_years(conn):
    """Fetch distinct years from sales reversal table.
    Returns a list of years."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT YEAR(date) AS year
                FROM sales_reversal
                ORDER BY year DESC;
                """)
            years = [row[0] for row in cursor.fetchall()]
            return years, None
    except Exception as e:
        return None, str(e)

from connect_to_db import connect_db

conn = connect_db()
# years, err = fetch_distinct_years(conn)
# if not err:
#     print("Years:", years)
# else:
#     print(err)
