import re
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
from base_window import BaseWindow
from accounting_export import ReportExporter
from authentication import VerifyPrivilegePopup
from order_utils import OrderItemsGui, OrderPayment
from order_popups import EditOrderWindow
from working_on_orders import (
    order_items_history, fetch_distinct_years_users, fetch_pending_orders,
    delete_order, fetch_unpaid_orders, fetch_all_orders_logs
)


class OrderedItemsWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Order Reports")
        self.center_window(self.master, 1000, 700, parent)
        self.master.transient(parent)
        self.master.configure(bg="lightblue")
        self.master.grab_set()

        self.user = user
        self.conn = conn
        self.selected_year = tk.StringVar()
        self.selected_month = tk.StringVar()
        data, msg = fetch_distinct_years_users(conn)
        if msg:
            messagebox.showerror("Error", msg, parent=self.master)
        self.years = data["years"]
        self.title = None
        self.months = [
            ("", None), ("January", 1), ("February", 2), ("March", 3),
            ("April", 4), ("May", 5), ("June", 6), ("July", 7), ("August", 8),
            ("September", 9), ("October", 10), ("November", 11),
            ("December", 12),
        ]
        # Bold Table Headings and content font
        style = ttk.Style(self.master)
        style.configure("Treeview", font=("Arial", 10))
        style.configure(
            "Treeview.Heading", font=("Arial", 12, "bold", "underline")
        )
        self.columns = [
            "No.", "Product Code", "Product Name", "Quantity", "Unit Price",
            "Total Revenue"
        ]
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="groove"
        )
        self.year_cb = ttk.Combobox(
            self.top_frame, textvariable=self.selected_year, state="readonly",
            width=10, values=self.years,
        )
        self.month_cb = ttk.Combobox(
            self.top_frame, values=[name for name, _num in self.months],
            width=12, state="readonly", textvariable=self.selected_month
        )
        self.label = tk.Label(
            self.top_frame, text="", bg="lightblue",
            font=("Arial", 16, "bold", "underline")
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings", height=20
        )

        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.top_frame.pack(side="top", fill="x")
        tk.Label(
            self.top_frame, text="Select Year:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0))
        self.year_cb.pack(side="left", padx=(0, 5))
        if self.years:
            self.year_cb.set(self.years[0])
        else:
            messagebox.showinfo(
                "Info", "No Order Logs Found.", parent=self.master
            )
        tk.Label(
            self.top_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 5))
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        btn_frame = tk.Frame(
            self.top_frame, bg="lightblue", bd=4, relief="groove"
        )
        btn_frame.pack(side="right")
        action_btn = {
            "Export PDF": self.on_export_pdf,
            "Print Logs": self.on_print
        }
        for text, command in action_btn.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="raised",
                bg="dodgerblue", fg="white",
            ).pack(side="left")
        self.label.pack(anchor="center", padx=20)
        # self.top_frame.pack(side="top", fill="x")
        self.table_frame.pack(side="left", fill="both", expand=True,)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.bind(
            "<MouseWheel>", lambda e: self.tree.yview_scroll(-1 * (
                    e.delta // 120
            ), "units")
        )

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        label = "Most Ordered Items In"
        year = int(self.selected_year.get())
        if self.selected_month.get():
            month = dict(self.months).get(self.selected_month.get())
            label += f" {self.selected_month.get()}"
        else:
            month = None
        label += f" {year}."
        self.label.configure(text=label)
        self.title = label
        items = order_items_history(self.conn, year, month)
        if isinstance(items, str):
            messagebox.showerror("Error", items, parent=self.master)
            return
        for i, row in enumerate(items, start=1):
            name = re.sub(r"\s+", " ", str(row["product_name"])).strip()
            quantity = int(row["total_quantity"])
            unit_price = f"{float(row["unit_price"]):,.2f}"
            total_price = f"{float(row["total_revenue"]):,.2f}"
            self.tree.insert("", "end", values=(
                i,
                row["product_code"],
                name,
                quantity,
                unit_price,
                total_price
            ))
        self.auto_adjust_column_widths()

    def auto_adjust_column_widths(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_value = str(self.tree.set(item, col))
                cell_width = font.measure(cell_value)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 10)

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No.": vals[0],
                "Product Code": vals[1],
                "Product Name": vals[2],
                "Quantity": vals[3],
                "Unit Price": vals[4],
                "Total Revenue": vals[5]
            })
        return rows

    def _make_exporter(self):
        title = self.title
        columns = [
            "No.", "Product Code", "Product Name", "Quantity", "Unit Price",
            "Total Revenue"
        ]
        rows = self._collect_current_rows()
        return ReportExporter(self.master, title, columns, rows)

    def _check_privilege(self):
        priv = "View Ordered Items"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        return getattr(verify, "result", None) == "granted"

    def on_export_pdf(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Export PDF.", parent=self.master
            )
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Print Logs.", parent=self.master
            )
            return
        exporter = self._make_exporter()
        exporter.print()


class PendingOrdersWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Orders Documentation")
        self.center_window(self.window, 1100, 700, parent)
        self.window.configure(bg="lightblue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.selected_order_id = None
        self.items_tree = None
        # Bold Table Headings and content font
        style = ttk.Style(self.window)
        style.configure("Treeview", font=("Arial", 11))
        style.configure(
            "Treeview.Heading", font=("Arial", 12, "bold", "underline")
        )
        self.columns = [
            "No.", "Order ID", "Customer Name", "Contact", "Date Ordered",
            "Deadline", "Amount", "Status"
        ]
        # Left Frame for buttons
        self.main_frame = tk.Frame(self.window, bg="lightblue", bd=4,
                                   relief="solid")
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue", bd=4,
                                  relief="groove")
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(self.table_frame, columns=self.columns,
                                 show="headings")

        self.build_ui()
        self.create_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", pady=(0, 10), padx=10, expand=True)
        self.top_frame.pack(side="top", fill="x", padx=5)
        self.table_frame.pack(side="left", fill="both", expand=True)
        title_frame = tk.Frame(self.top_frame, bg="lightblue")
        btn_frame = tk.Frame(self.top_frame, bg="lightblue")
        title_frame.pack(side="left", padx=10)
        btn_frame.pack(side="right")
        tk.Label(
            title_frame, text="Current Undelivered Orders.", bg="lightblue",
            font=("Arial", 16, "bold", "underline")
        ).pack(anchor="center", padx=20)
        buttons = {
            "Deliver Order": self.deliver_order,
            "Delete Order": self.delete_order,
        }
        for text, command in buttons.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="raised"
            ).pack(side="left")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=40)
        self.tree.bind("<<TreeviewSelect>>", self.order_details)
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            -1 * (e.delta // 120), "units"
        ))

    def create_table(self):
        orders = fetch_pending_orders(self.conn)
        for i, order in enumerate(orders, start=1):
            self.tree.insert("", "end", values=(
                i,
                order["order_id"],
                order["customer_name"],
                order["contact"],
                order["date_placed"],
                order["deadline"],
                f"{order["amount"]:,.2f}",
                order["status"]
            ))
        self.auto_resize_columns()

    def auto_resize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_value = str(self.tree.set(item, col))
                cell_width = font.measure(cell_value)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 5)

    def order_details(self, event=None):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.selected_order_id = values[1]

    def deliver_order(self):
        order_id = self.selected_order_id
        if not order_id:
            messagebox.showwarning(
                "No Selection",
                "Please select Order first.", parent=self.window
            )
            return
        # Verify user privilege
        priv = "View Ordered Items"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.window
            )
            return
        OrderItemsGui(self.window, self.conn, self.user, order_id)

    def delete_order(self):
        order_id = self.selected_order_id
        if not order_id:
            messagebox.showwarning(
                "No Selection",
                "Please select Order first.", parent=self.window
            )
            return
        # Verify user privilege
        priv = "Delete Order"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.window
            )
            return
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to DELETE Order: {order_id}?",
            parent=self.window
        )
        if confirm:
            try:
                success, msg = delete_order(self.conn, order_id, self.user)
                if success:
                    messagebox.showinfo("Success", msg, parent=self.window)
                    self.selected_order_id = None
                else:
                    messagebox.showerror("Error", msg, parent=self.window)
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to Delete order: {str(e)}.", parent=self.window
                )
        else:
            messagebox.showinfo(
                "Cancelled", "Order Deletion Cancelled.", parent=self.window
            )


class UnpaidOrdersWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Orders Payment")
        self.center_window(self.master, 1000, 600, parent)
        self.master.configure(bg="lightgreen")
        self.master.transient(parent)
        self.master.grab_set()

        self.user = user
        self.conn = conn
        self.selected_order_id = None
        # Bold Table Headings and content font
        style = ttk.Style(self.master)
        style.configure("Treeview", rowheight=20, font=("Arial", 10))
        style.configure(
            "Treeview.Heading", font=("Arial", 12, "bold", "underline")
        )
        self.columns = [
            "No.", "Order ID", "Customer Name", "Contact", "Date Placed",
            "Amount", "Status", "Balance"
        ]
        self.main_frame = tk.Frame(self.master, bg="lightblue", bd=4,
                                   relief="solid")
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings", height=20
        )

        self.build_ui()
        self.load_data()

    def build_ui(self):
        # Main Frame for layout
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        table_top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="groove"
        )
        table_top_frame.pack(side="top", fill="x", padx=5)
        tk.Label(
            table_top_frame, text="Current Unpaid Orders.", bg="lightblue",
            font=("Arial", 16, "bold", "underline")
        ).pack(padx=10, side="left")  # Title
        label_frame = tk.Frame(table_top_frame, bg="lightblue")
        label_frame.pack(side="left", fill="x", padx=10)
        tk.Label(
            label_frame, text="Select Order To Pay", bg="lightblue",
            font=("Arial", 13, "italic", "underline"), fg="dodgerblue"
        ).pack(padx=30, anchor="center")
        btn_frame = tk.Frame(table_top_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=10)
        action_btn = {
            "Refresh": self.load_data,
            "Pay Order": self.pay_order,
            "Export PDF": self.on_export_pdf,
            "Print Orders": self.on_print
        }
        for text, command in action_btn.items():
            tk.Button(
                btn_frame, text=text, bg="green", bd=2, relief="sunken",
                fg="white", command=command
            ).pack(side="left")
        # Left frame for table
        self.table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Treeview for orders
        scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=50, anchor="center")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            -1 * (e.delta // 120), "units"
        ))
        # Bind row selection
        self.tree.bind("<<TreeviewSelect>>", self.order_details)

    def load_data(self):
        orders_data = fetch_unpaid_orders(self.conn)
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Populate table with data
        for i, order in enumerate(orders_data, start=1):
            self.tree.insert("", "end", values=(
                i,
                order['order_id'],
                order['customer_name'],
                order['contact'],
                order['date_placed'],
                f"{order['amount']:,.2f}",
                order['status'],
                f"{order['balance']:,.2f}"
            ))
        self.autosize_columns()

    def order_details(self, event=None):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.selected_order_id = values[1]

    def pay_order(self):
        order_id = self.selected_order_id
        if not order_id:
            messagebox.showwarning(
                "No Selection",
                "Please Select Order to Pay First.", parent=self.master
            )
            return
        # Verify user privilege
        priv = "Receive Order Payment"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        OrderPayment(self.master, self.conn, self.user, order_id)

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No.": vals[0],
                "Order ID": vals[1],
                "Customer Name": vals[2],
                "Contact": vals[3],
                "Date Placed": vals[4],
                "Amount": vals[5],
                "Status": vals[6],
                "Balance": vals[7]
            })
        return rows

    def _make_exporter(self):
        title = "Current Unpaid Orders"
        columns = [
            "No.", "Order ID", "Customer Name", "Contact", "Date Placed",
            "Amount", "Status", "Balance"
        ]
        rows = self._collect_current_rows()
        return ReportExporter(self.master, title, columns, rows)

    def _check_privilege(self):
        priv = "Manage Orders"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        return getattr(verify, "result", None) == "granted"

    def on_export_pdf(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Export PDF.", parent=self.master
            )
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Print Logs.", parent=self.master
            )
            return
        exporter = self._make_exporter()
        exporter.print()

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_value = str(self.tree.set(item, col))
                cell_width = font.measure(cell_value)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 5)


class EditOrdersWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Edit Pending Orders")
        self.center_window(self.master, 1100, 650, parent)
        self.master.configure(bg="lightgreen")
        self.master.grab_set()
        self.master.transient(parent)

        self.conn = conn
        self.user = user
        self.selected_order_id = None
        self.selected_product_code = None
        self.selected_product_amount = None
        style = ttk.Style(self.master)
        style.configure("Treeview", font=("Arial", 11))
        style.configure(
            "Treeview.Heading", font=("Arial", 13, "bold", "underline")
        )
        self.columns = [
            "No.", "Order ID", "Customer Name", "Contact", "Date Placed",
            "Deadline", "Amount", "Status"
        ]
        # Layout frames
        self.main_frame = tk.Frame(
            self.master, bg="lightgreen", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=4, relief="solid"
        )
        self.btn_frame = tk.Frame(self.top_frame, bg="lightgreen")
        self.table_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.load_orders_table()

    def build_ui(self):
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.top_frame.pack(fill="x")
        tk.Label(
            self.top_frame, text="Current Pending Orders", bg="lightgreen",
            font=("Arial", 15, "bold", "underline")
        ).pack(side="left", padx=10)
        tk.Label(
            self.top_frame, text="Select Order To Take Action.", fg="blue",
            bg="lightgreen", font=("Arial", 13, "italic", "underline")
        ).pack(side="left", padx=20)
        self.btn_frame.pack(side="right", padx=5)
        buttons = {
            "Edit Order Details": self.edit_order_details,
            "Edit Order Items": self.edit_order_items,
            "Delete Order": self.order_delete
        }
        for text, command in buttons.items():
            tk.Button(
                self.btn_frame, text=text, command=command, relief="raised",
                bd=2, bg="blue", fg="white"
            ).pack(side="left")
        self.btn_frame.pack_forget()
        self.table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Bind selection
        self.tree.bind("<<TreeviewSelect>>", self.on_order_selected)
        self.tree.bind(
            "<MouseWheel>", lambda e: self.tree.yview_scroll(-1 * (
                    e.delta // 120
            ), "units")
        )

    def load_orders_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        orders = fetch_pending_orders(self.conn)
        for i, order in enumerate(orders, start=1):
            self.tree.insert("", "end", values=(
                i,
                order["order_id"],
                order["customer_name"],
                order["contact"],
                order["date_placed"],
                order["deadline"],
                f"{order["amount"]:,}",
                order["status"]
            ))
        self.auto_adjust_column_widths()

    def on_order_selected(self, event):
        selected = self.tree.focus()
        if selected:
            self.selected_order_id = self.tree.item(selected)["values"][1]
            self.btn_frame.pack(side="right", padx=5)

    def edit_order_items(self):
        if not self.selected_order_id:
            messagebox.showerror(
                "Not Selected", "No Selected Order", parent=self.master
            )
            return
        # Verify user privilege
        priv = "Edit Order"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        OrderItemsGui(
            self.master, self.conn, self.user, self.selected_order_id
        )

    def order_delete(self):
        if not self.selected_order_id:
            messagebox.showwarning(
                "No Order", "Select an order first.", parent=self.master
            )
            return
        order_id = self.selected_order_id
        # Verify user privilege
        priv = "Delete Order"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            "Make Sure Order Payments Are Refunded Before Deleting.\n"
            f"You Want to DELETE Order: {order_id}?", parent=self.master
        )
        if confirm:
            try:
                success, msg = delete_order(
                    self.conn, self.selected_order_id, self.user
                )
                if success:
                    messagebox.showinfo("Success", msg, parent=self.master)
                    self.load_orders_table()
                else:
                    messagebox.showerror("Error", msg, parent=self.master)
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to Delete order: {e}", parent=self.master
                )
        else:
            messagebox.showinfo(
                "Cancelled", "Order Deletion Cancelled.", parent=self.master
            )

    def edit_order_details(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(
                "No Selection",
                "Please select an order to edit.", parent=self.master
            )
            return
        # Get selected row data
        values = self.tree.item(selected_item, 'values')
        if not values:
            messagebox.showerror(
                "Error",
                "Unable to retrieve selected Order Data.", parent=self.master
            )
            return
        order_id = values[1]
        customer_name = values[2]
        contact = values[3]
        deadline = values[5]
        total_amount = float(values[6].replace(",", ""))
        # Verify user privilege
        priv = "Delete Order"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        order = {
            "order_id": order_id,
            "customer_name": customer_name,
            "contact": contact,
            "deadline": deadline,
            "total_amount": total_amount
        }
        EditOrderWindow(self.master, self.conn, order, self.user)

    def auto_adjust_column_widths(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_value = str(self.tree.set(item, col))
                cell_width = font.measure(cell_value)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 5)


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
        style.configure(
            "Treeview.Heading", font=("Arial", 12, "bold", "underline")
        )
        style.configure("Treeview", font=("Arial", 10))
        self.main_frame = tk.Frame(self.top, bg="lightblue", bd=4, relief="solid")
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.filter_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.top_frame, textvariable=self.selected_year, state="readonly",
            width=10, values=self.years,
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_user, width=15,
            state="disabled", values=self.users,
        )
        self.month_cb = ttk.Combobox(
            self.filter_frame, values=[name for name, _num in self.months],
            width=12, state="disabled",
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.title_frame = tk.Frame(
            self.top_frame, bg="lightblue", width=100, bd=4, relief="ridge"
        )
        self.title_label = tk.Label(
            self.title_frame, text="", bg="lightblue", bd=4, relief="flat",
            font=("Arial", 16, "bold", "underline"), fg="dodgerblue"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.refresh_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.top_frame.pack(fill="x", padx=5)
        # Year Selector
        tk.Label(
            self.top_frame, text="Select Year:", bg="lightblue",
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
        # Title
        self.title_frame.pack(side="left", padx=20)
        self.title_label.pack(anchor="center", padx=10)
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
            self.tree.insert("", "end", values=(
                i,
                row["order_id"],
                row["log_date"],
                row["user"],
                row["action"],
                f"{row['total_amount']:,.2f}"
            ))
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
            self.tree.column(col, width=max_width + 2)


if __name__ == "__main__":
    from connect_to_db import connect_db
    conn = connect_db()
    root = tk.Tk()
    OrderLogsWindow(root, conn, "Sniffy")
    root.mainloop()