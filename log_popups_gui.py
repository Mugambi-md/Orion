import re
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import messagebox
from datetime import date
from authentication import VerifyPrivilegePopup, DescriptionFormatter
from base_window import BaseWindow
from accounting_export import ReportExporter
from working_on_accounting import (
    fetch_finance_log_filter_data, fetch_finance_logs,
)
from working_on_orders import (
    fetch_all_orders_logs, fetch_distinct_years_users
)
from working_sales import (
    fetch_sales_control_log_filter_data, fetch_distinct_years,
    fetch_sales_logs, fetch_reversals_by_month
)
from working_on_stock import fetch_product_control_logs, fetch_distinct_years


class FinanceLogsWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.top = tk.Toplevel(parent)
        self.top.title("Finance Logs")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 1100, 700, parent)
        self.top.transient(parent)
        self.top.grab_set()

        self.conn = conn
        self.user = user
        success, data = fetch_finance_log_filter_data(conn)
        if not success:
            messagebox.showerror("Error", data, parent=self.top)
        self.years = data["years"]
        self.users = data["usernames"]
        self.selected_year = tk.StringVar()
        self.filter_user_var = tk.BooleanVar(value=False)
        self.filter_month_var = tk.BooleanVar(value=False)
        self.selected_user = tk.StringVar()
        self.selected_month = tk.StringVar()
        self.title = None
        self.months = [
            ("January", 1), ("February", 2), ("March", 3), ("April", 4),
            ("May", 5), ("June", 6), ("July", 7), ("August", 8),
            ("September", 9), ("October", 10), ("November", 11),
            ("December", 12),
        ]
        self.columns = [
            "No.", "Date", "Time", "User", "Document No.", "Action"
        ]
        style = ttk.Style(self.top)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", rowheight=40, font=("Arial", 10))
        self.main_frame = tk.Frame(self.top, bg="lightblue", bd=4, relief="solid")
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.filter_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_year, width=5,
            state="readonly", values=self.years, font=("Arial", 11)
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_user, width=7,
            state="disabled", values=self.users, font=("Arial", 11)
        )
        self.month_cb = ttk.Combobox(
            self.filter_frame, values=[name for name, _num in self.months],
            width=10, state="disabled", font=("Arial", 11)
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.title_label = tk.Label(
            self.top_frame, text="", bg="lightblue", bd=4, relief="ridge",
            font=("Arial", 16, "bold", "underline"), fg="dodgerblue"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.refresh_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.top_frame.pack(fill="x", pady=(5, 0))
        # Title
        self.title_label.pack(anchor="center", ipady=5, ipadx=10)
        # Filter Frame
        self.filter_frame.pack(fill="x")
        tk.Label(
            self.filter_frame, text="Select Year:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.year_cb.pack(side="left", padx=(0, 5))
        if self.years:
            self.year_cb.set(self.years[0])
        else:
            messagebox.showinfo(
                "Info", "No Order Logs Found.", parent=self.top
            )
        self.year_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.refresh_table()
        )
        filter_outer = tk.Frame(
            self.filter_frame, bg="lightblue", bd=2, relief="groove"
        )
        filter_outer.pack(side="left", padx=2, ipady=2, ipadx=2)
        tk.Label(
            filter_outer, text="Filter By:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(5, 0))
        tk.Checkbutton(
            filter_outer, variable=self.filter_user_var, bg="lightblue",
            text="User", command=self.toggle_filters,
            font=("Arial", 10, "bold")
        ).pack(side="left")
        tk.Checkbutton(
            filter_outer, variable=self.filter_month_var, bg="lightblue",
            text="Month", command=self.toggle_filters,
            font=("Arial", 10, "bold")
        ).pack(side="left")
        # User Filter
        tk.Label(
            self.filter_frame, text="Select User:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.user_cb.pack(side="left", padx=(0, 5))
        # Month Filter
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 5))
        tk.Button(
            self.filter_frame, text="Refresh", bd=2, relief="groove",
            command=self.refresh_table, bg="dodgerblue", fg="white"
        ).pack(side="left")
        btn_frame = tk.Frame(self.filter_frame, bg="lightblue")
        btn_frame.pack(side="right")
        action_btn = {
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
            "Print Logs": self.on_print
        }
        for text, command in action_btn.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="groove",
                bg="dodgerblue", fg="white",
            ).pack(side="left")
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.table_frame.pack(fill="both", expand=True)
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def toggle_filters(self):
        if self.filter_user_var.get():
            self.user_cb["state"] = "readonly"
        else:
            self.user_cb.set("")
            self.user_cb["state"] = "disabled"
        if self.filter_month_var.get():
            self.month_cb["state"] = "readonly"
        else:
            self.month_cb.set("")
            self.month_cb["state"] = "disabled"
        self.refresh_table()

    def refresh_table(self):
        year_str = self.selected_year.get()
        if not year_str:
            return
        year = int(year_str)
        month = None
        user = None
        title = "Finance Logs"
        if self.filter_user_var.get() and self.user_cb.get():
            user = self.user_cb.get()
            title += f" For {user.capitalize()}"
        if self.filter_month_var.get() and self.month_cb.get():
            month = dict(self.months).get(self.month_cb.get())
            title += f" In {self.month_cb.get()}"
        title += f" {year}."
        self.title_label.configure(text=title)
        self.title = title

        success, result = fetch_finance_logs(self.conn, year, month, user)
        if not success:
            messagebox.showerror("Error", result, parent=self.top)
            return
        # Clear current rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        formatter = DescriptionFormatter(50, 10)
        for i, row in enumerate(result, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            action = formatter.format(row["action"])
            self.tree.insert("", "end", values=(
                i,
                row["log_date"].strftime("%d/%m/%Y"),
                row["log_time"],
                row["username"],
                row["receipt_no"],
                action
            ), tags=(tag,))
        self.auto_resize()

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No.": vals[0],
                "Date": vals[1],
                "Time": vals[2],
                "User": vals[3],
                "Document No.": vals[4],
                "Action": vals[5]
            })
        return rows

    def _make_exporter(self):
        title = self.title
        columns = ["No.", "Date", "Time", "User", "Document No.", "Action"]
        rows = self._collect_current_rows()
        return ReportExporter(self.top, title, columns, rows)

    def _check_privilege(self):
        priv = "View Finance Logs"
        verify = VerifyPrivilegePopup(self.top, self.conn, self.user, priv)
        return getattr(verify, "result", None) == "granted"

    def on_export_pdf(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Export PDF.", parent=self.top
            )
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied", "You Don't Permission to Print Logs.",
                parent=self.top
            )
            return
        exporter = self._make_exporter()
        exporter.print()

    def on_export_excel(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied", "You Don't Permission to Export Logs.",
                parent=self.top
            )
            return
        exporter = self._make_exporter()
        exporter.export_excel()

    def auto_resize(self):
        """Resize columns to fit content."""
        font = tkFont.Font()
        for col in self.columns:
            # Start with the column header width
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            # Add Padding for readability
            self.tree.column(col, width=max_width)


class OrderLogsWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.top = tk.Toplevel(parent)
        self.top.title("Order Logs")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 1100, 700, parent)
        self.top.transient(parent)
        self.top.grab_set()

        self.conn = conn
        self.user = user
        data, msg = fetch_distinct_years_users(conn)
        if msg:
            messagebox.showerror("Error", msg, parent=self.top)
        self.years = data["years"]
        self.users = data["users"]
        self.selected_year = tk.StringVar()
        self.filter_user_var = tk.BooleanVar(value=False)
        self.filter_month_var = tk.BooleanVar(value=False)
        self.selected_user = tk.StringVar()
        self.selected_month = tk.StringVar()
        self.title = None
        self.months = [
            ("January", 1), ("February", 2), ("March", 3), ("April", 4),
            ("May", 5), ("June", 6), ("July", 7), ("August", 8),
            ("September", 9), ("October", 10), ("November", 11),
            ("December", 12),
        ]
        self.columns = [
            "No", "Order ID", "Date", "User", "Operation", "Amount"
        ]
        style = ttk.Style(self.top)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", roeheight=20, font=("Arial", 10))
        self.main_frame = tk.Frame(
            self.top, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.filter_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_year, width=5,
            state="readonly", values=self.years, font=("Arial", 11)
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_user, width=8,
            state="disabled", values=self.users, font=("Arial", 11)
        )
        self.month_cb = ttk.Combobox(
            self.filter_frame, values=[name for name, _num in self.months],
            width=10, state="disabled", font=("Arial", 11)
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.title_label = tk.Label(
            self.top_frame, text="", bg="lightblue", bd=4, relief="ridge",
            font=("Arial", 16, "bold", "underline"), fg="dodgerblue"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.refresh_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.top_frame.pack(fill="x", pady=(5, 0))
        # Title
        self.title_label.pack(anchor="center", ipadx=10, ipady=5)
        # Year Selector
        tk.Label(
            self.filter_frame, text="Select Year:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.year_cb.pack(side="left", padx=(0, 5))
        if self.years:
            self.year_cb.set(self.years[0])
        else:
            messagebox.showinfo(
                "Info", "No Order Logs Found.", parent=self.top
            )
        self.year_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.refresh_table()
        )
        # Filter Frame
        filter_outer = tk.Frame(self.filter_frame, bg="lightblue", bd=2,
                                relief="groove")
        filter_outer.pack(side="left", padx=10)
        tk.Label(
            filter_outer, text="Filter By:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0))
        tk.Checkbutton(
            filter_outer, variable=self.filter_user_var, bg="lightblue",
            text="User", command=self.toggle_filters,
            font=("Arial", 11, "bold")
        ).pack(side="left")
        tk.Checkbutton(
            filter_outer, variable=self.filter_month_var, bg="lightblue",
            text="Month", command=self.toggle_filters,
            font=("Arial", 11, "bold")
        ).pack(side="left")
        # Filter Frame
        self.filter_frame.pack(fill="x", padx=5)
        # User Filter
        tk.Label(
            self.filter_frame, text="Select User:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.user_cb.pack(side="left", padx=(0, 5))
        # Month Filter
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 5))
        tk.Button(
            self.filter_frame, text="Refresh", bd=4, relief="raised",
            command=self.refresh_table, bg="dodgerblue", fg="white"
        ).pack(side="left")
        btn_frame = tk.Frame(self.filter_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=10)
        action_btn = {
            "Export PDF": self.on_export_pdf,
            "Print Logs": self.on_print
        }
        for text, command in action_btn.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="raised",
                bg="dodgerblue", fg="white",
            ).pack(side="left")
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.table_frame.pack(fill="both", expand=True)
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def toggle_filters(self):
        if self.filter_user_var.get():
            self.user_cb["state"] = "readonly"
        else:
            self.user_cb.set("")
            self.user_cb["state"] = "disabled"
        if self.filter_month_var.get():
            self.month_cb["state"] = "readonly"
        else:
            self.month_cb.set("")
            self.month_cb["state"] = "disabled"
        self.refresh_table()

    def refresh_table(self):
        year_str = self.selected_year.get()
        if not year_str:
            return
        year = int(year_str)
        month = None
        user = None
        title = "Order Logs"
        if self.filter_user_var.get() and self.user_cb.get():
            user = self.user_cb.get()
            title += f" For {user.capitalize()}"
        if self.filter_month_var.get() and self.month_cb.get():
            month = dict(self.months).get(self.month_cb.get())
            title += f" In {self.month_cb.get()}"
        title += f" {year}."
        self.title_label.configure(text=title)
        self.title = title

        result = fetch_all_orders_logs(self.conn, year, month, user)
        if isinstance(result, str):
            messagebox.showerror("Error", result, parent=self.top)
            return
        # Clear current rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, row in enumerate(result, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                row["order_id"],
                row["log_date"].strftime("%d/%m/%Y"),
                row["user"],
                row["action"],
                f"{row['total_amount']:,.2f}"
            ), tags=(tag,))
        self.auto_resize()

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0],
                "Order ID": vals[1],
                "Date": vals[2],
                "User": vals[3],
                "Operation": vals[4],
                "Amount": vals[5]
            })
        return rows

    def _make_exporter(self):
        title = self.title
        columns = ["No", "Order ID", "Date", "User", "Operation", "Amount"]
        rows = self._collect_current_rows()
        return ReportExporter(self.top, title, columns, rows)

    def _check_privilege(self):
        priv = "View Order Logs"
        verify = VerifyPrivilegePopup(self.top, self.conn, self.user, priv)
        return getattr(verify, "result", None) == "granted"

    def on_export_pdf(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Export PDF.", parent=self.top
            )
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied", "You Don't Permission to Print Logs.")
            return
        exporter = self._make_exporter()
        exporter.print()

    def auto_resize(self):
        """Resize columns to fit content."""
        font = tkFont.Font()
        for col in self.columns:
            # Start with the column header width
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            # Add Padding for readability
            self.tree.column(col, width=max_width)

