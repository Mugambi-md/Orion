import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from base_window import BaseWindow
from accounting_export import ReportExporter
from authentication import VerifyPrivilegePopup, DescriptionFormatter
from working_on_employee import fetch_log_filter_data, fetch_logs
from table_utils import TreeviewSorter
from log_popups_gui import (
    FinanceLogsWindow, OrderLogsWindow, MonthlyReversalLogs, SalesLogsWindow,
    ProductLogsWindow
)


class SystemLogsWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.top = tk.Toplevel(parent)
        self.top.title("System Logs")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 1330, 700, parent)
        self.top.transient(parent)
        self.top.grab_set()

        self.conn = conn
        self.user = user
        success, data = fetch_log_filter_data(conn)
        if not success:
            messagebox.showerror("Error", data, parent=self.top)
        self.years = data["years"]
        self.usernames = data["usernames"]
        self.sections = data["sections"]
        self.selected_year = tk.StringVar()
        self.filter_user_var = tk.BooleanVar(value=False)
        self.filter_month_var = tk.BooleanVar(value=False)
        self.filter_section_var = tk.BooleanVar(value=False)
        self.selected_user = tk.StringVar()
        self.selected_month = tk.StringVar()
        self.selected_section = tk.StringVar()
        self.title = None
        self.months = [
            ("", None), ("January", 1), ("February", 2), ("March", 3),
            ("April", 4), ("May", 5), ("June", 6), ("July", 7),
            ("August", 8), ("September", 9), ("October", 10),
            ("November", 11), ("December", 12),
        ]
        self.columns = ["No", "Date", "Time", "User", "Section", "Operation"]
        style = ttk.Style(self.top)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.top, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.filter_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_year, width=5,
            state="readonly", values=self.years, font=("Arial", 12)
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_user, width=8,
            state="disabled", values=self.usernames, font=("Arial", 12)
        )
        self.month_cb = ttk.Combobox(
            self.filter_frame, values=[name for name, _num in self.months],
            width=10, state="disabled", font=("Arial", 12)
        )
        self.section_cb = ttk.Combobox(
            self.filter_frame, width=12, state="disabled",
            values=self.sections, textvariable=self.selected_section,
            font=("Arial", 12)
        )
        self.title_label = tk.Label(
            self.top_frame, text="", bg="lightblue", fg="dodgerblue",
            font=("Arial", 20, "bold", "underline")
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()
        self.sorter.set_row_height(style, 40)

        self.build_ui()
        self.refresh_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.top_frame.pack(side="top", fill="x", pady=(5, 0))
        self.title_label.pack(side="left", padx=5)
        # Navigation Frame
        top_btn_frame = tk.Frame(
            self.top_frame, bg="lightblue", bd=4, relief="groove"
        )
        top_btn_frame.pack(side="right")
        navigation_btn = {
            "Stock Logs": self.stock_logs,
            "Sales Logs": self.sales_logs,
            "Sales Reversal Logs": self.sales_reversal_logs,
            "Finance Logs": self.finance_logs,
            "Order Logs": self.order_logs
        }
        for text, command in navigation_btn.items():
            tk.Button(
                top_btn_frame, text=text, bd=4, relief="groove", bg="green",
                fg="white", font=("Arial", 11, "bold"), command=command
            ).pack(side="left")
        # Filter Frame
        self.filter_frame.pack(fill="x")
        # Year Selector
        tk.Label(
            self.filter_frame, text="Select Year:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(2, 0))
        self.year_cb.pack(side="left", padx=(0, 3))
        if self.years:
            self.year_cb.set(self.years[0])
        else:
            messagebox.showinfo(
                "Info", "No Order Logs Found.", parent=self.top
            )
        self.year_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.refresh_table()
        )
        # Filter Checkbox Frame
        filter_outer = tk.Frame(
            self.filter_frame, bg="lightblue", bd=2, relief="groove"
        )
        filter_outer.pack(side="left", padx=2)
        tk.Label(
            filter_outer, text="Filter By:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(2, 0))
        tk.Checkbutton(
            filter_outer, variable=self.filter_section_var, bg="lightblue",
            text="section", command=self.toggle_filters,
            font=("Arial", 11, "bold")
        ).pack(side="left")
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
        # User Filter
        tk.Label(
            self.filter_frame, text="Section:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(2, 0))
        self.section_cb.pack(side="left", padx=(0, 3))
        tk.Label(
            self.filter_frame, text="User:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(3, 0))
        self.user_cb.pack(side="left", padx=(0, 3))
        # Month Filter
        tk.Label(
            self.filter_frame, text="Month:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(3, 0))
        self.month_cb.pack(side="left", padx=(0, 3))
        tk.Button(
            self.filter_frame, text="Refresh", bd=4, relief="ridge",
            font=("Arial", 10, "bold"), command=self.refresh_table
        ).pack(side="left")
        btn_frame = tk.Frame(self.filter_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=3)
        action_btn = {
            "Export PDF": self.on_export_pdf,
            "Print Logs": self.on_print
        }
        for text, command in action_btn.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=4, relief="groove",
                bg="dodgerblue", fg="white", font=("Arial", 10, "bold")
            ).pack(side="left")
        self.user_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.refresh_table()
        )
        self.month_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.refresh_table()
        )
        self.section_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.refresh_table()
        )
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
        if self.filter_section_var.get():
            self.section_cb["state"] = "readonly"
        else:
            self.section_cb.set("")
            self.section_cb["state"] = "disabled"
        self.refresh_table()

    def refresh_table(self):
        year_str = self.selected_year.get()
        if not year_str:
            return
        year = int(year_str)
        month = None
        user = None
        dept = None
        title = "System Logs"
        if self.filter_user_var.get() and self.user_cb.get():
            user = self.user_cb.get()
            title += f" For {user.capitalize()}"
        if self.filter_month_var.get() and self.month_cb.get():
            month = dict(self.months).get(self.month_cb.get())
            title += f" In {self.month_cb.get()}"
        title += f" {year}"
        if self.filter_section_var.get() and self.section_cb.get():
            dept = self.section_cb.get()
            title += f" In {dept}"
        self.title_label.configure(text=title)
        self.title = title

        success, logs = fetch_logs(self.conn, year, month, user, dept)
        if not success:
            messagebox.showerror("Error", logs, parent=self.top)
            return
        # Clear current rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        formatter = DescriptionFormatter(80, 10)
        for i, row in enumerate(logs, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            action = formatter.wrap(row["action"])
            self.tree.insert("", "end", values=(
                i,
                row["log_date"].strftime("%d/%m/%Y"),
                row["log_time"],
                row["username"],
                row["section"],
                action
            ), tags=(tag,))
        self.sorter.autosize_columns(5)

    def has_privilege(self, privilege: str) -> bool:
        """Check if the current user has the required privilege."""
        dialog = VerifyPrivilegePopup(
            self.top, self.conn, self.user, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You do not have permission to {privilege}.",
                parent=self.top
            )
            return False
        return True

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0],
                "Date": vals[1],
                "Time": vals[2],
                "User": vals[3],
                "Section": vals[4],
                "Operation": vals[5]
            })
        return rows

    def _make_exporter(self):
        title = self.title
        columns = ["No", "Date", "Time", "User", "Section", "Operation"]
        rows = self._collect_current_rows()
        return ReportExporter(self.top, title, columns, rows)

    def on_export_pdf(self):
        if not self.has_privilege("View Logs"):
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self.has_privilege("View Logs"):
            return
        exporter = self._make_exporter()
        exporter.print()

    def stock_logs(self):
        if not self.has_privilege("View Products Logs"):
            return
        ProductLogsWindow(self.top, self.conn, self.user)

    def sales_logs(self):
        if not self.has_privilege("View Products Logs"):
            return
        SalesLogsWindow(self.top, self.conn, self.user)

    def order_logs(self):
        if not self.has_privilege("View Order Logs"):
            return
        OrderLogsWindow(self.top, self.conn, self.user)

    def sales_reversal_logs(self):
        if not self.has_privilege("View Sales Logs"):
            return
        MonthlyReversalLogs(self.top, self.conn, self.user)

    def finance_logs(self):
        if not self.has_privilege("View Finance Logs"):
            return
        FinanceLogsWindow(self.top, self.conn, self.user)

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn = connect_db()
    root = tk.Tk()
    SystemLogsWindow(root, conn, "Sniffy")
    root.mainloop()