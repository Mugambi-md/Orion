import tkinter as tk
from tkinter import ttk, messagebox
from window_functionality import to_uppercase
from working_sales import fetch_sales_product

class MakeSaleWindow:
    def __init__(self, parent):
        self.sale_items = [] # Keep track of sales list
        self.payment_list = [] # Keep track of payments
        self.sale_win = tk.Toplevel(parent)
        self.sale_win.title("Make Sales")
        self.sale_win.geometry("1000x600")
        self.sale_win.configure(bg="Lightblue")
        self.sale_win.grab_set()
        self.create_widgets()

    def create_widgets(self):
        # Lef Frame
        left_frame = tk.Frame(self.sale_win, bg="blue", width=400)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        # Right Frame
        right_frame = tk.Frame(self.sale_win, bg="white")
        right_frame.pack(side="right", expand=True,fill="both", padx=5, pady=5)
        # Add to sales list section
        add_frame = tk.LabelFrame(left_frame, text="Add To Sales List", bg="white")
        add_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(add_frame, text="Enter Product Code:", bg="white").pack(padx=5, pady=(5, 2), anchor="w")
        self.search_entry = tk.Entry(add_frame, width=25)
        self.search_entry.pack(padx=5, pady=(2, 5))
        self.search_entry.bind("<KeyRelease>", lambda event: to_uppercase(self.search_entry))
        self.search_button = tk.Button(add_frame, text="Search", width=25, command=self.search_product)
        self.search_button.pack(padx=5, pady=(0, 10))
        self.quantity_label = tk.Label(add_frame, text="Enter Product Quantity:", bg="white")
        self.quantity_entry = tk.Entry(add_frame, width=25)
        self.add_button = tk.Button(add_frame, text="Add To List", width=25, command=self.add_to_list)
        self.post_sale_button = tk.Button(add_frame, text="Post Sale", width=25, command=self.show_payment_popup)
        # Sales List Table
        self.sale_list = ttk.Treeview(right_frame, columns=("No", "Product Code", "Product Name", "Quantity", "Price", "Total"), show="headings")
        for col in ["No", "Product Code", "Product Name", "Quantity", "Price", "Total"]:
            self.sale_list.heading(col, text=col)
        self.sale_list.column("No", width=20, anchor="center")
        self.sale_list.column("Product Code", width=100)
        self.sale_list.column("Product Name", width=100)
        self.sale_list.column("Quantity", width=50, anchor="center")
        self.sale_list.column("Price", width=50, anchor="center")
        self.sale_list.column("Total", width=50, anchor="center")
        self.sale_list.pack(fill="both", expand=True, pady=(5, 0))
        # Total Cost Section
        total_frame = tk.Frame(right_frame, bg="lightblue")
        total_frame.pack(fill="x",padx=2, pady=2)
        self.total_cost_var = tk.StringVar(value="0.00")
        total_cost_label = tk.Label(total_frame, textvariable=self.total_cost_var, bg="white", font=("Arial", 12, "bold"))
        total_cost_label.pack(side="right")
        tk.Label(total_frame, text="Total Cost:", bg="lightblue", font=("Arial", 12, "bold")).pack(side="right", padx=5)
    def search_product(self):
        code = self.search_entry.get().strip().upper()
        if not code:
            messagebox.showerror("Error", "Please Enter Product Code.")
            return
        result = fetch_sales_product(code)
        if isinstance(result, tuple):
            self.product_code, self.product_name, self.available_quantity, self.wholesale_price, self.retail_price = result
            answer = messagebox.askyesno("Add Product", f"Do you want to add '{self.product_name}' to the sales list?")
            if answer:
                self.quantity_label.pack(padx=5, pady=(5, 2))
                self.quantity_entry.pack(padx=5, pady=(2, 5))
                self.add_button.pack(padx=5, pady=(0, 10))
                self.quantity_entry.focus_set()
        else:
            messagebox.showerror("Not Found", result)
    def add_to_list(self):
        qty_str = self.quantity_entry.get().strip()
        if not qty_str.isdigit():
            messagebox.showerror("Invalid Input", "Please enter a valid quantity.")
            return
        qty = int(qty_str)
        if qty > self.available_quantity:
            messagebox.showerror("Not Enough Stock", f"Available quantity for '{self.product_name}' is {self.available_quantity}. You don't have enough quantity to make the sale.")
            return
        price = self.wholesale_price if qty >= 10 else self.retail_price
        total = qty * price
        no = len(self.sale_items) + 1
        # Add to internal list and Treeview
        self.sale_items.append((no, self.product_code, self.product_name, qty, price, total))
        self.refresh_sale_list()
        # Update total cost
        total_cost = sum(item[5] for item in self.sale_items)
        self.total_cost_var.set(f"{total_cost:.2f}")
        another = messagebox.askyesno("Continue?", "Do you want to enter another product?")
        if another:
            self.search_entry.delete(0, tk.END)
            self.quantity_entry.delete(0, tk.END)
            self.quantity_label.pack_forget()
            self.quantity_entry.pack_forget()
            self.add_button.pack_forget()
            self.search_entry.focus_set()
        else:
            self.post_sale_button.pack(padx=5, pady=5)
    def refresh_sale_list(self):
        for row in self.sale_list.get_children():
            self.sale_list.delete(row)
        for item in self.sale_items:
            self.sale_list.insert("", "end", values=item)
    def show_payment_popup(self):
        if not self.sale_items:
            messagebox.showwarning("No Items", "No items in sales list.")
            return
        popup = tk.Toplevel(self.sale_win)
        popup.title("Payments")
        popup.resizable(False, False)
        w, h = 300, 250
        self.sale_win.update_idletasks()
        main_x = self.sale_win.winfo_x()
        main_y = self.sale_win.winfo_y()
        main_w = self.sale_win.winfo_width()
        main_h = self.sale_win.winfo_height()
        x = main_x + (main_w - w) // 2
        y = main_y + (main_h - h) // 2
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.grab_set()
        tk.Label(popup, text="Payment Method", font=("Arial", 12, "bold")).pack(pady=5)
        partial_var = tk.BooleanVar()
        tk.Checkbutton(popup, text="Partial Payment", variable=partial_var, command=lambda: toggle_partial()).pack(pady=5)
        tk.Label(popup, text="Cash:").pack()
        cash_entry = tk.Entry(popup)
        cash_entry.pack(pady=(0, 10))
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
                total_required = float(self.total_cost_var.get())
                complete_btn.config(state="normal" if total_entered >= total_required else "disabled")
            except ValueError:
                complete_btn.config(state="disabled")
        def finalize_payment():
            try:
                cash = float(cash_entry.get() or 0)
                mpesa = float(mpesa_entry.get() or 0) if partial_var.get() else 0
                total_entered = cash + mpesa
                total_required = float(self.total_cost_var.get())
                change = total_entered - total_required if total_entered > total_required else 0
                if cash > 0:
                    self.payment_list.append(("cash", cash))
                if mpesa > 0:
                    self.payment_list.append(("mpesa", mpesa))
                messagebox.showinfo("Transaction Complete", f"Change: {change:.2f}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        cash_entry.bind("<KeyRelease>", update_button_state)
        mpesa_entry.bind("<KeyRelease>", update_button_state)

#if __name__ == "__main__":
    #root = tk.Tk()
    #root.withdraw()
    #app=MakeSaleWindow(root)
    #root.mainloop()