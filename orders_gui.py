import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
from base_window import BaseWindow
from new_order_gui import NewOrderWindow
from order_utils import OrderItemsGui
from authentication import VerifyPrivilegePopup
from table_utils import TreeviewSorter
from order_windows import (
    OrderedItemsWindow, UnpaidOrdersWindow, PendingOrdersWindow,
    EditOrdersWindow,
)
from report_preview import ReportPreviewer
from working_on_orders import fetch_orders_by_year, fetch_order_years


class OrdersWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Order Management")
        self.center_window(self.window, 1150, 700, parent)
        self.window.configure(bg="lightblue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.buttons = {
            "New Order": self.new_order,
            "Order Payments": self.order_payments,
            "Edit Order": self.edit_order,
            "Pending Orders": self.work_on_orders,
            "Items Ordered": self.view_ordered_items
        }
        self.columns = [
            "No", "ID", "Customer", "Contact", "Date", "Deadline", "Amount",
            "Status"
        ]
        self.year_var = tk.StringVar()
        self.all_orders = None
        years = fetch_order_years(self.conn)
        if isinstance(years, str):
            messagebox.showerror(
                "Error", f"Failed to Fetch Years:\n{years}.",
                parent=self.window
            )
            self.years = []
            return
        if not years:
            messagebox.showwarning(
                "No Data", "No Years Found In Orders.", parent=self.window
            )
            self.years = []
            return
        self.years = years
        # Bold Table Headings and content font
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.button_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.title_label = tk.Label(
            self.button_frame, text="", bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline")
        )
        self.year_cb = ttk.Combobox(
            self.button_frame, textvariable=self.year_var, state="readonly",
            width=5, font=("Arial", 12), values=self.years
        )
        self.year_cb.current(0)
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, show="headings", columns=self.columns
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.bind_mousewheel()
        self.sorter.attach_sorting()

        self.setup_ui()
        self.load_orders()

    def setup_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Orders Table (left)
        self.button_frame.pack(side="top", fill="x")
        # Top frame for buttons
        top_frame = tk.Frame(self.button_frame, bg="lightblue")
        top_frame.pack(side="top", fill="x", padx=5)
        for text, command in self.buttons.items():
            tk.Button(
                top_frame, text=text, command=command, bd=4, relief="groove",
                bg="dodgerblue", fg="white", height=1, font=("Arial", 12, "bold")
            ).pack(side="left", padx=0)
        # title_frame = tk.Frame(self.button_frame, bg="lightblue")
        # title_frame.pack(side="top", fill="x")
        self.title_label.pack(anchor="center")


        tk.Label(
            self.button_frame, text="Order Year:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0), anchor="s")
        self.year_cb.pack(side="left", padx=(0, 5), anchor="s")
        self.year_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.load_orders()
        )
        buttons = {
            "View Report": self.view_orders_report,
            "View Items": self.view_order_details
        }
        for text, command in buttons.items():
            tk.Button(
                self.button_frame, text=text, command=command, bg="blue",
                fg="white", bd=2, relief="groove", font=("Arial", 10, "bold")
            ).pack(side="right", anchor="s")
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
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        self.tree.tag_configure(
            "totalrow", background="#c5cae9", foreground="blue",
            font=("Arial", 12, "bold", "underline")
        )

    def load_orders(self):
        """Populate the orders table."""
        selected_year = self.year_var.get()
        year = int(selected_year)
        success, orders = fetch_orders_by_year(self.conn, year)
        if not success:
            messagebox.showerror("Error", orders, parent=self.window)
            return
        self.all_orders = orders
        for row in self.tree.get_children():
            self.tree.delete(row)

        total_amount = 0.00
        for i, order in enumerate(self.all_orders, start=1):
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
        if orders:
            self.tree.insert("", "end", values=(
                "", "", "", "", "TOTAL", "", f"{total_amount:,.2f}", ""
            ), tags=("totalrow",))
        self.sorter.autosize_columns()
        title_text = f"Pending and Delivered Orders of {year}."
        self.title_label.configure(text=title_text)

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
        state = self.tree.item(selected[0])["values"][7]
        refill = self.load_orders
        OrderItemsGui(
            self.window, self.conn, self.user, order_id, refill, state
        )


    def view_orders_report(self):
        data = []
        for order in self.all_orders:
            data.append({
                "ID": order["order_id"],
                "Customer": order["customer_name"],
                "Contact": order["contact"],
                "Date": order["date_placed"].strftime("%d/%m/%Y"),
                "Deadline": order["deadline"].strftime("%d/%m/%Y"),
                "Amount": f"{order["amount"]:,.2f}",
                "Status": order["status"]
                })
        preview = ReportPreviewer(self.user)
        preview.show(Orders=data)

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

    # Placeholders buttons actions
    def new_order(self):
        if not self.has_privilege("Receive Order"):
            return
        NewOrderWindow(self.window, self.conn, self.user)

    def order_payments(self):
        if not self.has_privilege("Receive Order Payment"):
            return
        UnpaidOrdersWindow(self.window, self.conn, self.user)

    def edit_order(self):
        if not self.has_privilege("Edit Order"):
            return
        EditOrdersWindow(self.window, self.conn, self.user)

    def view_ordered_items(self):
        if not self.has_privilege("View Ordered Items"):
            return
        OrderedItemsWindow(self.window, self.conn, self.user)

    def work_on_orders(self):
        if not self.has_privilege("Manage Orders"):
            return
        PendingOrdersWindow(self.window, self.conn, self.user)

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root=tk.Tk()
    OrdersWindow(root, conn, "Sniffy")
    root.mainloop()