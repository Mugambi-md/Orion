import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import tkinter.messagebox as messagebox
from base_window import BaseWindow
from new_order_gui import NewOrderWindow
from order_utils import OrderItemsGui
from authentication import VerifyPrivilegePopup
from order_windows import (
    OrderedItemsWindow, UnpaidOrdersWindow, PendingOrdersWindow,
    EditOrdersWindow, OrderLogsWindow
)
from report_preview import ReportPreviewer
from working_on_orders import fetch_all_orders


class OrdersWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Order Management")
        self.center_window(self.window, 1300, 700, parent)
        self.window.configure(bg="blue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.buttons = {
            "New Order": self.new_order,
            "Order Payments": self.order_payments,
            "Edit Order": self.edit_order,
            "Pending Orders": self.work_on_orders,
            "Ordered Items": self.view_ordered_items,
            "Order Logs": self.view_logs
        }
        self.columns = [
            "No", "Order ID", "Customer", "Contact", "Date", "Deadline",
            "Amount", "Status"
        ]
        # Bold Table Headings and content font
        style = ttk.Style(self.window)
        style.configure("Treeview", rowheight=25, font=("Arial", 10))
        style.configure(
            "Treeview.Heading", font=("Arial", 11, "bold", "underline")
        )
        self.main_frame = tk.Frame(
            self.window, bg="blue", bd=4, relief="solid"
        )
        self.orders_frame = tk.Frame(self.main_frame, bg="blue")
        self.button_frame = tk.Frame(self.orders_frame, bg="blue")
        self.table_frame = tk.Frame(self.orders_frame, bg="blue")
        self.tree = ttk.Treeview(
            self.table_frame, show="headings", columns=self.columns
        )

        self.setup_ui()
        self.load_orders()

    def setup_ui(self):
        self.main_frame.pack(
            side="top", fill="both", expand=True, padx=10, pady=(0, 10)
        )
        top_frame = tk.Frame(self.main_frame, bg="blue") # Top frame for buttons
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5)
        for text, command in self.buttons.items():
            tk.Button(
                top_frame, text=text, command=command, bd=4, relief="raised"
            ).pack(side=tk.LEFT)
        # Orders Table (left)
        self.orders_frame.pack(fill=tk.BOTH, expand=True, padx=10,
                               pady=(0, 10))
        self.button_frame.pack(side=tk.TOP, fill=tk.X, padx=5)
        title_frame = tk.Frame(self.button_frame, bg="blue")
        title_frame.pack(side="left", padx=20)
        tk.Label(
            title_frame, text="All Current Orders Pending & Delivered",
            bg="blue", fg="white", font=("Arial", 16, "bold", "underline")
        ).pack(anchor="center")
        tk.Button(
            self.button_frame, text="View Report", bd=2, relief="solid",
            command=self.view_orders_report
        ).pack(side="right")
        tk.Button(
            self.button_frame, text="View Details", bd=2, relief="solid",
            command=self.view_order_details
        ).pack(side="right")
        self.table_frame.pack(fill=tk.BOTH, expand=True)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind(
            "<MouseWheel>", lambda e: self.tree.yview_scroll(
                -1 * (e.delta // 120), "units"
            )
        )

    def load_orders(self):
        """Populate the orders table."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        orders = fetch_all_orders(self.conn)
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
        self.autosize_columns()

    def view_order_details(self):
        """Open the order details window."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "No Selection",
                "Please Select an Order First.", parent=self.window
            )
            return
        order_id = self.tree.item(selected[0])["values"][1]
        OrderItemsGui(self.window, self.conn, self.user, order_id)


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


    # Placeholders buttons actions
    def new_order(self):
        NewOrderWindow(self.window, self.conn, self.user)
    def order_payments(self):
        UnpaidOrdersWindow(self.window, self.conn, self.user)
    def edit_order(self):
        EditOrdersWindow(self.window, self.conn, self.user)
    def view_ordered_items(self):
        OrderedItemsWindow(self.window, self.conn, self.user)
    def work_on_orders(self):
        PendingOrdersWindow(self.window, conn, self.user)

    def view_logs(self):
        OrderLogsWindow(self.window, self.conn, self.user)

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn = connect_db()
    root = tk.Tk()
    app=OrdersWindow(root, conn, 'Sniffy')
    #root.withdraw()
    root.mainloop()