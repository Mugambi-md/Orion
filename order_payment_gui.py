import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from connect_to_db import connect_db
from working_on_orders import fetch_unpaid_orders, receive_order_payment
conn = connect_db()

class UnpaidOrdersWindow:
    def __init__(self, parent, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Orders Payment")
        self.master.geometry("1000x600")
        self.master.configure(bg="lightgreen")
        self.master.grab_set()
        self.user = user
        
        self.conn = connect_db()
        title_label = tk.Label(self.master, text="CURRENT UNPAID ORDERS", font=("Arial", 12, "bold"), bg="lightgreen")
        title_label.pack(pady=4) # Title
        # Instruction
        
        # Main Frame for layout
        main_frame = tk.Frame(self.master, bg="lightblue")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Left frame for table
        table_frame = tk.Frame(main_frame, bg="lightblue")
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        instruction_label = tk.Label(table_frame, text="Select Order To Pay", font=("Arial", 11, "bold"), bg="lightblue")
        instruction_label.pack(pady=3)
        # Right frame for payment logic (placeholder for now)
        self.payment_frame = tk.Frame(main_frame, bg="gray", width=300)
        self.payment_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.payment_frame.pack_propagate(False)
        # Treeview for orders
        columns = ("Order ID", "Customer Name", "Contact", "Date Placed", "Amount", "Status", "Balance")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=len(col))
        self.tree.pack(fill=tk.BOTH, expand=True)
        orders_data = fetch_unpaid_orders(self.conn)
        # Populate table with data
        for order in orders_data:
            self.tree.insert("", "end", values=(
                order['order_id'],
                order['customer_name'],
                order['contact'],
                order['date_placed'],
                order['amount'],
                order['status'],
                order['balance']
            ))
        # Bind row selection
        self.tree.bind("<<TreeviewSelect>>", self.on_order_select)

    def on_order_select(self, event):
        selected = self.tree.focus()
        if selected:
            order_data = self.tree.item(selected)["values"]
            order_id = order_data[0]
            # Clear the payment frame
            for widget in self.payment_frame.winfo_children():
                widget.destroy()
            # Store the selected order id for use
            self.selected_order_id = order_id
            label = tk.Label(self.payment_frame, text=f"Procesing payment for Order ID: {order_id}", bg="lightgray")
            label.grid(row=0, column=0, columnspan=2, pady=10)
            # Cash label and entry
            tk.Label(self.payment_frame, text="Cash:",bg="lightgray").grid(row=1, column=0, sticky="e", padx=5, pady=5)
            self.cash_entry = tk.Entry(self.payment_frame)
            self.cash_entry.grid(row=1, column=1, padx=5, pady=5)
            self.cash_entry.focus_set()
            self.cash_entry.bind("<Return>", lambda e: self.mpesa_entry.focus_set())
            # Mpesa label and entry
            tk.Label(self.payment_frame, text="Mpesa:", bg="lightgray").grid(row=2, column=0, sticky="e", padx=5, pady=5)
            self.mpesa_entry = tk.Entry(self.payment_frame)
            self.mpesa_entry.grid(row=2, column=1, padx=5, pady=5)
            self.mpesa_entry.bind("<Return>", lambda e: self.post_payment())
            # Post payment button
            post_btn = tk.Button(self.payment_frame, text="Post Payment", command=self.post_payment)
            post_btn.grid(row=3, column=0, columnspan=2, pady=10)
    def post_payment(self):
        try:
            cash = float(self.cash_entry.get() or 0)
            mpesa = float(self.mpesa_entry.get() or 0)
            amount_to_pay = cash + mpesa
            if amount_to_pay <= 0:
                messagebox.showerror("Input Error", "Please enter a valid amount.")
                return
            method = f"cash: {cash}" if mpesa == 0 else f"mpesa: {mpesa}" if cash == 0 else f"cash: {cash}, mpesa: {mpesa}"
            confirm = messagebox.askyesno("Confirm Payment", f"Do you want to post payment of {amount_to_pay:.2f} for Order ID {self.selected_order_id}?")
            if confirm:
                receive_order_payment(self.selected_order_id, amount_to_pay, method, self.user, self.conn)
                self.cash_entry.config(state="disabled")
                self.mpesa_entry.config(state="disabled")
            else:
                self.mpesa_entry.focus_set()
        except ValueError:
            messagebox.showerror("Input Error", "Please enter Numeric Values.")
        
# if __name__ == "__main__":
#     conn = connect_db()
#     user = 'user'
#     root = tk.Tk()
#     root.withdraw()
#     app=UnpaidOrdersWindow(root, user)
#     root.mainloop()