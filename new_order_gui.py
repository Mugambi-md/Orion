from connect_to_db import connect_db
from working_on_orders import insert_order_data, fetch_order_product
from window_functionality import to_uppercase
from tkinter import ttk, messagebox
from base_window import BaseWindow
from datetime import date
import tkinter as tk
conn = connect_db()

class NewOrderWindow(BaseWindow):
    def __init__(self, master, conn, user):
        self.master = tk.Toplevel(master)
        self.master.title("New Order")
        self.center_window(self.master, 1000, 600)
        self.master.configure(bg="green")
        self.master.grab_set()
        self.user = user
        self.conn = conn
        
        self.order_items = []
        self.total_amount = 0

        self.create_left_frame()
        self.create_right_frame()
    def create_left_frame(self):
        self.left_frame = tk.Frame(self.master, bg="blue", padx=5, pady=5)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(self.left_frame, text="Custormer Name:", bg="lightblue").grid(row=0, column=0, padx=5, pady=(5, 2)) # Customer Info (2 - columns: label top, entry below)
        self.customer_name_entry = tk.Entry(self.left_frame)
        self.customer_name_entry.grid(row=1, column=0, padx=5, pady=2)
        self.customer_name_entry.bind("<Return>", lambda e: self.contact_entry.focus_set())
        self.customer_name_entry.bind("<KeyRelease>", self.capitalize_customer_name)
        tk.Label(self.left_frame, text="Contact:", bg="lightblue").grid(row=0, column=1, padx=5, pady=(5, 2))
        self.contact_entry = tk.Entry(self.left_frame)
        self.contact_entry.grid(row=1, column=1, padx=5, pady=2)
        self.contact_entry.bind("<Return>", lambda e: self.deadline_entry.focus_set())
        tk.Label(self.left_frame, text="Deadline:", bg="lightblue").grid(row=0, column=2, padx=5, pady=(5, 2))
        self.deadline_entry = tk.Entry(self.left_frame)
        self.deadline_entry.grid(row=1, column=2, padx=5, pady=2)
        self.deadline_entry.bind("<Return>", lambda e: self.handle_next())
        self.next_button = tk.Button(self.left_frame, text="Next", command=self.handle_next) # Next Button
        self.next_button.grid(row=2, column=0, columnspan=3, padx=5, pady=2)
        tk.Label(self.left_frame, text="", bg="blue").grid(row=3, column=0, columnspan=3, pady=5)
        self.search_section = tk.Frame(self.left_frame, bg="blue") # Product search section (initially hidden)
        tk.Label(self.search_section, text="Enter Product Code:", bg="lightblue").grid(row=0, column=0, padx=5, pady=2)
        self.product_code_entry = tk.Entry(self.search_section)
        self.product_code_entry.bind("<KeyRelease>", lambda event: to_uppercase(self.product_code_entry))
        self.product_code_entry.grid(row=1, column=0, padx=5, pady=2)
        self.search_button = tk.Button(self.search_section, text="Search", command=self.search_product)
        self.search_button.grid(row=2, column=0, pady=5)
        tk.Label(self.search_section, text="Quantity", bg="lightblue").grid(row=0, column=1, padx=5, pady=2)
        self.quantity_entry = tk.Entry(self.search_section)
        self.quantity_entry.grid(row=1, column=1, padx=5, pady=2)

        self.add_button = tk.Button(self.search_section, text="Add to Order", command=self.add_to_order)
        self.add_button.grid(row=2, column=1, pady=5)
        self.submit_button = tk.Button(self.search_section, text="Submit Order", command=self.submit_order)
        self.submit_button.grid(row=3, column=0, columnspan=2, pady=10)
        self.submit_button.grid_remove()

        self.product_name_var = tk.StringVar()
        self.wholesale_price_var = tk.StringVar()
        self.retail_price_var = tk.StringVar()

    def create_right_frame(self):
        self.right_frame = tk.Frame(self.master, bg="blue", padx=5, pady=5)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        button_frame = tk.Frame(self.right_frame, bg="blue")
        button_frame.pack(fill=tk.X, pady=(0, 2))
        self.delete_btn = tk.Button(button_frame, text="Delete Item", command=self.delete_selected_item, state="disabled")
        self.edit_btn = tk.Button(button_frame, text="Edit Quantity", state="disabled")
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        columns = ("Product Code", "Product Name", "Quantity", "Unit Price", "Total Price")
        self.tree = ttk.Treeview(self.right_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=50)
        self.tree.pack(expand=True, fill=tk.BOTH)
        self.total_label = tk.Label(self.right_frame, text="Total: 0.00", fg="red", font=("Arial", 13, "bold"))
        self.total_label.pack(side=tk.RIGHT,padx=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_selection_change)

    def on_tree_selection_change(self, event=None):
        selected = self.tree.selection()
        if selected:
            self.delete_btn.config(state="normal")
            self.edit_btn.config(state="normal")
        else:
            self.delete_btn.config(state="disabled")
            self.edit_btn.config(state="disabled")
    def delete_selected_item(self):
        selected = self.tree.selection()
        if not selected:
            return
        self.tree.delete(selected[0])
        self.delete_btn.config(state="disabled")
        self.edit_btn.config(state="disabled")
    def handle_next(self):
        name = self.customer_name_entry.get()
        contact = self.contact_entry.get()
        deadline = self.deadline_entry.get()
        if not name or not contact or not deadline:
            messagebox.showwarning("Missing Info", "Please fill all customer info fields.")
            return
        self.customer_name_entry.config(state="disabled")
        self.contact_entry.config(state="disabled")
        self.deadline_entry.config(state="disabled")
        self.next_button.config(state="disabled")
        self.search_section.grid(row=4, column=0, columnspan=3, sticky="ew", pady=5)
        self.product_code_entry.focus_set()
        self.product_code_entry.bind("<Return>", lambda e: self.search_product())

    def search_product(self):
        code = self.product_code_entry.get().upper()
        try:
            result = fetch_order_product(code)
            self.product_name = result["product_name"]
            self.wholesale_price = float(result["wholesale_price"])
            self.retail_price = float(result["retail_price"])
            answer = messagebox.askyesno("Confirm", f"Add '{self.product_name}' to order?")
            if answer:
                self.quantity_entry.focus_set()
                self.quantity_entry.bind("<Return>", lambda e: self.add_to_order())
            else:
                self.product_code_entry.delete(0, tk.END)
                self.product_code_entry.focus_set()
        except ValueError as ve:
            messagebox.showerror("Product Not Found", str(ve))
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
    def add_to_order(self):
        try:
            code = self.product_code_entry.get().upper()
            qty = int(self.quantity_entry.get())
            if not code or qty <=0:
                messagebox.showerror("Input Error", "Please enter a valid product code and quantity.")
                return
            existing_item = next((item for item in self.order_items if item['product_code'] == code), None)
            if existing_item:
                for iid in self.tree.get_children():
                    values = self.tree.item(iid, 'values')
                    if values[0] == code:
                        self.tree.delete(iid)
                        break
                self.total_amount -= existing_item['total_price'] # Remove old item from list and update total
                self.order_items.remove(existing_item)
                qty += existing_item['quantity']
            unit_price = self.wholesale_price if qty >= 10 else self.retail_price
            total = unit_price * qty
            self.tree.insert("", "end", values=(code, self.product_name, qty, unit_price, total)) # Add updated item
            self.order_items.append({
                "product_code": code,
                "product_name": self.product_name,
                "quantity": qty,
                "unit_price": unit_price,
                "total_price": total
            })
            self.total_amount += total # Update total label
            self.total_label.config(text=f"Total: {self.total_amount:.2f}")
            another = messagebox.askyesno("More?", "Do you want to add another Product?") # Ask to add more
            if another:
                self.product_code_entry.config(state="normal")
                self.quantity_entry.config(state="normal")
                self.product_code_entry.delete(0, tk.END)
                self.quantity_entry.delete(0, tk.END)
                self.product_code_entry.focus()
                self.product_code_entry.bind("<Return>", lambda e: self.search_product())
                self.submit_button.grid_remove()
            else:
                self.search_button.config(state="disabled")
                self.product_code_entry.config(state="disabled")
                self.quantity_entry.config(state="disabled")
                self.add_button.config(state="disabled")
                self.submit_button.grid(row=4, column=0, columnspan=2, pady=10)
                self.submit_button.focus_set()
                self.submit_button.bind("<Return>", lambda e: self.submit_order())
        except Exception as e:
            messagebox.showerror("Error", str(e))
    def submit_order(self):
        if not self.order_items:
            messagebox.showwarning("Missing", "No items in Order List.")
            return
        def continue_submission(paid_amount, cash, mpesa):
            balance = self.total_amount - paid_amount
            payment_data = {
                "total_amount": self.total_amount,
                "paid_amount": paid_amount,
                "balance": balance,
                "method": f"Cash: {cash}, Mpesa: {mpesa}"
            }
            customer_name = self.customer_name_entry.get()
            contact = self.contact_entry.get()
            deadline = self.deadline_entry.get()
            order_data = {
                "customer_name": customer_name,
                "contact": contact,
                "date_placed": str(date.today()),
                "deadline": deadline,
                "amount": self.total_amount
            }
            confirm = messagebox.askyesno("Post Order", "Do you want to post this order?")
            if confirm:
                result = insert_order_data(self.conn, order_data, self.order_items, self.user, payment_data)
                messagebox.showinfo("Result", result)
                if "successfully" in result.lower():
                    self.customer_name_entry.delete(0, 'end')
                    self.contact_entry.delete(0, 'end')
                    self.deadline_entry.delete(0, 'end')
                    self.product_code_entry.delete(0, 'end')
                    self.quantity_entry.delete(0, 'end')
                    self.order_items.clear()
                    self.total_amount = 0
        wants_to_pay = messagebox.askyesno("Payment", "Do you want to pay the order?")
        if wants_to_pay:
            OrderPaymentWindow(self.master, continue_submission)
        else:
            confirm = messagebox.askyesno("Post Order", "Do you want to post this order without payment?")
            if confirm:
                continue_submission(0, 0, 0)
        
    def capitalize_customer_name(self, event=None):
        widget = event.widget
        name = widget.get()
        cursor_position = widget.index(tk.INSERT)
        capitalized = ' '.join(word.capitalize() for word in name.split(' '))
        if name != capitalized:
            widget.delete(0, tk.END)
            widget.insert(0, capitalized)
            widget.icursor(cursor_position)
