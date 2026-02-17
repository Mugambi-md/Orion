import datetime
import re
import calendar
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date
from base_window import BaseWindow
from analysis_gui_graph import LineAnalysisWindow, MonthLineAnalysis
from analysis_gui_pie import AnalysisWindow
from accounting_export import ReportExporter
from receipt_gui_and_print import ReceiptViewer
from authentication import VerifyPrivilegePopup
from log_popups_gui import MonthlyReversalLogs
from windows_utils import CurrencyFormatter
from window_functionality import FocusChain
from table_utils import TreeviewSorter
from working_sales import (
    fetch_sales_last_24_hours, fetch_sale_by_year,
    fetch_sales_summary_by_year, tag_reversal,
    get_retail_price, fetch_pending_reversals,
    reject_tagged_reversal, delete_rejected_reversal, authorize_reversal,
    fetch_filter_values, fetch_sales_by_month_and_user, fetch_sales_items,
    post_reversal, CashierControl, fetch_cashier_control_users, get_net_sales,
    # fetch_all_sales_users
)


class Last24HoursSalesWindow(BaseWindow):
    def __init__(self, parent, conn, username):
        self.window = tk.Toplevel(parent)
        self.window.title("24 Hours Sales Logs")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 800, 700, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = username
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.columns = (
            "No", "Date", "Time", "Receipt No", "Amount", "Total"
        )
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        # Table frame
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings",
            selectmode="browse"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()
        self.load_data()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Header Frame
        header_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        header_frame.pack(fill="x")
        label_txt = f"Last 24 Hours Sales Of {self.user.capitalize()}."
        tk.Label(
            header_frame, text=label_txt, bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline")
        ).pack(side="left", anchor="s", padx=(5, 0))
        tk.Button(
            header_frame, text="Print Receipt", fg="blue", bd=4,
            relief="groove", font=("Arial", 11, "bold"),
            command=self.print_receipt
        ).pack(side="right", anchor="s")
        self.table_frame.pack(fill="both", expand=True)
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        # Treeview setup
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")


    def print_receipt(self):
        selected = self.tree.selection()
        if selected:
            receipt_no = self.tree.item(selected[0])["values"][3]
            # Call your receipt printing function here
            ReceiptViewer(self.conn, receipt_no, self.user)
        else:
            messagebox.showwarning(
                "Info",
                "Please select a sale to print receipt.", parent=self.window
            )

    def load_data(self):
        data, error = fetch_sales_last_24_hours(self.conn, self.user)
        if error:
            messagebox.showerror("Error", error, parent=self.window)
            return
        # Clear previous data
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Insert data
        total = 0.00
        for i, row in enumerate(data, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            total += float(row["total_amount"])
            self.tree.insert("", "end", values=(
                i,
                row["sale_date"].strftime("%d/%m/%Y"),
                row["sale_time"],
                row["receipt_no"],
                f"{row['total_amount']:,.2f}",
                f"{total:,.2f}"
            ), tags=(tag,))
        self.sorter.autosize_columns(5)


class MonthlySalesSummary(BaseWindow):
    def __init__(self, parent, conn):
        self.window = tk.Toplevel(parent)
        self.window.title("Monthly Sales Summary")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 800, 700, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        # Load filter values from DB
        users, years, err = fetch_filter_values(self.conn)
        if err:
            messagebox.showerror(
                "Error",
                f"Failed to fetch filter values:\n{err}", parent=self.window
            )
            self.window.destroy()
            return
        # Data holders for filter options
        self.users = users
        self.years = years if years else [date.today().year]
        self.user = tk.StringVar()
        self.show_all_var = tk.BooleanVar()
        self.months = [
            ("January", 1), ("February", 2), ("March", 3), ("April", 4),
            ("May", 5), ("June", 6), ("July", 7), ("August", 8),
            ("September", 9), ("October", 10), ("November", 11),
            ("December", 12),
        ]
        current_month_num = date.today().month
        current_month_name = dict((num, name) for name, num in self.months)[
            current_month_num
        ]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.columns = ("No", "Sale Date", "Amount", "Total Sales")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.top_frame, width=5, values=self.years, state="readonly",
            font=("Arial", 12)
        )
        self.title_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.title_label = tk.Label(
            self.title_frame, text="", bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline")
        )
        # Filters combobox
        self.month_cb = ttk.Combobox(
            self.top_frame, values=[name for name, _num in self.months],
            width=10, font=("Arial", 12)
        )
        self.month_cb.set(current_month_name)
        self.user_cb = ttk.Combobox(
            self.top_frame, textvariable=self.user, values=self.users,
            width=10, state="readonly", font=("Arial", 12)
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.setup_widgets()
        self.load_data()

    def setup_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.title_frame.pack(fill="x", pady=(5, 0))
        self.title_label.pack(side="top", anchor="s")
        self.top_frame.pack(fill="x")
        tk.Label(
            self.top_frame, text="Select Year:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0), anchor="s")
        self.year_cb.current(0)
        self.year_cb.pack(side="left", padx=(0, 5), anchor="s")
        tk.Label(
            self.top_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0), anchor="s")
        self.month_cb.pack(side="left", padx=(0, 5), anchor="s")
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.top_frame, text="User:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0), anchor="s")
        self.user_cb.pack(side="left", padx=(0, 5), anchor="s")
        tk.Checkbutton(
            self.top_frame, text="Show All", variable=self.show_all_var,
            bg="lightblue", command=self.toggle_show_all,
            font=("Arial", 12, "bold")
        ).pack(side="left", anchor="s")
        tk.Button(
            self.top_frame, text="Sales Graph", bg="blue", fg="white", bd=4,
            relief="groove", font=("Arial", 10, "bold"),
            command=self.analysis
        ).pack(side="right", anchor="s", padx=5)
        # Bind selection Changes
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        # Table and Scrollbar
        self.table_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Define alternating row styles
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        self.tree.tag_configure(
            "total", font=("Arial", 13, "bold", "underline"),
            background="blue", foreground="white"
        )

    def toggle_show_all(self):
        """Handle logic for show all checkbox."""
        if self.show_all_var.get():
            # Disable user selection
            self.user.set("")
            self.user_cb.configure(state="disabled")
        else:
            self.user_cb.configure(state="readonly")
        self.load_data()  # Refresh table

    def load_data(self):
        user = None
        month = dict(self.months).get(self.month_cb.get())
        year = self.year_cb.get()
        txt = f"Sales Summary In {self.month_cb.get()}"
        if not self.show_all_var.get():
            # if self.user_var.get() and self.user_cb.get():
            if self.user.get():
                user = self.user_cb.get()
                txt += f" For {user.capitalize()}"
        txt += f" {year}."
        self.title_label.configure(text=txt)
        data, error = fetch_sales_by_month_and_user(
            self.conn, year, month, user
        )
        # Clear tree
        if error:
            messagebox.showerror("Error", error, parent=self.window)
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Insert rows with running balance
        running_total = 0.0
        for i, row in enumerate(data, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            amount = float(row["daily_total"])
            running_total += amount
            self.tree.insert("", "end", values=(
                i,
                row["sale_date"].strftime("%d/%m/%Y"),
                f"{amount:,.2f}",
                f"{running_total:,.2f}"
            ), tags=(tag,))
        if data:
            report_day = datetime.date.today().strftime('%d/%m/%Y')
            entry_title = f"Total Sales As at {report_day}"
            self.tree.insert("", "end", values=(
                "", entry_title, "", f"{running_total:,.2f}"
            ), tags=("total",))
        self.sorter.autosize_columns(5)

    def analysis(self):
        """View line graph window."""
        sale_year = int(self.year_cb.get())
        sale_month = dict(self.months).get(self.month_cb.get())
        user = None
        if not self.show_all_var.get() and self.user.get():
            user = self.user_cb.get()

        rows, err = fetch_sales_by_month_and_user(
            self.conn, sale_year, sale_month, user
        )
        if err:
            messagebox.showerror(
                "Error", f"Failed to Fetch Sales:\n{err}.",
                parent=self.window
            )
            return
        if not rows:
            messagebox.showerror(
                "No Data", "No Data Found For Selected Filter(s)",
                parent=self.window
            )
            return
        rows.sort(key=lambda r: r["sale_date"])
        cumulative_total = 0
        for r in rows:
            cumulative_total += r["daily_total"]
            r["cumulative"] = cumulative_total
        metrics = {
            "Daily Sales": lambda r: r["daily_total"],
            "Cumulative Sales": lambda r: r["cumulative"],
        }

        title_text = f"Sales Summary In {self.month_cb.get()}"
        if user:
            title_text += f" For {user}"
        title_text += f" {sale_year}."
        MonthLineAnalysis(title_text, rows, metrics, "sale_date")


class YearlySalesWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Yearly Cumulative Sales")
        self.center_window(self.master, 1100, 700, parent)
        self.master.configure(bg="lightblue")
        self.master.transient(parent)
        self.master.grab_set()

        self.conn = conn
        self.user = user
        # Load filter values from DB
        users, years, err = fetch_filter_values(self.conn)
        if err:
            messagebox.showerror(
                "Error",
                f"Failed to fetch filter values:\n{err}", parent=self.master
            )
            self.master.destroy()
            return
        # Data holders for filter options
        self.users = users
        self.years = years if years else [date.today().year]
        self.months = [
            ("", None), ("January", 1), ("February", 2), ("March", 3),
            ("April", 4), ("May", 5), ("June", 6), ("July", 7),
            ("August", 8), ("September", 9), ("October", 10),
            ("November", 11), ("December", 12),
        ]
        self.columns = [
            "No", "Sale Date", "Receipt No", "User", "Sale Amount",
            "Total Sales"
        ]
        # Bold headings
        style = ttk.Style()
        style.theme_use("clam")
        # Variables for checkboxes
        self.month_var = tk.BooleanVar()
        self.user_var = tk.BooleanVar()
        self.show_all_var = tk.BooleanVar()
        # Frames
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        # Title Label
        self.title_label = tk.Label(
            self.main_frame, text="", bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline")
        )
        self.filter_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="flat"
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.year_cb = ttk.Combobox(
            self.filter_frame, width=5, values=self.years, state="readonly",
            font=("Arial", 12)
        )
        # Filters combobox
        self.month_cb = ttk.Combobox(
            self.filter_frame, width=10, state="disabled",
            font=("Arial", 12), values=[name for name, _num in self.months]
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, width=10, state="disabled", values=self.users,
            font=("Arial", 12)
        )
        # Table
        self.product_table = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.product_table, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.title_label.pack(side="top", anchor="center", pady=(5, 0))
        # Filter frame
        self.filter_frame.pack(fill="x")
        tk.Label(
            self.filter_frame, text="Year:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", anchor="s")
        self.year_cb.set(self.years[0])
        self.year_cb.pack(side="left", anchor="s", padx=(0, 3))
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        # Checkboxes Frame
        check_box = tk.Frame(
            self.filter_frame, bg="lightblue", bd=1, relief="ridge"
        )
        check_box.pack(side="left", anchor="s", padx=5)
        tk.Label(
            check_box, text="Sort By:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(2, 0))
        tk.Checkbutton(
            check_box, bg="lightblue", variable=self.month_var, text="Month",
            command=self.toggle_filters, font=("Arial", 11, "bold")
        ).pack(side="left")
        tk.Checkbutton(
            check_box, variable=self.user_var, bg="lightblue", text="User",
            command=self.toggle_filters, font=("Arial", 11, "bold")
        ).pack(side="left")
        tk.Checkbutton(
            check_box, text="Show All", variable=self.show_all_var,
            bg="lightblue", command=self.toggle_show_all,
            font=("Arial", 11, "bold")
        ).pack(side="left")
        tk.Label(
            self.filter_frame, text="Month:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", anchor="s", padx=(3, 0))
        self.month_cb.pack(side="left", anchor="s", padx=(0, 3))
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.filter_frame, text="User:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", anchor="s", padx=(3, 0))
        self.user_cb.pack(side="left", anchor="s", padx=(0, 3))
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        btn_frame = tk.Frame(
            self.filter_frame, bg="lightblue", bd=2, relief="ridge"
        )
        btn_frame.pack(side="right", anchor="s")
        btns = {
            "Receipt": self.print_receipt,
            "Graph": self.open_line_analysis,
            "Print": self.on_print,
            "Export": self.on_export_excel,
        }
        for text, command in btns.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=4, relief="groove",
                bg="blue", fg="white", font=("Arial", 10, "bold"),
            ).pack(side="left", anchor="s")
        self.table_frame.pack(fill="both", expand=True)
        # Table + Scrollbars
        vsb = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.product_table.yview
        )
        self.product_table.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        # Configure headings
        for col in self.columns:
            self.product_table.heading(col, text=col)
            self.product_table.column(col, anchor="center", width=20)
        self.product_table.pack(fill="both", expand=True)
        self.product_table.tag_configure(
            "total", font=("Arial", 13, "bold", "underline"),
            background="blue", foreground="white"
        )
        self.product_table.tag_configure("evenrow", background="#fffde7")
        self.product_table.tag_configure("oddrow", background="#e0f7e9")

    def toggle_show_all(self):
        """Handle logic for show all checkbox."""
        if self.show_all_var.get():
            # If Show all is checked, uncheck month and user filters
            self.month_var.set(False)
            self.user_var.set(False)
            self.toggle_filters()  # disable combo boxes
        self.load_data()  # Refresh table

    def toggle_filters(self):
        """Enable/Disable combo boxes based on checkboxes."""
        # If Show All is checked, force disable filters
        if self.show_all_var.get():
            self.month_cb.configure(state="disabled")
            self.user_cb.configure(state="disabled")
            return
        self.month_cb.configure(
            state="readonly" if self.month_var.get() else "disabled"
        )
        self.user_cb.configure(
            state="readonly" if self.user_var.get() else "disabled"
        )
        self.load_data()

    def load_data(self):
        """Load sales data based on current year only (initial)."""
        self.product_table.delete(*self.product_table.get_children())
        year = int(self.year_cb.get())
        # Filters
        month = None
        user = None
        # Only apply filters if show all is unchecked
        title_text = f"Cumulative Sales"
        if not self.show_all_var.get():
            if self.user_var.get() and self.user_cb.get():
                user = self.user_cb.get()
                title_text += f" For {user.capitalize()}"
            if self.month_var.get() and self.month_cb.get():
                month = dict(self.months).get(self.month_cb.get())
                title_text += f" In {self.month_cb.get()}"
        title_text += f" {year}."
        rows, err = fetch_sale_by_year(self.conn, year, month, user)
        if err:
            messagebox.showerror(
                "Error", f"Failed to fetch sales:\n{err}.",
                parent=self.master
            )
            return
        cumulative_total = 0
        for idx, row in enumerate(rows, start=1):
            cumulative_total += row["total_amount"]
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.product_table.insert("", "end", values=(
                idx,
                row["sale_date"].strftime("%d/%m/%Y"),
                row["receipt_no"],
                row["user"],
                f"{row["total_amount"]:,.2f}",
                f"{cumulative_total:,.2f}",
            ), tags=(tag,))
        if rows:
            self.product_table.insert("", "end", values=(
                "", "", "Total Sales", "", "", f"{cumulative_total:,.2f}"
            ), tags=("total",))
        self.title_label.configure(text=title_text)
        self.sorter.autosize_columns()

    def print_receipt(self):
        selected = self.product_table.selection()
        if selected:
            receipt_no = self.product_table.item(selected[0])["values"][2]
            # Call your receipt printing function here
            ReceiptViewer(self.conn, receipt_no, self.user)
        else:
            messagebox.showwarning(
                "Info", "Please Select Sale to Print Receipt.",
                parent=self.master
            )

    def open_line_analysis(self):
        """View line graph window."""
        year = int(self.year_cb.get())
        month = None
        user = None
        if not self.show_all_var.get():
            if self.month_var.get() and self.month_cb.get():
                month = dict(self.months).get(self.month_cb.get())
            if self.user_var.get() and self.user_cb.get():
                user = self.user_cb.get()

        rows, err = fetch_sale_by_year(self.conn, year, month, user)
        if err:
            messagebox.showerror(
                "Error", f"Failed to Fetch Sales:\n{err}.",
                parent=self.master
            )
            return
        if not rows:
            messagebox.showerror(
                "No Data", "No Sales Data Found For Selected Filter(s)",
                parent=self.master
            )
            return
        cumulative_total = 0
        for r in rows:
            cumulative_total += r["total_amount"]
            r["cumulative"] = cumulative_total
        metrics = {
            "Sale Amount": lambda r: r["total_amount"],
            "Total Sales": lambda r: r["cumulative"],
        }
        if not user:

            def make_metric_total(uname):
                return lambda r: r["total_amount"] if r["user"] == uname else None

            def make_metric_cumulative(uname):
                return lambda r: r["cumulative"] if r["user"] == uname else None

            users = {}
            for r in rows:
                u = r["user"]
                users.setdefault(u, []).append(r)
            # Compute cumulative per user
            for u, ur in users.items():
                cumu = 0
                for r in ur:
                    cumu += r["total_amount"]
                    r["cumulative"] = cumu
                metrics[f"{u} Total"] = make_metric_total(u)
                metrics[f"{u} Cumulative"] = make_metric_cumulative(u)

        title = f"Sales Analysis {year}"
        if user:
            title += f" For {user}"
        if month:
            title += f" In {self.month_cb.get()}"
        LineAnalysisWindow(title, rows, metrics, "sale_date")

    def _collect_rows(self):
        rows = []
        for item in self.product_table.get_children():
            vals = self.product_table.item(item, "values")
            rows.append(
                {
                    "No": vals[0],
                    "Sale Date": vals[1],
                    "Receipt No": vals[2],
                    "User": vals[3],
                    "Sale Amount": vals[4],
                    "Total Sales": vals[5],
                }
            )
        return rows

    def _make_exporter(self):
        year = self.year_cb.get()
        title = f"Cumulative Sales for Year {year}."
        columns = [
            "No", "Sale Date", "Receipt No", "User", "Sale Amount",
            "Total Sales"
        ]
        rows = self._collect_rows()
        return ReportExporter(self.master, title, columns, rows)

    def on_export_excel(self):
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_export_pdf(self):
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        exporter = self._make_exporter()
        exporter.print()


