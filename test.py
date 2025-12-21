import tkinter as tk
from tkinter import messagebox, ttk
from base_window import BaseWindow
import datetime
from working_on_employee import insert_logs
from working_on_accounting import  SalesJournalRecorder
def search_products(conn, field, keyword):
    """Search products by field (e.g., 'product_name' or 'product_code') using like %keyword%."""
    pattern = f"%{keyword}%"
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"""
            SELECT product_code, product_name, quantity, wholesale_price, retail_price
            FROM products
            WHERE {field} LIKE %s
            ORDER BY {field}
            LIMIT 15
            """, (pattern,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Error searching products: {e}")
        return []

def modify_email(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE cashier_control
            SET status='open'
            WHERE id=19;
            """)
            conn.commit()
            print("Column Updated successfully.")
    except Exception as e:
        print(f"Error: {e}")

def add_sale_time_column_if_missing(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM sales LIKE 'sale_time'")
            result = cursor.fetchone()
            if not result:
                cursor.execute("""
                        ALTER TABLE sales
                        ADD COLUMN sale_time TIME NOT NULL
                        AFTER sale_date
                        """)
                conn.commit()
                print("Column 'sale time' added successfully.")
            else:
                print("Column 'sale_time' already exists.")
    except Exception as e:
        print(f"Error adding sale time: {e}")


from connect_to_db import connect_db
conn=connect_db()
# modify_email(conn)