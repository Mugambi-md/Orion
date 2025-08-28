from connect_to_db import connect_db
from datetime import date

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
                wholesale_price, retail_price, min_stock_level
            FROM products;
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
                    'min_stock_level': int(row[7])
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


def add_to_existing_product(conn, code, quantity, new_cost=None, new_wholesale_price=None, new_retail_price=None, new_min_stock_level=None):
    if not conn:
        return "Database Connection Failed."
    try:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT quantity, cost, wholesale_price, retail_price, min_stock_level
            FROM products WHERE product_code=%s""", (code,))
            product = cursor.fetchone() # Check in products table
            if not product:
                return f"Product '{code}' not found in database."
            else:
                existing_quantity, current_cost, current_wholesale, current_retail, current_min_level = product
            # Use current Values if none provided
            updated_quantity = existing_quantity + quantity
            updated_cost = new_cost if new_cost is not None else current_cost
            updated_wholesale = new_wholesale_price if new_wholesale_price is not None else current_wholesale
            updated_retail = new_retail_price if new_retail_price is not None else current_retail
            updated_min_level = new_min_stock_level if new_min_stock_level is not None else current_min_level
            # Update Products Table
            cursor.execute("""
                UPDATE products SET
                       quantity = %s,
                       cost = %s,
                       wholesale_price =%s,
                       retail_price = %s,
                       min_stock_level = %s
                WHERE product_code = %s
                """, (updated_quantity, updated_cost, updated_wholesale, updated_retail, updated_min_level, code))
            # Update Stock Table
            cursor.execute("""
                UPDATE stock SET
                       wholesale_price = %s,
                       retail_price = %s
                WHERE product_code = %s
                """, (updated_wholesale, updated_retail, code))
            # Insert into replenishments
            date_filled = date.today()
            cursor.execute("""
                UPDATE replenishments SET
                        product_name = (SELECT product_name FROM products WHERE product_code=%s),
                        quantity = %s,
                        cost_per_unit = %s,
                        date_replenished = %s
                WHERE product_code = %s
                """, (code, updated_quantity, updated_cost, date_filled, code))
            conn.commit()
            return f"Stock for Product Code '{code}' Updated successfully."
    except Exception as e:
        conn.rollback()
        return f"Error Updating Product: {e}"


def log_stock_change(conn, product_code, product_name, description, quantity, total, user):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""INSERT INTO product_control_logs (log_date, product_code, product_name, description,
                       quantity, total, user)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       """, (date.today(), product_code, product_name, description, quantity, total, user))
        conn.commit()
        return f"Successfully logged {product_name}."
    except Exception as e:
        conn.rollback()
        return f"Failed to log stock changes: {e}"

