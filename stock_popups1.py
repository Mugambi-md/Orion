import tkinter as tk
from datetime import date
from tkinter import messagebox
from base_window import BaseWindow
from windows_utils import ScrollableFrame
from stock_summary import  FetchSummary
from summary_gui import SummaryPreviewWindow
from  order_windows import PendingOrdersWindow
from stock_windows import DeletedItemsWindow


class WindowTest(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Window Summary Display Test")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 900, 650, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.summary = FetchSummary(self.conn)
        self.labels = []

        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.right_frame = tk.Frame(
            self.main_frame, bg="lightgray", bd=4, relief="ridge", width=300
        )
        self.inside_frame = ScrollableFrame(self.right_frame, "white")

        self.build_ui()
        self.show_summary()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
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
    root=tk.Tk()
    WindowTest(root, conn, "Sniffy")
    root.mainloop()