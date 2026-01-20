import re
import tkinter as tk
from tkinter import ttk, messagebox
from base_window import BaseWindow
from accounting_export import ReportExporter
from authentication import VerifyPrivilegePopup
from order_utils import OrderItemsGui, OrderPayment
from order_popups import EditOrderWindow
from table_utils import TreeviewSorter
from working_on_orders import (
    order_items_history, fetch_distinct_years_users, fetch_pending_orders,
    delete_order, fetch_unpaid_orders
)


class OrderedItemsWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.configure(bg="lightblue")
        self.master.title("Order Reports")
        self.center_window(self.master, 1000, 700, parent)
        self.master.transient(parent)
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
            ("April", 4), ("May", 5), ("June", 6), ("July", 7),
            ("August", 8), ("September", 9), ("October", 10),
            ("November", 11), ("December", 12),
        ]
        # Bold Table Headings and content font
        style = ttk.Style(self.master)
        style.theme_use("clam")
        self.columns = [
            "No.", "Product Code", "Product Name", "Quantity", "Unit Price",
            "Total Revenue"
        ]
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.top_frame, textvariable=self.selected_year, width=5,
            state="readonly", values=self.years, font=("Arial", 11)
        )
        self.month_cb = ttk.Combobox(
            self.top_frame, values=[name for name, _num in self.months],
            width=10, state="readonly", textvariable=self.selected_month,
            font=("Arial", 11)
        )
        self.label = tk.Label(
            self.main_frame, text="", bg="lightblue", fg="blue",
            font=("Arial", 18, "bold", "underline")
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No.")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.label.pack(anchor="center")
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
            self.top_frame, bg="lightblue", bd=4, relief="ridge"
        )
        btn_frame.pack(side="right")
        action_btn = {
            "Export PDF": self.on_export_pdf,
            "Print List": self.on_print
        }
        for text, command in action_btn.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="groove",
                bg="dodgerblue", fg="white", font=("Arial", 10, "bold")
            ).pack(side="left")
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
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        self.tree.tag_configure(
            "totalrow", background="#c5cae9",
            font=("Arial", 12, "bold", "underline")
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
        total_quantity = 0
        total_unit_price = 0
        cum_total_price = 0
        for i, row in enumerate(items, start=1):
            name = re.sub(r"\s+", " ", str(row["product_name"])).strip()
            quantity = int(row["total_quantity"])
            unit_price = f"{float(row['unit_price']):,.2f}"
            total_price = f"{float(row['total_revenue']):,.2f}"
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                row["product_code"],
                name,
                quantity,
                unit_price,
                total_price
            ), tags=(tag,))
            total_quantity += quantity
            total_unit_price += float(row["unit_price"])
            cum_total_price += float(row["total_revenue"])
        self.tree.insert("", "end", values=(
            "", "", "Total", total_quantity, f"{total_unit_price:,.2f}",
            f"{cum_total_price:,.2f}"
            ), tags=("totalrow",))
        self.sorter.autosize_columns(10)

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
                "Denied", "You Don't Permission To Print Order Items.",
                parent=self.master
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
        style.theme_use("clam")
        self.columns = [
            "No.", "Order ID", "Customer Name", "Contact", "Date Ordered",
            "Deadline", "Amount", "Status"
        ]
        # Left Frame for buttons
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No.")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()
        self.create_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", pady=(0, 10), padx=10, expand=True)
        self.top_frame.pack(side="top", fill="x")
        self.table_frame.pack(side="left", fill="both", expand=True)
        btn_frame = tk.Frame(self.top_frame, bg="lightblue")
        btn_frame.pack(side="right")
        tk.Label(
            self.top_frame, text="Current Undelivered Orders.", fg="blue",
            bg="lightblue", font=("Arial", 18, "bold", "underline")
        ).pack(side="left")
        buttons = {
            "Deliver Order": self.deliver_order,
            "Delete Order": self.delete_order,
        }
        for text, command in buttons.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="groove",
                bg="blue", fg="white", font=("Arial", 10, "bold")
            ).pack(side="left")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.bind("<<TreeviewSelect>>", self.order_details)
        scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        self.tree.tag_configure(
            "totalrow", background="#c5cae9",
            font=("Arial", 12, "bold", "underline")
        )

    def create_table(self):
        orders = fetch_pending_orders(self.conn)
        if isinstance(orders, str):
            messagebox.showerror("Error", orders, parent=self.window)
            return
        total_amount = 0
        for i, order in enumerate(orders, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                order["order_id"],
                order["customer_name"],
                order["contact"],
                order["date_placed"].strftime("%d/%m/%Y"),
                order["deadline"].strftime("%d/%m/%Y"),
                f"{order['amount']:,.2f}",
                order["status"]
            ), tags=(tag,))
            total_amount += float(order["amount"])
        self.tree.insert("", "end", values=(
            "", "", "Total", "", "", "", f"{total_amount:,.2f}", ""
        ), tags=("totalrow",))
        self.sorter.autosize_columns()

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
        self.center_window(self.master, 1050, 700, parent)
        self.master.configure(bg="lightgreen")
        self.master.transient(parent)
        self.master.grab_set()

        self.user = user
        self.conn = conn
        self.selected_order_id = None
        # Bold Table Headings and content font
        style = ttk.Style(self.master)
        style.theme_use("clam")
        self.columns = [
            "No.", "Order ID", "Customer Name", "Contact", "Date Placed",
            "Amount", "Status", "Balance"
        ]
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No.")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()
        self.load_data()

    def build_ui(self):
        # Main Frame for layout
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        table_top_frame = tk.Frame(self.main_frame, bg="lightblue")
        table_top_frame.pack(side="top", fill="x")
        tk.Label(
            table_top_frame, text="Current Unpaid Orders.", bg="lightblue",
            fg="blue", font=("Arial", 18, "bold", "underline")
        ).pack(side="left")  # Title
        label_frame = tk.Frame(table_top_frame, bg="lightblue")
        label_frame.pack(side="left", fill="x", padx=40)
        tk.Label(
            label_frame, text="Select Order To Pay", bg="lightblue",
            font=("Arial", 13, "italic", "underline"), fg="dodgerblue"
        ).pack(anchor="center")
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
                btn_frame, text=text, bg="green", bd=2, relief="groove",
                fg="white", command=command, font=("Arial", 10, "bold")
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
        # Bind row selection
        self.tree.bind("<<TreeviewSelect>>", self.order_details)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        self.tree.tag_configure(
            "totalrow", background="#c5cae9",
            font=("Arial", 12, "bold", "underline")
        )

    def load_data(self):
        orders_data = fetch_unpaid_orders(self.conn)
        if isinstance(orders_data, str):
            messagebox.showerror("Error", orders_data, parent=self.master)
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Populate table with data
        total_amount = 0
        total_bal = 0
        for i, order in enumerate(orders_data, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                order['order_id'],
                order['customer_name'],
                order['contact'],
                order['date_placed'].strftime("%d/%m/%Y"),
                f"{order['amount']:,.2f}",
                order['status'],
                f"{order['balance']:,.2f}"
            ), tags=(tag,))
            total_amount += float(order["amount"])
            total_bal += float(order["balance"])
        self.tree.insert("", "end", values=(
            "", "", "", "", "TOTAL", f"{total_amount:,.2f}", "",
            f"{total_bal:,.2f}"
        ), tags=("totalrow",))
        self.sorter.autosize_columns()

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


class EditOrdersWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Edit Orders")
        self.center_window(self.master, 1100, 700, parent)
        self.master.configure(bg="lightgreen")
        self.master.grab_set()
        self.master.transient(parent)

        self.conn = conn
        self.user = user
        self.selected_order_id = None
        self.selected_product_code = None
        self.selected_product_amount = None
        style = ttk.Style(self.master)
        style.theme_use("clam")
        self.columns = [
            "No.", "Order ID", "Customer Name", "Contact", "Date Placed",
            "Deadline", "Amount", "Status"
        ]
        # Layout frames
        self.main_frame = tk.Frame(
            self.master, bg="lightgreen", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.btn_frame = tk.Frame(self.top_frame, bg="lightgreen")
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=4, relief="ridge"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No.")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()
        self.load_orders_table()

    def build_ui(self):
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.top_frame.pack(fill="x")
        tk.Label(
            self.top_frame, text="Current Pending Orders", bg="lightgreen",
            fg="blue", font=("Arial", 18, "bold", "underline")
        ).pack(side="left", padx=(0, 20))
        l_text = "Select Order To Take Action."
        tk.Label(
            self.top_frame, text=l_text, fg="blue", bg="lightgreen",
            width=30, font=("Arial", 13, "italic", "underline")
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
            self.tree.column(col, anchor="center", width=30)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Bind selection
        self.tree.bind("<<TreeviewSelect>>", self.on_order_selected)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def load_orders_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        orders = fetch_pending_orders(self.conn)
        for i, order in enumerate(orders, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                order["order_id"],
                order["customer_name"],
                order["contact"],
                order["date_placed"].strftime("%d/%m/%Y"),
                order["deadline"].strftime("%d/%m/%Y"),
                f"{order["amount"]:,}",
                order["status"]
            ), tags=(tag,))
        self.sorter.autosize_columns()

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

