from datetime import date
from connect_to_db import connect_db
def insert_new_product(product_code, product_name, description, quantity, cost, wholesale_price, retail_price, min_stock_level):
    conn = connect_db()
    if not conn:
        return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            cursor.execute("""INSERT INTO stock (
                           product_code, product_name, retail_price, wholesale_price)
                           VALUES (%s, %s, %s, %s)
                           """,(product_code, product_name, retail_price, wholesale_price))
            cursor.execute("""INSERT INTO products (product_code, product_name, description, quantity, cost,
                           wholesale_price,retail_price, min_stock_level
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                           """, (product_code, product_name, description, quantity, cost, wholesale_price, retail_price, min_stock_level))
            date_replenished = date.today()
            cursor.execute("""INSERT INTO replenishments (
                           product_code, product_name, quantity, cost_per_unit, date_replenished
                           ) VALUES (%s, %s, %s, %s, %s)
                           """, (product_code, product_name, quantity, cost, date_replenished))
        conn.commit()
        return f"New Product '{product_name}' inserted successfully."
    except Exception as e:
        conn.rollback()
        return f"Error Inserting New Product: {e}"
    finally:
        conn.close()

def delete_product(product_code):
    conn = connect_db()
    if not conn:
        return "Database Connection Failed!"
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM stock WHERE product_code = %s", (product_code,)
            )
        conn.commit()
        return f"Product with code '{product_code}' deleted successfully."
    except Exception as e:
        conn.rollback()
        return f"Error deleting product: {e}"
    finally:
        conn.close()

def update_quantity(product_code, new_quantity):
    conn = connect_db()
    if not conn:
        return "Database Connection Failed!"
    try:
        with conn.cursor() as cursor:
            cursor.execute("""UPDATE products
                    SET quantity=%s
                    WHERE product_code=%s
                    """, (new_quantity, product_code))
            cursor.execute("""UPDATE replenishments
                    SET quantity=%s
                    WHERE product_code=%s
                    """, (new_quantity, product_code))
        conn.commit()
        return "Quantity updated successfully."
    except Exception as e:
        conn.rollback()
        return f"Error updating quantity: {e}"
    finally:
        conn.close()


def fetch_product_data(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT product_code, product_name, description, quantity,
                retail_price, wholesale_price
            FROM products""")
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        raise e
def update_price(conn, code, retail, wholesale):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""UPDATE stock set retail_price=%s, wholesale_price=%s
                                        WHERE product_code=%s
                                        """, (retail, wholesale, code))
            cursor.execute("""UPDATE products set retail_price=%s, wholesale_price=%s
                            WHERE product_code=%s
                            """, (retail, wholesale, code))
            conn.commit()
            return f"Price updated successfully for: {code}"
    except Exception as e:
        conn.rollback()
        raise e

def update_description(conn, code, new_description):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE products SET description=%s where product_code=%s;",
                (new_description, code))
            conn.commit()
            return f"Description For {code} Updated successfully"
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
            WHERE product_code LIKE %s OR product_name LIKE %s
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
            SELECT s.id AS product_id, p.product_code, p.product_name, p.description,
                p.quantity, p.cost, p.retail_price, p.wholesale_price
            FROM products p
            JOIN stock s ON p.product_code = s.product_code
            WHERE p.product_code = %s OR p.product_name = %s;
            """, (keyword, keyword))
            return cursor.fetchone(), None
    except Exception as e:
        return None, f"Error searching product: {str(e)}."

# conn = connect_db()
# rows, err =search_product_details(conn, "Latin Basin")
# if not err:
#     for row in rows:
#         print(row)
# else:
#     print(err)