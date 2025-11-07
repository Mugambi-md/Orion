from datetime import date


def insert_order_data(conn, order_data, items, user, payment_data=None):
    try:
        client_name = order_data["customer_name"]
        contacts = order_data["contact"]
        date_placed = order_data["date_placed"]
        deadline = order_data['deadline']
        amount = order_data['amount']
        with conn.cursor() as cursor:
            # Insert into orders table
            cursor.execute("""
            INSERT INTO orders (customer_name, contact, date_placed,
                deadline, amount)
            VALUES (%s, %s, %s, %s, %s)
            """, (client_name, contacts, date_placed, deadline, amount))
            order_id = cursor.lastrowid
            #Insert Items
            for item in items:
                code = item['product_code']
                item_name = item['product_name']
                qty = item['quantity']
                price = item['unit_price']
                total_price = item['total_price']
                cursor.execute("""
                INSERT INTO order_items (order_id, product_code, product_name,
                    quantity, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (order_id, code, item_name, qty, price, total_price))
            if payment_data:
                total_amount = payment_data['total_amount']
                paid = payment_data['paid_amount']
                balance = payment_data['balance']
                method = payment_data['method']
                # Insert Payment
                cursor.execute("""
                INSERT INTO orders_payments (order_id, total_amount,
                    paid_amount, balance, method)
                VALUES (%s, %s, %s, %s, %s)
                """, (order_id, total_amount, paid, balance, method))
                status = f"Paid; {paid}, Remaining Balance; {balance}."
            else:
                status = "Order Unpaid."
        action = f"Received Order {order_id} From {client_name}. {status}."
        success, msg = log_order_action(conn, order_id, amount, user, action)
        if not success:
            return f"Error Recording Logs: {msg}"
        conn.commit()
        return "Order data recorded and logged successfully."
    except Exception as e:
        conn.rollback()
        return f"Error inserting order data: {str(e)}."

def log_order_action(conn, order_id, total_amount, user, action):
    try:
        log_date = date.today()
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO orders_logs (log_date, order_id, total_amount, user,
                action)
            VALUES (%s, %s, %s, %s, %s)
            """, (log_date, order_id, total_amount, user, action))
        conn.commit()
        return True, "Order recorded successfully."
    except Exception as e:
        conn.rollback()
        return True, f"Error logging order action: {str(e)}."

def update_order_item(conn, order_id, product_data, user):
    try:
        code = product_data.get("product_code")
        qty = product_data.get("quantity")
        price = product_data.get("unit_price")
        total_price = product_data.get("total_price")
        adjustment = product_data.get("adjustment")
        with conn.cursor() as cursor:
            cursor.execute("""UPDATE order_items
                           SET quantity=%s, unit_price=%s, total_price=%s
                           WHERE order_id = %s AND product_code = %s;
                           """, (qty, price, total_price, order_id, code))
        success, message = adjust_order_amount(conn, order_id, adjustment)
        if not success:
            conn.rollback()
            return False, f"Error Adjusting Amount: {message}."
        action = f"Edited Order; {order_id}. Added {qty} to Item {code}."
        success, msg = log_order_action(
            conn, order_id, total_price, user, action
        )
        if not success:
            conn.rollback()
            return False, f"Error Recording Logs: {msg}."
        conn.commit()
        return True, "Order Item Updated Successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error Updating Item: {str(e)}."

def add_order_item(conn, order_id, product_data, user):
    """Adds a product to an order and updates the order total and logs action"""
    try:
        code = product_data.get("product_code")
        name = product_data.get("product_name")
        qty = product_data.get("quantity")
        price = product_data.get("unit_price")
        total_price = product_data.get("total_price")
        if not all([code, name, qty, price, total_price]):
            return False, "Missing Required Product Details."
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO order_items (order_id, product_code, product_name,
                quantity, unit_price, total_price)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, code, name, qty, price, total_price))
            adjustment = total_price
        success, message = adjust_order_amount(conn, order_id, adjustment)
        if not success:
            conn.rollback()
            return False, f"Failed To Adjust Order Total: {str(message)}."
        action = f"Edited Order; {order_id}. Added {name} to Order Items."
        success, msg = log_order_action(
            conn, order_id, adjustment, user, action
        )
        if not success:
            conn.rollback()
            return False, f"Failed to Record Log: {str(msg)}"
        conn.commit()
        return True, f"{name} Added Successfully to Order No. {order_id}."
    except Exception as e:
        conn.rollback()
        return False, f"Error Adding Product to Order: {str(e)}."