class OrderPaymentWindow(BaseWindow):
    def __init__(self, master, on_complete_callback):
        self.top = tk.Toplevel(master)
        self.top.title("Order Payment")
        self.top.configure(bg="lightgreen")
        self.top.grab_set()
        self.center_window(self.top, 250, 150)
        self.on_complete_callback = on_complete_callback
        tk.Label(self.top, text="Cash:", bg="green").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.cash_entry = tk.Entry(self.top)
        self.cash_entry.grid(row=0, column=1, padx=5, pady=3)
        self.cash_entry.bind("<Return>", lambda e: self.mpesa_entry.focus_set())
        tk.Label(self.top, text="Mpesa:", bg="green").grid(row=1, column=0, padx=5, pady=3, sticky="e")
        self.mpesa_entry = tk.Entry(self.top)
        self.mpesa_entry.grid(row=1, column=1, padx=5, pady=3)
        self.mpesa_entry.bind("<Return>", lambda e: self.complete())
        button_frame = tk.Frame(self.top, bg="lightgreen")
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.top.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        complete_btn = tk.Button(button_frame, text="Complete", command=self.complete)
        complete_btn.pack(side=tk.RIGHT, padx=10)
        self.cash_entry.focus_set()
    def complete(self):
        try:
            cash = float(self.cash_entry.get() or 0)
            mpesa = float(self.mpesa_entry.get() or 0)
            total_paid = cash + mpesa
            self.on_complete_callback(total_paid, cash, mpesa)
            self.top.destroy()
        except ValueError:
            messagebox.showerror("Invalind Input", "Enter valid amounts.")

# if __name__ == "__main__":
#      root = tk.Tk()
#      app = NewOrderWindow(root, conn, "Sniffy")
#      #root.withdraw()
#      root.mainloop()