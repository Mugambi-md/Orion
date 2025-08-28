import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
from datetime import date
from base_window import BaseWindow
from receipt_gui_and_print import ReceiptViewer
from working_sales import (
    fetch_sales_control_by_month, fetch_sales_last_24_hours, fetch_sales_by_year,
                           fetch_filter_values, fetch_sales_by_month_and_user, fetch_all_sales_users
)

class SalesControlReportWindow(BaseWindow):
    def __init__(self, parent, conn):
        self.report_win = tk.Toplevel(parent)
        self.report_win.title("Sales Control Report")
        self.report_win.configure(bg="blue")
        self.center_window(self.report_win, 950, 500)
        self.report_win.transient(parent)
        self.report_win.grab_set()

        self.conn = conn
        self.current_year = date.today().year
        self.current_month = date.today().month
        self.title_frame = tk.Frame(self.report_win, bg="blue")
        self.year_var = tk.StringVar(value=str(self.current_year))
        self.years = [str(y) for y in range(self.current_year - 10, self.current_year + 1)]
        self.title_label = tk.Label(self.title_frame, text=f"Monthly Sales Report For {self.current_year}",
                                    font=("Arial", 16, "bold"), bg="blue", fg="white")
        self.month_frame = tk.Frame(self.report_win, bg="blue")
        self.year_combo = ttk.Combobox(self.month_frame, textvariable=self.year_var, values=self.years, state="readonly")
        self.month_var = tk.StringVar(value=f"{self.current_month:02}")
        self.months = [f"{m:02}" for  m in range(1, 13)]
        self.month_combo = ttk.Combobox(self.month_frame, textvariable=self.month_var,
                                        values=self.months, state="readonly")
        style = ttk.Style(self.report_win)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.tree_frame = tk.Frame(self.report_win, bg="blue")
        self.columns = ("No", "Date", "Receipt No", "Description", "User", "Amount", "Cumulative Total")
        self.tree = ttk.Treeview(self.tree_frame, columns=self.columns, show="headings")

        self.setup_widgets()
        self.bind_mousewheel()
        self.load_data()

    def setup_widgets(self):
        # Title and year selection
        self.title_frame.pack(padx=5)
        self.title_label.pack(padx=5)
        tk.Label(self.month_frame, text="Year:", bg="blue", fg="white",
                 font=("Arial", 12)).pack(side="left", padx=(5, 0))
        self.year_combo.pack(side="left", padx=(0, 5))
        self.year_combo.bind("<<ComboboxSelected>>", lambda e: self.update_title_and_data())
        self.month_frame.pack(padx=10)
        tk.Label(self.month_frame, text="Select Month:", bg="blue", fg="white",
                 font=("Arial", 12)).pack(side="left", padx=(5, 0))
        self.month_combo.set(f"{self.current_month:02}")
        self.month_combo.pack(side="left", padx=(0, 5))
        self.month_combo.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def bind_mousewheel(self):
        # Windows and Linux
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(-1 * int(e.delta / 120), "units"))
        # MacOS
        self.tree.bind("<Button-4>", lambda e: self.tree.yview_scroll(-1, "units"))
        self.tree.bind("<Button-5>", lambda e: self.tree.yview_scroll(1, "units"))

    def update_title_and_data(self):
        selected_year = self.year_var.get()
        self.title_label.config(text=f"Monthly Sales Report for {selected_year}.")
        self.load_data()

    def load_data(self):
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
        except ValueError:
            return # Avoid loading if values are invalid
        rows = fetch_sales_control_by_month(self.conn, year, month)
        # Clear previous rows
        self.tree.delete(*self.tree.get_children())
        # Insert new data
        for i, row in enumerate(rows, start=1):
            self.tree.insert("", "end", values=(
                i,
                row["date"],
                row["receipt_no"],
                row["description"],
                row["user"],
                f"{row['amount']:,.2f}",
                f"{row['cumulative_total']:,.2f}"
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

class Last24HoursSalesWindow(BaseWindow):
    def __init__(self, parent, conn, username):
        self.window = tk.Toplevel(parent)
        self.window.title("Last 24 Hours Sales")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 700, 450)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = username
        # Fonts
        header_frame = tk.Frame(self.window, bg="lightblue")
        header_frame.pack(padx=10)
        print_btn = tk.Button(header_frame, text="Print Receipt", command=self.print_receipt)
        print_btn.pack(side="right")
        # Table frame
        table_frame = tk.Frame(self.window, bg="lightblue")
        table_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        # Treeview setup
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.columns = ("No", "Date", "Time", "Receipt No", "Amount")
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings", yscrollcommand=scrollbar.set)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)
        # Mousewheel scroll binding
        self.bind_mousewheel()
        self.load_data()

    def print_receipt(self):
        selected = self.tree.selection()
        if selected:
            receipt_no = self.tree.item(selected[0])["values"][3]
            # Call your receipt printing function here
            ReceiptViewer(self.window, self.conn, receipt_no, self.user)
        else:
            messagebox.showwarning("Info", "Please select a sale to print its receipt.")

    def load_data(self):
        data, error =fetch_sales_last_24_hours(self.conn, self.user)
        if error:
            messagebox.showerror("Error", error)
            return
        # Clear previous data
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Insert data
        for i, row in enumerate(data, start=1):
            self.tree.insert("", "end", values=(
                i,
                row["sale_date"],
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
            self.tree.column(col, width=max_width + 10)
    def bind_mousewheel(self):
        # Windows and Linux
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(-1 * int(e.delta / 120), "units"))
        # MacOS
        self.tree.bind("<Button-4>", lambda e: self.tree.yview_scroll(-1, "units"))
        self.tree.bind("<Button-5>", lambda e: self.tree.yview_scroll(1, "units"))

class MonthlySalesSummary(BaseWindow):
    def __init__(self, parent, conn):
        self.window = tk.Toplevel(parent)
        self.window.title("Monthly Sales Summary")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 1000, 500)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.current_year = date.today().year
        self.current_month = date.today().month
        self.user_var = tk.StringVar()
        self.year_var = tk.StringVar(value=str(self.current_year))
        self.month_var = tk.StringVar(value=f"{self.current_month:02}")
        self.columns = (
            "No", "Date", "Receipt No", "Description", "Amount",
            "Running Balance"
        )
        self.top_frame = tk.Frame(self.window, bg="lightblue")
        self.user_combo = ttk.Combobox(
            self.top_frame, textvariable=self.user_var, state="readonly",
            width=15
        )
        self.year_combo = ttk.Combobox(
            self.top_frame, textvariable=self.year_var, width=5,
            state="readonly", values=[str(y) for y in range(
                self.current_year - 10, self.current_year + 1
            )]
        )
        self.month_combo = ttk.Combobox(
            self.top_frame, textvariable=self.month_var, width=3,
            state="readonly", values=[f"{m:02}" for m in range(1, 13)]
        )
        self.table_frame = tk.Frame(self.window, bg="lightblue")
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.scrollbar = ttk.Scrollbar(self.table_frame)
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings",
            yscrollcommand=self.scrollbar.set
        )

        self.setup_widgets()
        self.load_users()
        self.load_data()

    def setup_widgets(self):
        self.top_frame.pack(fill="x", pady=(5, 0), padx=5)
        tk.Label(self.top_frame, text="User:", bg="lightblue").pack(side="left", padx=(5, 0))
        self.user_combo.pack(side="left", padx=(0, 5))
        tk.Label(self.top_frame, text="Year:", bg="lightblue").pack(side="left", padx=(5, 0))
        self.year_combo.pack(side="left", padx=(0, 5))
        tk.Label(self.top_frame, text="Month:", bg="lightblue").pack(side="left", padx=(5, 0))
        self.month_combo.pack(side="left", padx=(0, 5))
        # Bind selection Changes
        self.user_combo.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        self.year_combo.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        self.month_combo.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        # Table and Scrollbar
        self.table_frame.pack(fill="both", expand=True, padx=(0, 5), pady=5)
        self.scrollbar.pack(side="right", fill="y")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.tree.yview)
        # Windows/Linux
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            -1 * int(e.delta / 120), "units"
        ))
        self.tree.bind(
            "Button-4", lambda e: self.tree.yview_scroll(-1, "units")
        )  # macOS
        self.tree.bind(
            "Button-5", lambda e: self.tree.yview_scroll(1, "units")
        )
        self.tree.tag_configure(
            "summary", font=("Arial", 11, "bold", "underline")
        )

    def load_users(self):
        try:
            users = fetch_all_sales_users(self.conn) # Returns a list of usernames
            self.user_combo['values'] = users
            if users:
                self.user_var.set(users[0])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load users: {str(e)}")

    def load_data(self):
        user = self.user_var.get()
        if not user:
            return
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Invalid year or month.")
            return
        data, error = fetch_sales_by_month_and_user(self.conn, year, month, user)
        # Clear tree
        if error:
            messagebox.showerror("Error", error)
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Insert rows with running balance
        running_total = 0.0
        for i, row in enumerate(data, start=1):
            desc = row["description"].lower()
            amount = float(row["amount"])
            if desc == "sale":
                running_total += amount
            elif desc == "sale reversal":
                running_total -= amount
            self.tree.insert("", "end", values=(
                i,
                row["date"],
                row["receipt_no"] or "-",
                row["description"],
                f"{amount:,.2f}",
                f"{running_total:,.2f}"
            ))
        self.tree.insert("", "end", values=("", "", "", "", "", ""))
        summary_txt = f"Total Monthly Sales For {user.capitalize()}"
        self.tree.insert("", "end", values=(
            "", "", "", summary_txt, "", f"{running_total:,.2f}"
        ), tags=("summary",))
        self.autosize_columns()

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                val = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(val))
            self.tree.column(col, width=max_width + 10)




class YearlySalesWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Yearly Cumulative Sales")
        self.center_window(self.master, 1100, 650, parent)
        self.master.configure(bg="lightblue")
        self.master.transient(parent)
        self.master.grab_set()

        self.conn = conn
        self.user = user
        # Load filter values from DB
        product_names, users, years, err = fetch_filter_values(self.conn)
        if err:
            messagebox.showerror("Error",
                                 f"Failed to fetch filter values:\n{err}")
            self.master.destroy()
            return
        # Data holders for filter options
        self.users = users
        self.product_names = product_names
        self.years = years if years else [date.today().year]
        self.months = [
            ("January", 1), ("February", 2), ("March", 3), ("April", 4), ("May", 5),
            ("June", 6), ("July", 7), ("August", 8), ("September", 9),
            ("October", 10), ("November", 11), ("December", 12)
        ]
        self.columns = [
            "No", "User", "Date", "Receipt No", "Product Code",
            "Product Name", "Quantity", "Unit Price", "Total Amount"
        ]
        # Variables for checkboxes
        self.month_var = tk.BooleanVar()
        self.user_var = tk.BooleanVar()
        self.product_var = tk.BooleanVar()
        # Frames
        self.top_frame = tk.Frame(self.master, bg="lightblue")
        self.filter_frame = tk.Frame(self.master, bg="lightblue")
        self.table_frame = tk.Frame(self.master, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.top_frame, width=8, values=self.years, state="readonly"
        )
        # Filters combobox
        self.month_cb = ttk.Combobox(
            self.filter_frame, width=12, state="disabled",
            values=[name for name, _num in self.months]
        )
        self.product_cb = ttk.Combobox(
            self.filter_frame, width=20, state="disabled",
            values=self.product_names
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, width=15, state="disabled", values=self.users
        )
        # Title Label
        self.title_label = tk.Label(
            self.master, bg="blue", fg="white", font=("Arial", 14, "bold"),
            text=f"Cumulative Sales for Year {self.year_cb.get()}"
        )
        # Table
        self.product_table = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self.top_frame.pack(fill="x", pady=5)
        tk.Label(self.top_frame, text="Select Sales Year:", bg="lightblue"
                 ).pack(side="left", padx=(5, 0))
        self.year_cb.set(self.years[0])
        self.year_cb.pack(side="left", padx=(0, 5))
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(self.top_frame, text="Sort Sales By:", bg="lightblue"
                 ).pack(side="left", padx=(10, 0))
        tk.Checkbutton(
            self.top_frame, text="Month", variable=self.month_var,
            bg="lightblue", command=self.toggle_filters
        ).pack(side="left")
        tk.Checkbutton(
            self.top_frame, text="Product Name", variable=self.product_var,
            bg="lightblue", command=self.toggle_filters
        ).pack(side="left")
        tk.Checkbutton(
            self.top_frame, text="User", variable=self.user_var,
            bg="lightblue", command=self.toggle_filters
        ).pack(side="left")
        # Filter frame
        self.filter_frame.pack(fill="x", pady=3)
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue"
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 5))
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(
            self.filter_frame, text="Select Product Name:", bg="lightblue"
        ).pack(side="left", padx=(5, 0))
        self.product_cb.pack(side="left", padx=(0, 5))
        self.product_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.load_data()
        )
        tk.Label(self.filter_frame, text="Select User:", bg="lightblue"
                 ).pack(side="left", padx=(5, 0))
        self.user_cb.pack(side="left", padx=(0, 5))
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        self.title_label.pack(pady=(5, 0), anchor="center")
        self.table_frame.pack(fill="both", expand=True, pady=5, padx=(0, 10))
        # Table + Scrollbars
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical",
                            command=self.product_table.yview)
        hsb = ttk.Scrollbar(self.table_frame, orient="horizontal",
                            command=self.product_table.xview)
        self.product_table.configure(
            yscrollcommand=vsb.set, xscrollcommand=hsb.set
        )
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        # Bold headings
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        # Configure headings
        for col in self.columns:
            self.product_table.heading(col, text=col)
            self.product_table.column(col, anchor="center", width=50)
        self.product_table.pack(fill="both", expand=True)
        self.product_table.bind(
            "<MouseWheel>", lambda e: self.product_table.yview_scroll(
                -1 * int(e.delta / 120), "units"
        ))
        self.product_table.bind(
            "Button-4", lambda e: self.product_table.yview_scroll(-1, "units")
        )  # macOS
        self.product_table.bind(
            "Button-5", lambda e: self.product_table.yview_scroll(1, "units")
        )

    def toggle_filters(self):
        """Enable/Disable combo boxes based on checkboxes."""
        self.month_cb.configure(
            state="readonly" if self.month_var.get() else "disabled"
        )
        self.product_cb.configure(
            state="readonly" if self.product_var.get() else "disabled"
        )
        self.user_cb.configure(
            state="readonly" if self.user_var.get() else "disabled"
        )

    def load_data(self):
        """Load sales data based on current year only (initial)."""
        self.product_table.delete(*self.product_table.get_children())
        year = int(self.year_cb.get())
        # Filters
        month = None
        product_name = None
        user = None
        if self.month_var.get() and self.month_cb.get():
            month = dict(self.months).get(self.month_cb.get())
        if self.product_var.get() and self.product_cb.get():
            product_name = self.product_cb.get()
        if self.user_var.get() and self.user_cb.get():
            user = self.user_cb.get()
        rows, err = fetch_sales_by_year(self.conn, year, month,
                                        product_name, user)
        if err:
            messagebox.showerror(
                "Error", f"Failed to fetch sales:\n{err}"
            )
            return
        for idx, row in enumerate(rows, start=1):
            self.product_table.insert("", "end", values=(
                idx,
                row["user"],
                row["date"],
                row["receipt_no"],
                row["product_code"],
                row["product_name"],
                row["quantity"],
                f"{row["unit_price"]:,.2f}",
                f"{row["total_amount"]:,.2f}",
            ))
        self.title_label.configure(text=f"Cumulative Sales for Year {year}.")
        self._resize_columns()

    def _resize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.product_table.get_children():
                val = str(self.product_table.set(item, col))
                max_width = max(max_width, font.measure(val))
            self.product_table.column(col, width=max_width + 10)

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root=tk.Tk()
    YearlySalesWindow(root, conn, "sniffy")
    root.mainloop()