def adjust_order_amount(conn, order_id, adjustment):
    """Adjustment positive value to increase or negative to decrease the amount."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE orders
            SET amount = amount + %s
            WHERE order_id = %s
            """, (adjustment, order_id))
            cursor.execute("""
            UPDATE orders_payments
            SET total_amount = total_amount + %s,
                balance = balance + %s
            WHERE order_id = %s;
            """, (adjustment, adjustment, order_id))
            conn.commit()
            return True, "Order Amount Updated successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error Adjusting Amount: {str(e)}."

def fetch_order_product(conn, product_code):
    """Fetch product name, wholesale and retail price by product code."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT product_name, wholesale_price, retail_price
            FROM products
            WHERE product_code = %s AND is_active = 1;
            """, (product_code,))
            result = cursor.fetchone()
            if result:
                return {
                    "product_name": result[0],
                    "wholesale_price": result[1],
                    "retail_price": result[2]
                }
            else:
                raise ValueError(f"No Product with Code: {product_code}.")
    except Exception as e:
        raise e

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
def fetch_pending_orders(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT order_id, customer_name, contact, date_placed, deadline,
                amount, status
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

def fetch_order_balance_by_id(conn, order_id):
    try:
        with conn.cursor(dictionary=True)as cursor:
            cursor.execute("""
                SELECT
                    total_amount,
                    paid_amount,
                    (total_amount - paid_amount) AS balance
                FROM orders_payments
                WHERE order_id = %s;
            """, (order_id,))
            result = cursor.fetchone()
            if not result:
                return None # No record found
            return result #{'total_amount':.., 'paid_amount':.., 'balance':..}
    except Exception as e:
        return {"error": f"Error fetching payments: {str(e)}."}


def fetch_order_items_by_order_id(conn, order_id):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM order_items WHERE order_id = %s", (order_id,)
            )
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching order items: {str(e)}."

def fetch_orders_payments_by_order_id(conn, order_id):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM orders_payments WHERE order_id = %s;",
                (order_id,)
            )
            return cursor.fetchone()
    except Exception as e:
        return f"Error fetching payments: {str(e)}."


def fetch_unpaid_orders(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT o.order_id, o.customer_name, o.contact, o.date_placed,
                    o.amount, o.status, p.balance
                FROM orders o
                JOIN orders_payments p ON o.order_id=p.order_id
                WHERE p.balance > 0 AND o.status = "Pending"
                ORDER BY o.order_id DESC
            """)
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching unpaid orders: {str(e)}"
    
def receive_order_payment(conn, order_id, payment_data, user):
    try:
        cash = float(payment_data.get("cash", 0) or 0)
        mpesa = float(payment_data.get("mpesa", 0) or 0)
        total_payment = cash + mpesa
        if total_payment <= 0:
            return False, "Invalid Payment Amount."
        # Combine payment methods dynamically
        methods = []
        if cash > 0:
            methods.append("Cash")
        if mpesa > 0:
            methods.append("Mpesa")
        method_str = " & ".join(methods) if methods else "Unknown"
        with conn.cursor() as cursor:
            # Fetch existing payment details
            cursor.execute("""
            SELECT total_amount, paid_amount, balance
            FROM orders_payments
            WHERE order_id=%s;
            """, (order_id,))
            result = cursor.fetchone()
            if not result:
                return False, f"No Payment Record for Order: {order_id}."
            total_amount = float(result[0])
            paid_amount = float(result[1])
            balance = float(result[2])
            if balance == 0:
                return False, "This Order is Already Paid Fully."
            new_paid = paid_amount + total_payment
            new_balance = total_amount - new_paid
            if new_balance < 0:
                return False, "Amount Exceeds the Remaining Balance."
            # Determine action type
            fully_paid = (total_payment == total_amount or new_paid == total_amount)
            if fully_paid:
                status = 'Full Payment'
            else:
                status = 'Partial Payment'
            # Update orders payments
            cursor.execute("""
                UPDATE orders_payments
                SET paid_amount = paid_amount + %s,
                    balance = balance - %s,
                    method = %s
                WHERE order_id=%s
            """, (total_payment, total_payment, method_str, order_id))
            rb = f"{new_balance:,.2f}"
        action = f"Received {status} of {paid_amount:,.2f}."
        success, msg = log_order_action(
            conn, order_id, total_payment, user, action
        )
        if success:
            conn.commit()
            return True, f"Payment recorded successfully. Balance: {rb}."
        else:
            conn.rollback()
            return False, f"Error Recording Logs: {str(msg)}."
    except Exception as e:
        conn.rollback()
        return False, f"Database Error: {str(e)}"
    
def update_order_details(conn, order_data, user):
    try:
        customer_name = order_data["customer_name"]
        contact = order_data["contact"]
        deadline = order_data["deadline"]
        order_id = order_data["order_id"]
        total_amount = order_data["total_amount"]
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE orders
            SET customer_name = %s,
                contact = %s,
                deadline = %s
            WHERE order_id = %s
            """, (customer_name, contact, deadline, order_id))
            details = f"{customer_name}, {contact}, {deadline}"
        action = f"Updated Order #{order_id}, Details to {details}."
        success, msg = log_order_action(
            conn, order_id, total_amount, user, action
        )
        if success:
            conn.commit()
            return "Order updated successfully."
        else:
            conn.rollback()
            return f"Error Updating Logs: {str(msg)}."
    except Exception as e:
        conn.rollback()
        return f"Error Updating Order: {str(e)}."

