import re
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import messagebox
from authentication import VerifyPrivilegePopup, DescriptionFormatter
from base_window import BaseWindow
from accounting_export import ReportExporter
from working_on_stock import fetch_all_products
from stock_windows import ProductsDetailsWindow
from log_popups_gui import ProductLogsWindow
from stock_reconciliation_gui import ReconciliationWindow
from stock_popups import (
    NewProductPopup, AddStockPopup, DeleteProductPopup
)


class StockWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("ORION STOCK")
        self.center_window(self.master, 1350, 700, parent)
        self.master.configure(bg="lightblue")
        self.master.transient(parent)
        self.master.grab_set()

        self.conn = conn
        self.user = user
        self.all_products = fetch_all_products(self.conn)
        self.current_products = self.all_products
        self.selected_product_code = None # Initialize
        # Ui set up
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.search_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="groove"
        )
        self.center_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree_frame = tk.Frame(self.center_frame, bg="lightblue")
        self.columns = [
            "No", "Code", "Name", "Description", "Quantity", "Cost",
            "Wholesale Price", "Retail Price", "Min Stock", "Restocked"
        ]
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 11))
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"))
        self.search_type = tk.StringVar(value="Name")
        self.search_var = tk.StringVar()
        self.search_option = ttk.Combobox(
            self.search_frame, textvariable=self.search_type, width=5,
            values=["Name", "Code"], state="readonly", font=("Arial", 11)
        )
        self.search_entry = tk.Entry(
            self.search_frame, textvariable=self.search_var, width=20, bd=4,
            relief="raised", font=("Arial", 11)
        )
        self.tree = ttk.Treeview(
            self.tree_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.update_table()

    def build_ui(self):
        """Build user interface."""
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.search_frame.pack(side="top", fill="x")
        action_frame = tk.Frame(self.search_frame, bg="lightblue")
        action_frame.pack(side="top", fill="x", padx=10)
        button_actions = {
            "New Product": self.open_new_product_popup,
            "Add Stock": self.open_add_stock_popup,
            "Delete Product": self.delete_product,
            "Stock Reconciliation": self.open_reconciliation,
            "Products Report": self.open_product_detail_window,
            "Stock Logs": self.open_logs_window
        }
        for text, action in button_actions.items():
            tk.Button(
                action_frame, text=text, bd=4, relief="groove", fg="white",
                bg="dodgerblue", command=action, font=("Arial", 10, "bold")
            ).pack(side="left")
        # Center frame for table and tittle
        self.center_frame.pack(side="left", fill="both", expand=True)
        # Top Right frame for actions
        tk.Label(
            self.search_frame, bg="lightblue", text="Search By:",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0))
        self.search_option.pack(side="left", padx=(0, 5))
        tk.Label(
            self.search_frame, bg="lightblue", text="Search Item:",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0))
        self.search_entry.pack(side="left", padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", lambda e: self.perform_search())
        tk.Label(
            self.search_frame, text="Stock Items Details", bd=4, relief="flat",
            bg="lightblue", font=("Arial", 16, "bold", "underline")
        ).pack(side="left", padx=30)
        btn_frame = tk.Frame(
            self.search_frame, bg="lightblue", bd=2, relief="raised"
        )
        btn_frame.pack(side="right", padx=10)
        buttons = {
            "Refresh": self.refresh,
            "Print Report": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel
        }
        for text, command in buttons.items():
            tk.Button(
                btn_frame, text=text, bd=4, relief="raised", bg="dodgerblue",
                fg="white", command=command
            ).pack(side="left")

        self.tree_frame.pack(fill="both", expand=True)
        tree_scroll = ttk.Scrollbar(
            self.tree_frame, orient="vertical", command=self.tree.yview
        )
        # Set Headings
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))
        self.tree.bind(
            "<Button-4>", lambda e: self.tree.yview_scroll(-1, "units")
        )
        self.tree.bind(
            "<Button-5>", lambda e: self.tree.yview_scroll(1, "units")
        )
        # Define alternating row styles
        self.tree.tag_configure("row1", background="#d1ecf1")  # Cyan tint
        self.tree.tag_configure("row2", background="#f8d7da")  # Pink/red tint
        self.tree.tag_configure("row3", background="#fff3cd")  # Yellow tint

    def update_table(self, products=None):
        self.tree.delete(*self.tree.get_children())
        if products is None:
            self.current_products = self.all_products[:]
        else:
            self.current_products = products[:]
        formatter = DescriptionFormatter(40, 10)
        for i, row in enumerate(self.current_products, start=1):
            name = re.sub(r"\s+", " ", str(row["product_name"])).strip()
            desc = formatter.format(row["description"])
            tag = f"row{(i % 3) + 1}"
            self.tree.insert("", "end", values=(
                i,
                row["product_code"],
                name,
                desc,
                row["quantity"],
                f"{row["cost"]:,}",
                f"{row["wholesale_price"]:,}",
                f"{row["retail_price"]:,}",
                row["min_stock_level"],
                row["date_replenished"].strftime("%d/%m/%Y")
            ), tags=(tag,))

        self.autosize_columns()

    def autosize_columns(self):
        """Auto-resize columns based on the content."""
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                width = font.measure(text)
                if width > max_width:
                    max_width = width
            self.tree.column(col, width=max_width + 10)

    def perform_search(self):
        keyword = self.search_var.get().strip()
        mode = self.search_type.get()
        if not keyword:
            self.update_table(self.all_products)
            return
        if mode == "Code":
            products = [
                p for p in self.all_products if str(
                    p["product_code"]
                ).lower().startswith(keyword)
            ]
        else: # Name
            products = [
                p for p in self.all_products if str(
                    p["product_name"]
                ).lower().startswith(keyword)
            ]
        self.update_table(products)

    def refresh(self):
        products = fetch_all_products(self.conn)
        self.update_table(products)

    def has_privilege(self, privilege: str) -> bool:
        """Check if the current user has the required privilege."""
        dialog = VerifyPrivilegePopup(
            self.master, self.conn, self.user, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You do not have permission to {privilege}.",
                parent=self.master
            )
            return False
        return True

    def open_new_product_popup(self):
        if not self.has_privilege("Admin New Product"):
            return
        NewProductPopup(self.master, self.conn, self.user)

    def open_reconciliation(self):
        if not self.has_privilege("Manage Stock"):
            return
        ReconciliationWindow(self.master, self.conn, self.user)

    def open_product_detail_window(self):
        if not self.has_privilege("View Products"):
            return
        ProductsDetailsWindow(self.master, self.user, self.conn)

    def open_add_stock_popup(self):
        if not self.has_privilege("Add Stock"):
            return
        AddStockPopup(self.master, self.conn, self.user, self.refresh)

    def delete_product(self):
        if not self.has_privilege("Admin Delete Product"):
            return
        DeleteProductPopup(self.master, self.conn, self.user, self.refresh)

    def open_logs_window(self):
        if not self.has_privilege("View Product Logs"):
            return
        ProductLogsWindow(self.master, self.conn, self.user)

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0],
                "Code": vals[1],
                "Name": vals[2],
                "Description": vals[3],
                "Quantity": vals[4],
                "Cost": vals[5],
                "Wholesale Price": vals[6],
                "Retail Price": vals[7],
                "Min Stock": vals[8],
                "Restocked": vals[9]
            })
        return rows

    def _make_exporter(self):
        title = "Stock Items Report."
        columns = [
            "No", "Code", "Name", "Description", "Quantity", "Cost",
            "Wholesale Price", "Retail Price", "Min Stock", "Restocked"
        ]
        rows = self._collect_current_rows()
        return ReportExporter(self.master, title, columns, rows)

    def on_export_pdf(self):
        if not self.has_privilege("View Products"):
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_export_excel(self):
        if not self.has_privilege("View Products"):
            return
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_print(self):
        if not self.has_privilege("View Products"):
            return
        exporter = self._make_exporter()
        exporter.print()


if __name__ == "__main__":
    from connect_to_db import connect_db
    conn = connect_db()
    root = tk.Tk()
    StockWindow(root, conn, "sniffy")
    root.mainloop()