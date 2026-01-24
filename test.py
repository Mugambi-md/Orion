import bcrypt
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
            ALTER TABLE logins
            ADD COLUMN pass_change ENUM('true', 'false') NOT NULL DEFAULT 'true'
            AFTER password;
            """)
            conn.commit()
            print("Pass Change Column Added successfully.")
    except Exception as e:
        print(f"Error: {str(e)}")

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


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(
        plain_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

def migrate_passwords(conn):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT no, password FROM logins;")
        users = cursor.fetchall()
        for user in users:
            if user["password"].startswith("$2b$"):
                continue
            hashed_pass = hash_password(user["password"])
            cursor.execute("""
                UPDATE logins
                SET password = %s
                WHERE no = %s;
            """, (hashed_pass, user["no"]))
    conn.commit()
    print("Password migration completed successfully.")

def update_access_clearance(conn):
    """
    Update clearance column for access records where clearance is NULL or empty.
    Rules:
    - One-word privilege -> 'access <privilege>'
    - Multi-word privilege -> privilege as-is

    Returns:
        (success: bool, message: str)
    """
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Fetch privileges with no clearance
            cursor.execute("""
                SELECT no, privilege
                FROM access
                WHERE clearance IS NULL OR clearance = '';
            """)
            rows = cursor.fetchall()

            if not rows:
                return True, "No access records require updating."

            update_query = """
                UPDATE access
                SET clearance = %s
                WHERE no = %s;
            """

            for row in rows:
                privilege = row["privilege"].strip()

                # Check if single-word or multi-word
                if len(privilege.split()) == 1:
                    clearance = f"access {privilege}"
                else:
                    clearance = privilege

                cursor.execute(update_query, (clearance, row["no"]))

        conn.commit()
        return True, f"{len(rows)} access records updated successfully."

    except Exception as e:
        conn.rollback()
        return False, f"Failed to update access clearance: {str(e)}."

# from connect_to_db import connect_db
# conn=connect_db()
# success, msg = update_access_clearance(conn)
# print(success, msg)