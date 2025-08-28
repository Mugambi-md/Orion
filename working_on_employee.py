from connect_to_db import connect_db
conn = connect_db()
from datetime import date

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

def insert_into_departments(conn, name):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM departments")
            count = cursor.fetchone()[0]
            code = int(f"{count + 1}0")
            cursor.execute("INSERT INTO departments (name, code) VALUES (%s, %s)", (name, code))
        conn.commit()
        return f"{name} inserted into departments with code: {code} Successfully."
    except Exception as e:
        conn.rollback()
        return f"Error: {e}"

def fetch_departments(conn):
    """Fetch name, code and number of employees from departments table.
    Returns a list of dictionaries.
    """
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT name, code, employees FROM departments")
            departments = cursor.fetchall()
            return departments
    except Exception as e:
        return f"Error fetching departments: {e}"


def get_departments(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM departments")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        return f"Error: {e}"

def username_exists(conn, keyword):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT username FROM employees WHERE username LIKE %s", (f"{keyword}%",))
            return cursor.fetchall()
    except Exception as e:
        return f"Error searching product codes: {e}"

def fetch_logins_by_username(conn, username):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT password, date_created, designation, access, status
            FROM logins
            WHERE username = %s
            """, (username,))
            row = cursor.fetchone()
            if row:
                password, date_created, access, status =row
                access_list = access.split(',') if access else []
                return {
                    'password': password,
                    'date_created': str(date_created),
                    'access': access_list,
                    'status': status
                }
            else:
                return None
    except Exception as e:
        return f"Username Error: {e}."

def update_login_password(conn, username, new_pass):
    try:
        with conn.cursor() as cursor:
            now = date.today()
            cursor.execute("""UPDATE logins
            SET password=%s, date_created=%s
            WHERE username=%s
            """, (new_pass, now, username))
            conn.commit()
            if cursor.rowcount == 0:
                return f"Username '{username}' not Found."
            else:
                return "Password updated successfully."
    except Exception as e:
        return f"Error updating password for '{username}': {e}"

def update_login_status(conn, identifier, status):
    """
    Args: conn: the database connection, identifier: the username or user code, status: Either active or disabled.
    Also deletes all access entries from login access for that user.
    """
    if status not in ("active", "disabled"):
        return "Invalid Status. Must be Active or Disabled."
    try:
        with conn.cursor() as cursor:
            # First get user code from the identifier
            cursor.execute("""
                SELECT user_code FROM logins
                WHERE username = %s OR user_code = %s
                """, (identifier, identifier))
            row = cursor.fetchone()
            if not row:
                return f"No matching user found for '{identifier}'."
            user_code = row[0]
            if status == "disabled":
                # Delete all access entries for this user
                cursor.execute("""DELETE FROM login_access WHERE user_code = %s""", (user_code,))
            # Update the login status
            cursor.execute("""
                UPDATE logins
                SET status=%s
                WHERE user_code=%s
                """, (status, user_code))

            conn.commit()
            return f"Status for '{identifier}' updated to '{status}'."
    except Exception as e:
        conn.rollback()
        raise e

def get_login_status_and_name(conn, identifier):
    """Fetch the employee's name and current login status using username or user_code.
        Returns: Tuple (name, status) if found, or None if not found."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT e.name, l.status
                FROM logins l
                JOIN employees e ON l.username=e.username
                WHERE l.username=%s OR l.user_code=%s
                """, (identifier, identifier))
            result = cursor.fetchone()
            if result:
                return result[0], result[1] # Name, Status
            return None
    except Exception as e:
        raise e

def insert_privilege(conn, privilege):
    """Insert new privilege into access table. Return success message or error string."""
    if not privilege.strip():
        return "Privilege cannot be empty."
    try:
        with conn.cursor() as cursor:
            cursor.execute("""INSERT INTO access (privilege)
                        VALUES (%s)
                        """, (privilege.strip(),))
            conn.commit()
            return f"Privilege '{privilege}' inserted successfully."
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            return f"Privilege '{privilege}' already exists."
        return f"Insert Error: {e}"

def get_user_info(conn, identifier):
    """Fetch user code and name using either username or user_code. Returns: Tuple: (user_code, name) or None."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT l.user_code, e.name
                    FROM logins l
                    JOIN employees e ON l.username=e.username
                    WHERE l.username=%s OR l.user_code=%s
                    """, (identifier, identifier))
            result = cursor.fetchone()
            if result:
                return result[0], result[1]
            else:
                return None
    except Exception as e:
        raise e

def get_all_privileges(conn):
    """Retrieve all privileges from access table with their IDs. Returns: List of tuples: [(no, privilege), ...]"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT no, privilege FROM access ORDER BY privilege ASC")
            return cursor.fetchall()
    except Exception as e:
        raise e