class YearlyProductSales(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Yearly Product Sales Performance")
        self.center_window(self.master, 1200, 700, parent)
        self.master.configure(bg="lightblue")
        self.master.transient(parent)
        self.master.grab_set()

        self.conn = conn
        self.user = user
        # Load filter values from DB
        users, years, err = fetch_filter_values(self.conn)
        if err:
            messagebox.showerror(
                "Error", f"Failed to fetch filter values:\n{err}.",
                parent=self.master
            )
            self.master.destroy()
            return
        # Data holders for filter options
        self.rows = None
        self.users = users
        self.years = years if years else [date.today().year]
        self.months = [
            ("", None), ("January", 1), ("February", 2), ("March", 3),
            ("April", 4), ("May", 5), ("June", 6), ("July", 7),
            ("August", 8), ("September", 9), ("October", 10),
            ("November", 11), ("December", 12)
        ]
        self.columns = [
            "No", "Item Code", "Item Name", "Qty", "Unit Cost", "Total Cost",
            "Unit Price", "Sale Amount", "Profit"
        ]
        # Variables for checkboxes
        self.month_var = tk.BooleanVar()
        self.user_var = tk.BooleanVar()
        self.show_all_var = tk.BooleanVar()
        # Bold headings
        style = ttk.Style(self.master)
        style.theme_use("clam")
        # Frames
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        # Title Label
        self.title = None
        self.title_label = tk.Label(
            self.main_frame, text="", bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline")
        )
        # self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.filter_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.filter_frame, width=5, values=self.years, state="readonly",
            font=("Arial", 12)
        )
        # Filters combobox
        self.month_cb = ttk.Combobox(
            self.filter_frame, width=10, state="disabled",
            font=("Arial", 12), values=[name for name, _num in self.months],
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, width=9, state="disabled", values=self.users,
            font=("Arial", 12)
        )
        # Table Frame
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.title_label.pack(side="top", anchor="center")
        self.filter_frame.pack(fill="x")
        self.table_frame.pack(fill="both", expand=True)
        check_frame = tk.Frame(
            self.filter_frame, bg="lightblue", bd=1, relief="ridge"
        )
        tk.Label(
            check_frame, text="Sort By:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(2, 0))
        tk.Checkbutton(
            check_frame, variable=self.month_var, command=self.toggle_filters
            , bg="lightblue", text="Month", font=("Arial", 11, "bold")
        ).pack(side="left")
        tk.Checkbutton(
            check_frame, variable=self.user_var, bg="lightblue", text="User",
            command=self.toggle_filters, font=("Arial", 11, "bold")
        ).pack(side="left")
        tk.Checkbutton(
            check_frame, text="Show All", variable=self.show_all_var,
            bg="lightblue", command=self.toggle_show_all,
            font=("Arial", 11, "bold")
        ).pack(side="left")
        # Filter frame
        tk.Label(
            self.filter_frame, text="Year:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0), anchor="s")
        self.year_cb.set(self.years[0])
        self.year_cb.pack(side="left", padx=(0, 5), anchor="s")
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        check_frame.pack(side="left")
        tk.Label(
            self.filter_frame, text="Month:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0), anchor="s")
        self.month_cb.pack(side="left", padx=(0, 5), anchor="s")
        self.month_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.load_data()
        )
        tk.Label(
            self.filter_frame, text="Username:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0), anchor="s")
        self.user_cb.pack(side="left", padx=(0, 5), anchor="s")
        btn_frame = tk.Frame(
            self.filter_frame, bg="lightblue", bd=2, relief="ridge"
        )
        btn_frame.pack(side="right", anchor="s")
        btns = {
            "Pie Chart": self.view_analysis_charts,
            "Expt PDF": self.on_export_pdf,
            "Expt Excel": self.on_export_excel,
            "Print": self.on_print,
        }
        for text, command in btns.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=4, relief="groove",
                bg="dodgerblue", fg="white", font=("Arial", 10, "bold")
            ).pack(side="left", anchor="s")
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        # Table + Scrollbars
        vsb = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        # Configure headings
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=20)
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure(
            "total", font=("Arial", 12, "bold", "underline"),
            background="blue", foreground="white"
        )
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def toggle_show_all(self):
        """Handle logic for show all checkbox."""
        if self.show_all_var.get():
            # If Show all is checked, uncheck month and user filters
            self.month_var.set(False)
            self.user_var.set(False)
            self.toggle_filters()  # disable combo boxes
        self.load_data()  # Refresh table

    def toggle_filters(self):
        """Enable/Disable combo boxes based on checkboxes."""
        # If Show All is checked, force disable filters
        if self.show_all_var.get():
            self.month_cb.configure(state="disabled")
            self.user_cb.configure(state="disabled")
            return
        self.month_cb.configure(
            state="readonly" if self.month_var.get() else "disabled"
        )
        self.user_cb.configure(
            state="readonly" if self.user_var.get() else "disabled"
        )
        self.load_data()

    def load_data(self):
        """Load sales data based on current year only (initial)."""
        self.tree.delete(*self.tree.get_children())
        year = int(self.year_cb.get())
        # Filters
        month = None
        user = None
        title = "Products Sales Performance"
        # Only apply filters if show all is unchecked
        if not self.show_all_var.get():
            if self.user_var.get() and self.user_cb.get():
                user = self.user_cb.get()
                title += f" For {user.capitalize()}"
            if self.month_var.get() and self.month_cb.get():
                month = dict(self.months).get(self.month_cb.get())
                title += f" in {self.month_cb.get()}"
        title += f" {year}."
        rows, err = fetch_sales_summary_by_year(self.conn, year, month, user)
        if err:
            messagebox.showerror(
                "Error", f"Failed to fetch sales:\n{err}.",
                parent=self.master
            )
            return
        # Totals accumulators
        total_qty = 0
        total_cost_sum = 0
        total_amount_sum = 0
        total_profit_sum = 0
        self.rows = []  # Reset processed rows
        for idx, row in enumerate(rows, start=1):
            total_cost = float(row["unit_cost"] * row["total_quantity"])
            est_unit_price = (
                float(row["total_amount"] / row["total_quantity"])
                if row["total_quantity"]
                else 0
            )
            name = re.sub(r"\s+", " ", str(row["product_name"])).strip()
            total_profit = float(row["total_amount"]) - total_cost
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            precessed_row = {
                "No": idx,
                "Item Code": row["product_code"],
                "Item Name": name,
                "Qty": row["total_quantity"],
                "Unit Cost": f"{row["unit_cost"]:,.2f}",
                "Total Cost": f"{total_cost:,.2f}",
                "Unit Price": f"{est_unit_price:,.2f}",
                "Sale Amount": f"{row["total_amount"]:,.2f}",
                "Profit": f"{total_profit:,.2f}",
            }
            self.rows.append(precessed_row)
            self.tree.insert(
                "", "end", values=list(precessed_row.values()), tags=(tag,)
            )
            # Update totals
            total_qty += int(row["total_quantity"])
            total_cost_sum += total_cost
            total_amount_sum += float(row["total_amount"])
            total_profit_sum += total_profit
        if rows:
            # Compute weighted averages for costs and prices
            avg_unit_cost = total_cost_sum / total_qty if total_qty else 0
            avg_unit_price = total_amount_sum / total_qty if total_qty else 0
            self.tree.insert("", "end", values=(
                "",
                "",
                "TOTALS",
                total_qty,
                f"{avg_unit_cost:,.2f}",
                f"{total_cost_sum:,.2f}",
                f"{avg_unit_price:,.2f}",
                f"{total_amount_sum:,.2f}",
                f"{total_cost_sum:,.2f}",
            ), tags=("total",))
        self.title = title
        self.title_label.configure(text=self.title)
        self.sorter.autosize_columns(10)

    def view_analysis_charts(self):
        """Open analysis window with pie/ bar for current rows."""
        if not self.rows:
            messagebox.showinfo(
                "Data", "No Sales data to Analyze.", parent=self.master
            )
            return

        metrics = {
            "Quantity": lambda r: float(r["Qty"]) if r["Qty"] else 0,
            "Total Amount Sold": lambda r: (float(
                r["Sale Amount"].replace(",", "")
            ) if r["Sale Amount"] else 0),
            "Total Profit": lambda r: (float(
                r["Profit"].replace(",", "")
            ) if r["Profit"] else 0),
        }
        AnalysisWindow(
            self.master, self.title, self.rows, metrics, "Item Name"
        )

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append(
                {
                    "No": vals[0],
                    "Item Code": vals[1],
                    "Item Name": vals[2],
                    "Qty": vals[3],
                    "Unit Cost": vals[4],
                    "Total Cost": vals[5],
                    "Unit Price": vals[6],
                    "Sale Amount": vals[7],
                    "Profit": vals[8],
                }
            )
        return rows

    def _make_exporter(self):
        title = self.title
        columns = [
            "No", "Item Code", "Item Name", "Qty", "Unit Cost", "Total Cost",
            "Unit Price", "Sale Amount", "Profit",
        ]
        rows = self._collect_rows()
        return ReportExporter(self.master, title, columns, rows)

    def has_privilege(self) -> bool:
        """Check if the current user has the required privilege."""
        privilege = "Export Sales Data"
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

    def on_export_excel(self):
        # Verify user privilege
        if not self.has_privilege():
            return
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_export_pdf(self):
        # Verify user privilege
        if not self.has_privilege():
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        # Verify user privilege
        if not self.has_privilege():
            return
        exporter = self._make_exporter()
        exporter.print()

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root=tk.Tk()
    YearlyProductSales(root, conn, "Sniffy")
    root.mainloop()
class SalesControlReportWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.report_win = tk.Toplevel(parent)
        self.report_win.title("Sales Details And Reversal")
        self.report_win.configure(bg="lightblue")
        self.center_window(self.report_win, 1150, 700, parent)
        self.report_win.transient(parent)
        self.report_win.grab_set()

        self.conn = conn
        self.user = user
        self.all_rows = []
        users, years, err = fetch_filter_values(self.conn)
        if err:
            messagebox.showerror(
                "Error", f"Failed to fetch filter values:\n{err}.",
                parent=self.report_win
            )
            self.report_win.destroy()
            return
        # Data holders for filter options
        self.users = users
        self.years = years if years else [date.today().year]
        self.months = [
            ("", None), ("January", 1), ("February", 2), ("March", 3),
            ("April", 4), ("May", 5), ("June", 6), ("July", 7),
            ("August", 8), ("September", 9), ("October", 10),
            ("November", 11), ("December", 12),
        ]
        # Variables for checkboxes
        self.month_var = tk.BooleanVar()
        self.day_var = tk.BooleanVar()
        self.user_var = tk.BooleanVar()
        self.show_all_var = tk.BooleanVar()
        self.columns = (
            "No", "Date", "User", "Receipt No", "Product Code",
            "Product Name", "Quantity", "Unit Price", "Total",
        )
        style = ttk.Style(self.report_win)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.report_win, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.filter_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.filter_frame, width=5, values=self.years, state="readonly",
            font=("Arial", 11)
        )
        self.year_cb.set(self.years[0])
        self.month_cb = ttk.Combobox(
            self.filter_frame, width=10, state="disabled",
            values=[name for name, _num in self.months], font=("Arial", 11)
        )
        self.day_cb = ttk.Combobox(
            self.filter_frame, width=5, state="disabled", font=("Arial", 11)
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, width=7, state="disabled", values=self.users,
            font=("Arial", 11)
        )
        self.search_entry = tk.Entry(
            self.filter_frame, bd=4, relief="raised", font=("Arial", 12),
            width=15
        )
        self.tree = ttk.Treeview(
            self.tree_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(
            self.tree, self.columns, "No"
        )
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()

        self.setup_widgets()
        self.load_data()

    def setup_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Title and year selection
        self.top_frame.pack(fill="x", pady=3)
        tk.Label(
            self.top_frame, text="Sales Details And Reversal Tagging.",
            fg="blue", bg="lightblue", font=("Arial", 20, "bold", "underline")
        ).pack(side="left", anchor="s")
        # Checkboxes Frame
        check_frame = tk.Frame(
            self.top_frame, bg="lightgray", bd=2, relief="ridge"
        )
        check_frame.pack(side="right", padx=10)
        tk.Label(
            check_frame, text="Filter By:", bg="lightgray",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        # Check buttons for filters
        tk.Checkbutton(
            check_frame, variable=self.month_var, bg="lightgray", fg="blue",
            text="Month", command=self.toggle_filters,
            font=("Arial", 11, "bold"),
        ).pack(side="left")
        tk.Checkbutton(
            check_frame, variable=self.day_var, text="Day", bg="lightgray",
            fg="blue", font=("Arial", 11, "bold"),
            command=self.toggle_filters
        ).pack(side="left")
        tk.Checkbutton(
            check_frame, text="User", variable=self.user_var, bg="lightgray",
            fg="blue", font=("Arial", 11, "bold"),
            command=self.toggle_filters
        ).pack(side="left")
        tk.Checkbutton(
            check_frame, text="Show All", variable=self.show_all_var,
            bg="lightgray", fg="blue", command=self.toggle_show_all,
            font=("Arial", 11, "bold"),
        ).pack(side="left")
        # Filter Frame
        self.filter_frame.pack(fill="x")
        tk.Label(
            self.filter_frame, text="Select Year:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(3, 0), anchor="s")
        self.year_cb.pack(side="left", padx=(0, 3), anchor="s")
        self.year_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.load_data()
        )
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(3, 0), anchor="s")
        self.month_cb.pack(side="left", padx=(0, 3), anchor="s")
        self.month_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.update_days()
        )
        tk.Label(
            self.filter_frame, text="Select Day:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(3, 0), anchor="s")
        self.day_cb.pack(side="left", padx=(0, 3), anchor="s")
        self.day_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.filter_frame, text="Select User:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(3, 0), anchor="s")
        self.user_cb.pack(side="left", padx=(0, 3), anchor="s")
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.filter_frame, text="Receipt No.:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(3, 0), anchor="s")
        self.search_entry.pack(side="left", padx=(0, 3), anchor="s")
        self.search_entry.bind("<KeyRelease>", self.filter_by_receipt)
        tk.Button(
            self.filter_frame, text="Tag Reversal", bd=4, relief="groove",
            bg="dodgerblue", fg="white", font=("Arial", 10, "bold"),
            command=self.tag_reversal,
        ).pack(side="right", padx=3, anchor="s")
        self.tree_frame.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(
            self.tree_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def toggle_show_all(self):
        """Handle logic for show all checkbox."""
        if self.show_all_var.get():
            # If Show all is checked, uncheck month and user filters
            self.month_var.set(False)
            self.day_var.set(False)
            self.user_var.set(False)
            self.toggle_filters()  # disable combo boxes
        self.load_data()  # Refresh table

    def toggle_filters(self):
        """Enable/Disable combo boxes based on checkboxes."""
        # If Show All is checked, force disable filters
        if self.show_all_var.get():
            self.month_cb.configure(state="disabled")
            self.day_cb.configure(state="disabled")
            self.user_cb.configure(state="disabled")
            return
        self.month_cb.configure(
            state="readonly" if self.month_var.get() else "disabled"
        )
        self.user_cb.configure(
            state="readonly" if self.user_var.get() else "disabled"
        )
        self.day_cb.configure(
            state="readonly" if self.day_var.get() else "disabled"
        )
        self.load_data()

    def update_days(self):
        """Update day combobox on selected month/year."""
        if not self.month_cb.get():
            messagebox.showerror(
                "Month", "Select Month to show day.", parent=self.report_win
            )
            return
        year = int(self.year_cb.get())
        month_name = self.month_cb.get()
        month_num = dict((name, num) for name, num in self.months)[month_name]
        days_in_month = calendar.monthrange(year, month_num)[1]
        self.day_cb.configure(
            values=[str(d) for d in range(1, days_in_month + 1)]
        )
        self.load_data()

    def load_data(self):
        """Fetch and display filtered data."""
        try:
            year = int(self.year_cb.get())
            month = None
            day = None
            user = None
            if not self.show_all_var.get():
                if self.month_var.get() and self.month_cb.get():
                    month = dict((name, num) for name, num in self.months)[
                        self.month_cb.get()
                    ]
                if self.day_var.get() and self.day_cb.get():
                    day = int(self.day_cb.get())
                if self.user_var.get() and self.user_cb.get():
                    user = self.user_cb.get()
            rows, err = fetch_sales_items(self.conn, year, month, day, user)
            if err:
                messagebox.showerror(
                    "Error", f"Failed to fetch data:\n{err}.",
                    parent=self.report_win
                )
                return
            # Save rows for searching
            self.all_rows = rows
            self.update_tree(rows)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to Load data:\n{str(e)}.", parent=self.report_win
            )

    def update_tree(self, rows):
        # Clear previous rows
        self.tree.delete(*self.tree.get_children())
        # Insert new data
        for i, row in enumerate(rows, start=1):
            name = re.sub(r"\s+", " ", str(row["product_name"])).strip()
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                row["date"].strftime("%d/%m/%Y"),
                row["user"],
                row["receipt_no"],
                row["product_code"],
                name,
                row["quantity"],
                f"{row['unit_price']:,.2f}",
                f"{row['total_amount']:,.2f}",
            ), tags=(tag,))
        self.sorter.autosize_columns(5)

    def filter_by_receipt(self, event):
        """Filter current table by receipt number as user types."""
        query = self.search_entry.get().strip().lower()
        if not query:
            self.update_tree(self.all_rows)
        else:
            filtered = [
                row
                for row in self.all_rows
                if row["receipt_no"].lower().startswith(query)
            ]
            self.update_tree(filtered)

    def tag_reversal(self):
        """Handle reversal tagging with full or partial quantity."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "No Selection",
                "Please Select Item First.", parent=self.report_win
            )
            return
        # Extract row values
        row = self.tree.item(selected[0], "values")
        receipt_no = row[3]
        product_code = str(row[4])
        product_name = row[5]
        quantity = int(row[6])
        unit_price = float(row[7].replace(",", ""))  # Remove formatting
        total_price = float(row[8].replace(",", ""))
        # Ask user for reversal type
        choice = messagebox.askquestion(
            "Reversal Type",
            "Do you want to reverse full quantity?\n\n"
            "Click 'Yes' for Full Reversal, 'No' for Partial Reversal.",
            parent=self.report_win
        )
        if choice == "yes":
            # Full Reversal
            receipt = receipt_no
            code = product_code
            name = product_name
            qty = quantity
            price = unit_price
            refund = total_price
        else:
            receipt = receipt_no
            code = product_code
            name = product_name
            # Partial Reversal
            partial_qty = simpledialog.askinteger(
                "Partial Reversal",
                f"Enter Quantity to reverse:",
                minvalue=1,
                maxvalue=quantity,
            )
            if not partial_qty:
                return  # user canceled partial reversal
            remaining_qty = quantity - partial_qty
            adjusted_price = unit_price
            # Business rule: Retail price if remaining falls below 10
            if quantity >= 10 > remaining_qty:
                price = get_retail_price(self.conn, code)
                if price is not None and not isinstance(price, str):
                    adjusted_price = float(price)
                else:
                    adjusted_price = unit_price
            remaining_total = remaining_qty * adjusted_price
            to_refund = total_price - remaining_total

            qty = partial_qty
            price = adjusted_price
            refund = to_refund

        # Verify user privilege
        priv = "Tag Reversal"
        verify = VerifyPrivilegePopup(
            self.report_win, self.conn, self.user, priv
        )
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.report_win
            )
            return

        success, msg = tag_reversal(
            self.conn, receipt, code, name, price, qty, refund, self.user
        )
        if success:
            messagebox.showinfo("Success", msg, parent=self.report_win)
        else:
            messagebox.showerror("Error", msg, parent=self.report_win)


class SalesReversalWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Reversal Authorization and Posting")
        self.center_window(self.window, 1200, 600, parent)
        self.window.configure(bg="lightblue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.columns = [
            "No", "Date", "Receipt No", "Product Code", "Product Name",
            "Unit Price", "Qty", "Refund", "Tagged By", "Authorized By",
            "Posted"
        ]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.bottom_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.del_frame = tk.Frame(self.bottom_frame, bg="lightblue")
        self.filter_cb = ttk.Combobox(
            self.bottom_frame, values=["Tagged", "Authorized", "Rejected"],
            state="readonly", font=("Arial", 12), width=10
        )
        self.filter_cb.current(0)
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()

        self.build_ui()
        self.load_data()

    def build_ui(self):
        """Builds the User Interface of the window."""
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        title_label = "Sales Reversal Authorization And Posting."
        tk.Label(
            self.main_frame, text=title_label, bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline")
        ).pack(anchor="center", pady=(3, 0))
        button_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="flat"
        )
        button_frame.pack(side="top", fill="x", anchor="s")
        action_btn = [
            ("Authorize", self.authorize_selected),
            ("Reject", self.reject_selected),
            ("Post", self.post_selected)
        ]
        for text, command in action_btn:
            tk.Button(
                button_frame, text=text, command=command, bg="blue",
                fg="white", bd=4, relief="groove", font=("Arial", 10, "bold")
            ).pack(side="left", anchor="s")
        tk.Button(
            button_frame, text="Reversal Logs", command=self.view_logs,
            bd=4, relief="groove", bg="dodgerblue", fg="white",
            font=("Arial", 10, "bold")
        ).pack(side="right", anchor="s")
        # Table Frame
        self.table_frame.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        # Bottom Frame
        self.bottom_frame.pack(side="bottom", fill="x")
        self.bottom_frame.configure(height=50)
        tk.Label(
            self.bottom_frame, text="Select View:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(10, 0))
        self.filter_cb.pack(side="left", padx=(0, 10))
        self.filter_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.load_data()
        )
        self.del_frame.pack(side="right", padx=10)
        tk.Label(
            self.del_frame, text="Select Reversal to Delete:", bg="lightblue",
            font=("Arial", 11, "italic"), fg="blue"
        ).pack(side="left")
        tk.Button(
            self.del_frame, text="Delete Reversal", bg="red", fg="blue",
            bd=4, relief="ridge", command=self.delete_reversal,
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=0)

    def load_data(self):
        """Fetch and display reversals."""
        # Clear table
        selected = self.filter_cb.get()
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Map filter text to function parameter
        if selected == "Rejected":
            self.del_frame.pack(side="right", padx=10)
        else:
            self.del_frame.pack_forget()

        rows, error = fetch_pending_reversals(self.conn, selected)
        if error:
            messagebox.showerror("Error", error, parent=self.window)
            return
        # Insert into table
        for i, row in enumerate(rows, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                row["date"].strftime("%d/%m/%Y"),
                row["receipt_no"],
                row["product_code"],
                row["product_name"],
                f"{row["unit_price"]:,.2f}",
                row["quantity"],
                f"{row["refund"]:,.2f}",
                row["tag"],
                row["authorized"] if row["authorized"] is not None else "",
                row["posted"] if row["posted"] is not None else "",
            ), tags=(tag,))
        self.sorter.autosize_columns()

    def has_privilege(self, privilege: str) -> bool:
        """Check if the current user has the required privilege."""
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You do not have permission to {privilege}.",
                parent=self.window
            )
            return False
        return True

    def view_logs(self):
        """Opens Logs window."""
        # Verify user privilege
        if not self.has_privilege("View Sales Records"):
            return
        MonthlyReversalLogs(self.window, self.conn, self.user)

    def authorize_selected(self):
        """Authorize the selected reversal if user is not the tagger."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "No Selection",
                "Please Select a Row to Authorize.", parent=self.window
            )
            return
        values = self.tree.item(selected_item[0], "values")
        tagged_by = values[8]
        receipt = values[2]
        code = values[3]
        if tagged_by == self.user:
            messagebox.showwarning(
                "Not Allowed",
                "You Can't Authorize Tag You Prepared.", parent=self.window
            )
            return
        # Verify user privilege
        if not self.has_privilege("Authorize Reversal"):
            return
        # Call authorize here
        success, msg = authorize_reversal(self.conn, receipt, code, self.user)
        if success:
            messagebox.showinfo("Success", msg, parent=self.window)
            self.load_data()
        else:
            messagebox.showerror("Error", msg, parent=self.window)

    def reject_selected(self):
        """Reject the selected reversal if user is not the tagger."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "No Selection",
                "Please Select a Row To Reject.", parent=self.window
            )
            return
        values = self.tree.item(selected_item[0], "values")
        receipt_no = values[2]
        product_code = values[3]
        tagged_by = values[8]
        if tagged_by == self.user:
            messagebox.showwarning(
                "Not Allowed",
                "You Can't Reject Tag You Prepared.", parent=self.window
            )
            return
        # Verify user privilege
        if not self.has_privilege("Authorize Reversal"):
            return
        # Call Function to Reject
        success, msg = reject_tagged_reversal(
            self.conn, receipt_no, product_code, self.user
        )
        if success:
            messagebox.showinfo("Success", msg, parent=self.window)
            self.load_data()
        else:
            messagebox.showerror("Error", msg, parent=self.window)

    def post_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "No Selection",
                "Please select a row to Delete.", parent=self.window
            )
            return
        values = self.tree.item(selected_item[0], "values")
        authorization = values[9]
        receipt = values[2]
        code = values[3]
        price = float(values[5].replace(",", ""))
        qty = int(values[6])
        if authorization == self.user:
            messagebox.showwarning(
                "Not Allowed",
                "You Can't Post Reversal You Authorized.", parent=self.window
            )
            return
        # Verify user privilege
        if not self.has_privilege("Post Reversal"):
            return
        # Call Function to Reject
        success, msg = post_reversal(
            self.conn, receipt, code, self.user, qty, price
        )
        # post_reversal(conn, receipt, code, user, qty, price)
        if success:
            messagebox.showinfo("Success", msg, parent=self.window)
            self.load_data()
        else:
            messagebox.showerror("Error", msg, parent=self.window)

    def delete_reversal(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "No Selection",
                "Please select a row to Delete.", parent=self.window
            )
            return
        values = self.tree.item(selected_item[0], "values")
        tagged_by = values[8]
        receipt = values[2]
        code = values[3]
        if tagged_by != self.user:
            messagebox.showwarning(
                "Not Allowed",
                "You Can't Delete Tag You Didn't Prepare.",
                parent=self.window
            )
            return
        # Verify user privilege
        if not self.has_privilege("Tag Reversal"):
            return
        # Call Function to Reject
        success, msg = delete_rejected_reversal(
            self.conn, receipt, code, self.user
        )
        if success:
            messagebox.showinfo("Success", msg, parent=self.window)
            self.load_data()
        else:
            messagebox.showerror("Error", msg, parent=self.window)


class CashierReturnTreasury(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.configure(bg="lightblue")
        self.window.title("Return To Treasury")
        self.center_window(self.window, 250, 280, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.cashier_var = tk.StringVar()
        self.balance_var = tk.StringVar()
        self.amount = tk.StringVar()
        self.control = CashierControl(conn, user)
        style = ttk.Style(self.window)
        style.theme_use("clam")
        success, users = fetch_cashier_control_users(conn)
        if not success:
            messagebox.showerror("Error", users, parent=self.window)
        else:
            self.cashiers = users
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.bal_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.cash_entry = tk.Entry(
            self.bal_frame, textvariable=self.amount, width=10, bd=4,
            relief="raised", font=("Arial", 12)
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        l_text = "Return To Treasury."
        tk.Label(
            self.main_frame, text=l_text, bg="lightblue", fg="blue",
            font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="center", pady=(5, 0), ipadx=5)
        top_frame = tk.Frame(self.main_frame, bg="lightblue")
        top_frame.pack(fill="x")
        tk.Label(
            top_frame, text="Cashier Username:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(anchor="s", pady=(5, 0))
        user_cb = ttk.Combobox(
            top_frame, textvariable=self.cashier_var, values=self.cashiers,
            font=("Arial", 12), width=10, state="readonly"
        )
        user_cb.pack(pady=(0, 5), anchor="n")
        user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_net_sales())
        self.bal_frame.pack(fill="both", expand=True)
        bal_frame = tk.Frame(self.bal_frame, bg="lightblue")
        bal_frame.pack(fill="x")
        tk.Label(
            bal_frame, text="Net Sales:", bg="lightblue", fg="blue",
            font=("Arial", 12, "bold")
        ).pack(side="left", pady=5, padx=(10, 0))
        bal_entry = tk.Entry(
            bal_frame, textvariable=self.balance_var, fg="blue", bd=4,
            width=10, relief="raised", font=("Arial", 12, "bold")
        )
        bal_entry.pack(side="left", pady=5, padx=(0, 5))
        CurrencyFormatter.add_currency_trace(self.balance_var, bal_entry)
        tk.Label(
            self.bal_frame, text="Cash Returned:", bg="lightblue", fg="blue",
            font=("Arial", 12, "bold")
        ).pack(pady=(5, 0), anchor="s")
        self.cash_entry.pack(pady=(0, 5), anchor="n")
        CurrencyFormatter.add_currency_trace(self.amount, self.cash_entry)
        self.cash_entry.bind("<Return>", lambda e: self.post_return())
        tk.Button(
            self.bal_frame, text="Post Cash", bg="blue", fg="white", bd=4,
            relief="groove", font=("Arial", 11, "bold"),
            command=self.post_return
        ).pack(anchor="center", pady=5)

    def has_privilege(self, username, privilege: str) -> bool:
        """Check if the current user has the required privilege."""
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, username, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Denied", f"You Don't Have Permission to {privilege}.",
                parent=self.window
            )
            return False
        return True

    def load_net_sales(self):
        cashier = self.cashier_var.get().strip()
        if not self.has_privilege(cashier, "Make Sale"):
            return
        success, result = get_net_sales(self.conn, cashier)
        if not success:
            messagebox.showerror("Error", result, parent=self.window)
            return
        bal = str(int(result["net_sales"]))
        self.balance_var.set(bal)
        self.cash_entry.focus_set()

    def post_return(self):
        cash = self.amount.get().replace(",", "")
        if not cash:
            messagebox.showwarning(
                "Invalid", "Please Enter Valid Amount to Returned.",
                parent=self.window
            )
            return
        cash_returned = float(cash)
        net_sale = float(self.balance_var.get().replace(",", ""))
        balance = net_sale - cash_returned
        if not self.has_privilege(self.user, "Manage Cashiers"):
            return
        cashier = self.cashier_var.get().strip()
        details = {
            "cashier": cashier,
            "amount": cash_returned,
            "balance": balance
        }
        confirmation = messagebox.askyesno(
            "Confirm",
            f"Post Receipt of Ksh.{cash_returned} From {cashier}?",
            parent=self.window
        )
        if confirmation:
            success, msg = self.control.return_to_treasury(details)
            if success:
                messagebox.showinfo("Success", msg, parent=self.window)
                self.balance_var.set("")
                self.amount.set("")
            else:
                messagebox.showerror("Error", msg, parent=self.window)


class CashierEndDay(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.configure(bg="lightblue")
        self.window.title("Cashier End of Day")
        self.center_window(self.window, 350, 600, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.cashier_var = tk.StringVar()
        self.net_sale_var = tk.StringVar()
        self.bal_var = tk.StringVar(value="0")
        self.control = CashierControl(conn, user)
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.denominations = [1000, 500, 200, 100, 50, 20, 10, 5, 1]
        self.note_vars = {}
        self.total_vars = {}
        self.total_entries = {}
        self.entry_order = []
        self.grand_total_var = tk.StringVar(value="0")
        success, users = fetch_cashier_control_users(conn)
        if not success:
            messagebox.showerror("Error", users, parent=self.window)
        else:
            self.cashiers = users
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.bal_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="flat"
        )
        self.cashier_label = tk.Label(
            self.bal_frame, text="", bg="lightblue", fg="blue",
            font=("Arial", 12, "bold", "underline")
        )


        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        l_text = "Cashier End of Day."
        tk.Label(
            self.main_frame, text=l_text, bg="lightblue", fg="blue",
            font=("Arial", 18, "bold", "underline")
        ).pack(side="top", anchor="center", pady=(5, 0), ipadx=5)
        top_frame = tk.Frame(self.main_frame, bg="lightblue")
        top_frame.pack(fill="x")
        tk.Label(
            top_frame, text="Cashier Username:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(10, 0), pady=5)
        user_cb = ttk.Combobox(
            top_frame, textvariable=self.cashier_var, values=self.cashiers,
            font=("Arial", 12), width=10, state="readonly"
        )
        user_cb.pack(side="left", pady=5, padx=(0, 10))
        user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_net_sales())
        self.bal_frame.pack(fill="both", expand=True)
        self.cashier_label.pack(anchor="center", padx=5, pady=(5, 0))
        bal_frame = tk.Frame(self.bal_frame, bg="lightblue")
        bal_frame.pack(padx=10)
        tk.Label(
            bal_frame, text="Net Sales:", bg="lightblue", fg="blue",
            font=("Arial", 12, "bold")
        ).pack(side="left")
        bal_entry = tk.Entry(
            bal_frame, textvariable=self.net_sale_var, fg="blue", bd=2,
            width=10, relief="raised", font=("Arial", 11, "bold")
        )
        bal_entry.pack(side="left")
        CurrencyFormatter.add_currency_trace(self.net_sale_var, bal_entry)
        denom_frame = tk.LabelFrame(
            self.bal_frame, text="Cash Breakdown", bg="lightblue", bd=2,
            relief="ridge", font=("Arial", 10, "bold"), fg="blue"
        )
        denom_frame.pack(fill="x", pady=5)
        tk.Label(
            denom_frame, text="Denomination", bg="lightblue",
            font=("Arial", 12, "bold", "underline")
        ).grid(row=0, column=0, sticky="w", padx=(5, 0))
        tk.Label(
            denom_frame, text="Pieces", bg="lightblue", width=6,
            font=("Arial", 12, "bold", "underline"), anchor="w"
        ).grid(row=0, column=1, sticky="w", padx=5)
        tk.Label(
            denom_frame, text="Total", bg="lightblue",
            font=("Arial", 12, "bold", "underline")
        ).grid(row=0, column=2, sticky="e", padx=5)
        for row, value in enumerate(self.denominations, start=1):
            qty_var = tk.StringVar(value="0")
            total_var = tk.StringVar(value="0.00")

            self.note_vars[value] = qty_var
            self.total_vars[value] = total_var
            tk.Label(
                denom_frame, text=f"Ksh. {value}:", bg="lightblue",
                fg="blue", font=("Arial", 11, "bold")
            ).grid(row=row, column=0, pady=3, sticky="e")
            qty_entry = tk.Entry(
                denom_frame, textvariable=qty_var, width=5, bd=2,
                font=("Arial", 11)
            )
            qty_entry.grid(row=row, column=1, pady=3, sticky="w")
            self.entry_order.append(qty_entry)
            total_entry = tk.Entry(
                denom_frame, textvariable=total_var, width=9, bd=2,
                justify="right", state="readonly", font=("Arial", 11)
            )
            total_entry.grid(row=row, column=2, pady=3, padx=5)
            self.total_entries[value] = total_entry
            qty_var.trace_add(
                "write",
                lambda name, index, mode, v=value: self.update_denom_total(v)
            )
            CurrencyFormatter.add_currency_trace(
                total_var, total_entry
            )
        total_frame = tk.Frame(self.bal_frame, bg="lightblue")
        total_frame.pack(padx=10, pady=5)
        tk.Label(
            total_frame, text="Total Cash:", bg="lightblue", justify="right",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, padx=(10, 0), pady=2)
        total_entry = tk.Entry(
            total_frame, textvariable=self.grand_total_var, width=10, bd=2,
            font=("Arial", 12, "bold"), justify="right", state="readonly"
        )
        total_entry.grid(row=0, column=1, padx=(0, 10), pady=2)
        CurrencyFormatter.add_currency_trace(
            self.grand_total_var, total_entry
        )
        tk.Label(
            total_frame, text="Balance:", bg="lightblue", fg="red",
            font=("Arial", 12, "bold")
        ).grid(row=1, column=0, padx=(10, 0), pady=2, sticky="e")
        balance_entry = tk.Entry(
            total_frame, textvariable=self.bal_var, width=10, fg="red", bd=2,
            font=("Arial", 12, "bold"), justify="right", state="readonly"
        )
        balance_entry.grid(row=1, column=1, padx=(0, 10), pady=2, sticky="w")
        CurrencyFormatter.add_currency_trace(
            self.bal_var, balance_entry
        )
        tk.Button(
            self.bal_frame, text="End Day", bg="blue", fg="white", bd=4,
            relief="groove", font=("Arial", 11, "bold"),
            command=self.post_return
        ).pack(anchor="center", pady=5, ipadx=5)
        FocusChain(self.entry_order, self.post_return)

    def on_qty_change(self, value):
        self.update_denom_total(value)

    def update_denom_total(self, value):
        try:
            qty = int(self.note_vars[value].get())
        except ValueError:
            qty = 0
        total = qty * value
        self.total_vars[value].set(total)
        self.update_grand_total()

    def update_grand_total(self):
        total = 0
        for value in self.denominations:
            try:
                amount = int(self.total_vars[value].get().replace(",", ""))
            except ValueError:
                amount = 0
            total += amount
        net_sale = int(self.net_sale_var.get().replace(",", ""))
        if total > net_sale:
            messagebox.showwarning(
                "Warning", "Cash to Return Exceeds Cash Required.",
                parent=self.window
            )
        balance = net_sale - total
        self.grand_total_var.set(total)
        self.bal_var.set(balance)


    def load_net_sales(self):
        cashier = self.cashier_var.get().strip()
        success, result = get_net_sales(self.conn, cashier)
        if not success:
            messagebox.showerror("Error", result, parent=self.window)
            return
        bal = str(int(result["net_sales"]))
        self.net_sale_var.set(bal)
        self.bal_var.set(bal)
        self.cashier_label.configure(text=f"Net Sales For {cashier.title()}.")
        if self.entry_order:
            self.entry_order[0].focus_set()
            self.entry_order[0].selection_range(0, tk.END)
            self.entry_order[0].icursor(tk.END)

    def post_return(self):
        cash = self.grand_total_var.get().replace(",", "")
        if not cash:
            messagebox.showwarning(
                "Invalid", "Please Enter Valid Amount to Return.",
                parent=self.window
            )
            return
        cash_returned = float(cash)
        # net_sale = float(self.net_sale_var.get().replace(",", ""))
        balance = float(self.bal_var.get().replace(",", ""))
        privilege = "Manage Cashiers"
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Denied", f"You Don't Have Permission to {privilege}.",
                parent=self.window
            )
            return
        cashier = self.cashier_var.get().strip()
        details = {
            "cashier": cashier,
            "amount": cash_returned,
            "balance": balance
        }
        confirmation = messagebox.askyesno(
            "Confirm",
            f"Post Receipt of Ksh.{cash_returned:,.2f} From {cashier}.\n"
            f"With a Balance of {balance:,.2f}",
            parent=self.window
        )
        if confirmation:
            success, msg = self.control.end_transaction_day(details)
            if success:
                messagebox.showinfo("Success", msg, parent=self.window)
                for value in self.denominations:
                    self.note_vars[value].set("0")
                    self.total_vars[value].set("0")
                self.net_sale_var.set("0")
                self.grand_total_var.set("0")
                self.bal_var.set("0")
            else:
                messagebox.showerror("Error", msg, parent=self.window)
