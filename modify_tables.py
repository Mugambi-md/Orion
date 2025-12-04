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
                "ALTER TABLE access ADD COLUMN clearance TEXT;"
            )
            conn.commit()
            return True, "Table Column Added Successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error Modifying: {str(e)}"

def update_privileges(conn, descriptions):
    try:
        with conn.cursor() as cursor:
            for privilege, desc in descriptions.items():
                cursor.execute("""
                    UPDATE access
                    SET clearance = %s
                    WHERE privilege = %s;
                """, (desc, privilege))
        conn.commit()
        return True, "Clearance description updated successfully."
    except Exception as e:
        return False, f"Error Updating description: {str(e)}."


descriptions = {
    "Add User": "Add new user Account",
    "Manage User": "Access Employees window",
    "Assign Privilege": "Assigning Privileges to employees.",
    "General Product Report": "View Sales Product performance",
    "Change Product Price": "Change Product Prices",
    "General Sales Report": "View sales reports.",
    "View Finacial Accounts": "View Financial accounts Record",
    "Manage Finacial Accounts": "Access Accounting window",
    "Make Sale": "Allows user to make sale"
}
#
# from connect_to_db import connect_db
# conn=connect_db()
# success, msg = update_privileges(conn, descriptions)
# print(success, msg)