from datetime import date
from connect_to_db import connect_db
def insert_new_product(product_code, product_name, description, quantity, cost, wholesale_price, retail_price, min_stock_level):
    conn = connect_db()
    if not conn:
        return "Database connection failed."
    cursor = conn.cursor()
    try:
        found_in = []
        cursor.execute("SELECT product_code FROM stock WHERE product_code = %s", (product_code,)) # Check in stock tabe
        if cursor.fetchone():
            found_in.append("stock")
        cursor.execute("SELECT product_code FROM products WHERE product_code = %s", (product_code,)) # Check in products Table
        if cursor.fetchone():
            found_in.append("products")
        cursor.execute("SELECT product_code FROM replenishments WHERE product_code = %s", (product_code,)) # Check in replenishments Table
        if cursor.fetchone():
            found_in.append("replenishments")
        if found_in: # If found in any table, return a message
            tables = ", ".join(found_in)
            return f"Product Code '{product_code}' already exists in: {tables}. Do you want to update it?"
        else: # If not found, insert into all three tables
            cursor.execute("""INSERT INTO stock (
                           product_code, product_name, retail_price, wholesale_price)
                           VALUES (%s, %s, %s, %s)
                           """,(product_code, product_name, retail_price, wholesale_price))
            cursor.execute("""INSERT INTO products (product_code, product_name, description, quantity, cost,
                           wholesale_price,retail_price, min_stock_level
                           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                           """, (product_code, product_name, description, quantity, cost, wholesale_price, retail_price, min_stock_level))
            date_replenished = date.today()
            cost_per_unit = cost
            cursor.execute("""INSERT INTO replenishments (
                           product_code, product_name, quantity, cost_per_unit, date_replenished
                           ) VALUES (%s, %s, %s, %s, %s)
                           """, (product_code, product_name, quantity, cost_per_unit, date_replenished))
            conn.commit()
            return f"New Product '{product_name}' inserted successfully."
    except Exception as e:
        conn.rollback()
        return f"Error Inserting New Product: {e}"
    finally:
        cursor.close()
        conn.close()

def delete_product(product_code):
    conn = connect_db()
    if not conn:
        return "Database Connection Failed!"
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT product_code FROM stock WHERE product_code = %s", (product_code,))
        if not cursor.fetchone():
            return f"No Product found with code '{product_code}'."
        else:
            cursor.execute("DELETE FROM stock WHERE product_code = %s", (product_code,))
            conn.commit()
            return f"Product with code '{product_code}' deleted successfully."
    except Exception as e:
        return f"Error deleting product: {e}"
    finally:
        cursor.close()
        conn.close()

def update_quantity(product_code, new_quantity):
    conn = connect_db()
    if not conn:
        return "Database Connection Failed!"
    cursor = conn.cursor()
    try:
        messages = []
        found = False
        cursor.execute("SELECT 1 FROM products WHERE product_code = %s", (product_code,)) # Check in products table
        if cursor.fetchone():
            cursor.execute("""UPDATE products
                           SET quantity = %s
                           WHERE product_code = %s
                           """, (new_quantity, product_code))
            messages.append("Quantity updated in 'products' table.")
            found = True
        else:
            messages.append("Product code not found in 'products' table.")
        cursor.execute("SELECT 1 FROM replenishments WHERE product_code = %s", (product_code,)) # Check in replenishments table
        if cursor.fetchone():
            cursor.execute("""UPDATE replenishments
                           SET quantity = %s
                           WHERE product_code = %s
                           """, (new_quantity, product_code))
            messages.append("Quantity updated in 'replenishments' table.")
            found = True
        else:
            messages.append("Product code not found in 'replenishments' table.")
        if found:
            conn.commit()
        else:
            messages.append("No Updates Were Made.")
        return "\n".join(messages)
    except Exception as e:
        conn.rollback() # Undo Changes on error
        return f"Error updating quantity: {e}"
    finally:
        cursor.close()

def update_product(product_code, product_name, description, new_quantity, cost=None, wholesale_price=None, retail_price=None, min_stock_level=None):
    conn = connect_db()
    if not conn:
        return "Database connection failed."
    cursor = conn.cursor()
    try:
        missing_tables = []
        cursor.execute("SELECT 1 FROM stock WHERE product_code = %s", (product_code,)) # Check existence in stock
        if not cursor.fetchone():
            missing_tables.append("stock")
        cursor.execute("SELECT quantity FROM products WHERE product_code = %s", (product_code,)) # Check existence in products
        product_row = cursor.fetchone()
        if not product_row:
            missing_tables.append("products")
        cursor.execute("SELECT 1 FROM replenishments WHERE product_code = %s", (product_code,)) # Check existence in replenishments
        if not cursor.fetchone():
            missing_tables.append("replenishments")
        if missing_tables:
            return f"Product Code '{product_code}' not found in: {','.join(missing_tables)}."
        current_quantity = product_row[0] # Calculate new quantity
        updated_quantity = current_quantity + new_quantity
        # Update Products Table
        cursor.execute("""UPDATE products SET
                       product_name=%s,
                       description=%s,
                       quantity=%s,
                       cost= COALESCE(%s, cost),
                       wholesale_price=COALESCE(%s, retail_price),
                       retail_price=COALESCE(%s, retail_price),
                       min_stock_level=COALESCE(%s, min_stock_level)
                       WHERE product_code=%s
                       """, (product_name, description, updated_quantity, cost, wholesale_price, retail_price, min_stock_level, product_code))
        # Update Stock Table
        cursor.execute("""UPDATE stock SET
                       product_name = %s,
                       retail_price = COALESCE(%s, retail_price),
                       wholesale_price = COALESCE(%s, wholesale_price)
                       WHERE product_code = %s
                       """, (product_name, retail_price, wholesale_price, product_code))
        # Update Replenishments Table
        date = date.today()
        cursor.execute("""UPDATE replenishments SET
                       product_name = %s,
                       quantity = %s,
                       cost_per_unit = COALESCE(%s, cost_per_unit),
                       date_replenished = %s
                       WHERE product_code = %s
                       """, (product_name, updated_quantity, cost, date, product_code))
        conn.commit()
        return f"Product '{product_name}' updated successfully."
    except Exception as e:
        conn.rollback()
        return f"Error updating product: {e}"
    finally:
        cursor.close()
        conn.close()
