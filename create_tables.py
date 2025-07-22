from connect_to_db import connect_db

def create_tables():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS stock (
                           id INT AUTO_INCREMENT PRIMARY KEY,
                           product_code VARCHAR(50) NOT NULL UNIQUE,
                           product_name VARCHAR(100) NOT NULL,
                           retail_price DECIMAL(10,2) NOT NULL,
                           wholesale_price DECIMAL(10,2) NOT NULL
                           );
                        """)
            conn.commit()
            print("Stock table created successfully.")
        except Exception as e:
            print(f"Error creating stock table: {e}")

        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS product_control_logs (
                           id INT AUTO_INCREMENT PRIMARY KEY,
                           log_date DATE NOT NULL,
                           product_code VARCHAR(50) NOT NULL,
                           product_name VARCHAR(50) NOT NULL,
                           description VARCHAR(100) NOT NULL,
                           quantity INT,
                           total INT,
                           user VARCHAR(50) NOT NULL,
                           FOREIGN KEY (product_code) REFERENCES products(product_code)
                           );
                        """)
            conn.commit()
            print("Product Control Logs table created successfully.")
        except Exception as e:
            print(f"Error creating Product Control Logs table: {e}")

        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                           id INT PRIMARY KEY AUTO_INCREMENT,
                           product_code VARCHAR(50) NOT NULL UNIQUE,
                           product_name VARCHAR(100) NOT NULL,
                           description TEXT,
                           quantity INT NOT NULL,
                           cost DECIMAL(10,2) NOT NULL,
                           wholesale_price DECIMAL(10,2) NOT NULL,
                           retail_price DECIMAL(10,2) NOT NULL,
                           min_stock_level INT NOT NULL,
                           FOREIGN KEY (product_code) REFERENCES stock(product_code)
                            ON UPDATE CASCADE
                            ON DELETE CASCADE
                           );
                        """)
            conn.commit()
            print("Products table created successfully.")
        except Exception as e:
            print(f"Error creating products table: {e}")

        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS replenishments (
                           id INT AUTO_INCREMENT PRIMARY KEY,
                           product_code VARCHAR(50) NOT NULL UNIQUE,
                           product_name VARCHAR(100),
                           quantity INT NOT NULL,
                           cost_per_unit DECIMAL(10,2),
                           total_cost DECIMAL(10,2) AS (cost_per_unit * quantity) STORED,
                           date_replenished DATE NOT NULL,
                           FOREIGN KEY (product_code) REFERENCES stock(product_code)
                            ON UPDATE CASCADE
                            ON DELETE CASCADE
                           );
                        """)
            conn.commit()
            print("Replenishments table created successfully.")
        except Exception as e:
            print(f"Error creating replenishments table: {e}")

        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
                           id INT AUTO_INCREMENT PRIMARY KEY,
                           receipt_no VARCHAR(50) UNIQUE NOT NULL,
                           sale_date DATE NOT NULL,
                           sale_time TIME NOT NULL,
                           total_amount DECIMAL(10,2) NOT NULL,
                           user VARCHAR(50) NOT NULL
                           );
                        """)
            conn.commit()
            print("Sales table created successfully.")
        except Exception as e:
            print(f"Error creating sales table: {e}")

        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS sale_items (
                           id INT AUTO_INCREMENT PRIMARY KEY,
                           date DATE NOT NULL,
                           time TIME NOT NULL,
                           receipt_no VARCHAR(50),
                           product_code VARCHAR(50),
                           product_name VARCHAR(50) NOT NULL,
                           quantity INT NOT NULL,
                           unit_price DECIMAL(10, 2) NOT NULL,
                           total_amount DECIMAL(10, 2) AS (quantity * unit_price) STORED,
                           user VARCHAR(50),
                           FOREIGN KEY (receipt_no) REFERENCES sales(receipt_no),
                           FOREIGN KEY (product_code) REFERENCES products(product_code)
                           );
                        """)
            conn.commit()
            print("Sale Items table created successfully.")
        except Exception as e:
            print(f"Error creating sale items table: {e}")

        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS sales_control (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            date DATE NOT NULL,
                            receipt_no VARCHAR(50),
                            description VARCHAR(30) NOT NULL,
                            user VARCHAR(20) NOT NULL,
                            amount DECIMAL(10, 2) NOT NULL,
                            cumulative_total DECIMAL(10, 2) NOT NULL,
                            FOREIGN KEY (receipt_no) REFERENCES sales(receipt_no)
                            );
                            """)
            conn.commit()
            print("Sale control table created successfully.")
        except Exception as e:
            print(f"Error creating sale control table: {e}")

        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS payments (
                           id INT AUTO_INCREMENT PRIMARY KEY,
                           user VARCHAR(50) NOT NULL,
                           receipt_no VARCHAR(50) NOT NULL,
                           payment_date DATE NOT NULL,
                           amount_paid DECIMAL(10, 2) NOT NULL,
                           payment_method SET('Cash', 'Mpesa') NOT NULL,
                           FOREIGN KEY (receipt_no) REFERENCES sales(receipt_no)
                           );
                        """)
            conn.commit()
            print("Payments table created successfully.")
        except Exception as e:
            print(f"Error creating payments table: {e}")

        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS orders (
                           order_id INT AUTO_INCREMENT PRIMARY KEY,
                           customer_name VARCHAR(70) NOT NULL,
                           contact VARCHAR(20) NOT NULL,
                           date_placed DATE NOT NULL,
                           deadline DATE NOT NULL,
                           amount DECIMAL(10, 2) NOT NULL,
                           status ENUM('Pending', 'Delivered') NOT NULL DEFAULT 'Pending'
                           );
                        """)
            conn.commit()
            print("Orders table created successfully.")
        except Exception as e:
            print(f"Error creating orders table: {e}")

        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS order_items (
                           order_item_id INT AUTO_INCREMENT PRIMARY KEY,
                           order_id INT NOT NULL,
                           product_code VARCHAR(50) NOT NULL,
                           product_name VARCHAR(100) NOT NULL,
                           quantity INT NOT NULL,
                           unit_price DECIMAL(10, 2) NOT NULL,
                           total_price DECIMAL(10, 2) NOT NULL,
                           FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
                           FOREIGN KEY (product_code) REFERENCES products(product_code) ON DELETE CASCADE
                           );
                        """)
            conn.commit()
            print("Order items table created successfully.")
        except Exception as e:
            print(f"Error creating order items table: {e}")

        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS orders_payments (
                           payment_id INT AUTO_INCREMENT PRIMARY KEY,
                           order_id INT NOT NULL UNIQUE,
                           total_amount DECIMAL(10, 2) NOT NULL,
                           paid_amount DECIMAL(10, 2) NOT NULL,
                           balance DECIMAL(10, 2) NOT NULL,
                           method VARCHAR(40) NULL,
                           FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                           );
                        """)
            conn.commit()
            print("Order Payments table created successfully.")
        except Exception as e:
            print(f"Error creating orders Payments table: {e}")

        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS orders_logs (
                           log_date DATE NOT NULL,
                           log_id INT AUTO_INCREMENT PRIMARY KEY,
                           order_id INT NOT NULL,
                           total_amount DECIMAL(10, 2) NOT NULL,
                           user VARCHAR(50) NOT NULL,
                           action ENUM('Received Order', 'Partial Payment', 'Full Payment', 'Delivered', 'Edited Order') NOT NULL,
                           FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                           );
                        """)
            conn.commit()
            print("Order Logs table created successfully.")
        except Exception as e:
            print(f"Error creating orders Logs table: {e}")





        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_tables()