from connect_to_db import connect_db

def create_tables(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""CREATE TABLE IF NOT EXISTS departments (
            no INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(25) NOT NULL UNIQUE,
            code INT NOT NULL UNIQUE,
            employees INT NULL DEFAULT 0
            );
            """)
            print("Departments table created successfully.")

            cursor.execute("""CREATE TABLE IF NOT EXISTS employees (
            no INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(30) NOT NULL,
            username VARCHAR(15) NOT NULL UNIQUE,
            department VARCHAR(25) NOT NULL,
            designation VARCHAR(30) NOT NULL,
            national_id INT NOT NULL UNIQUE,
            phone VARCHAR(14) NOT NULL UNIQUE,
            email VARCHAR(50) NOT NULL UNIQUE,
            salary DECIMAL(10, 3) NOT NULL,
            FOREIGN KEY (department) REFERENCES departments(name)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
            );
            """)
            print("Employees table created successfully.")

            cursor.execute("""CREATE TABLE IF NOT EXISTS logins (
            no INT AUTO_INCREMENT PRIMARY KEY,
            user_code VARCHAR(10) NOT NULL UNIQUE,
            username VARCHAR(15) NOT NULL UNIQUE,
            password VARCHAR(20) NOT NULL DEFAULT '000000',
            date_created DATE NOT NULL,
            designation VARCHAR(20) NOT NULL,
            status ENUM('active', 'disabled') NOT NULL DEFAULT 'active',
            FOREIGN KEY (username) REFERENCES employees(username)
                ON UPDATE CASCADE
                ON DELETE CASCADE
            );
            """)
            print("Logins table created successfully.")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS access (
                no INT AUTO_INCREMENT PRIMARY KEY,
                privilege VARCHAR(70) NOT NULL UNIQUE,
                clearance TEXT
                );
            """)
            print("Access table created successfully.")

            cursor.execute("""CREATE TABLE IF NOT EXISTS login_access (
            user_code VARCHAR(10),
            access_id INT,
            PRIMARY KEY (user_code, access_id),
            FOREIGN KEY (user_code) REFERENCES logins(user_code)
                ON DELETE CASCADE,
            FOREIGN KEY (access_id) REFERENCES access(no)
                ON DELETE CASCADE
            );
            """)
            print("Login Access table created successfully.")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                log_date DATE NOT NULL,
                log_time TIME NOT NULL,
                username VARCHAR(30) NOT NULL,
                section VARCHAR(30) NOT NULL,
                action TEXT NOT NULL,
                INDEX (username),
                INDEX (section)
                );
            """)
            print("Logs table created successfully.")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cashier_control (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(30) NOT NULL,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    description TEXT NOT NULL,
                    debit DECIMAL(10, 2) DEFAULT 0.00,
                    credit DECIMAL(10, 2) DEFAULT 0.00,
                    status ENUM('open', 'closed') NOT NULL DEFAULT 'open'
                );
            """)
            print("Cashier Control table created successfully.")
        conn.commit()
    except Exception as e:
        print(f"Table Error: {e}")

# Run the function to create tables
if __name__ == "__main__":
    conn = connect_db()
    create_tables(conn)