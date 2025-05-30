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
                           SELECT id, product_code, product_name, description, quantity, cost, wholesale_price, retail_price, retail_price,
                           min_stock_level
                           FROM products;
                           """)
            rows = cursor.fetchall()
            for row in rows:
                product = {
                    'id': row[0],
                    'product_code': row[1],
                    'product_name': row[2],
                    'description': row[3],
                    'quantity': row[4],
                    'cost': float(row[5]),
                    'wholesale_price': float(row[6]),
                    'retail_price': float(row[7]),
                    'min_stock_level': row[8]
                }
                products.append(product)
        except Exception as e:
            print(f"Error fetching products: {e}")
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
            cursor.execute("""SELECT id, product_code, product_name, quantity, cost_per_unit, total_cost, date_replenished
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


def add_to_existing_product(product_code, added_quantity, new_cost=None, new_wholesale_price=None, new_retail_price=None, new_min_stock_level=None):
    conn = connect_db()
    if not conn:
        return "Database Connection Failed."
    cursor = conn.cursor()
    try:
        missing_tables = []
        cursor.execute("SELECT product_code FROM stock WHERE product_code = %s", (product_code,)) # Check in stock table
        in_stock = cursor.fetchone()
        if not in_stock:
            missing_tables.append("stock")
        cursor.execute("SELECT quantity, cost, wholesale_price, retail_price, min_stock_level FROM products WHERE product_code=%s", (product_code,))
        product = cursor.fetchone() # Check in products table
        if not product:
            missing_tables.append("products")
        else:
            existing_quantity, current_cost, current_wholesale, current_retail, current_min_level = product
        cursor.execute("SELECT product_code FROM replenishments WHERE product_code=%s", (product_code,)) # Check in replenishments
        in_replenishments = cursor.fetchone()
        if not in_replenishments:
            missing_tables.append("replenishments")
        if len(missing_tables) == 3: # If missing from all tables
            return f"Product Code '{product_code}' not found in database. Do you want to add it as new Product"
        if missing_tables: # If missing from some
            return f"Product Code '{product_code}' not found: {','.join(missing_tables)}. Operation cancelled."
        # Use current Values if none provided
        updated_quantity = existing_quantity + added_quantity
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
                       """, (updated_quantity, updated_cost, updated_wholesale, updated_retail, updated_min_level, product_code))
        # Update Stock Table
        cursor.execute("""
                       UPDATE stock SET
                       wholesale_price = %s,
                       retail_price = %s
                       WHERE product_code = %s
                       """, (updated_wholesale, updated_retail, product_code))
        # Insert into replenishments
        date_replenished = date.today()
        cursor.execute("""UPDATE replenishments 
                       SET product_name = (SELECT product_name FROM products WHERE product_code=%s),
                       quantity = %s,
                       cost_per_unit = %s,
                       date_replenished = %s
                       WHERE product_code = %s
                       """, (product_code, updated_quantity, updated_cost, date_replenished, product_code))
        conn.commit()
        return f"Stock for Product Code '{product_code}' Updated successfully."
    except Exception as e:
        conn.rollback()
        return f"Error Updating Product: {e}"
    finally:
        cursor.close()
        conn.close()

def log_stock_change(cursor, product_code, product_name, description, quantity, user):
    try:
        cursor.execute("SELECT quantity FROM products WHERE product_code = %s", (product_code,))
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Product with code {product_code} not found.")
        current_quantity = result[0]
        if description == "sold":
            new_total = current_quantity - quantity
        elif description in ("replenished", "returned"):
            new_total = current_quantity + quantity
        else:
            raise ValueError("Invalid description. Must be 'sold', 'replenished' or 'returned'.")
        # Insert log entry
        cursor.execute("""INSERT INTO product_control_logs (log_date, product_code, product_name, description,
                       quantity, total,user)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       """, (date.today(), product_code, product_name, description, quantity, new_total, user))
    except Exception as e:
        return(f"Failed to log stock changes: {e}")