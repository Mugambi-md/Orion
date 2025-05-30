import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import messagebox
from utils import capitalize_customer_name
from connect_to_db import connect_db
from order_add_item_gui import AddItemWindow, EditQuantityWindow
from working_on_orders import fetch_pendind_orders, fetch_orders_logs_by_order_id, fetch_order_items_by_order_id, update_order_details

class EditOrdersWindow:
    def __init__(self, parent, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Edit Pending Orders")
        self.master.geometry("1200x700")
        self.master.configure(bg="lightgreen")
        self.master.grab_set()

        self.conn = connect_db()
        self.user = user
        self.selected_order_id = None
        # Layout frames
        main_frame = tk.Frame(self.master, bg="lightgreen")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        # Left container (Top and Bottom)
        left_container = tk.Frame(main_frame, bg="lightgreen")
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Right container (Order Items)
        self.right_frame = tk.Frame(main_frame, bg="lightyellow", width=400)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        #self.right_frame.pack_propagate(False)
        # Top-left (Pending Orders)
        self.orders_frame = tk.LabelFrame(left_container, text="Current Pending Orders", bg="white", font=("Arial", 11, "bold"))
        self.orders_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.setup_pending_orders_table()
        # Bottom left (logs)
        self.logs_frame = tk.LabelFrame(left_container, text="Order Logs", bg="white", font=("Arial", 11, "bold"))
        self.logs_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.setup_logs_table()
    def setup_pending_orders_table(self):
        top = tk.Frame(self.orders_frame, bg="white")
        top.pack(side=tk.TOP, fill=tk.X, padx=5, pady=3)
        # Buttons  (initially hidden)
        self.edit_details_btn = tk.Button(top, text="Edit Order Details", command=self.edit_order_details)
        self.edit_items_btn = tk.Button(top, text="Edit Order Items", command=self.show_order_items)
        # Orders Treeview
        columns = ("Order ID", "Customer Name", "Contact", "Date Placed", "Deadline", "Amount", "Status")
        self.orders_tree = ttk.Treeview(self.orders_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.orders_tree.heading(col, text=col)
            self.orders_tree.column(col, anchor="center", width=len(col))
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(self.orders_frame, orient="vertical", command=self.orders_tree.yview)
        self.orders_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.orders_tree.bind("<<TreeviewSelect>>", self.on_order_selected) # Bind selection
        orders = fetch_pendind_orders(self.conn)
        for order in orders:
            self.orders_tree.insert("", "end", values=(
                order["order_id"],
                order["customer_name"],
                order["contact"],
                order["date_placed"],
                order["deadline"],
                order["amount"],
                order["status"]
            ))
        self.auto_adjust_column_widths(self.orders_tree)
    def setup_logs_table(self):
        columns = ("Date", "Order", "User", "Action", "Amount")
        self.logs_tree = ttk.Treeview(self.logs_frame, columns=columns, show="headings", height=9)
        for col in columns:
            self.logs_tree.heading(col, text=col)
            self.logs_tree.column(col, anchor="center", width=len(col))
        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(self.logs_frame, orient="vertical", command=self.logs_tree.yview)
        self.logs_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    def on_order_selected(self, event):
        selected = self.orders_tree.focus()
        if selected:
            self.selected_order_id = self.orders_tree.item(selected)["values"][0]
            if not self.edit_details_btn.winfo_ismapped():
                self.edit_details_btn.pack(side=tk.LEFT, padx=5)
            if not self.edit_items_btn.winfo_ismapped():
                self.edit_items_btn.pack(side=tk.LEFT, padx=5)
            # Fetch and populate logs for selected order
            self.populate_logs()
    def populate_logs(self):
        # Clear previous logs
        for i in self.logs_tree.get_children():
            self.logs_tree.delete(i)
        logs = fetch_orders_logs_by_order_id(self.conn, self.selected_order_id) # Fetch logs from db
        for log in logs:
            self.logs_tree.insert("", "end", values=(
                log["log_date"],
                log["order_id"],
                log["user"],
                log["action"],
                log["total_amount"]
            ))
        self.auto_adjust_column_widths(self.logs_tree)
    def show_order_items(self):
        # Clear right frame
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
        container = tk.Frame(self.right_frame, bg="lightyellow")
        container.pack(side=tk.LEFT, fill=tk.BOTH, padx=3, pady=3, expand=True)
        label = tk.Label(container, text=f"Order Items for Order ID: {self.selected_order_id}", bg="lightyellow", font=("Arial", 10, "bold"))
        label.pack(pady=1)
        tk.Label(container, text="Select Item to Edit.", bg="lightyellow", font=("Arial", 10, "bold")).pack(pady=1)
        btn_frame = tk.Frame(container, bg="lightyellow")
        btn_frame.pack(anchor="w", pady=(0, 3))
        self.add_item_btn = tk.Button(btn_frame, text="Add Item", command=self.add_another_item)
        self.add_item_btn.pack(side=tk.LEFT, padx=2)
        self.edit_quantity_btn = tk.Button(btn_frame, text="Edit Quantity", bg="red", command=self.edit_item_quantity)
        self.edit_quantity_btn.pack(side=tk.LEFT, padx=5)
        self.edit_quantity_btn.pack_forget()
        table_frame = tk.Frame(container, bg="lightyellow")
        table_frame.pack(anchor="w", fill=tk.BOTH, expand=True)
        columns = ("Order ID", "Product Code", "Product Name", "Quantity", "Unit Price", "Total")
        self.items_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, anchor="center", width=len(col)*10)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        items = fetch_order_items_by_order_id(self.conn, self.selected_order_id)
        self.total_cost = 0
        for item in items:
            self.items_tree.insert("", "end", values=(
                item["order_id"],
                item["product_code"],
                item["product_name"],
                item["quantity"],
                item["unit_price"],
                item["total_price"]
            ))
            self.total_cost += item["total_price"]
        self.auto_adjust_column_widths(self.items_tree)
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_selected)
        # Bottom label for total cost
        self.total_label = tk.Label(container, text=f"Total Cost: {self.total_cost}", bg="lightyellow", font=("Arial", 10, "bold"))
        self.total_label.pack(side=tk.BOTTOM, anchor="e", pady=3)
    def add_another_item(self):
        if not self.selected_order_id:
            messagebox.showwarning("No Order", "Select an order first.")
            return
        AddItemWindow(self.master, self.conn, self.selected_order_id, self.refresh_orders_table, self.user)
    def edit_item_quantity(self):
        selected = self.items_tree.focus()
        if selected:
            values = self.items_tree.item(selected)["values"]
            item_data = {
                "order": self.selected_order_id,
                "code": values[1],
                "product": values[2],
                "quantity": values[3],
                "price": values[4],
                "total": values[5]
            }
            EditQuantityWindow(self.master, self.conn, item_data, self.refresh_orders_table, self.user)
    def on_item_selected(self, event):
        selected = self.items_tree.focus()
        if selected:
            self.add_item_btn.pack_forget()
            self.edit_quantity_btn.pack(side=tk.LEFT, padx=5)
        else:
            self.edit_quantity_btn.pack_forget()
            self.add_item_btn.pack(side=tk.LEFT, padx=5)
    def edit_order_details(self):
        selected_item = self.orders_tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an order to edit.")
            return
        # Get selected row data
        values = self.orders_tree.item(selected_item, 'values')
        if not values:
            messagebox.showerror("Error", "Unable to retrieve data for the salected Order.")
            return
        order_id, customer_name, contact, deadline, total_amount = values[0], values[1], values[2], values[4], values[5]
        edit_win = tk.Toplevel(self.master) # Create popup Window
        edit_win.title("Edit Order Information")
        edit_win.configure(bg="lightblue")
        edit_win.geometry("300x250")
        edit_win.grab_set()
        # Labels and Entry widgets
        tk.Label(edit_win, text=f"Update details of order: {order_id}.", bg="lightblue", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        tk.Label(edit_win, text="Customer Name:", bg="lightblue").grid(row=1, column=0, padx=3, pady=2, sticky="e")
        entry_name = tk.Entry(edit_win, width=30)
        entry_name.grid(row=1, column=1, padx=3, pady=2)
        entry_name.insert(0, customer_name)
        entry_name.bind("<KeyRelease>", capitalize_customer_name)
        entry_name.focus()
        entry_name.select_range(0, tk.END)
        tk.Label(edit_win, text="Contact:", bg="lightblue").grid(row=2, column=0, padx=3, pady=2, sticky="e")
        entry_contact = tk.Entry(edit_win, width=30)
        entry_contact.grid(row=2, column=1, padx=3, pady=2)
        entry_contact.insert(0, contact)
        tk.Label(edit_win, text="Deadline:", bg="lightblue").grid(row=3, column=0, padx=3, pady=2, sticky="e")
        entry_deadline = tk.Entry(edit_win, width=30)
        entry_deadline.grid(row=3, column=1, padx=3, pady=2)
        entry_deadline.insert(0, deadline)
        def post_update():
            new_name = entry_name.get().strip()
            new_contact = entry_contact.get().strip()
            new_deadline = entry_deadline.get().strip()
            if not new_name or not new_contact or not new_deadline:
                messagebox.showwarning("Incomplete", "Please fill in all fields.")
                return
            update_order_details(self.conn, order_id, customer_name, contact, deadline, total_amount, self.user)
            edit_win.destroy()
        tk.Button(edit_win, text="Post Update", command=post_update).grid(row=4, column=0, columnspan=2, pady=10)
    
    def auto_adjust_column_widths(self, tree):
        for col in tree["columns"]:
            max_width = max([tk.font.Font().measure(str(tree.set(child, col))) for child in tree.get_children()] + [tk.font.Font().measure(col)])
            tree.column(col, width=max_width + 2)
    def refresh_orders_table(self):
        self.show_order_items()
        for i in self.orders_tree.get_children():
            self.orders_tree.delete(i)
        orders = fetch_pendind_orders(self.conn)
        for order in orders:
            self.orders_tree.insert("", "end", values=(
                order["order_id"],
                order["customer_name"],
                order["contact"],
                order["date_placed"],
                order["deadline"],
                order["amount"],
                order["status"]
            ))
        self.auto_adjust_column_widths(self.orders_tree)
        


# if __name__ == "__main__":
#     root = tk.Tk()
#     root.withdraw()
#     app = EditOrdersWindow(root, "Sniffy")
#     root.mainloop()