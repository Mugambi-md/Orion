import re
import tkinter as tk
from tkinter import ttk, messagebox
from sales_gui import MakeSaleWindow
from working_on_stock import view_all_products
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from accounting_export import ReportExporter
from orders_gui import OrdersWindow
from log_popups_gui import SalesLogsWindow, MonthlyReversalLogs
from table_utils import TreeviewSorter
from sales_popup import (
    SalesControlReportWindow, MonthlySalesSummary, SalesReversalWindow,
    YearlySalesWindow, YearlyProductSales, CashierReturnTreasury,
    CashierEndDay
)

class SalesGUI(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Sale and Sales Report Window")
        self.center_window(self.master, 1350, 700, parent)
        self.master.configure(bg="lightblue")
        self.master.transient(parent)
        self.master.grab_set()

        self.conn = conn
        self.user = user
        self.all_products = view_all_products(conn)
        self.current_products = self.all_products
        style = ttk.Style(self.master)
        style.theme_use("clam")
        self.columns = [
            "No", "Product Code", "Product Name", "Description", "Quantity",
            "Cost", "Retail Price", "W.Sale Price", "Min Stock"
        ]
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        # Left Frame Nav Buttons
        self.left_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.center_frame = tk.Frame(self.main_frame, bg="lightblue")
        # Top Frame search and sort controls
        self.top_controls = tk.Frame(self.center_frame, bg="lightblue")
        self.search_mode = ttk.Combobox(
            self.top_controls, values=["Name", "Code"], width=5,
            state="readonly", font=("Arial", 11)
        )
        self.search_label = tk.Label(
            self.top_controls, text="Search Product Name:", bg="lightblue",
            font=("Arial", 12, "bold")
        )
        self.search_entry = tk.Entry(
            self.top_controls, width=15, font=("Arial", 11), bd=4,
            relief="raised"
        )
        self.sort_column = ttk.Combobox(
            self.top_controls, width=7, values=["Name", "Code", "Quantity"],
            state="readonly", font=("Arial", 11)
        )
        self.sort_order = ttk.Combobox(
            self.top_controls, values=["Ascending", "Descending"], width=11,
            state="readonly", font=("Arial", 11)
        )
        self.btn_frame = tk.Frame(self.top_controls, bg="lightblue")
        # Table Treeview
        self.table_frame = tk.Frame(self.center_frame, bg="lightblue")
        self.product_table = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.product_table, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()

        self.build_ui()
        self.populate_table()
        self.sort_table()
        self.sorter.autosize_columns(5)

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.left_frame.pack(pady=(5, 0), side="top", fill="x")
        buttons = {
            "Sell": self.open_sell_window,
            "Return Treasury": self.return_treasury_window,
            "Cashier EOD": self.cashier_eod,
            "Orders": self.orders,
            "Monthly Summary": self.monthly_summary,
            "Sales Records": self.sales_records,
            "Product Impact": self.sales_analysis,
            "Tag Reversal": self.monthly_report,
            "Reversal Posting": self.reversal_authorization,
            "Reversal Logs": self.reversal_logs,
            "Sales Logs": self.sales_logs
        }
        for text, command in buttons.items():
            tk.Button(
                self.left_frame, text=text, command=command, bd=4,
                fg="white", relief="groove", bg="blue",
                font=("Arial", 11, "bold")
            ).pack(side="left")
        self.center_frame.pack(fill="both", expand=True)
        self.top_controls.pack(fill="x")
        # Table Title
        tk.Label(
            self.center_frame, text="Available Products In Stock", bd=2,
            relief="flat", bg="lightblue", fg="blue",
            font=("Arial", 18, "bold", "underline")
        ).pack(anchor="center", ipadx=10, pady=(2, 0))
        tk.Label(
            self.top_controls, text="Search By:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0))
        self.search_mode.current(0)
        self.search_mode.pack(side="left", padx=(0, 3))
        self.search_mode.bind(
            "<<ComboboxSelected>>", self.update_search_label
        )
        self.search_label.pack(side="left", padx=(3, 0))
        self.search_entry.pack(side="left", padx=(0, 3))
        self.search_entry.bind("<KeyRelease>", self.filter_table)
        tk.Label(
            self.top_controls, text="Sort By:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(3, 0))
        self.sort_column.pack(side="left")
        self.sort_column.set("Name")
        self.sort_order.pack(side="left")
        self.sort_order.set("Ascending")
        self.sort_order.bind("<<ComboboxSelected>>", self.sort_table)
        self.sort_column.bind("<<ComboboxSelected>>", self.sort_table)
        self.btn_frame.pack(side="right", padx=5)
        btns = {
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel
        }
        for text, command in btns.items():
            tk.Button(
                self.btn_frame, text=text, command=command, fg="white", bd=2,
                relief="solid", bg="dodgerblue", font=("Arial", 9, "bold")
            ).pack(side="right")
        self.table_frame.pack(fill="both", expand=True)
        # Scrollbars
        vsb = ttk.Scrollbar(
            self.table_frame, orient="vertical",
            command=self.product_table.yview
        )
        for col in self.columns:  # Set up headings
            self.product_table.heading(col, text=col)
            self.product_table.column(col, anchor="center", width=20)
        self.product_table.configure(yscrollcommand=vsb.set)
        self.product_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        # Expand table frame
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        # Bind mousewheel scrolling
        self.product_table.bind(
            "<MouseWheel>", lambda e: self.product_table.yview_scroll(
                -1 * (e.delta//120), "units"
            )
        )

    def populate_table(self, products=None):
        """Fetch data and insert into Treeview."""
        self.product_table.delete(*self.product_table.get_children())
        if products is None:
            self.current_products =  self.all_products[:]
        else:
            self.current_products = products[:]
        # description formater
        def format_description(text, max_len=50, min_second=5):
            if not text:
                return ""
            text = re.sub(r"\s+", " ", text).strip() # Normalize spaces
            if len(text) <= max_len:
                return text
            # Split at nearest space before/after max_len
            break_at = text.rfind(" ", 0, max_len)
            if break_at == -1:
                break_at = text.find(" ", max_len)
            if break_at == -1:
                break_at = max_len # Fallback
            first_part = text[:break_at].rstrip()
            second_part = text[break_at:].lstrip()
            if len(second_part) > min_second:
                return first_part + "..."
            else:
                return text

        for idx, product in enumerate(self.current_products, start=1):
            # Clean product_code, name and description
            code = re.sub(
                r"\s+", " ", str(product["product_code"])
            ).strip()
            name = re.sub(
                r"\s+", " ", str(product["product_name"])
            ).strip()
            description = format_description(product["description"] or "")
            row = [
                idx,
                code,
                name,
                description,
                product["quantity"],
                f"{product['cost']:,.2f}",
                f"{product['wholesale_price']:,.2f}",
                f"{product['retail_price']:,.2f}",
                product["min_stock_level"]
            ]
            tag = ["evenrow", "oddrow", "thirdrow"][idx % 3]
            self.product_table.insert("", "end", values=row, tags=(tag,))
        self.product_table.tag_configure("evenrow", background='#add8e6')  # Light Blue
        self.product_table.tag_configure("oddrow", background='#ffffff')  # white
        self.product_table.tag_configure("thirdrow", background='#d3d3d3')  # Light grey
        self.sorter.autosize_columns()


    def update_search_label(self, event=None):
        if self.search_mode.get() == "Code":
            self.search_label.config(text="Search Product Code:")
        else:
            self.search_label.config(text="Search Product Name:")

    def filter_table(self, event=None):
        keyword = self.search_entry.get().lower()
        mode = self.search_mode.get()
        if not keyword:
            self.populate_table(self.all_products)
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
        self.populate_table(products)

    def sort_table(self, event=None):
        key = self.sort_column.get()
        reverse = self.sort_order.get() == "Descending"
        key_map = {
            "Code": "product_code",
            "Name": "product_name",
            "Quantity": "quantity"
        }
        sort_key = key_map.get(key, "product_name")
        try:
            products = sorted(
                self.current_products,
                key=lambda x: x[sort_key],
                reverse=reverse
            )
        except KeyError:
            products = self.current_products
        self.populate_table(products)

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

    def _collect_rows(self):
        rows = []
        for item in self.product_table.get_children():
            vals = self.product_table.item(item, "values")
            rows.append({
                "No": vals[0],
                "Product Code": vals[1],
                "Product Name": vals[2],
                "Description": vals[3],
                "Quantity": vals[4],
                "Cost": vals[5],
                "Retail Price": vals[6],
                "W.Sale Price": vals[7],
                "Min Stock": vals[8]
            })
        return rows

    def _make_exporter(self):
        title = "Available Products In Stock"
        columns = [
            "No", "Product Code", "Product Name", "Description", "Quantity",
            "Cost", "Retail Price", "W.Sale Price", "Min Stock"
        ]
        rows = self._collect_rows()
        return ReportExporter(self.master, title, columns, rows)

    def on_export_excel(self):
        if not self.has_privilege("Export Products Records"):
            return
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_export_pdf(self):
        if not self.has_privilege("Export Products Records"):
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self.has_privilege("Export Products Records"):
            return
        exporter = self._make_exporter()
        exporter.print()

    def open_sell_window(self):
        if not self.has_privilege("Make Sale"):
            return
        MakeSaleWindow(self.master, self.conn, self.user)

    def return_treasury_window(self):
        if not self.has_privilege("Manage Cashier"):
            return
        CashierReturnTreasury(self.master, self.conn, self.user)

    def cashier_eod(self):
        if not self.has_privilege("Manage Cashier"):
            return
        CashierEndDay(self.master, self.conn, self.user)

    def monthly_summary(self):
        if not self.has_privilege("Sales Report"):
            return
        MonthlySalesSummary(self.master, self.conn)

    def sales_records(self):
        if not self.has_privilege("View Sales Records"):
            return
        YearlySalesWindow(self.master, self.conn, self.user)

    def sales_analysis(self):
        if not self.has_privilege("Sales Report"):
            return
        YearlyProductSales(self.master, self.conn, self.user)

    def monthly_report(self):
        if not self.has_privilege("Sales Report"):
            return
        SalesControlReportWindow(self.master, self.conn, self.user)

    def reversal_authorization(self):
        if not self.has_privilege("Manage Sales"):
            return
        SalesReversalWindow(self.master, self.conn, self.user)

    def reversal_logs(self):
        if not self.has_privilege("View Sales Logs"):
            return
        MonthlyReversalLogs(self.master, self.conn, self.user)

    def sales_logs(self):
        if not self.has_privilege("View Sales Logs"):
            return
        SalesLogsWindow(self.master, self.conn, self.user)

    def orders(self):
        if not self.has_privilege("Work On Order"):
            return
        OrdersWindow(self.master, self.conn, self.user)

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root=tk.Tk()
    SalesGUI(root, conn, "Sniffy")
    root.mainloop()