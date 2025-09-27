from datetime import date
from connect_to_db import connect_db
def insert_new_product(conn, product, user):
    """Insert a new product into stock and product tables.
    ARGS:
        conn: Active DB connection.
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
    cost = product["cost"]
    qty = product["quantity"]
    retail = product["retail_price"]
    wholesale = product["wholesale_price"]
    min_stock = product["min_stock_level"]
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO stock (product_code, product_name, retail_price,
                wholesale_price)
            VALUES (%s, %s, %s, %s);
            """,(code, name, retail, wholesale))
            cursor.execute("""
            INSERT INTO products (product_code, product_name, description,
                quantity, cost, wholesale_price,retail_price, min_stock_level,
                date_replenished)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (code, name, desc, qty, cost, wholesale, retail, min_stock, now))
            data = {
                "product_code": code,
                "description": "Added New Product",
                "quantity": qty,
                "total": cost,
                "user": user
            }
            success, message = log_stock_change(conn, data)
            if success:
                conn.commit()
                return f"New Product '{name}' inserted successfully."
            else:
                conn.rollback()
                return f"Error Updating Product Log: {message}"
    except Exception as e:
        conn.rollback()
        return f"Error Inserting New Product: {str(e)}"


def delete_product(conn, product_code):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE products
                SET is_active = 0
                WHERE product_code = %s;
                """, (product_code,))
        conn.commit()
        return True, f"Product code '{product_code}' deleted successfully."
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
                "quantity": 0,
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


def fetch_product_data(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT product_code, product_name, description, quantity,
                retail_price, wholesale_price
            FROM products
            WHERE is_active = 1;
            """)
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        raise e

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
                return f"Price updated successfully for: {code}."
            else:
                conn.rollback()
                return f"Error Updating Product Log: {message}"
    except Exception as e:
        conn.rollback()
        raise e

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
                "description": "Updated Item Details",
                "quantity": 0,
                "total": 0,
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
        conn.commit()
        return True, f"Successfully logged {name}."
    except Exception as e:
        conn.rollback()
        return False, f"Error Inserting logs: {str(e)}"


conn = connect_db()
# s=search_product_details(conn, "P1001")
# print(s)
# data = {
    # "product_code": "HH-DFT019",
    # "description": "Sold Item",
#     "quantity": 5,
#     "total": 20,
#     "user": "sniffy"
# }
# success, message = log_stock_change(conn, data)
# print(success, message)