def insert_user_privilege(conn, user_code, access_id):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                    INSERT IGNORE INTO login_access (user_code, access_id)
                    VALUES (%s, %s)
                    """, (user_code, access_id))
            conn.commit()
            if cursor.rowcount == 0:
                return False, f"Privilege already assigned to '{user_code}'."
            return True, f"Privilege successfully assigned to '{user_code}'."
    except Exception as e:
        conn.rollback()
        return False, f"Insert Error: {e}"

def get_user_privileges(conn, identifier):
    """Fetch user code, access id and privilege name for a given username or user code."""
    try:
        with conn.cursor() as cursor:
            # Get user_code if identifier is username
            cursor.execute("""SELECT user_code FROM logins
                        WHERE username=%s OR user_code=%s
                        """, (identifier, identifier))
            result = cursor.fetchone()
            if not result:
                return f"No user found for identifier: {identifier}."
            user_code = result[0]
            # Get privileges assigned to that user
            cursor.execute("""SELECT la.user_code, la.access_id, a.privilege
                    FROM login_access la
                    JOIN access a ON la.access_id=a.no
                    WHERE la.user_code=%s
                    """, (user_code,))
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching privileges: {e}."

def remove_user_privilege(conn, user_code, access_id):
    """Remove a specific privilege from a user. Returns a str: Success or error message."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""DELETE FROM login_access
                    WHERE user_code=%s AND access_id=%s
                    """, (user_code, access_id))
            if cursor.rowcount == 0:
                return f"No matching privilege found for user '{user_code}' and access ID '{access_id}'."
            conn.commit()
            return f"Privilege with ID {access_id} Removed from user '{user_code}'."
    except Exception as e:
        conn.rollback()
        return f"Error removing privilege: {e}."

def reset_user_password(conn, user_code, new_password="000000"):
    """Reset user's password to default or custom password and update date_created."""
    today = date.today()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""UPDATE logins
                    SET password=%s, date_created=%s
                    WHERE user_code=%s
                    """, (new_password, today, user_code))
            if cursor.rowcount == 0:
                return f"No matching user found for '{user_code}'."
            conn.commit()
            return f"Password for '{user_code}' reset successfully to '{new_password}'."
    except Exception as e:
        conn.rollback()
        return f"Error resetting password: {e}"
def check_username_exists(conn, username):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT username FROM logins WHERE username=%s", (username,))
            return cursor.fetchone() is not None
    except Exception as e:
        return False, f"{e}"
def fetch_password(conn, username):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT password FROM logins WHERE username=%s", (username,))
            return cursor.fetchone()
    except Exception as e:
        raise e

def get_assigned_privileges(conn, identifier):
    """Return status, list of privileges and role for a given username."""
    try:
        with conn.cursor() as cursor:
            # Fetch user_code and status
            cursor.execute("""SELECT user_code, status, designation
                    FROM logins
                    WHERE username=%s
                    """, (identifier,))
            result = cursor.fetchone()
            if not result:
                return None, [], None # No user found
            user_code, status, role = result
            # Fetch Privileges
            cursor.execute("""
                SELECT a.privilege
                        FROM login_access la
                        JOIN access a ON la.access_id=a.no
                        WHERE la.user_code=%s
                        """, (user_code,))
            privileges = [row[0] for row in cursor.fetchall()]
            return status, privileges, role, None
    except Exception as e:
        return None, [], None, str(e)

def fetch_all_employee_details(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT e.name, l.user_code, e.username, e.department, e.designation, e.national_id, e.phone, e.email,
                    e.salary, l.status
                FROM employees e
                JOIN logins l ON e.username=l.username
                ORDER BY e.name ASC
                """)
            return cursor.fetchall(), None
    except Exception as e:
        return [], str(e)
