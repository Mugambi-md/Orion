import tkinter as tk
from tkinter import messagebox, Menu
from authentication import VerifyPrivilegePopup
from windows_utils import ScrollableFrame
from sales_report_gui import (
    SalesGUI, MakeSaleWindow, CashierReturnTreasury, CashierEndDay
)
from stock_gui import StockWindow
from orders_gui import OrdersWindow
from accounting_gui import AccountWindow
from employee_gui import EmployeeManagementWindow

from employee_gui_popup import ChangePasswordPopup

class SystemDashboard:
    def __init__(self, conn, user):
        self.window = tk.Toplevel()
        self.window.title("Swift Glance System")
        self.window.iconbitmap("myicon.ico")
        self.window.configure(bg="lightblue")
        self.window.state("zoomed")
        # self.window.transient(master)
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
        btn_frame = ScrollableFrame(self.main_frame, "lightgray", 150)
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
                button_frame, text=text, command=command, bg="dodgerblue",
                fg="white", bd=4, relief="groove", width=len(text), height=1,
                font=("Arial", 12, "bold")
            ).pack(side="left", ipadx=5)
        btn_frame = tk.Frame(button_frame, height=1)
        btn_frame.pack(side="left")
        power_btn = tk.Button(
            btn_frame, text="⭕", font=("Arial", 16, "bold"),
            fg="red", width=2, height=1, relief="ridge",
            command=self.window.destroy
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
        tk.Label(
            btn_area, text="Sales Shortcuts", fg="blue", bg="lightgray",
            font=("Arial", 11, "bold", "underline")
        ).pack(anchor="w", pady=(5, 0))
        sales_btn = {
            "Make Sales": "Selling",
            "Return Treasury": "Return Treasury",
            "Cashier EOD": "EOD",
        }
        for text, action in sales_btn.items():
            tk.Button(
                btn_area, text=text, bg="dodgerblue", bd=4, relief="groove",
                fg="white", width=15, font=("Arial", 11, "bold"),
                command=lambda a=action: self.shortcuts_windows(a)
            ).pack(ipadx=5, padx=5)
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
        elif action == "Return Treasury":
            if not self.has_privilege("Manage Cashiers"):
                return
            CashierReturnTreasury(self.window, self.conn, self.user)
        elif action == "EOD":
            if not self.has_privilege("Manage Cashiers"):
                return
            CashierEndDay(self.window, self.conn, self.user)

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
    app = SystemDashboard(conn, "Sniffy")
    root.mainloop()



