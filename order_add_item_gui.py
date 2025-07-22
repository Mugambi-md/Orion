import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from windows_utils import to_uppercase
from working_on_orders import fetch_order_product, add_order_item, update_order_item, search_product_codes

class AddItemWindow(BaseWindow):
    def __init__(self, parent, conn, order_id, refresh_callback, user):
        self.order_id = order_id
        self.conn = conn
        self.user = user
        self.refresh_callback = refresh_callback

        self.top = tk.Toplevel(parent)
        self.top.title("Add Item To Order")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 300, 200)
        self.top.transient(parent)
        self.top.grab_set()

        # Grid Layout
        tk.Label(self.top, text="Enter Product Code:", bg="lightblue").grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.code_entry = tk.Entry(self.top)
        self.code_entry.focus_set()
        self.code_entry.grid(row=0, column=1, pady=5, padx=5)
        self.suggestions_listbox = tk.Listbox(self.top, height=5, bg="lightgray")
        self.suggestions_listbox.grid(row=1, column=1, sticky="we", padx=5)
        self.suggestions_listbox.bind("<<ListboxSelect>>", self.fill_selected_code)
        self.suggestions_listbox.grid_remove()
        self.code_entry.bind("<KeyRelease>", lambda e: to_uppercase(self.code_entry))
        self.code_entry.bind("<KeyRelease>", self.update_suggestions)
        self.code_entry.bind("<Return>", lambda e: self.search_btn.focus_set())
        self.search_btn = tk.Button(self.top, text="Search", command=self.search_product)
        self.search_btn.grid(row=1, column=0, columnspan=2, pady=5)
        self.search_btn.bind("<Return>", lambda e: self.search_product())
        tk.Label(self.top, text="Enter Product Quantity:", bg="lightblue").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.qty_entry = tk.Entry(self.top)
        self.qty_entry.grid(row=2, column=1, padx=5, pady=5)
        self.qty_entry.bind("<Return>", lambda e: self.add_button.focus_set())
        self.add_button = tk.Button(self.top, text="Add to Order", command=self.add_to_order)
        self.add_button.grid(row=3, column=0, columnspan=2, pady=10)
        self.add_button.bind("<Return>", lambda e: self.add_to_order())
    
    def update_suggestions(self, event=None):
        text = self.code_entry.get().strip().upper()
        self.code_entry.delete(0, tk.END)
        self.code_entry.insert(0, text)
        if not text:
            self.suggestions_listbox.grid_remove()
            return
        results = search_product_codes(self.conn, text)
        self.suggestions_listbox.delete(0, tk.END)
        if results:
            for item in results:
                display = f"{item['product_code']} - {item['product_name']}"
                self.suggestions_listbox.insert(tk.END, display)
            self.search_btn.grid_remove()
            self.suggestions_listbox.grid(row=1, column=1, sticky="we", padx=5)
        else:
            self.search_btn.grid(row=1, column=0, columnspan=2, pady=5)
            self.suggestions_listbox.grid_remove()
    def fill_selected_code(self, event=None):
        try:
            selection = self.suggestions_listbox.get(self.suggestions_listbox.curselection())
            code = selection.split(" - ")[0]
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, code)
            self.suggestions_listbox.delete(0, tk.END)
            self.suggestions_listbox.grid_remove()
            self.search_btn.grid(row=1, column=0, columnspan=2, pady=5)
            self.search_btn.focus_set()
        except:
            pass

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
        self.top = tk.Toplevel(parent)
        self.top.title("Edit Order Item Quantity")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 300, 200)
        self.top.transient(parent)
        self.top.grab_set()

        self.conn = conn
        self.item_data = item_data
        self.refresh_items_callback = refresh_items_callback
        self.user = user
        # Product Code
        tk.Label(self.top, text="Product Code:").pack(pady=(10, 0))
        self.product_code_entry = tk.Entry(self.top)
        self.product_code_entry.pack()
        self.product_code_entry.bind("<KeyRelease>", lambda e: to_uppercase(self.product_code_entry))
        self.product_code_entry.insert(0, item_data["code"])
        self.search_button = tk.Button(self.top, text="Search", command=self.search_product) # Search Button (can be expanded later)
        self.search_button.pack(pady=5)
        self.search_button.focus_set()
        # Quantity Entry
        tk.Label(self.top, text="New Quantity:").pack()
        self.quantity_entry = tk.Entry(self.top)
        self.quantity_entry.pack()
        self.quantity_entry.insert(0, str(item_data["quantity"]))
        self.quantity_entry.bind("<Return>", lambda e: self.post_btn.focus_set())
        # Update Button
        self.post_btn = tk.Button(self.top, text="Update Order", command=self.update_order)
        self.post_btn.pack(pady=5)
    
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
            self.product_code_entry.focus_set()
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
            answer = messagebox.askyesno("Confirm", f"Post '{self.product_name}' to order?")
            if answer:
                result = update_order_item(self.conn, order_id, product_code, new_quantity, unit_price, new_total_price, adjustment, self.user)
                if result:
                    messagebox.showinfo("Success", result)
                    self.refresh_items_callback()
                    self.top.destroy()
                else:
                    messagebox.showerror("Error", result)
            else:
                self.quantity_entry.focus_set()
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
            
    