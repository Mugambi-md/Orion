from connect_to_db import connect_db
conn = connect_db()
cursor = conn.cursor()
#cursor.execute("DROP TABLE IF EXISTS orders_payments;")