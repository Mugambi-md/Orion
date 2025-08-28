import tkinter as tk
import tkinter.font as tkFont 
from tkinter import ttk, messagebox
from base_window import BaseWindow
from working_on_stock2 import view_all_products
from accounting_export import ReportExporter
from authentication import VerifyPrivilegePopup

class ProductsDetailsWindow(BaseWindow):
    def __init__(self, parent, user, conn):
        self.window = tk.Toplevel(parent)
        self.window.title("Products Information")
        self.center_window(self.window, 1350, 700, parent)
        self.window.configure(bg="green")
        self.window.grab_set()
        self.window.transient(parent)

        self.user = user
        self.conn = conn
        self.right_frame = tk.Frame(self.window, padx=3, bg="green")
        self.tree_frame = tk.Frame(self.right_frame, bg="green")
        self.title = "Available Products Information"
        self.columns = [
            "No", "Code", "Name", "Description", "Quantity", "Cost",
            "Wholesale Price", "Retail Price", "Min Stock"
        ]
        self.tree = ttk.Treeview(self.tree_frame, columns=self.columns, show="headings")
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical")


        self.create_widgets()
        self.populate_table()

    def create_widgets(self):
        left_frame = tk.Frame(self.window, bg="green") # Left frame with buttons
        left_frame.pack(side="top", fill="x", padx=5)
        # Buttons on top
        tk.Button(left_frame, text="Product Statistics", width=20,
                  command=self.products_statistics).pack(padx=5, side="left")
        tk.Button(left_frame, text="Export Excel", width=15,
                  command=self.on_export_excel).pack(padx=5, side="left")
        tk.Button(left_frame, text="Export PDF", width=15,
                  command=self.on_export_pdf).pack(padx=5, side="left")
        tk.Button(left_frame, text="Print", width=15,
                  command=self.on_print).pack(padx=5, side="left")
        tk.Button(left_frame, text="Other Action", width=20,
                  command=self.another_action).pack(padx=5, side="left")
        # Right frame with table
        self.right_frame.pack(side="left", fill="both", expand=True)
        # Table Title
        tk.Label(self.right_frame, text=self.title, bg="green", fg="white",
                 font=("Arial", 14, "bold"), anchor="center"
                 ).pack(pady=(5, 0))
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.configure("Treeview", rowheight=30)
        self.tree_frame.pack(pady=(0, 10), fill="both", expand=True)
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.tree.yview)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        # Set Headings
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.bind(
            "<MouseWheel>", lambda e:
            self.tree.yview_scroll(int(-1 * (e.delta / 120)), "units")
        )
        self.tree.bind("<Button-4>",
                       lambda e: self.tree.yview_scroll(-1, "units"))
        self.tree.bind("<Button-5>",
                       lambda e: self.tree.yview_scroll(1, "units"))

    def populate_table(self):
        products = view_all_products()
        total_qty = 0
        total_cost = 0.0
        total_wholesale = 0.0
        total_retail = 0.0
        for i, product in enumerate(products, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            values = [
                i,
                product["product_code"],
                product["product_name"],
                product["description"],
                product["quantity"],
                f"{product['cost']:,.2f}",
                f"{product['wholesale_price']:,.2f}",
                f"{product['retail_price']:,.2f}",
                product["min_stock_level"]
            ]
            self.tree.insert("", "end", values=values, tags=(tag,))
            # Accumulate totals
            total_qty += product["quantity"]
            total_cost += product["cost"]
            total_wholesale += product["wholesale_price"]
            total_retail += product["retail_price"]
        # Insert totals row
        total_values = [
            "",
            "",
            "",
            "TOTAL",
            f"{total_qty:,}",
            f"{total_cost:,.2f}",
            f"{total_wholesale:,.2f}",
            f"{total_retail:,.2f}",
            ""
        ]
        self.tree.insert("", "end", values=total_values, tags=("totalrow",))
        self.tree.tag_configure("totalrow", font=("Arial", 11, "bold", "underline"))
        grand_total_cost = total_cost * total_qty
        grand_total_wholesale = total_wholesale * total_qty
        grand_total_retail = total_retail * total_qty
        self.tree.insert("", "end", values=(
            "",
            "",
            "",
            "GRAND TOTAL",
            "",
            f"{grand_total_cost:,.2f}",
            f"{grand_total_wholesale:,.2f}",
            f"{grand_total_retail:,.2f}",
            ""
        ), tags=("grandtotalrow",))
        self.tree.tag_configure("grandtotalrow", background="#c5cae9",
                                font=("Arial", 12, "bold", "underline"))
        self.resize_columns()

    def resize_columns(self):
        """Auto-resize columns based on the content."""
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                width = font.measure(text)
                if width > max_width:
                    max_width = width
            self.tree.column(col, width=max_width + 3)


    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0] or "",
                "Code": vals[1] or "",
                "Name": vals[2] or "",
                "Description": vals[3] or "",
                "Quantity": vals[4] or "",
                "Cost": vals[5] or "",
                "Wholesale Price": vals[6] or "",
                "Retail Price": vals[7] or "",
                "Min Stock Level": vals[8] or ""
            })
        return rows
    def _make_exporter(self):
        title = "Available Product Information"
        columns = ["No", "Code", "Name", "Description", "Quantity", "Cost",
               "Wholesale Price", "Retail Price", "Min Stock Level"]
        rows = self._collect_rows()
        return ReportExporter(self.window, title, columns, rows)
    def on_export_excel(self):
        exporter = self._make_exporter()
        exporter.export_excel()
    def on_export_pdf(self):
        exporter = self._make_exporter()
        exporter.export_pdf()
    def on_print(self):
        exporter = self._make_exporter()
        exporter.print()

    def products_statistics(self):
        # Verify user privilege
        priv = "Stock Statistics"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
    def another_action(self):
        pass

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root = tk.Tk()
    # root.withdraw()
    app=ProductsDetailsWindow(root, "sniffy", conn)
    root.mainloop()
