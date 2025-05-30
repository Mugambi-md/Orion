from connect_to_db import connect_db
def get_stock_table():
    from working_on_stock2 import  view_stock
    title = "Stock Details"
    columns = ("No", "Code", "Name", "Retail Price", "Wholesale Price")
    data = view_stock()
    rows = [
        (
            i,
            row["code"],
            row["name"],
            row["retail"],
            row["wholesale"]
        ) for i, row in enumerate(data, start=1)
    ]
    return title, columns, rows, data

def get_products_table():
    from working_on_stock2 import view_all_products
    title = "Products details"
    columns = ("No", "Code", "Name", "Desciption", "Quantity", "Cost", "Wholesale Price", "Retail Price", "Min Stock Level")
    data = view_all_products()
    rows = [
        (
            i,
            row["product_code"],
            row["product_name"],
            row["description"],
            row["quantity"],
            row["cost"],
            row["wholesale_price"],
            row["retail_price"],
            row["min_stock_level"]
        ) for i, row in enumerate(data, start=1)
    ]
    return title, columns, rows, data

def get_replenishments_table():
    from working_on_stock2 import view_replenishments
    title = "Replenishments"
    columns = ("No", "Product Code", "Product Name", "Availabe Stock", "Cost Per Unit", "Total Cost", "Last Replenishment")
    data = view_replenishments()
    rows = [
        (
            i,
            row["product_code"],
            row["product_name"],
            row["quantity"],
            row["cost_per_unit"],
            row["total_cost"],
            row["date_replenished"]
        ) for i, row in enumerate(data, start=1)
    ]
    return title, columns, rows, data

def products_report_table():
    from working_on_stock2 import view_all_products
    conn = connect_db()
    cursor = conn.cursor()
    columns = ("No", "Code", "Name", "Desciption", "Quantity", "Cost", "Wholesale Price", "Retail Price", "Min Stock Level")
    data = view_all_products()
    rows = []
    for i, row in enumerate(data, start=1):
        product_code = row["product_code"]
        cursor.execute("SELECT date_replenished FROM replenishments WHERE product_code = %s", (product_code,))
        result = cursor.fetchone()
        last_date = result[0] if result else "N/A"
        rows.append((
            i,
            product_code,
            row["product_name"],
            row["description"],
            row["quantity"],
            row["cost"],
            row["wholesale_price"],
            row["retail_price"],
            row["min_stock_level"],
            last_date
        ))

    return columns, rows, data

