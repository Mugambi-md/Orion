from datetime import date
from working_on_accounting import SalesJournalRecorder
from working_on_employee import insert_logs

def insert_new_product(conn, product, user):
    """Insert a new product into stock and product tables.
    ARGS: conn: Active DB connection.
        product: dictionary containing product fields
                    {"product_code": str,
                    "product_name": str,
                    ...,
                    ...,}
        user: Username performing the operation
        """
    now = date.today()
    code = product["product_code"]
    name = product["product_name"]
    desc = product["description"]
    cost = float(product["cost"])
    qty = int(product["quantity"])
    retail = float(product["retail_price"])
    wholesale = float(product["wholesale_price"])
    min_stock = int(product["min_stock_level"])
    recorder = SalesJournalRecorder(conn, user)
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO stock (product_code, product_name, retail_price,
                wholesale_price)
            VALUES (%s, %s, %s, %s);
            """,(code, name, retail, wholesale))
            cursor.execute("""
            INSERT INTO products (product_code, product_name, description,
                quantity, cost, wholesale_price,retail_price,
                min_stock_level, date_replenished)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (code, name, desc, qty, cost, wholesale, retail, min_stock,
                now))
        data = {
            "product_code": code,
            "description": f"Added New Product; {name} : {code}",
            "quantity": qty,
            "total": cost,
            "user": user
        }
        success, message = log_stock_change(conn, data)
        if not success:
            conn.rollback()
            return f"Error Updating Product Log: {message}"
        else:
            cost = qty * cost
            ref = f"{code} {name}"
            accounts = {
                "Cash": {"type": "Asset", "description": "Cash In Hand"},
                "Inventory": {"type": "Asset", "description": "Stock Value"}
            }
            lines = [
                {"account_name": "Cash", "debit": 0, "credit": cost,
                 "description": "Inventory Replenishment (New Product)"},
                {"account_name": "Inventory", "debit": cost, "credit": 0,
                 "description": "Replenishment (New Product)."}
            ]
            description = f"Added New Product ({name})."
            success, err = recorder.record_sales(accounts, lines, ref, description)
            if not success:
                conn.rollback()
                return False, f"Error Recording Books of Accounts: {err}."
            conn.commit()
            return True, f"New Product '{name}' inserted successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error Inserting New Product: {str(e)}."

def delete_product(conn, code, user):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE products
                SET is_active = 0
                WHERE product_code = %s;
                """, (code,))
        data = {
            "product_code": code,
            "description": f"Deleted Product Code; #{code}",
            "quantity": 0,
            "total": 0,
            "user": user
        }
        success, message = log_stock_change(conn, data)
        if not success:
            conn.rollback()
            return False, f"Error Updating Product Log: {message}."
        else:
            conn.commit()
            return True, f"Product code '{code}' deleted successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error deleting product: {str(e)}"

def restore_deleted_product(conn, code, user):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE products
                SET is_active = 1
                WHERE product_code = %s;
                """, (code,))
        data = {
            "product_code": code,
            "description": f"Restored Deleted Product Code; #{code}",
            "quantity": 0,
            "total": 0,
            "user": user
        }
        success, message = log_stock_change(conn, data)
        if not success:
            conn.rollback()
            return False, f"Error Updating Product Log: {message}."
        conn.commit()
        return True, f"Product code '{code}' deleted successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error deleting product: {str(e)}"

