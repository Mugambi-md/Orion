import re
import tkinter as tk
from tkinter import StringVar
from tkinter import ttk
import tkinter.font as tkFont
from base_window import BaseWindow
from working_sales import search_products

class ProductSearchWindow(BaseWindow):
    def __init__(self, master, conn):
        self.window = tk.Toplevel(master)
        self.window.title("Search Products")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 750, 400, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.columns = ["No", "Product Code", "Product Name", "Quantity",
                        "Wholesale Price", "Retail Price"]
        self.top_frame = tk.Frame(self.window, bg="lightblue")
        self.combo = ttk.Combobox(
            self.top_frame, values=["Name", "Code"], state="readonly",
            width=10
        )
        self.search_label = tk.Label(
            self.top_frame, text="Enter Product Name To Search:", bg="lightblue",
            font=("Arial", 10, "bold")
        )
        self.search_var = StringVar()
        self.entry = tk.Entry(
            self.top_frame, textvariable=self.search_var, width=20,
            font=("Arial", 11)
        ) # Entry
        self.bottom_frame = tk.Frame(self.window, bg="lightblue")
        self.tree = ttk.Treeview(
            self.bottom_frame, columns=self.columns, show="headings"
        )
        # Style
        style = ttk.Style()
        style.configure(
            "Treeview.Heading", font=("Arial", 11, "bold", "underline")
        )
        style.configure("Treeview", rowheight=30, font=("Arial", 10))

        self.create_widgets()
        self.resize_columns()

    def create_widgets(self):
        # Top Frame
        self.top_frame.pack(fill="x", padx=10)
        self.bottom_frame.pack(fill="both", expand=True, pady=(0, 5), padx=5)
        tk.Label(
            self.top_frame, text="Search By:", bg="lightblue",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=(5, 0)) # Search Label
        self.combo.current(0)
        self.combo.pack(side="left", padx=(0, 5)) # Combobox
        self.combo.bind("<<ComboboxSelected>>", self.update_search_label) #Bind to update function
        self.search_label.pack(side="left", padx=(5, 0))
        self.entry.pack(side="left", padx=(0, 5))
        self.entry.bind("<KeyRelease>", self.perform_search)
        self.entry.focus_set()
        vsb = ttk.Scrollbar(
            self.bottom_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=20)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        alt_colors = ("#ffffff", "#e6f2ff")  # White and light blueish
        self.tree.tag_configure("evenrow", background=alt_colors[0])
        self.tree.tag_configure("oddrow", background=alt_colors[1])

    def perform_search(self, event=None):
        keyword = self.search_var.get().strip()
        field = self.combo.get()
        if field == "Name":
            search_field = "product_name"
        else:
            search_field = "product_code"
        if not keyword:
            self.tree.delete(*self.tree.get_children())
            return
        result = search_products(self.conn, search_field, keyword)
        # Clear and insert results
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(result, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            code = re.sub(r"\s+", " ", str(row["product_code"])).strip()
            name = re.sub(r"\s+", " ", str(row["product_name"])).strip()
            self.tree.insert("", "end", values=(
                i,
                code,
                name,
                row['quantity'],
                f"{row['wholesale_price']:,}",
                f"{row['retail_price']:,}"
            ), tags=(tag,))
        self.resize_columns()

    def resize_columns(self):
        font = tkFont.Font()  # Auto-size columns
        for col in self.columns:
            max_width = font.measure(col)  # Start with header width
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                width = font.measure(text)
                if width > max_width:
                    max_width = width
            self.tree.column(col, width=max_width + 5)


    def update_search_label(self, event=None):
        """Update search label based on selected combo option."""
        selected_option = self.combo.get()
        if selected_option == "Name":
            label = "Enter Product Name To Search:"
        else:
            label = "Enter Product Code To Search:"
        self.search_label.config(text=label)


# if __name__ == "__main__":
#     from connect_to_db import connect_db
#     root = tk.Tk()
#     # root.withdraw()
#     conn = connect_db()
#     ProductSearchWindow(root, conn)
#     root.mainloop()