import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import tkinter.messagebox as messagebox
from orders_edit_gui import EditOrdersWindow
from new_order_gui import NewOrderWindow
from order_payment_gui import UnpaidOrdersWindow
from order_reports_gui import ReportsWindow
from base_window import BaseWindow
from order_documentation_gui import OrdersDocumentationWindow
from report_preview import ReportPreviewer
from working_on_orders import *
from connect_to_db import connect_db
conn = connect_db()

class OrdersWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Orders Management")
        self.center_window(self.window, 1200, 600)
        self.window.configure(bg="blue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user

        self.setup_ui()
        self.load_orders()

    def setup_ui(self):
        top_frame = tk.Frame(self.window, bg="lightgreen") # Top frame for buttons
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        self.buttons = {
            "New Order": self.new_order,
            "Order Payments": self.order_payments,
            "Edit Order": self.edit_order,
            "History": self.view_logs,
            "Working On Orders": self.work_on_orders
        }
        for text, command in self.buttons.items():
            tk.Button(top_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)
        main_frame = tk.Frame(self.window, bg="blue") # Middle frame
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        tk.Label(main_frame, text="Current Pending Orders", bg="blue", fg="white", anchor="center", font=("Arial", 12, "bold")).pack(padx=5)
        # left frame with orders and logs - Vertically
        left_frame = tk.Frame(main_frame, bg="blue")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Orders Table (left)
        orders_frame = tk.LabelFrame(left_frame, text="Orders", bg="blue", fg="white", font=('Arial', 12, 'bold'),)
        orders_frame.pack(fill=tk.BOTH, expand=True)
        self.orders_button_frame = tk.Frame(orders_frame, bg="blue")
        self.orders_button_frame.pack(side=tk.TOP, fill=tk.X, padx=5)
        self.orders_view_button = tk.Button(self.orders_button_frame, text="View Report", command=self.view_orders_report)
        self.orders_view_button.pack(side=tk.RIGHT, padx=5)
        orders_table_frame = tk.Frame(orders_frame)
        orders_table_frame.pack(fill=tk.BOTH, expand=True)
        self.orders_tree = ttk.Treeview(orders_table_frame, columns=("Order ID", "Customer", "Contact", "Date", "Deadline", "Amount", "Status"), show="headings", height=10)
        style = ttk.Style()
        style.configure("Treeview", background="white", foreground="black", rowheight=25, fieldbackground="white")
        style.configure("Treeview.Heading", font="Arial 10 bold") # Bold Headings
        for col in self.orders_tree["columns"]:
            self.orders_tree.heading(col, text=col)
            self.orders_tree.column(col, anchor="center", width=50)
        self.orders_tree.bind("<<TreeviewSelect>>", self.load_order_details)
        self.orders_tree.bind("<MouseWheel>", lambda e: self._on_mousewheel(self.orders_tree, e)) # Windows/Linux
        orders_scrollbar = ttk.Scrollbar(orders_table_frame, orient="vertical", command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=orders_scrollbar.set)
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=2)
        orders_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Logs Table (below orders table)
        logs_frame = tk.LabelFrame(left_frame, text="Order Logs", bg="blue", fg="white", font=('Arial', 12, 'bold'),)
        logs_frame.pack(fill=tk.X)
        self.logs_button_frame = tk.Frame(logs_frame, bg="blue")
        self.logs_button_frame.pack(fill=tk.X, pady=(0, 2), padx=5)
        self.logs_view_button = tk.Button(self.logs_button_frame, text="View Report", command=self.view_logs_report)
        self.logs_view_button.pack(side=tk.RIGHT, padx=5)
        self.logs_view_button.config(state="disabled")
        log_table_frame = tk.Frame(logs_frame)
        log_table_frame.pack(fill=tk.BOTH, expand=True)
        self.logs_tree = ttk.Treeview(log_table_frame, columns=("Date", "Order ID", "User", "Action", "Amount"), show="headings", height=4)
        for col in self.logs_tree["columns"]:
            self.logs_tree.heading(col, text=col)
            self.logs_tree.column(col, anchor="center", width=40)
        logs_scrollbar = ttk.Scrollbar(log_table_frame, orient="vertical", command=self.logs_tree.yview)
        self.logs_tree.configure(yscrollcommand=logs_scrollbar.set)
        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=2)
        self.logs_tree.bind("<MouseWheel>", lambda e: self._on_mousewheel(self.logs_tree, e)) # Windows
        logs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Order Items Table (right)
        right_frame = tk.LabelFrame(main_frame, text="Order Items", bg="blue", fg="white", font=('Arial', 12, 'bold'))
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.items_button_frame = tk.Frame(right_frame, bg="blue")
        self.items_button_frame.pack(fill=tk.X, anchor="e", pady=(0, 2), padx=5)
        self.items_view_button = tk.Button(self.items_button_frame, text="View Report", command=self.view_items_report)
        self.items_view_button.pack(side=tk.RIGHT, padx=5)
        self.items_view_button.config(state="disabled")
        items_table_frame = tk.Frame(right_frame)
        items_table_frame.pack(fill=tk.BOTH, expand=True)
        self.items_tree = ttk.Treeview(items_table_frame, columns=("Order ID", "Code", "Name", "Qty", "Unit Price", "Total"), show="headings", height=20)
        for col in self.items_tree["columns"]:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, anchor="center", width=90)
        items_scrollbar = ttk.Scrollbar(items_table_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=2)
        self.items_tree.bind("<MouseWheel>", lambda e: self._on_mousewheel(self.items_tree, e)) # Windows
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
       
    def load_orders(self):
        for row in self.orders_tree.get_children():
            self.orders_tree.delete(row)
        orders = fetch_all_orders(self.conn)
        for order in orders:
            self.orders_tree.insert("", "end", values=(
                order["order_id"],
                order["customer_name"],
                order["contact"],
                order["date_placed"],
                order["deadline"],
                order["amount"],
                order["status"]
            ))
        self.window.after(100, lambda: self.autosize_columns(self.orders_tree))
        if orders:
            self.orders_view_button.config(state="normal")
        else:
            self.orders_view_button.config(state="disabled")
        messagebox.showinfo("Orders", "Showing All Pending Orders.")
    def load_order_details(self, event):
        selected = self.orders_tree.selection()
        if not selected:
            return
        order_id = self.orders_tree.item(selected[0])["values"][0]
        # Load items
        for row in self.items_tree.get_children():
            self.items_tree.delete(row)
        items = fetch_order_items_by_order_id(self.conn, order_id)
        for item in items:
            self.items_tree.insert("", "end", values=(
                item["order_id"],
                item["product_code"],
                item["product_name"],
                item["quantity"],
                item["unit_price"],
                item["total_price"]
            ))
        self.window.after(100, lambda: self.autosize_columns(self.items_tree))
        if items:
            self.items_view_button.config(state="normal")
        else:
            self.items_view_button.config(state="disabled")
        # Load logs
        for row in self.logs_tree.get_children():
            self.logs_tree.delete(row)
        logs = fetch_orders_logs_by_order_id(self.conn, order_id)
        for log in logs:
            self.logs_tree.insert("", "end", values=(
                log["log_date"],
                log["order_id"],
                log["user"],
                log["action"],
                log["total_amount"]
            ))
        self.window.after(100, lambda: self.trigger_autosize(self.logs_tree))
        if logs:
            self.logs_view_button.config(state="normal")
        else:
            self.logs_view_button.config(state="disabled")
    def trigger_autosize(self, treeview):
        self.autosize_columns(treeview)
    def view_orders_report(self):
        orders = fetch_all_orders(self.conn)
        data = []
        for order in orders:
            data.append({
                "Order ID": order["order_id"],
                "Customer": order["customer_name"],
                "Contact": order["contact"],
                "Date": order["date_placed"],
                "Deadline": order["deadline"],
                "Amount":order["amount"],
                "Status": order["status"]
                })
        preview = ReportPreviewer(self.user)
        preview.show(Orders=data)
    def view_logs_report(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select Order first.")
            return
        order_id = self.orders_tree.item(selected[0])["values"][0]
        logs = fetch_orders_logs_by_order_id(self.conn, order_id)
        order_logs = []
        for log in logs:
            order_logs.append({
                "Log Date": log["log_date"],
                "Order": log["order_id"],
                "User": log["user"],
                "Action": log["action"],
                "Amount": log["total_amount"]
                })
        preview = ReportPreviewer(self.user)
        preview.show(Logs=order_logs)
    def view_items_report(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select Order first.")
            return
        order_id = self.orders_tree.item(selected[0])["values"][0]
        items = fetch_order_items_by_order_id(self.conn, order_id)
        order_items = []
        for item in items:
            order_items.append({
                "Order ID": item["order_id"],
                "Product Code": item["product_code"],
                "Product Name": item["product_name"],
                "Quantity": item["quantity"],
                "Unit Price": item["unit_price"],
                "Total Price": item["total_price"]
                })
        preview = ReportPreviewer(self.user)
        preview.show(Order_Items=order_items)
    def autosize_columns(self, treeview, *args):
        font = tkFont.Font()
        for col in treeview["columns"]:
            max_width = font.measure(col)
            for item in treeview.get_children():
                cell_value = str(treeview.set(item, col))
                cell_width = font.measure(cell_value)
                if cell_width > max_width:
                    max_width = cell_width
            treeview.column(col, width=max_width + 2)
    def _on_mousewheel(self, treeview, event=None): # Mouse wheel scrolling (window and Linux)
            treeview.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    # Placeholders buttons actions
    def new_order(self):
        NewOrderWindow(self.window, self.conn, self.user)
    def order_payments(self):
        UnpaidOrdersWindow(self.window, self.user)
    def edit_order(self):
        EditOrdersWindow(self.window, self.user)
    def view_logs(self):
        ReportsWindow(self.window, self.conn, self.user)
    def work_on_orders(self):
        OrdersDocumentationWindow(self.window, conn, self.user)
if __name__ == "__main__":
    conn = connect_db()
    root = tk.Tk()
    app=OrdersWindow(root, conn, 'Sniffy')
    #root.withdraw()
    root.mainloop()