class MonthlyReversalLogs(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Reversal Logs")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 1300, 700, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        years, err = fetch_distinct_years(self.conn)
        if err:
            self.years = date.today().year
        else:
            self.years = years
        self.months = [
            ("", None), ("January", 1), ("February", 2), ("March", 3),
            ("April", 4), ("May", 5), ("June", 6), ("July", 7),
            ("August", 8), ("September", 9), ("October", 10),
            ("November", 11), ("December", 12),
        ]
        self.columns = [
            "No", "Date", "Receipt", "Product Code", "Product Name", "Price",
            "Quantity", "Refund", "Tagged By", "Authorized By", "Posted",
        ]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", rowheight=20, font=("Arial", 10))
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        # Top Frame
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.top_frame, values=self.years, state="readonly", width=5,
            font=("Arial", 11)
        )
        self.year_cb.current(0)
        self.month_cb = ttk.Combobox(
            self.top_frame, values=[name for name, _num in self.months],
            width=10, state="readonly", font=("Arial", 11)
        )
        # Table Frame
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.title = tk.Label(
            self.top_frame, text="Reversals For", bg="lightblue", bd=4,
            font=("Arial", 14, "bold", "underline"), relief="raised"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings", height=20
        )


        self.build_ui()
        self.load_data()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.top_frame.pack(fill="x", padx=5)
        self.table_frame.pack(fill="both", expand=True)
        self.title.pack(side="left", padx=20, ipadx=10, ipady=2)
        tk.Label(
            self.top_frame, text="Select Year:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(10, 5))
        self.year_cb.pack(side="left", padx=(0, 10))
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.top_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(10, 5))
        self.month_cb.pack(side="left", padx=(0, 10))
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Button(
            self.top_frame, text="Export PDF", bg="dodgerblue", fg="red",
            bd=4, relief="groove", command=self.export
        ).pack(side="right", padx=5)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        vsb = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def load_data(self):
        """Load Reversals for selected year and month."""
        # Clear old data
        for item in self.tree.get_children():
            self.tree.delete(item)
        year = int(self.year_cb.get())
        month = None
        title = f"Reversals In"
        if self.month_cb.get():
            month = dict(self.months).get(self.month_cb.get())
            month_name = self.month_cb.get()
            title += f" {month_name}"
        if not year:
            return
        title += f" {year}."
        # Insert into table
        success, rows = fetch_reversals_by_month(self.conn, year, month)
        if not success:
            messagebox.showerror(
                "Error", f"Error Fetching Data: {rows}", parent=self.window
            )
            return

        for i, row in enumerate(rows, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            name = re.sub(r"\s+", " ", str(row["product_name"])).strip()
            self.tree.insert("", "end", values=(
                i,
                row["date"].strftime("%d/%m/%Y"),
                row["receipt_no"],
                row["product_code"],
                name,
                f"{row["unit_price"]:,.2f}",
                row["quantity"],
                f"{row["refund"]:,.2f}",
                row["tag"] if row["tag"] is not None else "",
                row["authorized"] if row["authorized"] is not None else "",
                row["posted"] if row["posted"] is not None else "",
            ), tags=(tag,))
        self.auto_resize()
        self.title.configure(text=title)

    def auto_resize(self):
        """Resize columns to fit content."""
        font = tkFont.Font()
        for col in self.columns:
            # Start with the column header width
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            # Add Padding for readability
            self.tree.column(col, width=max_width)

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append(
                {
                    "No": vals[0],
                    "Date": vals[1],
                    "Receipt": vals[2],
                    "Product Code": vals[3],
                    "Product Name": vals[4],
                    "Price": vals[5],
                    "Quantity": vals[6],
                    "Refund": vals[7],
                    "Tagged By": vals[8],
                    "Authorized By": vals[9],
                    "Posted": vals[10],
                }
            )
        return rows

    def _make_exporter(self):
        title = f"Reversals For {self.month_cb.get()} {self.year_cb.get()}."
        columns = [
            "No", "Date", "Receipt", "Product Code", "Product Name", "Price",
            "Quantity", "Refund", "Tagged By", "Authorized By", "Posted",
        ]
        rows = self._collect_rows()
        return ReportExporter(self.window, title, columns, rows)
    def export(self):
        """Export data to PDF."""
        exporter = self._make_exporter()
        exporter.export_pdf()

class SalesLogsWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.top = tk.Toplevel(parent)
        self.top.title("Sales Logs")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 1100, 700, parent)
        self.top.transient(parent)
        self.top.grab_set()

        self.conn = conn
        self.user = user
        success, data = fetch_sales_control_log_filter_data(conn)
        if not success:
            messagebox.showerror("Error", data, parent=self.top)
        self.years = data["years"]
        self.users = data["usernames"]
        self.selected_year = tk.StringVar()
        self.filter_user_var = tk.BooleanVar(value=False)
        self.filter_month_var = tk.BooleanVar(value=False)
        self.selected_user = tk.StringVar()
        self.selected_month = tk.StringVar()
        self.title = None
        self.months = [
            ("January", 1), ("February", 2), ("March", 3), ("April", 4),
            ("May", 5), ("June", 6), ("July", 7), ("August", 8),
            ("September", 9), ("October", 10), ("November", 11),
            ("December", 12),
        ]
        self.columns = [
            "No.", "Date", "Time", "Product Code", "Receipt No.", "Action",
            "User"
        ]
        style = ttk.Style(self.top)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", roeheight=20, font=("Arial", 11))
        self.main_frame = tk.Frame(
            self.top, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.filter_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_year, width=5,
            state="readonly", values=self.years, font=("Arial", 11)
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_user, width=8,
            state="disabled", values=self.users, font=("Arial", 11)
        )
        self.month_cb = ttk.Combobox(
            self.filter_frame, values=[name for name, _num in self.months],
            width=10, state="disabled", font=("Arial", 11)
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.title_label = tk.Label(
            self.top_frame, text="", bg="lightblue", bd=4, relief="ridge",
            font=("Arial", 16, "bold", "underline"), fg="dodgerblue"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.refresh_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.top_frame.pack(fill="x", pady=(5, 0))
        # Title
        self.title_label.pack(anchor="center", ipadx=10)
        # Year Selector
        tk.Label(
            self.filter_frame, text="Select Year:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.year_cb.pack(side="left", padx=(0, 5))
        if self.years:
            self.year_cb.set(self.years[0])
        else:
            messagebox.showinfo(
                "Info", "No Order Logs Found.", parent=self.top
            )
        self.year_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.refresh_table()
        )
        # Filter Frame
        filter_outer = tk.Frame(self.filter_frame, bg="lightblue", bd=2,
                                relief="groove")
        filter_outer.pack(side="left", padx=5)
        tk.Label(
            filter_outer, text="Filter By:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0))
        tk.Checkbutton(
            filter_outer, variable=self.filter_user_var, bg="lightblue",
            text="User", command=self.toggle_filters,
            font=("Arial", 11, "bold")
        ).pack(side="left")
        tk.Checkbutton(
            filter_outer, variable=self.filter_month_var, bg="lightblue",
            text="Month", command=self.toggle_filters,
            font=("Arial", 11, "bold")
        ).pack(side="left")
        # Filter Frame
        self.filter_frame.pack(fill="x", padx=5)
        # User Filter
        tk.Label(
            self.filter_frame, text="Select User:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.user_cb.pack(side="left", padx=(0, 5))
        # Month Filter
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 5))
        tk.Button(
            self.filter_frame, text="Refresh", bd=2, relief="groove",
            command=self.refresh_table, bg="dodgerblue", fg="white"
        ).pack(side="left")
        btn_frame = tk.Frame(self.filter_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=10)
        action_btn = {
            "Export PDF": self.on_export_pdf,
            "Print Logs": self.on_print
        }
        for text, command in action_btn.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="groove",
                bg="dodgerblue", fg="white",
            ).pack(side="left")
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.table_frame.pack(fill="both", expand=True)
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def toggle_filters(self):
        if self.filter_user_var.get():
            self.user_cb["state"] = "readonly"
        else:
            self.user_cb.set("")
            self.user_cb["state"] = "disabled"
        if self.filter_month_var.get():
            self.month_cb["state"] = "readonly"
        else:
            self.month_cb.set("")
            self.month_cb["state"] = "disabled"
        self.refresh_table()

    def refresh_table(self):
        year_str = self.selected_year.get()
        if not year_str:
            return
        year = int(year_str)
        month = None
        user = None
        title = "Sales Logs"
        if self.filter_user_var.get() and self.user_cb.get():
            user = self.user_cb.get()
            title += f" For {user.capitalize()}"
        if self.filter_month_var.get() and self.month_cb.get():
            month = dict(self.months).get(self.month_cb.get())
            title += f" In {self.month_cb.get()}"
        title += f" {year}."
        self.title_label.configure(text=title)
        self.title = title
        success, data = fetch_sales_logs(self.conn, year, month, user)
        if not success:
            messagebox.showerror("Error", data, parent=self.top)
            return

        # Clear current rows
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, row in enumerate(data, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                row["date"].strftime("%d/%m/%Y"),
                row["time"],
                row["product_code"],
                row["receipt_no"],
                row["description"],
                row["user"]
            ), tags=(tag,))
        self.auto_resize()

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No.": vals[0],
                "Date": vals[1],
                "Time": vals[2],
                "Product Code": vals[3],
                "Receipt No.": vals[4],
                "Action": vals[5],
                "User": vals[6]
            })
        return rows

    def _make_exporter(self):
        title = self.title
        columns = [
            "No.", "Date", "Time", "Product Code", "Receipt No.", "Action",
            "User"
        ]
        rows = self._collect_current_rows()
        return ReportExporter(self.top, title, columns, rows)

    def _check_privilege(self):
        priv = "View Order Logs"
        verify = VerifyPrivilegePopup(self.top, self.conn, self.user, priv)
        return getattr(verify, "result", None) == "granted"

    def on_export_pdf(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Export PDF.", parent=self.top
            )
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied", "You Don't Permission to Print Logs.",
                parent=self.top
            )
            return
        exporter = self._make_exporter()
        exporter.print()

    def auto_resize(self):
        """Resize columns to fit content."""
        font = tkFont.Font()
        for col in self.columns:
            # Start with the column header width
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            # Add Padding for readability
            self.tree.column(col, width=max_width)


class ProductLogsWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.top = tk.Toplevel(parent)
        self.top.title("Stock Products Logs")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 1200, 700, parent)
        self.top.transient(parent)
        self.top.grab_set()

        self.conn = conn
        self.user = user
        years, error = fetch_distinct_years(conn)
        if error:
            messagebox.showerror("Database Error", error, parent=self.top)
        self.years = years
        self.selected_year = tk.StringVar()
        self.filter_month_var = tk.BooleanVar(value=False)
        self.selected_month = tk.StringVar()
        self.title = None
        self.months = [
            ("", None), ("January", 1), ("February", 2), ("March", 3),
            ("April", 4), ("May", 5), ("June", 6), ("July", 7), ("August", 8),
            ("September", 9), ("October", 10), ("November", 11),
            ("December", 12),
        ]
        self.columns = [
            "No", "User", "Date", "Item Code", "Product Name", "Operation",
            "Quantity", "Amount"
        ]
        style = ttk.Style(self.top)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 10))
        self.main_frame = tk.Frame(self.top, bg="lightblue", bd=4, relief="solid")
        self.top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.filter_frame = tk.Frame(self.top_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_year, width=5,
            state="readonly", values=self.years, font=("Arial", 11)
        )
        self.month_cb = ttk.Combobox(
            self.filter_frame, values=[name for name, _num in self.months],
            width=10, state="readonly", font=("Arial", 11),
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.title_label = tk.Label(
            self.top_frame, text="", bg="lightblue", bd=4, relief="flat",
            font=("Arial", 16, "bold", "underline"), fg="dodgerblue"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.refresh_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.top_frame.pack(fill="x")
        # Title
        self.title_label.pack(anchor="center", fill="x")
        # Filter Frame
        self.filter_frame.pack(fill="x", padx=5)
        # Year Selector
        tk.Label(
            self.filter_frame, text="Select Year:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.year_cb.pack(side="left", padx=(0, 10))
        if self.years:
            self.year_cb.set(self.years[0])
        else:
            messagebox.showinfo(
                "Info", "No Order Logs Found.", parent=self.top
            )
        self.year_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.refresh_table()
        )

        # Month Filter
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 5))
        tk.Button(
            self.filter_frame, text="Refresh", bd=4, relief="raised",
            command=self.refresh_table, bg="dodgerblue", fg="white"
        ).pack(side="left")
        btn_frame = tk.Frame(self.filter_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=10)
        action_btn = {
            "Export PDF": self.on_export_pdf,
            "Print Logs": self.on_print
        }
        for text, command in action_btn.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="raised",
                bg="dodgerblue", fg="white",
            ).pack(side="left")
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.table_frame.pack(fill="both", expand=True)
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        alt_colors = ("#ffffff", "#e6f2ff")  # White and light blueish
        self.tree.tag_configure("evenrow", background=alt_colors[0])
        self.tree.tag_configure("oddrow", background=alt_colors[1])


    def refresh_table(self):
        year_str = self.selected_year.get()
        if not year_str:
            return
        year = int(year_str)
        month = None
        title = "Stock Items Logs In"
        if self.month_cb.get():
            month = dict(self.months).get(self.month_cb.get())
            title += f" {self.month_cb.get()}"
        title += f" {year}."
        self.title_label.configure(text=title)
        self.title = title

        success, logs = fetch_product_control_logs(self.conn, year, month)
        if not success:
            messagebox.showerror("Error", logs, parent=self.top)
            return
        # Clear current rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, log in enumerate(logs, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            name = re.sub(r"\s+", " ", str(log["product_name"])).strip()
            self.tree.insert("", "end", values=(
                i,
                log["user"],
                log["log_date"],
                log["product_code"],
                name,
                log["description"],
                log["quantity"],
                f"{log['total']:,.2f}"
            ), tags=(tag,))
        self.auto_resize()

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0],
                "User": vals[1],
                "Date": vals[2],
                "Item Code": vals[3],
                "Product Name": vals[4],
                "Operation": vals[5],
                "Quantity": vals[6],
                "Amount": vals[7]
            })
        return rows

    def _make_exporter(self):
        title = self.title
        columns = [
            "No", "User", "Date", "Item Code", "Product Name", "Operation",
            "Quantity", "Amount"
        ]
        rows = self._collect_current_rows()
        return ReportExporter(self.top, title, columns, rows)

    def _check_privilege(self):
        priv = "View Logs"
        verify = VerifyPrivilegePopup(self.top, self.conn, self.user, priv)
        return getattr(verify, "result", None) == "granted"

    def on_export_pdf(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Export PDF.", parent=self.top
            )
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Print Logs.", parent=self.top
            )
            return
        exporter = self._make_exporter()
        exporter.print()

    def auto_resize(self):
        """Resize columns to fit content."""
        font = tkFont.Font()
        for col in self.columns:
            # Start with the column header width
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            # Add Padding for readability
            self.tree.column(col, width=max_width)
