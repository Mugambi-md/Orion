def get_products_for_sales_table():
    from working_on_stock2 import view_all_products
    columns = ("No", "Product Code", "Product Name", "Description", "Quantity", "Retail Price", "Wholesale Price")
    data = view_all_products()
    rows = [
        (
            i,
            row["product_code"],
            row["product_name"],
            row["description"],
            row["quantity"],
            row["retail_price"],
            row["wholesale_price"]
        ) for i, row in enumerate(data, start=1)
    ]
    return columns, rows