def fetch_user_details_and_privileges(conn, identifier):
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Fetch user details
            cursor.execute("""
                SELECT user_code, username, designation
                FROM logins
                WHERE username = %s OR user_code =%s
                LIMIT 1;
                """, (identifier, identifier))
            user = cursor.fetchone()
            if not user:
                return None, [] # No user found

            # Fetch privileges
            cursor.execute("""
                SELECT a.privilege
                FROM login_access la
                JOIN access a ON la.access_id = a.no
                WHERE la.user_code = %s
                """, (user['user_code'],))
            privileges = cursor.fetchall() # List of dictionaries
            return user, privileges
    except Exception as e:
        return {f"Error: {str(e)}"}, []
def fetch_all_users(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT user_code, username FROM logins ORDER BY username;")
            rows = cursor.fetchall()
            if not rows:
                return "No Users found in the database."
            return rows
    except Exception as e:
        return f"Error: {str(e)}"

def fetch_user_identity(conn, identifier):
    """Fetch username and user code from logins table using either."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT username, user_code
                FROM logins
                WHERE username = %s OR user_code=%s
                LIMIT 1;
                """, (identifier, identifier))
            row = cursor.fetchone()
            if not row:
                return "No matching user found."
            else:
                return row
    except Exception as e:
        return f"Error: {str(e)}"

def fetch_employee_login_info(conn, identifier):
    """Fetches name, username, designation, national_id, phone, email, salary
    and status. Returns (True, rows) or (False, error_message)."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT
                    e.name,
                    e.username,
                    l.user_code,
                    e.designation,
                    e.national_id,
                    e.phone,
                    e.email,
                    e.salary,
                    l.status
                FROM employees e
                JOIN logins l ON e.username = l.username
                WHERE e.username = %s OR l.user_code = %s
                LIMIT 1;
                """, (identifier, identifier))
            row = cursor.fetchone()
            if not row:
                return False, f"No matching employee for identifier '{identifier}'."
            return True, row
    except Exception as e:
        return False, f"Error fetching Employee Info: {e}."

def update_employee_info(conn, info):
    """Updates employee/login field except user_code using user_code as
    identifier. Expects 'info' dict with keys: code, name, username,
    designation, national_id, phone, email, salary """
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Fetch current username for given user_code
            cursor.execute(
                "SELECT username FROM logins WHERE user_code = %s LIMIT 1",
                (info["user_code"],)
            )
            row = cursor.fetchone()
            if not row:
                return False, f"No login found for user code '{info['user_code']}'."
            current_username = row["username"]
            # Update employees (only provided fields)
            emp_fields = []
            emp_values = []
            for field in ("name", "username", "designation", "national_id",
                          "phone", "email", "salary"):
                if field in info:
                    emp_fields.append(f"{field} = %s")
                    emp_values.append(info[field])
            if emp_fields:
                emp_values.append(current_username) # WHERE filter
                cursor.execute(
                    f"UPDATE employees SET {','.join(emp_fields)} WHERE username=%s",
                    tuple(emp_values)
                )
            # Update logins (username, designation, status if provided)
            login_fields = []
            login_values = []
            if "username" in info:
                login_fields.append("username = %s")
                login_values.append(info["username"])
            if "designation" in info:
                login_fields.append("designation = %s")
                login_values.append(info["designation"])
            if "status" in info:
                login_fields.append("status = %s")
                login_values.append(info["status"])
            if login_fields:
                login_values.append(info["user_code"])
                cursor.execute(
                    f"UPDATE logins SET {','.join(login_fields)} WHERE user_code = %s",
                    tuple(login_values)
                )
        conn.commit()
        return True, "Employee info updated successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error updating employee info: {e}."


