import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
from base_window import BaseWindow
from report_exporter import DeliveryExporter
from working_on_orders import fetch_pendind_orders, fetch_order_payment_by_id, fetch_order_items_by_order_id, mark_order_as_delivered, delete_order
from connect_to_db import connect_db

conn=connect_db()

class OrdersDocumentationWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Orders Documentation")
        self.center_window(self.window, 1000, 600)
        self.window.configure(bg="lightblue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.selected_order_id = None
        # Left Frame for buttons
        self.left_frame = tk.Frame(self.window, background="lightblue", width=200)
        self.left_frame.pack(side="left", fill="y", padx=5, pady=5)
        tk.Label(self.left_frame, bg="lightblue").pack(pady=5)
        self.buttons = {
            "Deliver Order": self.deliver_order,
            "Delete Order": self.delete_order,
        }
        for text, command in self.buttons.items():
            tk.Button(self.left_frame, text=text, command=command).pack(pady=3)
        self.right_frame = tk.Frame(self.window, bg="lightblue")
        self.right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        self.create_table()

    def create_table(self):
        columns = ("Order ID", "Customer Name", "Contact", "Date Ordered", "Deadline", "Amount", "Status")
        tk.Label(self.right_frame, text="Current Undelivered Orders.", font=("Arial", 11, "bold"), bg="lightblue").pack(anchor="center", padx=2)
        self.tree = ttk.Treeview(self.right_frame, columns=columns, show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.bind("<<TreeviewSelect>>", self.order_details)
        self.tree.bind("<MouseWheel>", lambda e: self._on_mousewheel(self.tree, e)) # Windows/Linux
        orders_scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=orders_scrollbar.set)
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        orders_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        orders = fetch_pendind_orders(self.conn)
        for order in orders:
            self.tree.insert("", "end", values=(
                order["order_id"],
                order["customer_name"],
                order["contact"],
                order["date_placed"],
                order["deadline"],
                order["amount"],
                order["status"]
            ))
        self.auto_resize_columns(self.tree)
    
    def _on_mousewheel(self, treeview, event=None): # Mouse wheel scrolling (window and Linux)
            treeview.yview_scroll(int(-1 * (event.delta / 120)), "units")
    def auto_resize_columns(self, tree):
        font = tkFont.Font()
        for col in tree["columns"]:
            max_width = font.measure(col) # Start with header width
            for item in tree.get_children():
                text = tree.set(item, col)
                width = font.measure(str(text))
                if width > max_width:
                    max_width = width
            tree.column(col, width=max_width + 10)

    def order_details(self, event=None):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.selected_order_id = values[0]

    def deliver_order(self):
        if not self.selected_order_id:
            messagebox.showwarning("No Selection", "Please select Order first.")
            return
        order_id = self.selected_order_id
        result = fetch_order_payment_by_id(self.conn, order_id)
        if isinstance(result, str): # Error string returned
            messagebox.showerror("Error", result)
            return
        balance = result['balance']
        popup = tk.Toplevel(self.window)
        popup.title("Order Delivery Options")
        popup.geometry("600x500")
        popup.configure(bg="lightblue")
        popup.transient(self.window)
        popup.grab_set()
        if balance > 0:
            msg_text = f"NOT fully paid. Balance: {balance}"
        else:
            msg_text = "Fully Paid. You can print the Delivery Note."
        self.status = msg_text
        tk.Label(popup, text="Ordered Items.",bg="lightblue", font=("Arial", 11, "bold")).pack(anchor="center", padx=5, pady=2)
        btn_frame = tk.Frame(popup, bg="lightblue")
        btn_frame.pack(pady=2)
        tk.Button(btn_frame, text="Print & Mark Delivered",command=lambda: self.mark_print_delivery(popup), bg="blue", fg="white", padx=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Print Delivery", command=lambda: self.print_delivery_note(popup), bg="green", fg="white", padx=10, pady=2).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Clear Balance", command=popup.destroy, bg="darkorange", fg="white", padx=10, pady=2).pack(side="right", padx=5)
        columns = ("No", "Product Code", "Product Name", "Quantity", "Unit Price", "Total Price")
        self.items_tree = ttk.Treeview(popup, columns=columns, show="headings")
        for col in columns:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, anchor="center", width=50)
        items_scrollbar = ttk.Scrollbar(popup, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)
        self.items_tree.bind("<MouseWheel>", lambda e: self._on_mousewheel(self.items_tree, e)) # Windows/Linux
        self.items_tree.pack(side=tk.LEFT, fill="both", expand=True, padx=(4, 0), pady=3)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=3)
        items = fetch_order_items_by_order_id(self.conn, order_id)
        for i, item in enumerate(items, start=1):
            self.items_tree.insert("", "end", values=(
                i,
                item["product_code"],
                item["product_name"],
                item["quantity"],
                item["unit_price"],
                item["total_price"]
            ))
        self.auto_resize_columns(self.items_tree)
        messagebox.showinfo("Order Status", msg_text)
        total_sum = sum(item["total_price"] for item in items)
        self.items_tree.insert("", "end", values=("", "","", "", "TOTAL", total_sum), tags=("total",))
        self.items_tree.tag_configure("total", background="lightgray", font=("Arial", 10, "bold"))
        
    def collect_treeview_data(self):
        data = []
        for row_id in self.items_tree.get_children():
            data.append(self.items_tree.item(row_id)["values"])
        return data
    
    def mark_print_delivery(self, parent_popup):
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to Mark Order: {self.selected_order_id} Delivered?")
        if not confirm:
            self.print_delivery_note(parent_popup)
        else:
            try:
                result= mark_order_as_delivered(self.conn, self.selected_order_id)
                if result:
                    self.print_delivery_note(parent_popup)
                    messagebox.showinfo("Succes", result)
                    self.selected_order_id = None
                    parent_popup.destroy()
                else:
                    messagebox.showerror("Error", result)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update order: {e}")
    def print_delivery_note(self, parent_popup):
        data = self.collect_treeview_data()
        exporter = DeliveryExporter(self.selected_order_id, data, self.status)
        path = exporter.export_to_pdf()
        messagebox.showinfo("PDF Exported", f"Saved to: {path}")
        parent_popup.destroy()
         
    def delete_order(self):
        if not self.selected_order_id:
            messagebox.showwarning("No Selection", "Please select Order first.")
            return
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to DELETE Order: {self.selected_order_id}?")
        if confirm:
            try:
                result = delete_order(self.conn, self.selected_order_id, self.user)
                messagebox.showinfo("Success", result)
                self.selected_order_id = None
            except Exception as e:
                messagebox.showerror("Error", f"Failed to Delete order: {e}")
        else:
            messagebox.showinfo("Cancelled", "Order Deletion Cancelled.")
    
         
# if __name__ == "__main__":
#     root = tk.Tk()
#     # root.withdraw()
#     app = OrdersDocumentationWindow(root, conn, "Sniffy")
#     root.mainloop()