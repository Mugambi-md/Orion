from connect_to_db import connect_db
from datetime import date
conn = connect_db()

def insert_order_data(conn, order_data, items, user, payment_data=None):
    try:
        with conn.cursor() as cursor:
            # Insert into orders table
            cursor.execute("""INSERT INTO orders (customer_name, contact, date_placed, deadline, amount)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (
                               order_data['customer_name'],
                               order_data['contact'],
                               order_data['date_placed'],
                               order_data['deadline'],
                               order_data['amount']
                               ))
            order_id = cursor.lastrowid
            #Insert Items
            for item in items:
                cursor.execute("""INSERT INTO order_items (order_id, product_code, product_name, quantity,
                               unit_price, total_price)VALUES (%s, %s, %s, %s, %s, %s)
                               """, (
                                   order_id,
                                   item['product_code'],
                                   item['product_name'],
                                   item['quantity'],
                                   item['unit_price'],
                                   item['total_price']                       
                           ))
            # Insert Payment
            cursor.execute("""INSERT INTO orders_payments (order_id, total_amount, paid_amount, balance, method)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (
                               order_id,
                               payment_data['total_amount'],
                               payment_data['paid_amount'],
                               payment_data['balance'],
                               payment_data['method']
                               ))
            log_order_action(conn, order_id, order_data['amount'], user, 'Received Order')
        conn.commit()
        return "Order data recorded and logged successfully."
    except Exception as e:
        conn.rollback()
        return f"Error inserting order data: {e}"
def log_order_action(conn, order_id, total_amount, user, action):
    try:
        log_date = date.today()
        with conn.cursor() as cursor:
            cursor.execute("""INSERT INTO orders_logs (log_date, order_id, total_amount, user, action)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (log_date, order_id, total_amount, user, action))
        conn.commit()
        return f"Order: {action} succesfully."
    except Exception as e:
        conn.rollback()
        return f"Error logging order action: {e}"
def update_order_item(conn, order_id, product_code, new_quantity, new_unit_price, new_total_price, adjustment, user):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""UPDATE order_items
                           SET quantity=%s, unit_price=%s, total_price=%s
                           WHERE order_id = %s AND product_code = %s
                           """, (new_quantity, new_unit_price, new_total_price, order_id, product_code))
            adjust_order_amount(conn, order_id, adjustment)
            log_order_action(conn, order_id, new_total_price, user, "Edited Order")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
def add_order_item(conn, order_id, product_code, product_name, quantity, unit_price, total_price, user):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""INSERT INTO order_items (order_id, product_code, product_name, quantity, unit_price, total_price)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           """, (order_id, product_code, product_name, quantity, unit_price, total_price))
            cursor.execute("""UPDATE orders_payments
                           SET total_amount = total_amount + %s
                           WHERE order_id = %s
                           """,(total_price, order_id))
            adjustment = total_price
            adjust_order_amount(conn, order_id, adjustment)
            log_order_action(conn, order_id, adjustment, user, 'Edited Order')
        conn.commit()
        return f"{product_name} Added Successfully to Order No. {order_id}."
    except Exception as e:
        conn.rollback()
        return f"Error Adding {product_name} to order: {e}"
def adjust_order_amount(conn, order_id, adjustment):
    """Adjustment positive value to increase or negative to decrease the amount."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""UPDATE orders
                           SET amount = amount + %s
                           WHERE order_id = %s
                           """, (adjustment, order_id))
            conn.commit()
            return f"Order amount Updated successfully for order ID {order_id}."
    except Exception as e:
        conn.rollback()
        return f"Error adjusting order amount: {e}"

def fetch_order_product(product_code):
    """Fetch product name, wholesale and retail price by product code."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""SELECT product_name, wholesale_price, retail_price
                       FROM products
                       WHERE product_code = %s
                       """, (product_code,))
        result = cursor.fetchone()
        if result:
            return {
                "product_name": result[0],
                "wholesale_price": result[1],
                "retail_price": result[2]
            }
        else:
            raise ValueError(f"No Product found with Product Code: {product_code}")
    except Exception as e:
        raise e
    finally:
        if conn:
            conn.close()

def fetch_all_orders(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""SELECT * FROM orders
                           ORDER BY
                                CASE status
                                    WHEN 'Pending' THEN 0
                                    WHEN 'Delivered' THEN 1
                                    ELSE 2
                                END,
                                order_id DESC
                           """)
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching orders: {e}"
def fetch_pendind_orders(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""SELECT order_id, customer_name, contact, date_placed, deadline, amount, status
                           FROM orders
                           WHERE status='pending'
                           ORDER BY order_id DESC
                           """)
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching pending orders: {e}"
def fetch_all_order_items(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""SELECT
                                oi.order_id,
                                oi.product_code,
                                oi.product_name,
                                oi.quantity,
                                oi.unit_price,
                                oi.total_price
                           FROM order_items oi
                           JOIN orders o ON oi.order_id = o.order_id
                           WHERE o.status = 'pending'
                           ORDER BY oi.order_id DESC
                        """)
            raw_items = cursor.fetchall()
            
            return raw_items
    except Exception as e:
        return f"Error fetching order items: {e}"
