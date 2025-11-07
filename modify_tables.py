def keep_logs_after_order_delete(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = 'orders_logs'
            AND COLUMN_NAME = 'order_id'
            AND REFERENCED_TABLE_NAME = 'orders';
            """)
            result = cursor.fetchone()
            if not result:
                return False, "No foreign key constraint found for order_id."
            fk_name = result[0]
            # 2. Drop the foreign key
            cursor.execute(
                f"ALTER TABLE orders_logs DROP FOREIGN KEY {fk_name};"
            )
            # 3. Keep order id as NOT NULL
            cursor.execute(
                "ALTER TABLE orders_logs MODIFY order_id INT NOT NULL;"
            )
            conn.commit()
            return True, f"Foreign key '{fk_name}' dropped successfully.\nLogs will remain after order deletion."
    except Exception as e:
        conn.rollback()
        return False, f"Error Modifying table: {str(e)}."



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
# success, message = modify_column(conn)
# if success:
#     print(success, message)
# else:
#     print(success, message)