import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from working_on_orders import fetch_order_product, add_order_item, update_order_item

class AddItemWindow(BaseWindow):
    def __init__(self, parent, conn, order_id, refresh_callback, user):
        #self.parent = parent
        self.order_id = order_id
        self.conn = conn
        self.user = user
        self.refresh_callback = refresh_callback

        self.top = tk.Toplevel(parent)
        self.top.title("Add Item To Order")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 350, 200)
        self.top.grab_set()
        self.top.transient(parent)

        #self.center_popup()

        # Grid Layout
        tk.Label(self.top, text="Enter Product Code:", bg="lightblue").grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.code_entry = tk.Entry(self.top)
        self.code_entry.grid(row=0, column=1, pady=5, padx=5)
        self.search_btn = tk.Button(self.top, text="Search", command=self.search_product)
        self.search_btn.grid(row=1, column=0, columnspan=2, pady=5)
        tk.Label(self.top, text="Enter Product Quantity:", bg="lightblue").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.qty_entry = tk.Entry(self.top)
        self.qty_entry.grid(row=2, column=1, padx=5, pady=5)
        self.add_button = tk.Button(self.top, text="Add to Order", command=self.add_to_order)
        self.add_button.grid(row=3, column=0, columnspan=2, pady=10)
    # def center_popup(self):
    #     self.parent.update_idletasks()
    #     px = self.parent.winfo_x()
    #     py = self.parent.winfo_y()
    #     pw = self.parent.winfo_width()
    #     ph = self.parent.winfo_height()
    #     width, height = 350, 200
    #     x = px + (pw - width) // 2
    #     y = py + (ph - height) // 2
    #     self.top.geometry(f"{width}x{height}+{x}+{y}")
    def search_product(self):
        self.code = self.code_entry.get().strip().upper()
        if not self.code:
            messagebox.showerror("Input Error", "Product Code is Required.")
            return
        result = fetch_order_product(self.code)
        if result:
            self.product_name = result["product_name"]
            self.wholesale_price = float(result["wholesale_price"])
            self.retail_price = float(result["retail_price"])
            answer = messagebox.askyesno("Confirm", f"Add '{self.product_name}' to order?")
            if answer:
                self.qty_entry.focus_set()
            else:
                self.code_entry.delete(0, tk.END)
                self.code_entry.focus_set()
        else:
            messagebox.showinfo("Not Found", f"No Product Found With Code: {self.code}")
            self.code_entry.delete(0, tk.END)
            self.code_entry.focus_set()
    def add_to_order(self):
        if not hasattr(self, "product_name"):
            messagebox.showerror("Error", "Search and select a valid product first.")
            return
        try:
            qty = int(self.qty_entry.get().strip())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Quantity must be a positive integer.")
            return
        unit_price = self.wholesale_price if qty >= 10 else self.retail_price
        total_price = unit_price * qty
        feedback = add_order_item(self.conn, self.order_id, self.code, self.product_name, qty, unit_price, total_price, self.user)
        if feedback:
            messagebox.showinfo("Success", f"{self.product_name}, added to order.")
            self.refresh_callback()
            self.top.destroy()
        else:
            messagebox.showerror("Error", f"Failed to add item: {feedback}.")


class EditQuantityWindow(BaseWindow):
    def __init__(self, parent, conn, item_data, refresh_items_callback, user):
        #self.parent = parent
        self.top = tk.Toplevel(parent)
        self.top.title("Edit Order Item Quantity")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 400, 300)
        self.top.grab_set()
        self.top.transient(parent)
        #self.center_popup()

        self.conn = conn
        self.item_data = item_data
        self.refresh_items_callback = refresh_items_callback
        self.user = user
        # Product Code
        tk.Label(self.top, text="Product Code:").pack(pady=(10, 0))
        self.product_code_entry = tk.Entry(self.top)
        self.product_code_entry.pack()
        self.product_code_entry.insert(0, item_data["code"])
        self.search_button = tk.Button(self.top, text="Search", command=self.search_product) # Search Button (can be expanded later)
        self.search_button.pack(pady=5)
        self.search_button.focus_set()
        # Quantity Entry
        tk.Label(self.top, text="New Quantity:").pack()
        self.quantity_entry = tk.Entry(self.top)
        self.quantity_entry.pack()
        self.quantity_entry.insert(0, str(item_data["quantity"]))
        # Update Button
        tk.Button(self.top, text="Update Order", command=self.update_order).pack(pady=5)
    # def center_popup(self):
    #     self.parent.update_idletasks()
    #     px = self.parent.winfo_x()
    #     py = self.parent.winfo_y()
    #     pw = self.parent.winfo_width()
    #     ph = self.parent.winfo_height()
    #     width, height = 400, 300
    #     x = px + (pw - width) // 2
    #     y = py + (ph - height) // 2
    #     self.top.geometry(f"{width}x{height}+{x}+{y}")
    def search_product(self):
        self.code = self.product_code_entry.get().strip().upper()
        result = fetch_order_product(self.code)
        order_id = self.item_data["order"]
        if result:
            self.product_name = result["product_name"]
            self.wholesale_price = float(result["wholesale_price"])
            self.retail_price = float(result["retail_price"])
            answer = messagebox.askyesno("Confirm", f"Do you want to update '{self.product_name}' in order {order_id}?")
            if answer:
                self.quantity_entry.focus_set()
            else:
                self.search_button.focus_set()
        else:
            messagebox.showinfo("Not Found", f"No Product Found With Code: {self.code}")
    def update_order(self):
        try:
            new_quantity = int(self.quantity_entry.get())
            if new_quantity <= 0:
                raise ValueError("Quantity Must Be Positive.")
            product_code = str(self.item_data["code"])
            order_id = int(self.item_data["order"])
            current_total_price = float(self.item_data["total"])
            unit_price = self.wholesale_price if new_quantity >= 10 else self.retail_price
            new_total_price = unit_price * new_quantity
            adjustment = new_total_price - current_total_price
            update_order_item(self.conn, order_id, product_code, new_quantity, unit_price, new_total_price, adjustment, self.user)
            self.refresh_items_callback()
            self.top.destroy()
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
            
    