def order_items_history(conn, year, month=None):
    """
    Fetch product performance summary from order items table:
    - Product Code
    - Product Name
    - Total Quantity Sold (SUM)
    - Average Unit Price (AVG)
    - Total Revenue (SUM of total price)
    """
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT
                    oi.product_code,
                    oi.product_name,
                    SUM(oi.quantity) AS total_quantity,
                    ROUND(AVG(oi.unit_price), 2) AS unit_price,
                    SUM(oi.total_price) AS total_revenue
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.order_id
                WHERE YEAR(o.date_placed) = %s
            """
            params = [year]
            if month:
                query += " AND MONTH(o.date_placed) = %s"
                params.append(month)
            query += """
                GROUP BY product_code, product_name
                ORDER BY total_revenue DESC, total_quantity DESC;
            """
            cursor.execute(query, tuple(params))
            return cursor.fetchall()        
    except Exception as e:
        return f"Error fetching Order Items: {str(e)}"

def mark_order_as_delivered(conn, order_id, amount, user):
    """Mark the order as delivered for the given order ID."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE orders
            SET status = 'Delivered'
            WHERE order_id=%s
            """, (order_id,))
        action = f"Marked Order #{order_id} Delivered."
        success, msg = log_order_action(conn, order_id, amount, user, action)
        if not success:
            conn.rollback()
            return False, f"Failed to Log Delivery action: {msg}."
        items = fetch_items_for_delivery(conn, order_id)
        if isinstance(items, str):
            conn.rollback()
            return False, f"Error Fetching Items: {items}."
        success, msg = reduce_product_quantity_after_delivery(
            conn, order_id, items, user
        )
        if not success:
            conn.rollback()
            return False, f"Failed to Reduce Quantities:\n{msg}."
        action = f"Stock Updated After Order #{order_id} Delivery."
        success, msg = log_order_action(conn, order_id, amount, user, action)
        if not success:
            conn.rollback()
            return False, f"Failed to Log Stock Update: {msg}."
        conn.commit()
        return True, f"Order {order_id} Marked Delivered and Stock Updated."
    except Exception as e:
        conn.rollback()
        return False, f"Error Marking Order Delivered: {str(e)}."

def delete_order(conn, order_id, user):
    """Delete the order with the given order ID."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            DELETE FROM orders
            WHERE order_id=%s;
            """, (order_id,))
        action = f"Deleted Order #{order_id}."
        success, msg = log_order_action(conn, order_id, 0, user, action)
        if success:
            conn.commit()
            return True, f"Order #{order_id} deleted successfully."
        else:
            conn.rollback()
            return False, "Error Deleting Order Item."
    except Exception as e:
        conn.rollback()
        return False, f"Error Deleting Item: {str(e)}."

def delete_order_item(conn, order_id, product_code, amount, user):
    """Delete order item and adjust orders total amount."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            DELETE FROM order_items
            WHERE order_id=%s AND product_code=%s
            """, (order_id, product_code))
        adjustment = (0 - amount)
        success, message = adjust_order_amount(conn, order_id, adjustment)
        if not success:
            conn.rollback()
            return False, f"Failed To Adjust Order Amount: {str(message)}."
        action = f"Deleted Order Item; {product_code} In Order #{order_id}."
        success, msg = log_order_action(conn, order_id, amount, user, action)
        if not success:
            conn.rollback()
            return False, "Failed To delete Order Item."
        conn.commit()
        return True, "Order Item Deleted Successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Failed to delete item: {str(e)}."

def search_product_codes(conn, keyword):
    try:
        pattern = f"{keyword}%"
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
            SELECT product_code, product_name
            FROM products
            WHERE product_code LIKE %s AND is_active = 1
            ORDER BY product_code
            LIMIT 10;
            """, (pattern,))
            return cursor.fetchall()
    except Exception as e:
        return f"Error searching product codes: {e}"


