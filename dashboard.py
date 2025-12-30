import tkinter as tk
from tkinter import messagebox, Menu
from authentication import VerifyPrivilegePopup
from windows_utils import ScrollableFrame
from sales_report_gui import (
    SalesGUI, MakeSaleWindow, CashierReturnTreasury, CashierEndDay,
    YearlyProductSales, SalesReversalWindow, SalesControlReportWindow
)
from stock_gui import (
    StockWindow, NewProductPopup, ReconciliationWindow, AddStockPopup,
    ProductsDetailsWindow
)
from stock_windows import DeletedItemsWindow
from orders_gui import (
    OrdersWindow, NewOrderWindow, UnpaidOrdersWindow, EditOrdersWindow
)
from accounting_gui import (
    AccountWindow, JournalEntryPopup, ReverseJournalPopup, ViewJournalWindow
)
from employee_gui import EmployeeManagementWindow

from employee_gui_popup import ChangePasswordPopup

class SystemDashboard:
    def __init__(self, conn, user):
        self.window = tk.Toplevel()
        self.window.title("Swift Glance System")
        self.window.iconbitmap("myicon.ico")
        self.window.configure(bg="lightblue")
        self.window.state("zoomed")
        self.window.grab_set()

        self.user = user
        self.conn = conn
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.center_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )

        self.create_widgets()

    def create_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10)
        left_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        left_frame.pack(side="left", fill="y")
        tk.Label(
            left_frame, text="SwiftGlance", bg="lightblue", fg="blue", bd=4,
            relief="groove", font=("Arial", 20, "bold", "underline")
        ).pack(side="top", fill="x", ipady=5)
        btn_frame = ScrollableFrame(left_frame, "lightgray", 170)
        btn_frame.pack(side="left", fill="y")
        button_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        button_frame.pack(side="top", fill="x", ipadx=5)
        self.center_frame.pack(fill="both", expand=True)
        btn_area = btn_frame.scrollable_frame
        # Button Labels and their corresponding command
        buttons = {
            "Sales": self.sales_window,
            "Stock": self.stock_window,
            "Orders": self.orders_window,
            "Finance": self.accounts_window,
            "Marketing": self.marketing_window,
            "Human Resource": self.hr_window
        }
        for text, command in buttons.items():
            tk.Button(
                button_frame, text=text, command=command, bg="blue",
                fg="white", bd=4, relief="groove", width=len(text), height=1,
                font=("Arial", 14, "bold")
            ).pack(side="left", ipadx=5)
        btn_frame = tk.Frame(button_frame)
        btn_frame.pack(side="left")
        power_btn = tk.Button(
            btn_frame, text="⭕", font=("Arial", 16, "bold"), fg="red",
            width=2, relief="ridge", command=self.window.destroy
        )
        power_btn.pack(side="left")
        arrow_btn = tk.Menubutton(
            btn_frame, text="▽", font=("Arial", 11), relief="ridge",
            anchor="sw", fg="#FF6666"
        )
        arrow_menu = Menu(arrow_btn, tearoff=0)
        arrow_menu.add_command(
            label="Log Out", command=self.window.destroy
        )
        arrow_menu.add_command(
            label="Change Password", command=self.change_password
        )
        arrow_btn.config(menu=arrow_menu)
        arrow_btn.pack(side="bottom")
        foot_frame = tk.Frame(self.window, bg="white", bd=2, relief="ridge")
        foot_frame.pack(side="bottom", fill="x")
        tk.Label(
            foot_frame, text=f"User: {self.user}", bg="white", width=10,
            fg="blue", font=("Arial", 11, "italic")
        ).pack(side="left", padx=(5, 40))
        footer = tk.Label(
            foot_frame, text="POINT OF SALE SYSTEM v1.0", bg="white",
            fg="blue", font=("Arial", 12, "italic"), width=30
        )
        footer.pack(side="left", padx=40)
        tk.Label(
            btn_area, text="Sales Shortcuts", fg="blue", bg="lightgray",
            font=("Arial", 12, "bold", "underline")
        ).pack(anchor="w", pady=(5, 0))
        sales_btn = {
            "Make Sales": "Selling",
            "Tag Reversal": "Tag",
            "Reversal Posting": "Posting",
            "Return Treasury": "Return Treasury",
            "Cashier EOD": "EOD",
            "Sales Impact": "Impact"
        }
        for text, action in sales_btn.items():
            tk.Button(
                btn_area, text=text, bg="dodgerblue", bd=4, relief="groove",
                fg="white", width=15, font=("Arial", 11, "bold"),
                command=lambda a=action: self.shortcuts_windows(a)
            ).pack(ipadx=5, padx=5)
        tk.Label(
            btn_area, text="Stock Shortcuts", fg="blue", bg="lightgray",
            font=("Arial", 12, "bold", "underline")
        ).pack(anchor="w", pady=(5, 0))
        stock_btn = {
            "New Product": "New",
            "Restock": "Add Stock",
            "Deleted Items": "Deleted",
            "Reconciliation": "Reconciliation",
            "Stock Reports": "Report"
        }
        for text, action in stock_btn.items():
            tk.Button(
                btn_area, text=text, bg="dodgerblue", bd=4, relief="groove",
                fg="white", width=15, font=("Arial", 11, "bold"),
                command=lambda a=action: self.shortcuts_windows(a)
            ).pack(ipadx=5, padx=5)
        tk.Label(
            btn_area, text="Order Shortcuts", fg="blue", bg="lightgray",
            font=("Arial", 12, "bold", "underline")
        ).pack(anchor="w", pady=(5, 0))
        orders_btn = {
            "Receive Orders": "Order",
            "Unpaid Orders": "Unpaid Order",
            "Edit Order": "Edit"
        }
        for text, action in orders_btn.items():
            tk.Button(
                btn_area, text=text, bg="dodgerblue", bd=4, relief="groove",
                fg="white", width=15, font=("Arial", 11, "bold"),
                command=lambda a=action: self.shortcuts_windows(a)
            ).pack(ipadx=5, padx=5)
        tk.Label(
            btn_area, text="Finance Shortcuts", fg="blue", bg="lightgray",
            font=("Arial", 12, "bold", "underline")
        ).pack(anchor="w", pady=(5, 0), padx=(0, 5))
        finance_btn = {
            "Payment": "Paying",
            "Payment Reversal": "Reverse",
            "View Journals": "View"
        }
        for text, action in finance_btn.items():
            tk.Button(
                btn_area, text=text, bg="dodgerblue", bd=4, relief="groove",
                fg="white", width=15, font=("Arial", 11, "bold"),
                command=lambda a=action: self.shortcuts_windows(a)
            ).pack(ipadx=5, padx=(5, 0))

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

    def shortcuts_windows(self, action):
        if action == "Selling":
            if not self.has_privilege("Make Sale"):
                return
            MakeSaleWindow(self.window, self.conn, self.user)
        elif action == "Tag":
            if not self.has_privilege("Tag Reversal"):
                return
            SalesControlReportWindow(self.window, self.conn, self.user)
        elif action == "Return Treasury":
            if not self.has_privilege("Manage Cashiers"):
                return
            CashierReturnTreasury(self.window, self.conn, self.user)
        elif action == "EOD":
            if not self.has_privilege("Manage Cashiers"):
                return
            CashierEndDay(self.window, self.conn, self.user)
        elif action == "Order":
            if not self.has_privilege("Receive Order"):
                return
            NewOrderWindow(self.window, self.conn, self.user)
        elif action == "Unpaid Order":
            if not self.has_privilege("Receive Order Payment"):
                return
            UnpaidOrdersWindow(self.window, self.conn, self.user)
        elif action == "Edit":
            if not self.has_privilege("Edit Order"):
                return
            EditOrdersWindow(self.window, self.conn, self.user)
        elif action == "Impact":
            if not self.has_privilege("Sales Report"):
                return
            YearlyProductSales(self.window, self.conn, self.user)
        elif action == "Posting":
            if not self.has_privilege("Manage Sales"):
                return
            SalesReversalWindow(self.window, self.conn, self.user)
        elif action == "New":
            if not self.has_privilege("Admin New Product"):
                return
            NewProductPopup(self.window, self.conn, self.user)
        elif action == "Add Stock":
            if not self.has_privilege("Add Stock"):
                return
            AddStockPopup(self.window, self.conn, self.user)
        elif action == "Deleted":
            if not self.has_privilege("Manage Stock"):
                return
            DeletedItemsWindow(self.window, self.conn, self.user)
        elif action == "Reconciliation":
            if not self.has_privilege("View Products"):
                return
            ReconciliationWindow(self.window, self.conn, self.user)
        elif action == "Report":
            if not self.has_privilege("Stock Level"):
                return
            ProductsDetailsWindow(self.window, self.user, self.conn)
        elif action == "Paying":
            if not self.has_privilege("Make Payment"):
                return
            JournalEntryPopup(self.window, self.conn, self.user)
        elif action == "Reverse":
            if not self.has_privilege("Reverse Payment"):
                return
            ReverseJournalPopup(self.window, self.conn, self.user)
        elif action == "View":
            if not self.has_privilege("View Journal"):
                return
            ViewJournalWindow(self.window, self.conn, self.user)

    def sales_window(self):
        if not self.has_privilege("Manage Sales"):
            return
        SalesGUI(self.window, self.conn, self.user)

    def stock_window(self):
        if not self.has_privilege("Manage Stock"):
            return
        StockWindow(self.window, self.conn, self.user)

    def orders_window(self):
        if not self.has_privilege("Manage Orders"):
            return
        OrdersWindow(self.window, self.conn, self.user)

    def accounts_window(self):
        if not self.has_privilege("Manage Accounting Books"):
            return
        AccountWindow(self.window, self.conn, self.user)

    def marketing_window(self):
        messagebox.showinfo(
            "Marketing", "Marketing Module Coming Soon.", parent=self.window
        )

    def hr_window(self):
        if not self.has_privilege("Manage Users"):
            return
        EmployeeManagementWindow(self.window, self.conn, self.user)

    def change_password(self):
        ChangePasswordPopup(self.window, self.conn, self.user)




if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root = tk.Tk()
    root.withdraw()
    app = SystemDashboard(conn, "Johnie")
    root.mainloop()



