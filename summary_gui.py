import re
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
from decimal import Decimal
from datetime import date, datetime

class SummaryPreviewWindow:
    def __init__(self, conn, title, columns, fetch, params=None):
        self.window = tk.Toplevel()
        self.window.title(f"{title}")
        self.window.configure(bg="lightblue")
        self.window.state("zoomed")
        self.window.transient()
        self.window.grab_set()

        self.conn = conn
        self.columns = columns
        self.fetch = fetch
        self.params = params
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"))
        style.configure("Treeview", font=("Arial", 11))
        self.sort_direction = {} # Track column sort direction

        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.title = tk.Label(
            self.main_frame, text=title, bg="lightblue", fg="blue", bd=4,
            relief="groove", font=("Arial", 22, "bold", "underline"),
            width=(len(title) + 10)
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.tree_columns = ["No."] + list(self.columns.keys())
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.tree_columns, show="headings"
        )

        self.build_ui()
        self.load_data()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        self.title.pack(anchor="center", ipadx=10)
        self.table_frame.pack(fill="both", expand=True)
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        x_scroll = ttk.Scrollbar(
            self.table_frame, orient="horizontal", command=self.tree.xview
        )
        for heading in self.tree_columns:
            self.tree.heading(
                heading,
                text=heading,
                command=lambda c=heading: self.sort_by_column(c)
            )
            self.tree.column(heading, anchor="center", width=30)
        self.tree.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )
        x_scroll.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def format_value(self, value):
        if value is None:
            return
        # Date detection
        if isinstance(value, (date, datetime)):
            return value.strftime("%d/%m/%Y")
        if isinstance(value, str):
            # ISO date string yyyy-mm-dd
            if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                return value.replace("-", "/")
        # Money detection
        if isinstance(value, Decimal):
            return f"{value:,.2f}"

        return value

    def call_fetch(self):
        if not self.params:
            return self.fetch()
        if len(self.params) == 1:
            return self.fetch(self.params[0])
        if len(self.params) == 2:
            return self.fetch(self.params[0], self.params[1])

    def load_data(self):
        rows, error = self.call_fetch()

        if error:
            messagebox.showerror("Error", error, parent=self.window)
            return
        for i, row in enumerate(rows, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            formatted_values = []
            for field in self.columns.values():
                formatted_values.append(self.format_value(row[field]))
            self.tree.insert(
                "", "end", values=[i] + formatted_values, tags=(tag,)
            )
        self.resize_columns()

    def sort_by_column(self, col):
        # Not sort the number column
        if col == "No.":
            return
        # Determine sort direction
        reverse = self.sort_direction.get(col, False)

        # Extract data From treeview
        data = []
        for item in self.tree.get_children():
            value = self.tree.set(item, col)
            data.append((value, item))
        # Try numeric sorting, fallback to text
        try:
            data.sort(
                key=lambda x: float(str(x[0]).replace(",", "")),
                reverse=reverse
            )
        except ValueError:
            data.sort(key=lambda x: x[0].lower(), reverse=reverse)
        # Reorder rows
        for index, (_, item) in enumerate(data):
            self.tree.move(item, "", index)
        # Toggle direction
        self.sort_direction[col] = not reverse
        # Show direction
        for heading in self.tree_columns:
            text = heading
            if heading == col:
                text += " ▲" if not reverse else " ▼"
            self.tree.heading(
                heading,
                text=text,
                command=lambda c=heading: self.sort_by_column(c)
            )
        # Re-number rows after sorting
        self.renumber_rows()


    def renumber_rows(self):
        for index, item in enumerate(self.tree.get_children(), start=1):
            # Update row number
            self.tree.set(item, "No.", index)
            # Re-apply zebra striping
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.item(item, tags=(tag,))

    def resize_columns(self):
        font = tkFont.Font()  # Auto-size columns
        for col in self.tree_columns:
            max_width = font.measure(col)  # Start with header width
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                width = font.measure(text)
                if width > max_width:
                    max_width = width
            self.tree.column(col, width=max_width + 2)





if __name__ == "__main__":
    from connect_to_db import connect_db
    from stock_summary import FetchSummary
    columns = {
        "Product Code": "product_code",
        "Product Name": "product_name",
        "Quantity": "quantity",
        "Cost": "cost",
        "Wholesale Price": "wholesale_price",
        "Retail Price": "retail_price",
        "Min Level": "min_stock_level",
        "Date Restocked": "date_replenished"
    }
    conn=connect_db()
    summary = FetchSummary(conn)
    fetch = summary.fetch_unsold_products
    root=tk.Tk()
    SummaryPreviewWindow(conn, "Stock Preview Test", columns, fetch)
    root.withdraw()

    root.mainloop()
