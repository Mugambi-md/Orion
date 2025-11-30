def keep_logs_after_order_delete(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = 'order_items'
            AND COLUMN_NAME = 'product_code'
            AND REFERENCED_TABLE_NAME = 'products';
            """)
            result = cursor.fetchone()
            if not result:
                print("No foreign key constraint found on product_code.")
            fk_name = result[0]
            # 2. Drop the foreign key
            cursor.execute(
                f"ALTER TABLE order_items DROP FOREIGN KEY {fk_name};"
            )
            print(f"Dropped old foreign key: {fk_name}.")
            # 3. Keep order id as NOT NULL
            cursor.execute("""
            ALTER TABLE order_items
            ADD CONSTRAINT fk_orderitems_productcode
            FOREIGN KEY (product_code)
            REFERENCES products(product_code)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
            """)
            conn.commit()
            print("Foreign key modified successfully (on update cascade added.")
    except Exception as e:
        conn.rollback()
        print(f"Error Modifying table: {str(e)}.")



def modify_column(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE orders_logs MODIFY COLUMN action TEXT NOT NULL;"
            )
            conn.commit()
            return True, "Table Column Modified Successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error Modifying: {str(e)}"

# from connect_to_db import connect_db
# conn=connect_db()
# keep_logs_after_order_delete(conn)