def fetch_all_orders_logs(conn, year, month=None, user=None):
    """
    Fetch order logs filtered by:
    -Year(required)
    -Month (Optional, 1-12)
    -Day (optional, day of the month)
    -User(optional, username)
    """
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
            SELECT log_date, log_id, order_id, total_amount, user, action
            FROM orders_logs
            WHERE YEAR(log_date) = %s
            """
            params = [year]
            if month:
                query += " AND MONTH(log_date) = %s"
                params.append(month)
            if user:
                query += " AND user = %s"
                params.append(user)
            query += " ORDER BY log_date DESC, log_id DESC;"
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching orders logs: {str(e)}."

def fetch_distinct_years_users(conn):
    """Fetch distinct years from orders logs table."""
    try:
        data = {"years": [], "user": []}
        with conn.cursor() as cursor:
            # Fetch distinct years
            cursor.execute("""
                SELECT DISTINCT YEAR(log_date) AS year
                FROM orders_logs
                ORDER BY year DESC
            """)
            data["years"] = [row[0] for row in cursor.fetchall()]
            # Fetch distinct users
            cursor.execute("""
                SELECT DISTINCT user
                FROM orders_logs
                ORDER BY user ASC
            """)
            data["users"] = [row[0] for row in cursor.fetchall()]
            return data, None
    except Exception as e:
        return {"years": [], "user": []}, f"Error: {str(e)}."

def reduce_product_quantity_after_delivery(conn, order_id, items, user):
    """Reduce product quantities after an order is delivered."""
    try:
        with conn.cursor() as cursor:
            for item in items:
                order_date = date.today()
                code = item.get("product_code")
                name = item.get("product_name")
                reduce_qty = int(item.get("quantity", 0))
                price = float(item.get("unit_price", 0))
                amount = reduce_qty * price
                if not code or reduce_qty <= 0:
                    return False, f"Invalid item data: {item}."
                # Insert into product_control logs
                desc = f"Order. #{order_id}. Delivered On, {order_date}."
                cursor.execute("""
                INSERT INTO product_control_logs (log_date, product_code,
                    product_name, description, quantity, total, user)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (order_date, code, name, desc, reduce_qty, amount, user))
                # Reduce quantity in Products
                cursor.execute("""
                    UPDATE products
                    SET quantity = quantity - %s
                    WHERE product_code = %s AND quantity >= %s
                    """, (reduce_qty, code, reduce_qty))
                if cursor.rowcount == 0:
                    conn.rollback()
                    return False, (
                        f"Failed to Update {item['product_name']}:\n"
                        f"Insufficient stock or Invalid product code."
                    )
        conn.commit()
        return True, "Product quantity reduced successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error reducing Quantities: {str(e)}."


def fetch_items_for_delivery(conn, order_id):
    """Fetch items for a specific order for reducing stock after delivery.
    Returns list of dicts containing code, name, qty and price or
        str: error message on failure."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT product_code, product_name, quantity, unit_price
                FROM order_items
                WHERE order_id = %s;
            """, (order_id,))
            rows = cursor.fetchall()
            if not rows:
                return f"No items found for order ID {order_id}."
            # Ensure clean and consistent format
            items = [
                {
                    "product_code": row["product_code"],
                    "product_name": row["product_name"],
                    "quantity": int(row["quantity"]),
                    "unit_price": float(row["unit_price"]),
                }
                for row in rows
            ]
            return items
    except Exception as e:
        return f"Error fetching delivery items: {str(e)}."

# from connect_to_db import connect_db
# conn = connect_db()
# success, message = mark_order_as_delivered(conn, 15, 25000, "sniffy")
# if success:
#     print(message)
# else:
#     print(message)