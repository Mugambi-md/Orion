import re
import tkinter as tk
from tkinter import ttk, messagebox
from window_functionality import to_uppercase
from windows_utils import CurrencyFormatter
from table_utils import TreeviewSorter
from working_sales import (
    fetch_sales_product, SalesManager, get_net_sales, CashierSessionService
)
from receipt_gui_and_print import ReceiptPrinter
from lookup_gui import ProductSearchWindow
from sales_popup import Last24HoursSalesWindow
from base_window import BaseWindow


class MakeSaleWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.sale_win = tk.Toplevel(parent)
        self.sale_win.title("Make Sales")
        self.center_window(self.sale_win, 1000, 600, parent)
        self.sale_win.configure(bg="lightblue")
        self.sale_win.grab_set()
        self.sale_win.transient(parent)

        self.conn = conn
        self.user = user
        self.sale_items = []  # Keep track of sales list
        self.payment_list = []  # Keep track of payments
        self.columns = [
            "No", "Product Code", "Product Name", "Quantity", "Price",
            "Total"
        ]
        style = ttk.Style(self.sale_win)
        style.theme_use("clam")
        self.total_cost_var = tk.StringVar(value="0.00")
        self.sales_manager = SalesManager(self.conn)
        self.valid_session = CashierSessionService(conn)
        success, totals = get_net_sales(conn, user)
        if success:
            day_sales = float(totals["net_sales"])
        else:
            messagebox.showerror(
                "Error", "Failed To Load Total Daily Sales.",
                parent=self.sale_win
            )
            day_sales = None
            self.sale_win.destroy()

        self.main_frame = tk.Frame(
            self.sale_win, bg="lightblue", bd=4, relief="solid"
        )
        self.left_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.add_frame = tk.LabelFrame(
            self.left_frame, bg="white", text="Add To Sales List"
        )
        sales = f"{day_sales:,.2f}"
        self.net_label = tk.Label(
            self.add_frame, text=sales, bg="blue", fg="white", width=10,
            bd=2, relief="ridge", font=("Arial", 11, "bold")
        )
        self.right_frame = tk.Frame(self.main_frame, bg="white")
        self.sale_list = ttk.Treeview(
            self.right_frame, columns=self.columns, show="headings"
        )
        self.search_entry = tk.Entry(
            self.add_frame, width=15, bd=4, relief="raised",
            font=("Arial", 11)
        )
        self.quantity_entry = tk.Entry(
            self.add_frame, width=10, state="disabled", bd=2,
            relief="raised", font=("Arial", 11)
        )
        self.add_button = tk.Button(
            self.add_frame, text="Add To List", state="disabled", bd=4,
            relief="groove", bg="blue", fg="white", command=self.add_to_list
        )
        self.post_sale_button = tk.Button(
            self.add_frame, text="Post Sale", state="disabled", bd=4,
            width=10, relief="groove", command=self.show_payment_popup
        )
        (self.product_code, self.product_name, self.available_quantity,
         self.wholesale_price, self.retail_price) = None, None, None, None, None
        self.sorter = TreeviewSorter(self.sale_list, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.bind_mousewheel()

        self.create_widgets()
        self.check_allowed()
        self.sorter.autosize_columns(10)

    def create_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Lef Frame
        self.left_frame.pack(side="left", fill="y")
        # Right Frame
        self.right_frame.pack(side="right", expand=True, fill="both")
        # Add to sales list section
        tk.Label(self.left_frame, bg="lightblue", text="").pack(pady=8)
        self.add_frame.pack(fill="x")
        tk.Label(
            self.add_frame, text="Product Code:", bg="white",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), anchor="w")
        self.search_entry.pack(padx=5, pady=(0, 5))
        self.search_entry.focus_set()
        self.search_entry.bind(
            "<KeyRelease>", lambda event: to_uppercase(self.search_entry)
        )
        self.search_entry.bind("<Return>", lambda e: self.search_product())
        tk.Button(
            self.add_frame, text="Search", width=10, bd=4, relief="groove",
            bg="lightgreen", fg="white", command=self.search_product
        ).pack(ipadx=5, pady=(0, 5))
        tk.Label(
            self.add_frame, text="Item Quantity:", bg="white",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), anchor="w")
        self.quantity_entry.pack(padx=10, pady=(0, 5))
        self.quantity_entry.bind("<Return>", lambda e: self.add_to_list())
        self.add_button.pack(padx=10, ipadx=5)
        self.post_sale_button.pack(padx=10, ipadx=5)
        self.net_label.pack(side="left", pady=10, ipady=5)
        tk.Button(
            self.add_frame, text=f"Logs ΞΞ", bg="blue", fg="white",
            bd=4, relief="ridge", command=self.logs_window, height=1,
            font=("Arial", 11, "bold")
        ).pack(side="left", ipadx=2, pady=10)
        tk.Button(
            self.left_frame, text="Look Up Products", bg="green", fg="white",
            bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.lookup_product
        ).pack(pady=5)
        btn_frame = tk.Frame(self.right_frame, bg="lightblue")
        btn_frame.pack(side="top", fill="x")
        tk.Button(
            btn_frame, text="Remove Item", bg="red", fg="white", bd=4,
            relief="ridge", font=("Arial", 10, "bold"),
            command=self.remove_selected
        ).pack(side="right", anchor="s")
        tk.Label(
            btn_frame, text="Sale List", bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline")
        ).pack(anchor="center")
        vsb = ttk.Scrollbar(
            self.right_frame, orient="vertical", command=self.sale_list.yview
        )
        self.sale_list.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        # Sales List Table
        for col in self.columns:
            self.sale_list.heading(col, text=col)
            self.sale_list.column(col, anchor="center", width=50)
        self.sale_list.pack(fill="both", expand=True)
        self.sale_list.tag_configure(
            "total", font=("Arial", 12, "bold", "underline")
        )

    def refresh_label(self):
        """Refreshes total sales label."""
        success, sales = get_net_sales(self.conn, self.user)
        if not success:
            messagebox.showerror(
                "Error",
                f"Failed to Load Net Sales: {sales}.", parent=self.sale_win
            )
        day_sale = float(sales["net_sales"])
        self.net_label.configure(text=f"{day_sale:,.2f}")

    def check_allowed(self):
        """Check if user closed previous day."""
        success, msg = self.valid_session.can_sell(self.user)
        if not success:
            messagebox.showwarning(
                "Close Day", f"Not Allowed To sell:\n{msg}",
                parent=self.sale_win
            )
            self.search_entry.configure(state="disabled")

    def search_product(self):
        code = self.search_entry.get().strip().upper()
        if not code:
            messagebox.showerror(
                "Error", "Please Enter Product Code.", parent=self.sale_win
            )
            return
        result = fetch_sales_product(self.conn, code)
        if isinstance(result, tuple):
            (self.product_code, self.product_name, self.available_quantity,
             self.wholesale_price, self.retail_price) = result
            answer = messagebox.askyesno(
                "Confirm", f"Add '{self.product_name}' to Sale?",
                parent=self.sale_win
            )
            if answer:
                self.quantity_entry.configure(state="normal")
                self.add_button.configure(state="normal")
                self.post_sale_button.configure(state="normal")
                self.quantity_entry.focus_set()
        else:
            messagebox.showerror("Not Found", result, parent=self.sale_win)

    def add_to_list(self):
        qty_str = self.quantity_entry.get().strip()
        if not qty_str.isdigit():
            messagebox.showerror(
                "Invalid", "Please Enter Valid Quantity.",
                parent=self.sale_win
            )
            return
        qty = int(qty_str)
        if qty > self.available_quantity:
            messagebox.showerror(
                "Not Enough Stock",
                "You Don't Have Enough Quantity to Sell.\n"
                f"Available quantity is {self.available_quantity}.",
                parent=self.sale_win
            )
            return
        existing_item = None
        for i, item in enumerate(self.sale_items):
            if item[1] == self.product_code:
                existing_item = (i, item)
                break
        if existing_item:
            index, old_item = existing_item
            old_qty = old_item[3]
            new_qty = old_qty + qty
            price = self.wholesale_price if new_qty >= 10 else self.retail_price
            total = new_qty * price
            name = re.sub(r"\s+", " ", str(self.product_name)).strip()
            update_item = (
                old_item[0],
                self.product_code,
                name,
                new_qty,
                f"{price:,.2f}",
                f"{total:,.2f}"
            )
            self.sale_items[index] = update_item
        else:
            price = self.wholesale_price if qty >= 10 else self.retail_price
            total = qty * price
            no = len(self.sale_items) + 1
            # Add to internal list and Treeview
            name = re.sub(r"\s+", " ", str(self.product_name)).strip()
            self.sale_items.append(
                (no, self.product_code, name, qty, f"{price:,.2f}",
                 f"{total:,.2f}")
            )
        self.refresh_sale_list()
        # Update total cost
        total_cost = sum(float(
            str(item[5]).replace(",", "")
        ) for item in self.sale_items)
        self.total_cost_var.set(f"{total_cost:,.2f}")
        another = messagebox.askyesno(
            "Continue?", "Continue Adding Items?", parent=self.sale_win
        )
        if another:
            self.search_entry.delete(0, tk.END)
            self.quantity_entry.delete(0, tk.END)
            self.quantity_entry.configure(state="disabled")
            self.add_button.configure(state="disabled")
            self.search_entry.focus_set()
        else:
            self.post_sale_button.bind(
                "<Return>", lambda e: self.show_payment_popup()
            )
            self.post_sale_button.focus_set()

    def remove_selected(self):
        """Remove selected item from sale list and update totals."""
        selected = self.sale_list.selection()
        if not selected:
            messagebox.showwarning(
                "No Selection", "Please Select Item to Remove.",
                parent=self.sale_win
            )
            return
        item_id = selected[0]
        values = self.sale_list.item(item_id, "values")
        if values and values[3] == "Total Cost":
            messagebox.showwarning(
                "Invalid", "Can't Remove Total Row.", parent=self.sale_win
            )
            return
        if values: # Remove from internal list
            product_code = values[1]
            self.sale_items = [
                item for item in self.sale_items if item[1] != product_code
            ]
        self.refresh_sale_list() # Refresh Treeview

    def refresh_sale_list(self):
        self.sale_list.delete(*self.sale_list.get_children()) # Clear old rows
        for idx, item in enumerate(self.sale_items, start=1):
            new_item = (idx,) + item[1:] # Replace No with new index
            self.sale_items[idx-1] = new_item
            self.sale_list.insert("", "end", values=new_item) # Reinsert all items
        total_cost = sum(float(
            str(item[5]).replace(",", "")
        ) for item in self.sale_items) # Calculate Total
        self.total_cost_var.set(f"{total_cost:,.2f}")
        if self.sale_items:
            self.sale_list.insert("", "end", values=("", "", "", "", "", ""))
            self.sale_list.insert("", "end", values=(
                "", "", "", "Total Cost", "", f"{total_cost:,.2f}"
            ), tags=("total",))
        self.sorter.autosize_columns(5)

    def show_payment_popup(self):
        success, msg = self.valid_session.can_sell(self.user)
        if not success:
            messagebox.showwarning(
                "Error", f"Error Selling:\n{msg}.", parent=self.sale_win
            )
            return
        if not self.sale_items:
            messagebox.showwarning(
                "No Items", "No Item To pay For.", parent=self.sale_win
            )
            return
        popup = tk.Toplevel(self.sale_win)
        popup.title("Payments")
        popup.resizable(False, False)
        self.center_window(popup, 200, 220, self.sale_win)
        popup.transient(self.sale_win)
        popup.grab_set()
        tk.Label(
            popup, text=" Payments ", fg="green", bd=4, relief="flat",
            font=("Arial", 14, "bold", "underline")
        ).pack(pady=(0, 5), ipadx=5)
        partial_var = tk.BooleanVar()
        tk.Checkbutton(
            popup, text="Partial Payment", variable=partial_var,
            font=("Arial", 12, "bold"), command=lambda: toggle_partial()
        ).pack(pady=(5, 0))
        tk.Label(popup, text="Cash:", font=("Arial", 12, "bold")).pack()
        cash_var = tk.StringVar()
        mpesa_var = tk.StringVar()
        cash_entry = tk.Entry(
            popup, textvariable=cash_var, bd=4, relief="raised", width=10,
            font=("Arial", 12)
        )
        cash_entry.pack(pady=(0, 5))
        cash_entry.focus_set()
        tk.Label(popup, text="M-PESA:", font=("Arial", 12, "bold")).pack()
        mpesa_entry = tk.Entry(
            popup, textvariable=mpesa_var, bd=4, relief="raised", width=10,
            font=("Arial", 12)
        )
        mpesa_entry.pack(pady=(0, 5))
        CurrencyFormatter.add_currency_trace(cash_var, cash_entry)
        CurrencyFormatter.add_currency_trace(mpesa_var, mpesa_entry)
        complete_btn = tk.Button(
            popup, text="Post Transaction", bd=4, relief="groove", bg="blue",
            fg="white", state="disabled", command=lambda: finalize_payment(),
            font=("Arial", 11, "bold")
        )
        complete_btn.pack(pady=(5, 0))
        def toggle_partial():
            if not partial_var.get():
                mpesa_entry.delete(0, tk.END)
        def update_button_state(*args):
            try:
                cash = float(cash_entry.get().replace(",", "") or 0)
                mpesa = float(
                    mpesa_entry.get().replace(",", "") or 0
                ) if partial_var.get() else 0
                total_entered = cash + mpesa
                required = float(
                    self.total_cost_var.get().replace(",", "")
                )
                complete_btn.config(
                    state="normal" if total_entered >= required else "disabled"
                )
            except ValueError:
                complete_btn.config(state="disabled")
        def finalize_payment():
            try:
                cash = float(cash_entry.get().replace(",", "") or 0)
                mpesa = float(
                    mpesa_entry.get().replace(",", "") or 0
                ) if partial_var.get() else 0
                total_entered = cash + mpesa
                total_required = float(
                    self.total_cost_var.get().replace(",", "")
                )
                if total_entered < total_required:
                    messagebox.showwarning(
                        "Insufficient", "Payment not Enough.", parent=popup
                    )
                    return
                # Prepare item list for SalesManager
                item_list = []
                for _, code, name, qty, price, total in self.sale_items:
                    price_clean = float(str(price).replace(",", ""))
                    item_list.append({
                        'product_code': code,
                        'product_name': name,
                        'quantity': qty,
                        'unit_price': price_clean
                    })
                # Create combined payment method string
                payment_parts = []
                if cash > 0:
                    self.payment_list.append(("cash", cash))
                    payment_parts.append("Cash")
                if mpesa > 0:
                    self.payment_list.append(("mpesa", mpesa))
                    payment_parts.append("Mpesa")
                payment_method = ",".join(payment_parts)
                success, result = self.sales_manager.record_sale(
                    self.user, item_list, payment_method, total_required
                )
                if success:
                    self.refresh_label()
                    receipt_no = result
                    change = total_entered - total_required
                    success, msg = ReceiptPrinter.print_receipt(self.conn, receipt_no)
                    if not success:
                        messagebox.showerror("Error", msg, parent=popup)
                    messagebox.showinfo(
                        "Transaction Complete",
                        f"Change: {change:.2f}", parent=popup
                    )
                    self.sale_items.clear()
                    self.payment_list.clear()
                    self.refresh_sale_list()
                    self.total_cost_var.set("0.00")
                    self.search_entry.delete(0, tk.END)
                    self.quantity_entry.delete(0, tk.END)
                    self.quantity_entry.configure(state="disabled")
                    self.add_button.configure(state="disabled")
                    self.post_sale_button.configure(state="disabled")
                    popup.destroy()
                    self.search_entry.focus_set()
                else:
                    messagebox.showerror("Error", result, parent=popup)
                    print(result)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=popup)
        cash_entry.bind("<KeyRelease>", update_button_state)
        mpesa_entry.bind("<KeyRelease>", update_button_state)

    def lookup_product(self):
        ProductSearchWindow(self.sale_win, self.conn)

    def logs_window(self):
        Last24HoursSalesWindow(self.sale_win, self.conn, self.user)

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root=tk.Tk()
    MakeSaleWindow(root, conn, "Bkendi")
    root.mainloop()