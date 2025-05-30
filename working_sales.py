from connect_to_db import connect_db
from working_on_stock2 import log_stock_change
from datetime import date
def insert_sale_data(receipt_no, sale_date, total_amount, user, items_list, payment_list):
    """Insert data into sales, sale_items, log stock changes and payments tables."""
    conn = connect_db()
    if not conn:
        return "Database Connection Failed."
    cursor = conn.cursor()
    try:
        conn.autocommit = False # Start transaction
        for item in items_list: # Insert Logs changes first
            product_code = item['product_code']
            product_name = item['product_name']
            description = "sold"
            quantity = item['quantity']
            log_stock_change(cursor, product_code, product_name, description, quantity, user) 
        # Insert into sales table
        cursor.execute("""INSERT INTO sales (receipt_no, sale_date, total_amount, user)
                       VALUES (%s, %s, %s, %s)
                       """, (receipt_no, sale_date, total_amount, user))
        for item in items_list:
            product_code = item['product_code']
            quantity_to_deduct = item['quantity']
            # Deduct from products table first
            cursor.execute("""UPDATE products
                           SET quantity = quantity - %s
                           WHERE product_code = %s
                           """, (quantity_to_deduct, product_code))
            # Deduct from Replenishments table
            cursor.execute("""UPDATE replenishments
                           SET quantity = quantity - %s
                           WHERE product_code = %s
                           """, (quantity_to_deduct, product_code))       
        # Insert each sale item (total_amount is auto-generated in DB)
        for item in items_list:
            cursor.execute("""INSERT INTO sale_items (receipt_no, product_code, product_name, quantity, unit_price, user)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           """, (
                               receipt_no,
                               item['product_code'],
                               item['product_name'],
                               item['quantity'],
                               item['unit_price'],
                               user
                           ))
        # Insert each payment (make sure cumulative payment does not exceed total)
        total_paid = 0
        for payment in payment_list:
            total_paid += payment['amount_paid']
            if total_paid > total_amount:
                raise ValueError("Total payment exceeds the sale amount.")
            cursor.execute("""INSERT INTO payments (user, receipt_no, payment_date, amount_paid, payment_method)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (
                               user,
                               receipt_no,
                               date.today(),
                               payment['amount_paid'],
                               payment['payment_method']
                           ))
        conn.commit()
        return "Sales data inserted successfully."
    except Exception as e:
        conn.rollback()
        return f"Error inserting sale data: {e}"
    finally:
        cursor.close()
        conn.close()

def fetch_sales_product(product_code):
    """Fetch product details by product code."""
    from connect_to_db import connect_db
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
