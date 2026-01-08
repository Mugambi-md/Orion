import tkinter as tk
from tkinter import messagebox
from datetime import date
from windows_utils import ScrollableFrame
from authentication import VerifyPrivilegePopup
from sales_report_gui import SalesGUI
from stock_gui import StockWindow
from orders_gui import OrdersWindow
from accounting_gui import AccountWindow
from employee_gui import EmployeeManagementWindow
from new_order_gui import NewOrderWindow
from logs_gui import SystemLogsWindow
from log_popups_gui import (
    SalesLogsWindow, MonthlyReversalLogs, OrderLogsWindow, FinanceLogsWindow,
    ProductLogsWindow
)
from sales_popup import (
    MonthlySalesSummary, YearlySalesWindow, YearlyProductSales
)
from stock_reconciliation_gui import ReconciliationWindow
from stock_popups import DeleteProductPopup, NewProductPopup, RestoreProductPopup
from stock_windows import DeletedItemsWindow, ProductsDetailsWindow
from order_windows import (
    OrderedItemsWindow, EditOrdersWindow, PendingOrdersWindow
)
from account_popups import (
    OpeningBalancePopup, CloseYearPopup, InsertAccountPopup,
    ReverseJournalPopup
)
from employee_gui_popup import (
    EmployeePopup, LoginStatusPopup, PrivilegePopup, AssignPrivilegePopup,
    UserPrivilegesPopup, DepartmentsPopup, RemovePrivilegePopup,
    ResetPasswordPopup, EditEmployeeWindow
)
from stock_summary import  FetchSummary
from summary_gui import SummaryPreviewWindow