def update_quantity(conn, product_code, new_quantity, user):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE products
                SET quantity=%s
                WHERE product_code=%s
            """, (new_quantity, product_code))
        data = {
            "product_code": product_code,
            "description": "Updated Product Quantity",
            "quantity": new_quantity,
            "total": 0,
            "user": user
        }
        success, message = log_stock_change(conn, data)
        if success:
            conn.commit()
            return "Quantity updated successfully."
        else:
            conn.rollback()
            return f"Error Updating Product Log: {message}"
    except Exception as e:
        conn.rollback()
        return f"Error updating quantity: {str(e)}"

def add_to_existing_product(conn, product: dict, user: str):
    """Replenish an existing product (increase quantity, update prices if given).
    ARGS: conn -> MySQL connection object, product -> dict with product details,
    and user -> (str) user performing update. Returns (success: bool, message: str"""
    try:
        code = product["product_code"]
        add_qty = product.get("quantity", 0)
        date_filled = date.today()
        recorder = SalesJournalRecorder(conn, user)
        with conn.cursor() as cursor:
            # Fetch current details
            cursor.execute("""
            SELECT quantity, cost, wholesale_price, retail_price, min_stock_level
            FROM products WHERE product_code=%s AND is_active = 1;
            """, (code,))
            existing = cursor.fetchone() # Check in products table
            if not existing:
                return False, f"Product '{code}' not found in database."
            else:
                curr_quantity, curr_cost, curr_wholesale, curr_retail, curr_min_level = existing
            # Use current Values if none provided
            updated_quantity = curr_quantity + add_qty
            updated_cost = product.get("cost", curr_cost)
            updated_wholesale = product.get("wholesale_price", curr_wholesale)
            updated_retail = product.get("retail_price", curr_retail)
            updated_min_level = product.get("min_stock_level", curr_min_level)
            # Update Products Table
            cursor.execute("""
                UPDATE products
                SET quantity = %s,
                    cost = %s,
                    wholesale_price =%s,
                    retail_price = %s,
                    min_stock_level = %s,
                    date_replenished = %s
                WHERE product_code = %s;
                """, (updated_quantity, updated_cost, updated_wholesale,
                      updated_retail, updated_min_level, date_filled, code))
            # Update Stock Table
            cursor.execute("""
                UPDATE stock
                SET wholesale_price = %s,
                    retail_price = %s
                WHERE product_code = %s;
                """, (updated_wholesale, updated_retail, code))
        data = {
            "product_code": code,
            "description": "Replenished Item",
            "quantity": add_qty,
            "total": updated_quantity,
            "user": user
        }
        success, message = log_stock_change(conn, data)
        if not success:
            conn.rollback()
            return False, f"Error Updating Product Log: {message}."
        else:
            cost = add_qty * updated_cost
            ref = f"Replenishment of {code}"
            accounts = {
                "Cash": {"type": "Asset", "description": "Cash In Hand"},
                "Inventory": {"type": "Asset", "description": "Stock Value"}
            }
            lines = [
                {"account_name": "Cash", "debit": 0, "credit": cost,
                 "description": f"Inventory Replenishment {code}"},
                {"account_name": "Inventory", "debit": cost, "credit": 0,
                 "description": f"Replenishment {code}."}
            ]
            success, err = recorder.record_sales(
                accounts, lines, ref, "Replenishment"
            )
            if success:
                conn.commit()
                return True, f"Product '{code}' Replenished Successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error Replenishing Product: {str(e)}."

def update_price(conn, code, retail, wholesale, user):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE stock
                SET retail_price=%s, wholesale_price=%s
                WHERE product_code=%s
            """, (retail, wholesale, code))
            cursor.execute("""
                UPDATE products
                SET retail_price=%s, wholesale_price=%s
                WHERE product_code=%s
            """, (retail, wholesale, code))
        data = {
            "product_code": code,
            "description": "Changed Product Prices",
            "quantity": 0,
            "total": 0,
            "user": user
        }
        success, message = log_stock_change(conn, data)
        if success:
            conn.commit()
            return True, f"Price updated successfully for: {code}."
        else:
            conn.rollback()
            return False, f"Error Updating Product Log: {message}."
    except Exception as e:
        conn.rollback()
        return False, f"Error Updating Price: {str(e)}."

def update_description(conn, code, new_description, user):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE products SET description=%s where product_code=%s;",
                (new_description, code))
        data = {
            "product_code": code,
            "description": "Changed Product Description",
            "quantity": 0,
            "total": 0,
            "user": user
        }
        success, message = log_stock_change(conn, data)
        if success:
            conn.commit()
            return f"Description For {code} Updated successfully"
        else:
            conn.rollback()
            return f"Error Updating Product Log: {message}"
    except Exception as e:
        conn.rollback()
        raise e

