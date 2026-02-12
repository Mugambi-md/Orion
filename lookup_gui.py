import re
import tkinter as tk
from tkinter import StringVar
from tkinter import ttk
from base_window import BaseWindow
from working_sales import search_products
from table_utils import TreeviewSorter


class ProductSearchWindow(BaseWindow):
    def __init__(self, master, conn):
        self.window = tk.Toplevel(master)
        self.window.title("Search Products")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 750, 600, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.columns = [
            "No", "Item Code", "Item Name", "Qty", "Wholesale P.", "Retail P."
        ]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.combo = ttk.Combobox(
            self.top_frame, values=["Name", "Code"], state="readonly",
            width=6, font=("Arial", 12)
        )
        self.search_label = tk.Label(
            self.top_frame, text="Search Product Name:", bg="lightblue",
            font=("Arial", 12, "bold")
        )
        self.search_var = StringVar()
        self.entry = tk.Entry(
            self.top_frame, textvariable=self.search_var, width=15, bd=4,
            relief="raised", font=("Arial", 12)
        ) # Entry
        self.bottom_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.bottom_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.create_widgets()
        self.sorter.autosize_columns(10)

    def create_widgets(self):
        # Top Frame
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tk.Label(
            self.main_frame, text="Search Product(Item) In Stock", fg="blue",
            bg="lightblue", font=("Arial", 20, "bold", "underline")
        ).pack(side="top", anchor="s", pady=(5, 0))
        self.top_frame.pack(side="top", padx=10)
        self.bottom_frame.pack(fill="both", expand=True)
        tk.Label(
            self.top_frame, text="Search By:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0)) # Search Label
        self.combo.current(0)
        self.combo.pack(side="left", padx=(0, 5)) # Combobox
        # Bind to update function
        self.combo.bind("<<ComboboxSelected>>", self.update_search_label)
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
        self.sorter.autosize_columns(10)

    def update_search_label(self, event=None):
        """Update search label based on selected combo option."""
        selected_option = self.combo.get()
        if selected_option == "Name":
            label = "Search Product Name:"
        else:
            label = "Search Product Code:"
        self.search_label.config(text=label)

