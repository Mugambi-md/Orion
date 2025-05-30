def open_products_details_window():
    import tkinter as tk
    from tkinter import ttk
    from stock_access_tables import products_report_table
    from products_info_utls import export_products_to_csv
    window = tk.Toplevel()
    window.title("Products Information")
    window.geometry("1000x500")
    window.configure(bg="green")
    window.grab_set()
    left_frame = tk.Frame(window, width=200, bg="green") # Left frame with buttons
    left_frame.pack(side="left", fill="y")
    
    def products_statistics():
        pass
    def another_action():
        pass
    # Buttons on the left
    tk.Button(left_frame, text="Export To CSV", width=20, command=lambda: export_products_to_csv(window)).pack(pady=10)
    tk.Button(left_frame, text="Product Statistics", width=20, command=products_statistics).pack(pady=10)
    tk.Button(left_frame, text="Other Action", width=20, command=another_action).pack(pady=10)
    # Right frame with table
    right_frame = tk.Frame(window, padx=3, bg="skyblue")
    right_frame.pack(side="left", fill="both", expand=True)

    columns, rows, _ = products_report_table()
    title = "Available Products Information"
    # Table Title
    tk.Label(right_frame, text=title, font=("Arial", 14, "bold"), bg="skyblue").pack(pady=5)
    tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=100)
    # Add data with alternating row colors
    for i, row in enumerate(rows):
        tag = "evenrow" if i % 2 == 0 else "oddrow"
        tree.insert("", "end", values=row, tags=(tag,))
    tree.tag_configure("evenrow", background="#fffde7")
    tree.tag_configure("oddrow", background="#e0f7e9")
    tree.pack(padx=5, pady=5, fill="both", expand=True)