def search_product_codes(conn, keyword):
    try:
        pattern = f"{keyword}%"
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT product_code, product_name
            FROM products
            WHERE is_active = 1 AND (product_code LIKE %s OR product_name LIKE %s)
            ORDER BY product_code
            LIMIT 15;
            """, (pattern, pattern))
            return cursor.fetchall()
    except Exception as e:
        return f"Error searching product codes: {str(e)}."

def search_deleted_product_codes(conn, keyword):
    try:
        pattern = f"{keyword}%"
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT product_code, product_name
            FROM products
            WHERE is_active = 0 AND (product_code LIKE %s OR product_name LIKE %s)
            ORDER BY product_code
            LIMIT 5;
            """, (pattern, pattern))
            return cursor.fetchall()
    except Exception as e:
        return f"Error searching product codes: {str(e)}."


def search_product_details(conn, keyword):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT s.id AS product_id, p.product_code, p.product_name,
                p.description, p.quantity, p.cost, p.retail_price,
                p.wholesale_price, p.min_stock_level
            FROM products p
            JOIN stock s ON p.product_code = s.product_code
            WHERE (p.product_code=%s OR p.product_name=%s) AND p.is_active = 1;
            """, (keyword, keyword))
            return cursor.fetchone(), None
    except Exception as e:
        return None, f"Error searching product: {str(e)}."

def update_product_details(conn, product, user):
    """Update product details across stock, products and replenishment tables.
    Args; conn --> MySQL connection object, product --> Dict containing
    details to update. Returns; (success: bool, message: str)"""
    try:
        with conn.cursor() as cursor:
            product_id = product["product_id"]
            code = product["product_code"]
            name = product["product_name"]
            desc = product["description"]
            cost = product["cost"]
            qty = product["quantity"]
            retail = product["retail_price"]
            wholesale = product["wholesale_price"]
            min_stock = product["min_stock_level"]
            # Update Stock
            cursor.execute("""
                UPDATE stock
                SET product_code = %s,
                    product_name = %s,
                    retail_price = %s,
                    wholesale_price = %s
                WHERE id = %s;
            """, (code, name, retail, wholesale, product_id))
            # Update products
            cursor.execute("""
                UPDATE products
                SET product_name = %s, description = %s, quantity = %s,
                    cost = %s, retail_price = %s, wholesale_price = %s,
                    min_stock_level = %s
                WHERE product_code = %s;
            """, (name, desc, qty, cost, retail, wholesale, min_stock, code))
        data = {
            "product_code": code,
            "description": f"Updated {name} Details",
            "quantity": qty,
            "total": cost,
            "user": user
        }
        success, message = log_stock_change(conn, data)
        if success:
            conn.commit()
            return True, f"Product #{name} updated successfully."
        else:
            conn.rollback()
            return False, f"Error Updating Product Log: {message}"
    except Exception as e:
        return False, f"Error Updating Product: {str(e)}"


def log_stock_change(conn, data):
    """Insert a new log into the product control logs table. ARGS:
        conn -> MySQL connection, data -> dictionary with keys for code, name,
        description, qty, total, user"""
    try:
        code = data["product_code"]
        desc = data["description"]
        qty = data["quantity"]
        total = data["total"]
        user = data["user"]
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT product_name
                FROM products
                WHERE product_code = %s
            """, (code,))
            name = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO product_control_logs (log_date, product_code,
                    product_name, description, quantity, total, user)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (date.today(), code, name, desc, qty, total, user))
        success, msg = insert_logs(conn, user, "Stock", desc)
        if not success:
            conn.rollback()
            return False, f"Error Recording Logs: {msg}."
        conn.commit()
        return True, f"Successfully logged {name}."
    except Exception as e:
        conn.rollback()
        return False, f"Error Inserting logs: {str(e)}"


