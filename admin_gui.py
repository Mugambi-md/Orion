import tkinter as tk
from tkinter import messagebox
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
from stock_popups1 import DeleteProductPopup, RestoreProductPopup
from stock_popups import (
    NewProductPopup, ReconciliationWindow,
    DeletedItemsWindow
)
from order_windows import OrderedItemsWindow, EditOrdersWindow
from account_popups import (
    OpeningBalancePopup, CloseYearPopup, InsertAccountPopup,
    ReverseJournalPopup
)
from employee_gui_popup import (
    EmployeePopup, LoginStatusPopup, PrivilegePopup, AssignPrivilegePopup,
    UserPrivilegesPopup, DepartmentsPopup, RemovePrivilegePopup,
    ResetPasswordPopup, EditEmployeeWindow
)


class AdminWindow:
    def __init__(self, conn, user):
        self.master = tk.Toplevel()
        self.master.title("Admin System Management")
        self.master.configure(bg="lightblue")
        self.master.state("zoomed")
        self.master.grab_set()

        self.conn = conn
        self.user = user

        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.center_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )


        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        btn_frame = ScrollableFrame(self.main_frame, "lightblue", 150)
        btn_frame.pack(side="left", fill="y")
        btn_area = btn_frame.scrollable_frame
        self.center_frame.pack(side="left", fill="both", expand=True)
        nav_frame = tk.Frame(
            self.center_frame, bg="lightblue", bd=2, relief="ridge"
        )
        nav_frame.pack(side="top", fill="x", ipadx=20)
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

        free_frame = tk.Frame(self.center_frame, bd=4, relief="ridge")
        free_frame.pack(side="left", fill="both", expand=True)

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