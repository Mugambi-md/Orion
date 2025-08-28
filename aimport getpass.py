from datetime import date
from connect_to_db import connect_db

class EmployeeManager:
    def __init__(self, conn):
        self.conn = conn

    def insert_employee(self, name, username, department, designation, national_id, phone, email, salary):
        try:
            with self.conn.cursor() as cursor:
                # Insert Employee
                cursor.execute("""INSERT INTO employees (name, username, department, designation, national_id,
                            phone, email, salary)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (name, username, department, designation, national_id, phone, email, salary))
                user_code = self.create_employee_code(department)
                if not user_code:
                    self.conn.rollback()
                    return "Error generating user code."
                # Insert login
                login_result = self.insert_login_data(user_code, username)
                if "Error" in login_result:
                    self.conn.rollback()
                    return login_result
                # Increase employee count in department
                self.increase_employee_count(department)
                self.conn.commit()
                return f"Employee {name} of department {department} created successfully."
        except Exception as e:
            self.conn.rollback()
            return f"Insertion Error: {e}"

    def get_department_code(self, department_name):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT code FROM departments WHERE name=%s", (department_name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            return None

    def create_employee_code(self, department):
        try:
            dpt_code = self.get_department_code(department)
            if not dpt_code:
                return None
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM employees")
                count_result = cursor.fetchone()
                emp_count = count_result[0] if count_result else 0
            first_letter = department[0].upper()
            return f"{dpt_code}{emp_count}{first_letter}"
        except Exception as e:
            return None

    def insert_login_data(self, user_code, username):
        try:
            today = date.today()
            with self.conn.cursor() as cursor:
                # Fetch designation
                cursor.execute("SELECT designation FROM employees WHERE username=%s", (username,))
                result = cursor.fetchone()
                if not result:
                    return f"Error: No employee found with username '{username}'."
                designation = result[0]
                # Insert login
                cursor.execute("""INSERT INTO logins (user_code, username, date_created, designation)
                VALUES (%s, %s, %s, %s)
                """, (user_code, username, today, designation))
                return "Login created."
        except Exception as e:
            return f"Insert login Error: {e}"

    def increase_employee_count(self, department):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""UPDATE departments
                        SET employees = employees + 1
                        WHERE name=%s
                        """, (department,))
        except Exception as e:
            raise e


