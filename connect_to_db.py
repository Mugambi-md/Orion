import mysql.connector


# DB Connection Function
def connect_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Sniffy@96",
            database="Shop"
        )
        if connection.is_connected():
            print("Connected to MySQL database successfully!")
            return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Test the connection
if __name__ == "__main__":
    conn = connect_db()
    if conn:
        conn.close()