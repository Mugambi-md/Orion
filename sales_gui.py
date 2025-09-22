import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox
from window_functionality import to_uppercase
from working_sales import fetch_sales_product, SalesManager
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
        self.total_cost_var = tk.StringVar(value="0.00")
        self.sales_manager = SalesManager(self.conn)
        self.left_frame = tk.Frame(self.sale_win, bg="lightblue", width=300)
        self.add_frame = tk.LabelFrame(self.left_frame, bg="white",
                                       text="Add To Sales List")
        self.right_frame = tk.Frame(self.sale_win, bg="white")
        self.sale_list = ttk.Treeview(
            self.right_frame, columns=self.columns, show="headings"
        )
        self.search_entry = tk.Entry(self.add_frame, width=20)
        self.quantity_entry = tk.Entry(self.add_frame, width=20, state="disabled")
        self.add_button = tk.Button(
            self.add_frame, text="Add To List", width=20, state="disabled",
            command=self.add_to_list
        )
        self.post_sale_button = tk.Button(
            self.add_frame, text="Post Sale", width=20, state="disabled",
            command=self.show_payment_popup
        )
        (self.product_code, self.product_name, self.available_quantity,
         self.wholesale_price, self.retail_price) = None, None, None, None, None


        self.create_widgets()

    def create_widgets(self):
        # Lef Frame
        self.left_frame.pack(side="left", fill="y", padx=(5, 0), pady=5)
        # Right Frame
        self.right_frame.pack(
            side="right", expand=True, fill="both", padx=(0, 5), pady=5
        )
        # Add to sales list section
        self.add_frame.pack(fill="x", pady=(0, 5))
        tk.Label(
            self.add_frame, text="Enter Product Code:", bg="white",
            font=("Arial", 11)
        ).pack(padx=5, pady=(5, 2), anchor="w")
        self.search_entry.pack(padx=5, pady=(2, 5))
        self.search_entry.focus_set()
        self.search_entry.bind(
            "<KeyRelease>", lambda event: to_uppercase(self.search_entry)
        )
        self.search_entry.bind("<Return>", lambda e: self.search_product())
        tk.Button(
            self.add_frame, text="Search", width=20,
            command=self.search_product
        ).pack(padx=5, pady=(0, 10))
        tk.Label(
            self.add_frame, text="Enter Product Quantity:", bg="white",
            font=("Arial", 11)
        ).pack(padx=5, pady=(5, 2), anchor="w")
        self.quantity_entry.pack(padx=5, pady=(2, 5))
        self.quantity_entry.bind("<Return>", lambda e: self.add_to_list())
        self.add_button.pack(padx=5, pady=(0, 10))
        self.post_sale_button.pack(padx=5, pady=5)
        tk.Button(
            self.add_frame, text="Look Up Items", bg="green", fg="white",
            command=self.lookup_product
        ).pack(pady=3)
        tk.Button(
            self.left_frame, text="View Logs", width=20, bg="blue",
            fg="white", command=self.logs_window, bd=4, relief="solid"
        ).pack(padx=5)
        style = ttk.Style(self.sale_win)
        style.configure("Treeview", rowheight=30, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        btn_frame = tk.Frame(self.right_frame, bg="white")
        btn_frame.pack(side="top", fill="x", padx=5)
        tk.Button(
            btn_frame, text="Remove Item", bg="red", fg="white", bd=4,
            relief="solid", command=self.remove_selected
        ).pack(side="right", padx=5)
        tk.Label(
            btn_frame, text="Sale List", bg="white",
            font=("Arial", 14, "bold")
        ).pack(anchor="center", padx=5)
        vsb = ttk.Scrollbar(self.right_frame, orient="vertical",
                            command=self.sale_list.yview)
        self.sale_list.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        # Sales List Table
        for col in self.columns:
            self.sale_list.heading(col, text=col)
            self.sale_list.column(col, anchor="center", width=50)
        self.sale_list.pack(fill="both", expand=True, pady=(5, 0))
        self.sale_list.tag_configure(
            "total", font=("Arial", 12, "bold", "underline")
        )

    def search_product(self):
        code = self.search_entry.get().strip().upper()
        if not code:
            messagebox.showerror("Error", "Please Enter Product Code.")
            return
        result = fetch_sales_product(self.conn, code)
        if isinstance(result, tuple):
            self.product_code, self.product_name, self.available_quantity, self.wholesale_price, self.retail_price = result
            answer = messagebox.askyesno(
                "Add Product", f"Add '{self.product_name}' to Sales list?"
            )
            if answer:
                self.quantity_entry.configure(state="normal")
                self.add_button.configure(state="normal")
                self.post_sale_button.configure(state="normal")
                self.quantity_entry.focus_set()
        else:
            messagebox.showerror("Not Found", result)
    def add_to_list(self):
        qty_str = self.quantity_entry.get().strip()
        if not qty_str.isdigit():
            messagebox.showerror("Invalid Input",
                                 "Please enter a valid quantity.")
            return
        qty = int(qty_str)
        if qty > self.available_quantity:
            messagebox.showerror("Not Enough Stock", f"Available quantity for '{self.product_name}' is {self.available_quantity}. You don't have enough quantity to make the sale.")
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
            update_item = (
                old_item[0],
                self.product_code,
                self.product_name,
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
            self.sale_items.append((no, self.product_code, self.product_name, qty, f"{price:,.2f}", f"{total:,.2f}"))
        self.refresh_sale_list()
        # Update total cost
        total_cost = sum(float(
            str(item[5]).replace(",", "")
        ) for item in self.sale_items)
        self.total_cost_var.set(f"{total_cost:,.2f}")
        another = messagebox.askyesno("Continue?", "Do you want to enter another product?")
        if another:
            self.search_entry.delete(0, tk.END)
            self.quantity_entry.delete(0, tk.END)
            self.quantity_entry.configure(state="disabled")
            self.add_button.configure(state="disabled")
            self.search_entry.focus_set()
        else:
            self.post_sale_button.bind("<Return>", lambda e: self.show_payment_popup())
            self.post_sale_button.focus_set()

    def remove_selected(self):
        """Remove selected item from sale list and update totals."""
        selected = self.sale_list.selection()
        if not selected:
            messagebox.showwarning("No Selection",
                                   "Please select item to Remove.")
            return
        item_id = selected[0]
        values = self.sale_list.item(item_id, "values")
        if values and values[3] == "Total Cost":
            messagebox.showwarning("Invalid", "You Can't Remove Total Row.")
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
        self.autosize_columns()
    def show_payment_popup(self):
        if not self.sale_items:
            messagebox.showwarning("No Items", "No items in sales list.")
            return
        popup = tk.Toplevel(self.sale_win)
        popup.title("Payments")
        popup.resizable(False, False)
        self.center_window(popup, 300, 250, self.sale_win)
        popup.transient(self.sale_win)
        popup.grab_set()
        tk.Label(popup, text="Payment Method", font=("Arial", 12, "bold")).pack(pady=5)
        partial_var = tk.BooleanVar()
        tk.Checkbutton(popup, text="Partial Payment", variable=partial_var, command=lambda: toggle_partial()).pack(pady=5)
        tk.Label(popup, text="Cash:").pack()
        cash_entry = tk.Entry(popup)
        cash_entry.pack(pady=(0, 10))
        cash_entry.focus_set()
        tk.Label(popup, text="M-PESA:").pack()
        mpesa_entry = tk.Entry(popup)
        mpesa_entry.pack(pady=(0, 10))
        complete_btn = tk.Button(popup, text="Complete Transaction", state="disabled", command=lambda: finalize_payment())
        complete_btn.pack(pady=10)
        def toggle_partial():
            if not partial_var.get():
                mpesa_entry.delete(0, tk.END)
        def update_button_state(*args):
            try:
                cash = float(cash_entry.get() or 0)
                mpesa = float(mpesa_entry.get() or 0) if partial_var.get() else 0
                total_entered = cash + mpesa
                total_required = float(self.total_cost_var.get().replace(",", ""))
                complete_btn.config(state="normal" if total_entered >= total_required else "disabled")
            except ValueError:
                complete_btn.config(state="disabled")
        def finalize_payment():
            try:
                cash = float(cash_entry.get() or 0)
                mpesa = float(mpesa_entry.get() or 0) if partial_var.get() else 0
                total_entered = cash + mpesa
                total_required = float(self.total_cost_var.get().replace(",", ""))
                if total_entered < total_required:
                    messagebox.showwarning("Insufficient", "Payment is not enough.")
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
                success, result = self.sales_manager.record_sale(self.user, item_list, payment_method, total_required)
                if success:
                    receipt_no = result
                    change = total_entered - total_required
                    print_success, print_message = ReceiptPrinter.print_receipt(self.conn, receipt_no)
                    if not print_success:
                        messagebox.showerror("Error", print_message)
                    messagebox.showinfo("Transaction Complete", f"Change: {change:.2f}")
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
                else:
                    messagebox.showerror("Error", result)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        cash_entry.bind("<KeyRelease>", update_button_state)
        mpesa_entry.bind("<KeyRelease>", update_button_state)
    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.sale_list.get_children():
                cell_value = str(self.sale_list.set(item, col))
                cell_width = font.measure(cell_value)
                if cell_width > max_width:
                    max_width = cell_width
            self.sale_list.column(col, width=max_width + 5)
    def lookup_product(self):
        messagebox.showinfo("Info", "Look up products with code or name.")
        ProductSearchWindow(self.sale_win, self.conn)
    def logs_window(self):
        Last24HoursSalesWindow(self.sale_win, self.conn, self.user)

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn = connect_db()
    root = tk.Tk()
    app=MakeSaleWindow(root, conn, "sniffy")
    root.mainloop()