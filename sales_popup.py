import re
import calendar
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import tkinter.font as tkFont
from datetime import date
from base_window import BaseWindow
from analysis_gui_graph import LineAnalysisWindow
from analysis_gui_pie import AnalysisWindow
from accounting_export import ReportExporter
from receipt_gui_and_print import ReceiptViewer
from authentication import VerifyPrivilegePopup
from log_popups_gui import MonthlyReversalLogs
from working_sales import (
    fetch_sales_last_24_hours, fetch_sale_by_year,
    fetch_sales_summary_by_year, tag_reversal,
    get_retail_price, fetch_pending_reversals,
    reject_tagged_reversal, delete_rejected_reversal, authorize_reversal,
    fetch_filter_values, fetch_sales_by_month_and_user,
    fetch_all_sales_users, fetch_sales_items, post_reversal
)


class Last24HoursSalesWindow(BaseWindow):
    def __init__(self, parent, conn, username):
        self.window = tk.Toplevel(parent)
        self.window.title("Last 24 Hours Sales Logs")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 800, 650, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = username
        style = ttk.Style(self.window)
        style.theme_use("alt")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 10))
        self.columns = ("No", "Date", "Time", "Receipt No", "Amount")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        # Table frame
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.load_data()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Header Frame
        header_frame = tk.Frame(self.main_frame, bg="lightblue")
        header_frame.pack(fill="x", padx=10)
        label_txt = f"Last 24 Hours Sales For {self.user.capitalize()}."
        tk.Label(
            header_frame, text=label_txt, bg="lightblue", bd=4,
            relief="ridge", font=("Arial", 15, "bold", "underline")
        ).pack(side="left", padx=10, ipadx=10)
        tk.Button(
            header_frame, text="Print Receipt", command=self.print_receipt,
            bd=4, relief="groove"
        ).pack(side="right", anchor="e")
        self.table_frame.pack(fill="both", expand=True)
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        # Treeview setup
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)
        # Mousewheel scroll binding
        # Windows and Linux
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            -1 * int(e.delta / 120), "units"
        ))
        # MacOS
        self.tree.bind("<Button-4>", lambda e: self.tree.yview_scroll(
            -1, "units"
        ))
        self.tree.bind("<Button-5>", lambda e: self.tree.yview_scroll(
            1, "units"
        ))


    def print_receipt(self):
        selected = self.tree.selection()
        if selected:
            receipt_no = self.tree.item(selected[0])["values"][3]
            # Call your receipt printing function here
            ReceiptViewer(self.window, self.conn, receipt_no, self.user)
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
        for i, row in enumerate(data, start=1):
            self.tree.insert("", "end", values=(
                i,
                row["sale_date"].strftime("%d/%m/%Y"),
                row["sale_time"],
                row["receipt_no"],
                f"{row['total_amount']:,.2f}"
            ))
        self.autosize_columns()

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            # Start with the column header width
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            # Add Padding for readability
            self.tree.column(col, width=max_width + 5)


