import tkinter as tk
from tkinter import messagebox, Menu
from datetime import date
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
    OrdersWindow, NewOrderWindow, UnpaidOrdersWindow, EditOrdersWindow,
    PendingOrdersWindow
)
from accounting_gui import (
    AccountWindow, JournalEntryPopup, ReverseJournalPopup, ViewJournalWindow
)
from employee_gui import EmployeeManagementWindow
from employee_gui_popup import ChangePasswordPopup
from stock_summary import  FetchSummary
from summary_gui import SummaryPreviewWindow


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
        self.summary = FetchSummary(self.conn)
        self.labels = []
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.center_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.right_frame = tk.Frame(
            self.center_frame, bg="lightgray", bd=4, relief="ridge"
        )
        self.inside_frame = ScrollableFrame(self.right_frame, "white")


        self.create_widgets()
        self.show_summary()

    def create_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10)
        left_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        left_frame.pack(side="left", fill="y")
        tk.Label(
            left_frame, text="SwiftGlance", bg="lightblue", fg="blue",
            bd=4, relief="groove", font=("Arial", 20, "bold", "underline")
        ).pack(side="top", fill="x", ipady=5)
        btn_frame = ScrollableFrame(left_frame, "lightgray", 170)
        btn_frame.pack(side="left", fill="y")
        btn_area = btn_frame.scrollable_frame
        button_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        button_frame.pack(side="top", fill="x", ipadx=5)
        self.center_frame.pack(fill="both", expand=True)
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
                parent=self.window
            )
        low_stock, err = self.summary.fetch_low_stock_count()
        if not err:
            if  low_stock > 0:
                text = f"{low_stock} Products Are Bellow Minimum Level."
                self.labels.append((text, "low_stock"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Below Stock Level Count.",
                parent=self.window
            )
        falling_low, err = self.summary.fetch_low_stock_warning_count()
        if not err:
            if low_stock > 0:
                text = f"{falling_low} Products Are Falling To Minimum Soon."
                self.labels.append((text, "stock_warning"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Warning Stock Count.",
                parent=self.window
            )
        orders, err = self.summary.fetch_pending_orders_count()
        if not err:
            if low_stock > 0:
                text = f"{orders} Orders Are Pending Delivery."
                self.labels.append((text, "orders"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Pending Orders Count.",
                parent=self.window
            )
        deleted, err = self.summary.fetch_inactive_products_count()
        if not err:
            if deleted > 0:
                text = f"{deleted} Products Are Deleted (Archived)."
                self.labels.append((text, "deleted"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Delete Products Count.",
                parent=self.window
            )
        unsold, err = self.summary.fetch_unsold_product_count()
        if not err:
            if unsold > 0:
                text = f"{unsold} Items In Stock Have Never Been Sold."
                self.labels.append((text, "unsold"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Unsold Products Count.",
                parent=self.window
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
                parent=self.window
            )
        unsold_y, err = self.summary.fetch_unsold_product_count(curr_year)
        if not err:
            if unsold_y > 0:
                text = f"{unsold_y} Items Haven't Been Sold This Year."
                self.labels.append((text, "unsold_year"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Unsold Products Count Yearly.",
                parent=self.window
            )
        stock_items, err = self.summary.fetch_total_products()
        if not err:
            if stock_items > 0:
                text = f"Total Current Items In Stock Are; {stock_items}."
                self.labels.append((text, "all_stock"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Total Current Stock Items.",
                parent=self.window
            )
        stock_value, err = self.summary.fetch_total_inventory_value()
        if not err:
            if stock_value > 0:
                text = f"Current Stock Value is; {stock_value:,}."
                self.labels.append((text, "stock_value"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Current Stock Value.",
                parent=self.window
            )
        inactive_u, err = self.summary.fetch_disabled_user_count()
        if not err:
            if stock_value > 0:
                text = f"{inactive_u} Users Disabled From Loging In."
                self.labels.append((text, "disabled_users"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Disabled Users Count.",
                parent=self.window
            )
        active, err = self.summary.fetch_active_users_count()
        if not err:
            if active > 0:
                text = f"{active} Current Active Users."
                self.labels.append((text, "active_users"))
        else:
            messagebox.showerror(
                "Error", f"Error Fetching Active Users.", parent=self.window
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
            PendingOrdersWindow(self.window, self.conn, self.user)
        elif action == "deleted":
            DeletedItemsWindow(self.window, self.conn, self.user)
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
                parent=self.window
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
                parent=self.window
            )

    def open_summary_window(self, title, columns, fetch, param=None):
        if not param:
            SummaryPreviewWindow(self.conn, title, columns, fetch)
        else:
            SummaryPreviewWindow(self.conn, title, columns, fetch, param)




if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root = tk.Tk()
    root.withdraw()
    app = SystemDashboard(conn, "Sniffy")
    root.mainloop()



