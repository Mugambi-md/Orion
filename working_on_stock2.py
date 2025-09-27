from connect_to_db import connect_db
from datetime import date
from working_on_stock import log_stock_change

def view_stock():
    conn = connect_db()
    products = []
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, product_code, product_name, retail_price, wholesale_price FROM stock")
            rows = cursor.fetchall()
            for row in rows:
                product = {
                    'id': row[0],
                    'code': row[1],
                    'name': row[2],
                    'retail': row[3],
                    'wholesale': row[4]
                }
                products.append(product)
        except Exception as e:
            print(f"Error fetching products: {e}")
        finally:
            cursor.close()
            conn.close()

    return products

def view_all_products():
    conn = connect_db()
    products = []
    if conn:
        cursor = conn.cursor()
        try:
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
        finally:
            cursor.close()
            conn.close()
    
    return products

def view_replenishments():
    records = []
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
            SELECT id, product_code, product_name, quantity, cost_per_unit,
                total_cost, date_replenished
            FROM replenishments
            ORDER BY date_replenished DESC
            """)
            rows = cursor.fetchall()
            for row in rows:
                record = {
                    'id': row[0],
                    'product_code': row[1],
                    'product_name': row[2],
                    'quantity': row[3],
                    'cost_per_unit': float(row[4]),
                    'total_cost': float(row[5]),
                    'date_replenished': row[6].strftime("%Y-%m-%d") if row[6] else None
                }
                records.append(record)
        except Exception as e:
            print(f"Error fetching replenishments: {e}")
        finally:
            cursor.close()
            conn.close()
    return records


def add_to_existing_product(conn, product: dict, user: str):
    """Replenish an existing product (increase quantity, update prices if given).
    ARGS: conn -> MySQL connection object, product -> dict with product details,
    and user -> (str) user performing update. Returns (success: bool, message: str"""
    try:
        code = product["product_code"]
        add_qty = product.get("quantity", 0)
        date_filled = date.today()
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
            if success:
                conn.commit()
                return True, f"Product Code '{code}' Replenished Successfully."
            else:
                conn.rollback()
                return f"Error Updating Product Log: {message}"
    except Exception as e:
        conn.rollback()
        return False, f"Error Replenishing Product: {str(e)}."



# product_data = {
#     "product_code": "B234",
#     "quantity": 50,
#     "cost": 50,
#     "wholesale_price": 80.00,
#     "retail_price": 110.00,
#     "min_stock_level": 50
# }
# conn = connect_db()
# user = "test_user"
# succ, message = add_to_existing_product(conn, product_data, user)
# if succ:
#     print("Success:", message)
# else:
#     print("Message:", message)