def fetch_all_products(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT product_code, product_name, description, quantity, cost,
                wholesale_price, retail_price, min_stock_level, date_replenished
            FROM products
            WHERE is_active = 1;
            """)
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        raise e

def get_total_cost_by_codes(conn, items):
    """Calculates total cost of goods sold of the provided codes and qty.
    Items: list of dicts like [{'product_code': 'P01', 'quantity': 3}, ...].
    Returns: (total_cost, error_message)."""
    # No product codes provided
    if not items:
        return 0.00, None
    try:
        total_cost = 0.00
        with conn.cursor(dictionary=True) as cursor:
            for item in items:
                code = item.get("product_code")
                qty_sold = item.get("quantity", 0)
                if not code or qty_sold <= 0:
                    continue # Skip invalid or zero quantity entries
                cursor.execute("""
                    SELECT cost FROM products
                    WHERE product_code = %s
                """, (code,))
                result = cursor.fetchone()
                if result and result["cost"] is not None:
                    item_cost = float(result["cost"])
                    item_total = item_cost * qty_sold
                    total_cost += item_total
        return total_cost, None
    except Exception as e:
        return 0.00, f"Error fetching total cost: {e}."


def view_all_products(conn):
    products = []
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT product_code, product_name, description, quantity, cost,
                wholesale_price, retail_price, min_stock_level, date_replenished
            FROM products
            WHERE is_active = 1;
            """)
            rows = cursor.fetchall()
            for row in rows:
                product = {
                    'product_code': row[0],
                    'product_name': row[1],
                    'description': row[2],
                    'quantity': row[3],
                    'cost': float(row[4]),
                    'wholesale_price': float(row[5]),
                    'retail_price': float(row[6]),
                    'min_stock_level': int(row[7]),
                    'date_replenished': row[8]
                }
                products.append(product)
    except Exception as e:
        raise e
    return products

def fetch_product_control_logs(conn, year, month=None):
    """
    Fetch product control logs for a given year, optionally filter by month.
    """
    try:
        with conn.cursor(dictionary=True) as cursor:
            if month:
                cursor.execute("""
                    SELECT log_date, product_code, product_name, description,
                        quantity, total, user
                    FROM product_control_logs
                    WHERE YEAR(log_date) = %s AND MONTH(log_date) = %s
                    ORDER BY log_date DESC;
                """, (year, month))
            else:
                cursor.execute("""
                    SELECT log_date, product_code, product_name, description,
                        quantity, total, user
                    FROM product_control_logs
                    WHERE YEAR(log_date) = %s
                    ORDER BY log_date DESC;
                """, (year,))
            rows = cursor.fetchall()
            return True, rows if rows else []
    except Exception as e:
        return False, f"Error Fetching Logs: {str(e)}."

def fetch_distinct_years(conn):
    """Fetch distinct years from orders logs table."""
    try:
        with conn.cursor() as cursor:
            # Fetch distinct years
            cursor.execute("""
                SELECT DISTINCT YEAR(log_date) AS year
                FROM orders_logs
                ORDER BY year DESC
            """)
            years = [row[0] for row in cursor.fetchall()]
            return years, None
    except Exception as e:
        return None, f"Error: {str(e)}."

def fetch_deleted_products(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT product_code, product_name, description, quantity, cost,
                wholesale_price, retail_price, min_stock_level, date_replenished
            FROM products
            WHERE is_active = 0;
            """)
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        raise e

def get_product_codes(conn, keyword):
    try:
        pattern = f"{keyword}%"
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT product_code FROM products
            WHERE is_active = 1 AND product_code LIKE %s
            ORDER BY product_code
            LIMIT 15;
            """, (pattern,))
            rows = cursor.fetchall()
            return True, rows
    except Exception as e:
        return False, f"Error searching product codes: {str(e)}."

def update_min_stock_level(conn, product_code, quantity, user):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE products
                SET min_stock_level=%s
                WHERE product_code=%s
            """, (quantity, product_code))
        desc = f"Updated Product{product_code} Min Stock Level to{quantity}."
        data = {
            "product_code": product_code,
            "description": desc,
            "quantity": 0,
            "total": 0,
            "user": user
        }
        success, message = log_stock_change(conn, data)
        if not success:
            conn.rollback()
            return False, f"Error Updating Product Log: {message}."
        conn.commit()
        return True, "Minimum Quantity updated successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error updating minimum quantity: {str(e)}."

