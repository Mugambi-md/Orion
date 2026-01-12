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
            MODIFY COLUMN password VARCHAR(255) NOT NULL;
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

# from connect_to_db import connect_db
# conn=connect_db()
# migrate_passwords(conn)