class MonthlySalesSummary(BaseWindow):
    def __init__(self, parent, conn):
        self.window = tk.Toplevel(parent)
        self.window.title("Monthly Sales Summary")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 900, 650, parent)
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
        # self.month_var = tk.BooleanVar()
        self.user_var = tk.BooleanVar()
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
        self.columns = ("No", "Date", "Amount", "Running Balance")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.top_frame, width=8, values=self.years, state="readonly"
        )
        self.title_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.title_label = tk.Label(
            self.title_frame, text="Monthly Sales Summary.", bg="lightblue",
            font=("Arial", 15, "bold", "underline"), bd=2, relief="ridge"
        )
        # Filters combobox
        self.month_cb = ttk.Combobox(
            self.top_frame, values=[name for name, _num in self.months],
            width=10, font=("Arial", 11)
        )
        self.month_cb.set(current_month_name)
        self.user_cb = ttk.Combobox(
            self.top_frame, width=10, state="disabled", values=self.users,
            font=("Arial", 11)
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        style = ttk.Style(self.window)
        style.theme_use("classic")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", rowheight=25, font=("Arial", 10))
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.setup_widgets()
        self.load_users()
        self.load_data()

    def setup_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.title_frame.pack(fill="x", pady=(5, 0), padx=5)
        self.title_label.pack(anchor="center", ipadx=5)
        self.top_frame.pack(fill="x", pady=(5, 0), padx=5)
        tk.Label(
            self.top_frame, text="Select Sales Year:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.year_cb.current(0)
        self.year_cb.pack(side="left", padx=(0, 5))
        tk.Label(
            self.top_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 5))
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Checkbutton(
            self.top_frame, text="Sort by User", variable=self.user_var,
            bg="lightblue", command=self.toggle_filters,
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=5)
        tk.Label(
            self.top_frame, text="Select User:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(3, 0))
        self.user_cb.pack(side="left", padx=(0, 5))
        tk.Checkbutton(
            self.top_frame, text="Show All", variable=self.show_all_var,
            bg="lightblue", command=self.toggle_show_all,
            font=("Arial", 11, "bold")
        ).pack(side="left")
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
            self.tree.column(col, anchor="center", width=50)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Windows/Linux
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            -1 * int(e.delta / 120), "units"
        ))
        self.tree.bind("Button-4", lambda e: self.tree.yview_scroll(
            -1, "units"
        ))  # macOS
        self.tree.bind("Button-5", lambda e: self.tree.yview_scroll(
            1, "units"
        ))
        self.tree.tag_configure(
            "summary", font=("Arial", 12, "bold", "underline")
        )

    def toggle_show_all(self):
        """Handle logic for show all checkbox."""
        if self.show_all_var.get():
            # If Show all is checked, uncheck month and user filters
            self.user_var.set(False)
            self.toggle_filters()  # disable combo boxes
        self.load_data()  # Refresh table

    def toggle_filters(self):
        """Enable/Disable combo boxes based on checkboxes."""
        # If Show All is checked, force disable filters
        if self.show_all_var.get():
            self.user_cb.configure(state="disabled")
            return
        self.user_cb.configure(
            state="readonly" if self.user_var.get() else "disabled"
        )
        self.load_data()

    def load_users(self):
        try:
            users = fetch_all_sales_users(self.conn)  # Returns a list of usernames
            self.user_cb["values"] = users
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to load users: {str(e)}.",
                parent=self.window
            )

    def load_data(self):
        user = None
        month = dict(self.months).get(self.month_cb.get())
        year = self.year_cb.get()
        txt = f"Sales Summary In Month of {self.month_cb.get()}"
        if not self.show_all_var.get():
            if self.user_var.get() and self.user_cb.get():
                user = self.user_cb.get()
                txt += f" For {user.capitalize()}"
        txt += "."
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
            amount = float(row["daily_total"])
            running_total += amount
            self.tree.insert("", "end", values=(
                i,
                row["sale_date"].strftime("%d/%m/%Y"),
                f"{amount:,.2f}",
                f"{running_total:,.2f}"
            ))
        if data:
            self.tree.insert("", "end", values=(
                "", "Total Sales", "", f"{running_total:,.2f}"
            ), tags=("summary",))
        self.autosize_columns()

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                val = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(val))
            self.tree.column(col, width=max_width + 5)


class YearlySalesWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Yearly Cumulative Sales")
        self.center_window(self.master, 1000, 700, parent)
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
            "No", "Date", "Receipt No", "User", "Total Amount",
            "Cumulative Total"
        ]
        # Bold headings
        style = ttk.Style()
        style.theme_use("alt")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", rowheight=25, font=("Arial", 10))
        # Variables for checkboxes
        self.month_var = tk.BooleanVar()
        self.user_var = tk.BooleanVar()
        self.show_all_var = tk.BooleanVar()
        # Frames
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.filter_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.year_cb = ttk.Combobox(
            self.top_frame, width=5, values=self.years, state="readonly",
            font=("Arial", 11)
        )
        # Filters combobox
        self.month_cb = ttk.Combobox(
            self.filter_frame, width=10, state="disabled",
            values=[name for name, _num in self.months], font=("Arial", 11)
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, width=10, state="disabled", values=self.users,
            font=("Arial", 11)
        )
        # Title Label
        label_text = f"Cumulative Sales for Year {self.year_cb.get()}"
        self.title_label = tk.Label(
            self.top_frame, bg="lightblue", text=label_text, bd=4,
            relief="ridge", font=("Arial", 14, "bold", "underline")
        )
        # Table
        self.product_table = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.top_frame.pack(side="top", fill="x", pady=(5, 0))
        self.title_label.pack(side="left", ipadx=10)
        tk.Label(
            self.top_frame, text="Select Sales Year:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.year_cb.set(self.years[0])
        self.year_cb.pack(side="left", padx=(0, 5))
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        # Checkboxes Frame
        check_box = tk.Frame(
            self.top_frame, bg="lightblue", bd=2, relief="ridge"
        )
        check_box.pack(side="left")
        tk.Label(
            check_box, text="Sort By:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
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
        # Filter frame
        self.filter_frame.pack(fill="x", ipady=5)
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 5))
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.filter_frame, text="Select User:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.user_cb.pack(side="left", padx=(0, 5))
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        btn_frame = tk.Frame(self.filter_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=5)
        btns = {
            "View Receipt": self.print_receipt,
            "View Graph": self.open_line_analysis,
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
        }
        for text, command in btns.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="groove",
                bg="dodgerblue", fg="white", font=("Arial", 9, "bold")
            ).pack(side="left")
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
        self.product_table.bind(
            "<MouseWheel>",
            lambda e: self.product_table.yview_scroll(-1 * int(e.delta / 120), "units"),
        )
        self.product_table.bind(
            "Button-4", lambda e: self.product_table.yview_scroll(-1, "units")
        )  # macOS
        self.product_table.bind(
            "Button-5", lambda e: self.product_table.yview_scroll(1, "units")
        )
        self.product_table.tag_configure(
            "total", font=("Arial", 12, "bold", "underline")
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
        self.user_cb.configure(state="readonly" if self.user_var.get() else "disabled")
        self.load_data()

    def load_data(self):
        """Load sales data based on current year only (initial)."""
        self.product_table.delete(*self.product_table.get_children())
        year = int(self.year_cb.get())
        # Filters
        month = None
        user = None
        # Only apply filters if show all is unchecked
        if not self.show_all_var.get():
            if self.month_var.get() and self.month_cb.get():
                month = dict(self.months).get(self.month_cb.get())
            if self.user_var.get() and self.user_cb.get():
                user = self.user_cb.get()
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
        self.title_label.configure(text=f"Cumulative Sales for Year {year}.")
        self._resize_columns()

    def print_receipt(self):
        selected = self.product_table.selection()
        if selected:
            receipt_no = self.product_table.item(selected[0])["values"][2]
            # Call your receipt printing function here
            ReceiptViewer(self.master, self.conn, receipt_no, self.user)
        else:
            messagebox.showwarning(
                "Info", "Please select a sale to print its receipt.",
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
                "Error", f"Failed to fetch Sales:\n{err}.",
                parent=self.master
            )
            return
        if not rows:
            messagebox.showerror(
                "No Data", "No sales data found for the selected filter(s)",
                parent=self.master
            )
            return
        cumulative_total = 0
        for r in rows:
            cumulative_total += r["total_amount"]
            r["cumulative"] = cumulative_total
        metrics = {
            "Total Amount": lambda r: r["total_amount"],
            "Cumulative Total": lambda r: r["cumulative"],
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
                    "Date": vals[1],
                    "Receipt No": vals[2],
                    "User": vals[3],
                    "Total Amount": vals[4],
                    "Cumulative Total": vals[5],
                }
            )
        return rows

    def _make_exporter(self):
        year = self.year_cb.get()
        title = f"Cumulative Sales for Year {year}."
        columns = [
            "No",
            "Date",
            "Receipt No",
            "User",
            "Total Amount",
            "Cumulative Total",
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

    def _resize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.product_table.get_children():
                val = str(self.product_table.set(item, col))
                max_width = max(max_width, font.measure(val))
            self.product_table.column(col, width=max_width)


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
            "No", "Product Code", "Product Name", "Quantity", "Unit Cost",
            "Total Cost", "EST. Unit Price", "Total Amount", "Total Profit"
        ]
        # Variables for checkboxes
        self.month_var = tk.BooleanVar()
        self.user_var = tk.BooleanVar()
        self.show_all_var = tk.BooleanVar()
        # Bold headings
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        # Frames
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.filter_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.filter_frame, width=5, values=self.years, state="readonly",
            font=("Arial", 11)
        )
        # Filters combobox
        self.month_cb = ttk.Combobox(
            self.filter_frame, width=12, state="disabled",
            font=("Arial", 11), values=[name for name, _num in self.months],
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, width=10, state="disabled", values=self.users,
            font=("Arial", 11)
        )
        # Title Label
        self.title = "Products Sales Performance"
        self.title_label = tk.Label(
            self.top_frame, bg="blue", fg="white", text=self.title,
            font=("Arial", 14, "bold"), bd=2, relief="ridge"
        )
        # Table Frame
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.product_table = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Fixed Part
        self.top_frame.pack(side="top", fill="x", padx=5, pady=(5, 2))
        self.filter_frame.pack(fill="x", padx=5)
        self.table_frame.pack(fill="both", expand=True)
        self.title_label.pack(side="left", padx=10, ipadx=5)
        check_frame = tk.Frame(
            self.top_frame, bg="lightblue", bd=4, relief="groove"
        )
        check_frame.pack(side="left", padx=10)
        tk.Label(
            check_frame, text="Sort Sales By:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(15, 0))
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
            self.filter_frame, text="Select Sales Year:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(10, 0))
        self.year_cb.set(self.years[0])
        self.year_cb.pack(side="left", padx=(0, 15))
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 15))
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.filter_frame, text="Select User:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(15, 0))
        self.user_cb.pack(side="left", padx=(0, 15))
        btn_frame = tk.Frame(self.filter_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=5)
        btns = {
            "Analysis Charts": self.view_analysis_charts,
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
        }
        for text, command in btns.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="groove",
                bg="dodgerblue", fg="white",
            ).pack(side="left")
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())

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
        self.product_table.bind(
            "<MouseWheel>",
            lambda e: self.product_table.yview_scroll(-1 * int(e.delta / 120), "units"),
        )
        self.product_table.bind(
            "Button-4", lambda e: self.product_table.yview_scroll(-1, "units")
        )  # macOS
        self.product_table.bind(
            "Button-5", lambda e: self.product_table.yview_scroll(1, "units")
        )
        self.product_table.tag_configure(
            "total", font=("Arial", 12, "bold", "underline")
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
        self.user_cb.configure(state="readonly" if self.user_var.get() else "disabled")
        self.load_data()

    def load_data(self):
        """Load sales data based on current year only (initial)."""
        self.product_table.delete(*self.product_table.get_children())
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
                "Product Code": row["product_code"],
                "Product Name": name,
                "Quantity": row["total_quantity"],
                "Unit Cost": f"{row["unit_cost"]:,.2f}",
                "Total Cost": f"{total_cost:,.2f}",
                "EST. Unit Price": f"{est_unit_price:,.2f}",
                "Total Amount": f"{row["total_amount"]:,.2f}",
                "Total Profit": f"{total_profit:,.2f}",
            }
            self.rows.append(precessed_row)
            self.product_table.insert(
                "", "end", values=list(precessed_row.values()), tags=(tag,)
            )
            # Update totals
            total_qty += float(row["total_quantity"])
            total_cost_sum += total_cost
            total_amount_sum += float(row["total_amount"])
            total_profit_sum += total_profit
        if rows:
            # Compute weighted averages for costs and prices
            avg_unit_cost = total_cost_sum / total_qty if total_qty else 0
            avg_unit_price = total_amount_sum / total_qty if total_qty else 0
            self.product_table.insert("", "end", values=(
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
        self._resize_columns()

    def _resize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.product_table.get_children():
                val = str(self.product_table.set(item, col))
                max_width = max(max_width, font.measure(val))
            self.product_table.column(col, width=max_width + 10)

    def view_analysis_charts(self):
        """Open analysis window with pie/ bar for current rows."""
        if not self.rows:
            messagebox.showinfo(
                "Data", "No Sales data to Analyze.", parent=self.master
            )
            return

        metrics = {
            "Quantity": lambda r: float(r["Quantity"]) if r["Quantity"] else 0,
            "Total Amount Sold": lambda r: (float(
                r["Total Amount"].replace(",", "")
            ) if r["Total Amount"] else 0),
            "Total Profit": lambda r: (float(
                r["Total Profit"].replace(",", "")
            ) if r["Total Profit"] else 0),
        }
        AnalysisWindow(
            self.master, self.title, self.rows, metrics, "Product Name"
        )

    def _collect_rows(self):
        rows = []
        for item in self.product_table.get_children():
            vals = self.product_table.item(item, "values")
            rows.append(
                {
                    "No": vals[0],
                    "Product Code": vals[1],
                    "Product Name": vals[2],
                    "Quantity": vals[3],
                    "Unit Cost": vals[4],
                    "Total Cost": vals[5],
                    "EST. Unit Price": vals[6],
                    "Total Amount": vals[7],
                    "Total Profit": vals[8],
                }
            )
        return rows

    def _make_exporter(self):
        title = self.title
        columns = [
            "No", "Product Code", "Product Name", "Quantity", "Unit Cost",
            "Total Cost", "EST. Unit Price", "Total Amount", "Total Profit",
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


class SalesControlReportWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.report_win = tk.Toplevel(parent)
        self.report_win.title("Sales Details And Reversal")
        self.report_win.configure(bg="lightblue")
        self.center_window(self.report_win, 1200, 650, parent)
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
        self.main_frame = tk.Frame(
            self.report_win, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.filter_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.top_frame, width=8, values=self.years, state="readonly",
            font=("Arial", 11)
        )
        self.year_cb.set(self.years[0])
        self.month_cb = ttk.Combobox(
            self.filter_frame, width=12, state="disabled",
            values=[name for name, _num in self.months], font=("Arial", 11)
        )
        self.day_cb = ttk.Combobox(
            self.filter_frame, width=5, state="disabled", font=("Arial", 11)
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, width=15, state="disabled", values=self.users,
            font=("Arial", 11)
        )
        self.search_entry = tk.Entry(
            self.filter_frame, bd=2, relief="raised", font=("Arial", 11),
            width=15
        )
        self.tree = ttk.Treeview(
            self.tree_frame, columns=self.columns, show="headings"
        )
        style = ttk.Style(self.report_win)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", rowheight=25, font=("Arial", 10))

        self.setup_widgets()
        self.load_data()

    def setup_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Title and year selection
        self.top_frame.pack(fill="x", pady=(5, 0))
        tk.Label(
            self.top_frame, text="Sales Details And Reversal", fg="blue",
            font=("Arial", 15, "bold", "underline"), bg="lightblue", bd=4,
            relief="ridge"
        ).pack(side="left", anchor="center", padx=(10, 0), ipadx=5)
        tk.Label(
            self.top_frame, text="Select Sales Year:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(10, 0))
        self.year_cb.pack(side="left", padx=(0, 15))
        self.year_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.load_data()
        )
        # Checkboxes Frame
        check_frame = tk.Frame(
            self.top_frame, bg="lightblue", bd=2, relief="groove"
        )
        check_frame.pack(side="left", padx=10)
        tk.Label(
            check_frame, text="Sort Sales By:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(15, 0))
        # Check buttons for filters
        tk.Checkbutton(
            check_frame, variable=self.month_var, bg="lightblue",
            text="Month", command=self.toggle_filters,
            font=("Arial", 11, "bold"),
        ).pack(side="left")
        tk.Checkbutton(
            check_frame, variable=self.day_var, bg="lightblue", text="Day",
            command=self.toggle_filters, font=("Arial", 11, "bold"),
        ).pack(side="left")
        tk.Checkbutton(
            check_frame, text="User", variable=self.user_var, bg="lightblue",
            command=self.toggle_filters, font=("Arial", 11, "bold"),
        ).pack(side="left")
        tk.Checkbutton(
            check_frame, text="Show All", variable=self.show_all_var,
            bg="lightblue", command=self.toggle_show_all,
            font=("Arial", 11, "bold"),
        ).pack(side="left")
        # Filter Frame
        self.filter_frame.pack(fill="x", padx=5, pady=(5, 0))
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 5))
        self.month_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.update_days()
        )
        tk.Label(
            self.filter_frame, text="Select Day:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.day_cb.pack(side="left", padx=(0, 5))
        self.day_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.filter_frame, text="Select User:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.user_cb.pack(side="left", padx=(0, 5))
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.filter_frame, text="Search By Receipt No:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(10, 0))
        self.search_entry.pack(side="left", padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.filter_by_receipt)
        tk.Button(
            self.filter_frame, text="Tag Reversal", bd=2, relief="ridge",
            command=self.tag_reversal, bg="dodgerblue", fg="white",
        ).pack(side="right", padx=5)
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
        # Windows and Linux
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            -1 * int(e.delta / 120), "units"
        ))
        # MacOS
        self.tree.bind(
            "<Button-4>", lambda e: self.tree.yview_scroll(-1, "units")
        )
        self.tree.bind(
            "<Button-5>", lambda e: self.tree.yview_scroll(1, "units")
        )

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
        self.autosize_columns()

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
        # Verify user privilege
        priv = "Tag Reversal"
        verify_dialog = VerifyPrivilegePopup(
            self.report_win, self.conn, self.user, priv
        )
        if verify_dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.report_win
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

        success, msg = tag_reversal(
            self.conn, receipt, code, name, price, qty, refund, self.user
        )
        if success:
            messagebox.showinfo("Success", msg, parent=self.report_win)
        else:
            messagebox.showerror("Error", msg, parent=self.report_win)

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            # Start with the column header width
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            # Add Padding for readability
            self.tree.column(col, width=max_width)


class SalesReversalWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Sales Reversal Authorization and Posting")
        self.center_window(self.window, 1150, 650, parent)
        self.window.configure(bg="lightblue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.columns = [
            "No", "Date", "Receipt No", "Product Code", "Product Name",
            "Unit Price", "Quantity", "Refund", "Tagged By", "Authorized By",
            "Posted"
        ]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.configure("Treeview", rowheight=20, font=("Arial", 10))
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.bottom_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.del_frame = tk.Frame(
            self.bottom_frame, bg="lightblue", bd=2, relief="groove"
        )
        self.filter_cb = ttk.Combobox(
            self.bottom_frame, values=["Tagged", "Authorized", "Rejected"],
            state="readonly", font=("Arial", 11), width=10
        )
        self.filter_cb.current(0)

        self.build_ui()
        self.load_data()

    def build_ui(self):
        """Builds the User Interface of the window."""
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        button_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="groove"
        )
        button_frame.pack(side="top", fill="x", pady=(5, 0))
        action_btn = [
            ("Authorize", self.authorize_selected),
            ("Reject", self.reject_selected),
            ("Post", self.post_selected)
        ]
        for text, command in action_btn:
            tk.Button(
                button_frame, text=text, command=command, bg="blue",
                fg="white", bd=2, relief="groove", font=("Arial", 10, "bold")
            ).pack(side="left")
        tk.Button(
            button_frame, text="Reversal Logs", command=self.view_logs, bd=2,
            relief="groove", bg="dodgerblue", fg="white"
        ).pack(side="right", padx=10)
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
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(10, 0))
        self.filter_cb.pack(side="left", padx=(0, 10))
        self.filter_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.load_data()
        )
        self.del_frame.pack(side="right", padx=10)
        tk.Label(
            self.del_frame, text="Select Reversal to Delete", bg="lightblue",
            font=("Arial", 11, "italic"), fg="green"
        ).pack(side="left", padx=(5, 0))
        tk.Button(
            self.del_frame, text="Delete Reversal", bg="red", bd=2,
            relief="ridge", command=self.delete_reversal,
        ).pack(side="left", padx=(0, 5))

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
        self.autosize_columns()

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            # Start with the column header width
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            # Add Padding for readability
            self.tree.column(col, width=max_width + 3)

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
                "Please select a row to Reject.", parent=self.window
            )
            return
        values = self.tree.item(selected_item[0], "values")
        receipt_no = values[2]
        product_code = values[3]
        tagged_by = values[8]
        if tagged_by == self.user:
            messagebox.showwarning(
                "Not Allowed",
                "You can't Reject Tag You Prepared.", parent=self.window
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
        success, msg = post_reversal(self.conn, receipt, code, self.user, qty, price)
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
        # Call Function to Reject
        success, msg = delete_rejected_reversal(self.conn, receipt, code, self.user)
        if success:
            messagebox.showinfo("Success", msg, parent=self.window)
            self.load_data()
        else:
            messagebox.showerror("Error", msg, parent=self.window)