class AdminWindow:
    def __init__(self, conn, user):
        self.master = tk.Toplevel()
        self.master.title("Admin System Management")
        self.master.configure(bg="lightblue")
        self.master.state("zoomed")
        self.master.grab_set()

        self.conn = conn
        self.user = user
        self.summary = FetchSummary(self.conn)
        self.labels = []

        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.center_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.right_frame = tk.Frame(
            self.center_frame, bg="lightgray", bd=4, relief="ridge", width=300
        )
        self.inside_frame = ScrollableFrame(self.right_frame, "white")

        self.build_ui()
        self.show_summary()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        left_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        left_frame.pack(side="left", fill="y")
        btn_frame = ScrollableFrame(left_frame, "lightblue", 150)
        btn_frame.pack(side="left", fill="y")
        btn_area = btn_frame.scrollable_frame
        nav_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        nav_frame.pack(side="top", fill="x")
        self.center_frame.pack(side="left", fill="both", expand=True)
        nav_btns = {
            "Sales": self.sales_window,
            "Stock": self.stock_window,
            "Orders": self.order_window,
            "Finance": self.accounting_window,
            "Employees": self.employee_window,
            "System Logs": self.logs_window
        }
        for text, command in nav_btns.items():
            tk.Button(
                nav_frame, text=text, command=command, bd=4, relief="groove",
                font=("Arial", 14, "bold"), bg="blue", fg="white", height=1
            ).pack(side="left", ipadx=5)
        self.right_frame.pack(side="right", fill="y")
        tk.Label(
            self.right_frame, text="Full System Summary.", bg="lightgray",
            fg="blue", font=("Arial", 16, "bold", "underline")
        ).pack(side="top", fill="x", anchor="center", padx=5)
        tk.Button(
            self.right_frame, text="Refresh The Above List", bg="dodgerblue",
            fg="white", bd=4, relief="groove", command=self.show_summary,
            font=("Arial", 12, "bold")
        ).pack(side="bottom", fill="x", padx=(0, 10))
        self.inside_frame.pack(fill="y", expand=True)
        tk.Label(
            btn_area, text="Sales Shortcuts", bg="green", fg="white",
            bd=4, relief="flat", font=("Arial", 11, "bold", "underline")
        ).pack(anchor="w", pady=(5, 0))
        sale_btns = {
            "Sales Records": self.sales_record_window,
            "Sales Summary": self.monthly_sales_window,
            "Items Share": self.sales_performance_window,
            "Reversal Logs": self.reversal_window,
            "Sales Logs": self.sales_logs_window
        }
        for text, command in sale_btns.items():
            tk.Button(
                btn_area, text=text, command=command, bg="dodgerblue",
                bd=4, relief="groove", fg="white", width=12,
                font=("Arial", 11)
            ).pack(ipadx=5, fill="x")

        tk.Label(
            btn_area, text="Stock Shortcuts", bg="green", fg="white",
            bd=4, relief="flat", font=("Arial", 11, "bold", "underline")
        ).pack(anchor="w", pady=(5, 0))
        stock_btns = {
            "New Product": self.new_product_window,
            "Stock Details": self.stock_details_window,
            "Reconcile Stock": self.reconciliation_window,
            "Delete Item": self.delete_item_window,
            "Deleted Items": self.deleted_products_gui,
            "Restore Item": self.restore_item_gui,
            "Stock Logs": self.stock_logs_window
        }
        for text, command in stock_btns.items():
            tk.Button(
                btn_area, text=text, command=command, bg="dodgerblue", bd=4,
                relief="groove", fg="white", width=12, font=("Arial", 11)
            ).pack(ipadx=5, fill="x")

        tk.Label(
            btn_area, text="Order Shortcuts", bg="green", fg="white",
            bd=4, relief="flat", font=("Arial", 11, "bold", "underline")
        ).pack(anchor="w", pady=(5, 0))
        order_btns = {
            "New Order": self.new_order_window,
            "Edit Orders": self.edit_orders_window,
            "Ordered Items": self.ordered_items_window,
            "Order Logs": self.order_logs_window
        }
        for text, command in order_btns.items():
            tk.Button(
                btn_area, text=text, command=command, bg="dodgerblue", bd=4,
                relief="groove", fg="white", width=12, font=("Arial", 11)
            ).pack(ipadx=5, fill="x")

        tk.Label(
            btn_area, text="Finance Shortcuts", bg="green", fg="white",
            bd=4, relief="flat", font=("Arial", 11, "bold", "underline")
        ).pack(anchor="w", pady=(5, 0))
        finance_btns = {
            "Create Journal": self.create_journal_account,
            "Initial Account\nBalances": self.initial_account_balance,
            "Delete/Reverse\nEntry": self.delete_reverse_journal_entry,
            "End Trading\nPeriod": self.close_financial_year_window,
            "Finance Logs": self.finance_logs_window
        }
        for text, command in finance_btns.items():
            tk.Button(
                btn_area, text=text, command=command, bg="dodgerblue", bd=4,
                relief="groove", fg="white", width=12, font=("Arial", 11)
            ).pack(ipadx=5, fill="x")

        tk.Label(
            btn_area, text="Users Shortcuts", bg="green", fg="white",
            bd=4, relief="flat", font=("Arial", 11, "bold", "underline")
        ).pack(anchor="w", pady=(5, 0))
        employee_btns = {
            "Departments": self.departments_window,
            "Create Privilege": self.create_privilege_window,
            "Assign Privilege": self.assign_window,
            "Remove Privilege": self.remove_window,
            "Assigned\nPrivileges": self.privileges_window,
            "New User": self.new_user_window,
            "Edit User\nInformation": self.edit_user,
            "Activate/Deactivate\nUser": self.activate_deactivate_window,
            "Reset User\nPassword": self.reset_password_window,
        }
        for text, command in employee_btns.items():
            tk.Button(
                btn_area, text=text, command=command, bg="dodgerblue", bd=4,
                relief="groove", fg="white", width=12, font=("Arial", 11)
            ).pack(ipadx=5, fill="x")


    def has_privilege(self, privilege: str) -> bool:
        """Check if the current user has the required privilege."""
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

    def show_summary(self):
        self.build_summary_data()
        self.render_summary_labels()

    def build_summary_data(self):
        self.labels.clear()
        curr_year = date.today().year
        curr_month = date.today().month
        stock_out, err = self.summary.fetch_out_of_stock_count()
        if not err:
            if  stock_out > 0:
                text = f"{stock_out} Products Are Out Of Stock."
                self.labels.append((text, "out_of_stock"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Stock Out Count.",
                parent=self.master
            )
        low_stock, err = self.summary.fetch_low_stock_count()
        if not err:
            if  low_stock > 0:
                text = f"{low_stock} Products Are Bellow Minimum Level."
                self.labels.append((text, "low_stock"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Below Stock Level Count.",
                parent=self.master
            )
        falling_low, err = self.summary.fetch_low_stock_warning_count()
        if not err:
            if low_stock > 0:
                text = f"{falling_low} Products Are Falling To Minimum Soon."
                self.labels.append((text, "stock_warning"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Warning Stock Count.",
                parent=self.master
            )
        orders, err = self.summary.fetch_pending_orders_count()
        if not err:
            if low_stock > 0:
                text = f"{orders} Orders Are Pending Delivery."
                self.labels.append((text, "orders"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Pending Orders Count.",
                parent=self.master
            )
        deleted, err = self.summary.fetch_inactive_products_count()
        if not err:
            if deleted > 0:
                text = f"{deleted} Products Are Deleted (Archived)."
                self.labels.append((text, "deleted"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Delete Products Count.",
                parent=self.master
            )
        unsold, err = self.summary.fetch_unsold_product_count()
        if not err:
            if unsold > 0:
                text = f"{unsold} Items In Stock Have Never Been Sold."
                self.labels.append((text, "unsold"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Unsold Products Count.",
                parent=self.master
            )
        unsold_m, err = self.summary.fetch_unsold_product_count(
            curr_year, curr_month
        )
        if not err:
            if unsold_m > 0:
                text = f"{unsold_m} Items Haven't Been Sold This Month."
                self.labels.append((text, "unsold_month"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Unsold Products Count Monthly.",
                parent=self.master
            )
        unsold_y, err = self.summary.fetch_unsold_product_count(curr_year)
        if not err:
            if unsold_y > 0:
                text = f"{unsold_y} Items Haven't Been Sold This Year."
                self.labels.append((text, "unsold_year"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Unsold Products Count Yearly.",
                parent=self.master
            )
        stock_items, err = self.summary.fetch_total_products()
        if not err:
            if stock_items > 0:
                text = f"Total Current Items In Stock Are; {stock_items}."
                self.labels.append((text, "all_stock"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Total Current Stock Items.",
                parent=self.master
            )
        stock_value, err = self.summary.fetch_total_inventory_value()
        if not err:
            if stock_value > 0:
                text = f"Current Stock Value is; {stock_value:,}."
                self.labels.append((text, "stock_value"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Current Stock Value.",
                parent=self.master
            )
        inactive_u, err = self.summary.fetch_disabled_user_count()
        if not err:
            if stock_value > 0:
                text = f"{inactive_u} Users Disabled From Loging In."
                self.labels.append((text, "disabled_users"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Disabled Users Count.",
                parent=self.master
            )
        active, err = self.summary.fetch_active_users_count()
        if not err:
            if active > 0:
                text = f"{active} Current Active Users."
                self.labels.append((text, "active_users"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Active Users.", parent=self.master
            )
        all_users = active + inactive_u
        if all_users > 0:
            text = f"Number Of All System Users; {all_users}."
            self.labels.append((text, "all_users"))

    def render_summary_labels(self):
        label_area = self.inside_frame.scrollable_frame
        # Clear existing widgets
        for widget in label_area.winfo_children():
            widget.destroy()
        for i, (text, action) in enumerate(self.labels, start=1):
            lbl = tk.Label(
                label_area, text=f"{i}. {text}", bg="white", fg="blue",
                cursor="hand2", font=("Arial", 12, "bold")
            )
            lbl.pack(anchor="w", pady=5)
            # Hover effect
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(fg="darkred"))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(fg="blue"))
            # Click action
            lbl.bind(
                "<Button-1>", lambda e, a=action: self.on_summary_click(a)
            )

    def on_summary_click(self, action):
        """
        Handles all summary clicks and routes to the correct preview window.
        """
        curr_year = date.today().year
        curr_month = date.today().month
        stock_columns = {
            "Product Code": "product_code",
            "Product Name": "product_name",
            "Quantity": "quantity",
            "Cost": "cost",
            "Wholesale Price": "wholesale_price",
            "Retail Price": "retail_price",
            "Min Level": "min_stock_level",
            "Date Restocked": "date_replenished"
        }
        user_columns = {
            "Employee Name": "name",
            "Username": "username",
            "Department": "department",
            "Designation": "designation",
            "Phone Number": "phone",
            "Employee Email": "email",
            "User Code": "user_code",
            "Status": "status"
        }
        if action == "out_of_stock":
            self.open_summary_window(
                "Out Of Stock Products",
                stock_columns,
                self.summary.fetch_out_of_stock_products
            )
        elif action == "low_stock":
            self.open_summary_window(
                "Products Below Minimum Stock Level",
                stock_columns,
                self.summary.fetch_low_stock_products
            )
        elif action == "stock_warning":
            self.open_summary_window(
                "Product Falling Minimum Stock Level Soon.",
                stock_columns,
                self.summary.fetch_low_stock_warning_products
            )
        elif action == "stock_warning":
            self.open_summary_window(
                "Product Falling Minimum Stock Level Soon.",
                stock_columns,
                self.summary.fetch_low_stock_warning_products
            )
        elif action == "orders":
            PendingOrdersWindow(self.master, self.conn, self.user)
        elif action == "deleted":
            DeletedItemsWindow(self.master, self.conn, self.user)
        elif action == "unsold":
            self.open_summary_window(
                "Products Never Sold",
                stock_columns,
                self.summary.fetch_unsold_products
            )
        elif action == "unsold_month":
            self.open_summary_window(
                "Products Not Sold This Month.",
                stock_columns,
                self.summary.fetch_unsold_products,
                [curr_year, curr_month]
            )
        elif action == "unsold_year":
            self.open_summary_window(
                "Products Not Sold This Year.",
                stock_columns,
                self.summary.fetch_unsold_products,
                [curr_year]
            )
        elif action == "all_stock":
            self.open_summary_window(
                "All Products In Stock.",
                stock_columns,
                self.summary.fetch_all_stock_products
            )
        elif action == "stock_value":
            messagebox.showinfo(
                "Stock Value", "Access Stock Value In Stock Module.",
                parent=self.master
            )
        elif action == "disabled_users":
            self.open_summary_window(
                "Users Denied Access To The System.",
                user_columns,
                self.summary.fetch_disabled_users
            )
        elif action == "active_users":
            self.open_summary_window(
                "Current Active Employees.",
                user_columns,
                self.summary.fetch_active_users
            )
        elif action == "all_users":
            messagebox.showinfo(
                "Employees Info",
                "Get All Employees Info In Human Resource Module",
                parent=self.master
            )

    def open_summary_window(self, title, columns, fetch, param=None):
        if not param:
            SummaryPreviewWindow(self.conn, title, columns, fetch)
        else:
            SummaryPreviewWindow(self.conn, title, columns, fetch, param)


    def sales_window(self):
        # Verify user privilege
        if not self.has_privilege("Manage Sales"):
            return
        SalesGUI(self.master, self.conn, self.user)

    def stock_window(self):
        # Verify user privilege
        if not self.has_privilege("Manage Stock"):
            return
        StockWindow(self.master, self.conn, self.user)

    def order_window(self):
        # Verify user privilege
        if not self.has_privilege("Manage Orders"):
            return
        OrdersWindow(self.master, self.conn, self.user)

    def stock_details_window(self):
        # Verify user privilege
        if not self.has_privilege("Manage Stock"):
            return
        ProductsDetailsWindow(self.master, self.conn, self.user)

    def employee_window(self):
        # Verify user privilege
        if not self.has_privilege("Manage Users"):
            return
        EmployeeManagementWindow(self.master, self.conn, self.user)

    def accounting_window(self):
        # Verify user privilege
        if not self.has_privilege("Manage Accounting"):
            return
        AccountWindow(self.master, self.conn, self.user)

    def logs_window(self):
        # Verify user privilege
        if not self.has_privilege("Manage Logs"):
            return
        SystemLogsWindow(self.master, self.conn, self.user)

    def monthly_sales_window(self):
        if not self.has_privilege("Sales Report"):
            return
        MonthlySalesSummary(self.master, self.conn)

    def sales_record_window(self):
        if not self.has_privilege("View Sales Records"):
            return
        YearlySalesWindow(self.master, self.conn, self.user)

    def sales_performance_window(self):
        if not self.has_privilege("Sales Report"):
            return
        YearlyProductSales(self.master, self.conn, self.user)

    def reversal_window(self):
        if not self.has_privilege("View Sales Logs"):
            return
        MonthlyReversalLogs(self.master, self.conn, self.user)

    def sales_logs_window(self):
        if not self.has_privilege("View Sales Logs"):
            return
        SalesLogsWindow(self.master, self.conn, self.user)

    def new_product_window(self):
        if not self.has_privilege("Admin New Product"):
            return
        NewProductPopup(self.master, self.conn, self.user)

    def delete_item_window(self):
        if not self.has_privilege("Admin Delete Product"):
            return
        DeleteProductPopup(self.master, self.conn, self.user)

    def restore_item_gui(self):
        if not self.has_privilege("Admin Restore Product"):
            return
        RestoreProductPopup(self.master, self.conn, self.user)

    def deleted_products_gui(self):
        if not self.has_privilege("Manage Stock"):
            return
        DeletedItemsWindow(self.master, self.conn, self.user)

    def reconciliation_window(self):
        if not self.has_privilege("Manage Stock"):
            return
        ReconciliationWindow(self.master, self.conn, self.user)

    def stock_logs_window(self):
        if not self.has_privilege("View Product Logs"):
            return
        ProductLogsWindow(self.master, self.conn, self.user)

    def new_order_window(self):
        if not self.has_privilege("Receive Order"):
            return
        NewOrderWindow(self.master, self.conn, self.user)

    def edit_orders_window(self):
        if not self.has_privilege("Edit Order"):
            return
        EditOrdersWindow(self.master, self.conn, self.user)

    def ordered_items_window(self):
        if not self.has_privilege("View Ordered Items"):
            return
        OrderedItemsWindow(self.master, self.conn, self.user)

    def order_logs_window(self):
        if not self.has_privilege("View Order Logs"):
            return
        OrderLogsWindow(self.master, self.conn, self.user)

    def create_journal_account(self):
        # Verify user privilege
        if not self.has_privilege("Create Journal Accounts"):
            return
        InsertAccountPopup(self.master, self.conn, self.user)

    def initial_account_balance(self):
        # Verify user privilege
        privilege = "Initial Balances"
        if not self.has_privilege(privilege):
            return
        OpeningBalancePopup(self.master, self.conn, self.user)

    def delete_reverse_journal_entry(self):
        privilege = "Reverse Journal"
        if not self.has_privilege(privilege):
            return
        ReverseJournalPopup(self.master, self.conn, self.user)

    def close_financial_year_window(self):
        # Verify Access
        privilege = "Close Accounting Books"
        if not self.has_privilege(privilege):
            return
        CloseYearPopup(self.master, self.conn, self.user)

    def finance_logs_window(self):
        # Verify Access
        privilege = "View Finance Logs"
        if not self.has_privilege(privilege):
            return
        FinanceLogsWindow(self.master, self.conn, self.user)

    def departments_window(self):
        # Verify user privilege
        if not self.has_privilege("Add Department"):
            return
        DepartmentsPopup(self.master, self.conn, self.user)

    def create_privilege_window(self):
        # Verify user privilege
        if not self.has_privilege("Create Privilege"):
            return
        PrivilegePopup(self.master, self.conn, self.user)

    def new_user_window(self):
        # Verify user privilege
        if not self.has_privilege("Add User"):
            return
        EmployeePopup(self.master, self.conn, self.user)

    def edit_user(self):
        if not self.has_privilege("Edit Employee"):
            return
        EditEmployeeWindow(self.master, self.conn, self.user)

    def privileges_window(self):
        # Verify user privilege
        if not self.has_privilege("View User Privilege"):
            return
        UserPrivilegesPopup(self.master, self.conn, self.user)

    def assign_window(self):
        # Verify user privilege
        if not self.has_privilege("Assign Privilege"):
            return
        AssignPrivilegePopup(self.master, self.conn, self.user)

    def remove_window(self):
        # Verify user privilege
        if not self.has_privilege("Remove Privilege"):
            return
        RemovePrivilegePopup(self.master, self.conn, self.user)

    def activate_deactivate_window(self):
        # Verify user privilege
        privilege = "Deactivate User" or "Activate User"
        if not self.has_privilege(privilege):
            return
        LoginStatusPopup(self.master, self.conn, self.user)

    def reset_password_window(self):
        if not self.has_privilege("Reset Password"):
            return
        ResetPasswordPopup(self.master, self.conn, self.user)


if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root = tk.Tk()
    root.withdraw()
    AdminWindow(conn, "Sniffy")
    root.mainloop()