def fetch_order_payment_by_id(conn, order_id):
    try:
        with conn.cursor(dictionary=True)as cursor:
            cursor.execute("SELECT balance FROM orders_payments WHERE order_id=%s", (order_id,))
            return cursor.fetchone()
    except Exception as e:
        return f"Error fetching payments: {e}"
def fetch_all_orders_logs(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM orders_logs ORDER BY log_date DESC")
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching orders logs: {e}"
def fetch_order_items_by_order_id(conn, order_id):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching order items: {e}"
def fetch_orders_payments_by_order_id(conn, order_id):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM orders_payments WHERE order_id = %s", (order_id,))
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching payments: {e}"
def fetch_orders_logs_by_order_id(conn, order_id):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM orders_logs WHERE order_id=%s ORDER BY log_id DESC", (order_id,))
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching order logs: {e}"

def fetch_unpaid_orders(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""SELECT o.order_id, o.customer_name, o.contact, o.date_placed, o.amount, o.status, p.balance
                           FROM orders o
                           JOIN orders_payments p ON o.order_id=p.order_id
                           WHERE p.balance > 0
                           ORDER BY o.order_id DESC
                           """)
            return cursor.fetchall()
    except Exception as e:
        return(f"Error fetching unpaid orders: {e}")
    
def receive_order_payment(order_id, amount_to_pay, method, user, conn):
    try:
        with conn.cursor() as cursor:
            # Fetch existing payment details
            cursor.execute("""SELECT total_amount, paid_amount, balance
                           FROM orders_payments
                           WHERE order_id=%s
                           """, (order_id,))
            result = cursor.fetchone()
            if not result:
                return f"No payment record found for Order ID {order_id}."
            total_amount, paid_amount, balance = result
            if balance == 0:
                return "This order has already been fully paid."
            new_paid = paid_amount + amount_to_pay
            new_balance = total_amount - new_paid
            if new_balance < 0:
                return "Amount exceeds the remaining balance."
            # Determine action type
            if paid_amount == 0 and amount_to_pay == total_amount:
                action = 'Full Payment'
            elif new_paid == total_amount:
                action = 'Full Payment'
            else:
                action = 'Partial Payment'
            # Update orders payments
            cursor.execute("""UPDATE orders_payments
                           SET paid_amount=%s, balance=%s, method=%s
                           WHERE order_id=%s
                           """, (new_paid, new_balance, method, order_id))
            # Insert into orders logs
            cursor.execute("""INSERT INTO orders_logs (order_id, total_amount, user, action)
                           VALUES (%s, %s, %s, %s)
                           """, (order_id, amount_to_pay, user, action))
            conn.commit()
            return f"{action} recorded successfully for Order ID {order_id}. Remaining Balance: {new_balance:.2f}"
    except Exception as e:
        conn.rollback()
        return f"Database Error: str(e)"
    
def update_order_details(conn, order_id, customer_name, contact, deadline, total_amount, user):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""UPDATE orders
                           SET customer_name = %s, contact = %s, deadline = %s
                           WHERE order_id = %s
                           """, (customer_name, contact, deadline, order_id))
            log_order_action(conn, order_id, total_amount, user, 'Edited Order')

            conn.commit()
            return "Order updated successfully."
    except Exception as e:
        conn.rollback()
        raise

def order_items_history(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""SELECT order_id, product_code, product_name, quantity, unit_price, total_price,
                           COUNT(product_code) OVER (PARTITION BY product_code) AS product_frequency
                           FROM order_items
                           ORDER BY product_frequency DESC, product_code, order_id DESC
                        """)
            return cursor.fetchall()        
    except Exception as e:
        return f"Error fetching Order Items: {e}"

def mark_order_as_delivered(conn, order_id):
    """Mark the order as delivered for the given order ID."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""UPDATE orders
                           SET status = 'Delivered'
                           WHERE order_id=%s
                           """, (order_id,))
            conn.commit()
            return f"Order {order_id} marked delivered."
    except Exception as e:
        conn.rollback()
        raise

def delete_order(conn, order_id, user):
    """Delete the order with the given order ID."""
    try:
        log_order_action(conn, order_id, 0, user, "Edited Order")
        with conn.cursor() as cursor:
            cursor.execute("""DELETE FROM orders
                           WHERE order_id=%s
                           """, (order_id,))
        conn.commit()
        return f"Order #{order_id} deleted successfully."
    except Exception as e:
        conn.rollback()
        raise
def delete_order_item(conn, order_id, product_code, amount, user):
    """Delete order item and ajust orders total amount."""
    try:
        log_order_action(conn, order_id, amount, user, "Edited Order")
        with conn.cursor() as cursor:
            cursor.execute("""DELETE FROM order_items
                           WHERE order_id=%s AND product_code=%s
                           """, (order_id, product_code))
        adjustment = (0 - amount)
        adjust_order_amount(conn, order_id, adjustment)
        conn.commit()
        return f"Order Item {product_code} of Order {order_id} deleted successfully."
    except Exception as e:
        conn.rollback()
        return f"Failed to delete item: {e}"

def search_product_codes(conn, keyword):
    try:
        pattern = f"{keyword}%"
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""SELECT product_code, product_name
                           FROM products
                           WHERE product_code LIKE %s
                           ORDER BY product_code
                           LIMIT 10
                           """, (pattern,))
            return cursor.fetchall()
    except Exception as e:
        return f"Error searching product codes: {e}"

