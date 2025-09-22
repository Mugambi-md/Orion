import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from working_sales import search_product
from working_on_stock2 import add_to_existing_product
from window_functionality import to_uppercase, only_digits, auto_manage_focus
from working_on_stock import (delete_product, search_product_codes,
                              search_product_details)

class AddStockPopup(BaseWindow):
    def __init__(self, master, conn, refresh_callback=None):
        self.window = tk.Toplevel(master)
        self.window.title("Add Stock To Products")
        self.center_window(self.window, 300, 200, master)
        self.window.configure(bg="skyblue")
        self.window.transient(master)
        self.window.grab_set()
        self.conn = conn
        if refresh_callback:
            self.refresh_callback = refresh_callback
        else:
            self.refresh_callback = None

        self.labels = ["Product Code", "Quantity","New Cost", "New Wholesale Price", "New Retail Price", "New Min Stock Level"]
        self.entries = {}
        vcmd = (self.window.register(only_digits), '%S')

        for i, label in enumerate(self.labels):
            tk.Label(self.window, bg="skyblue", text=f"{label}:").grid(row=i, column=0, sticky="e", pady=3, padx=2)
            entry = tk.Entry(self.window, bg="white")
            if label != 'Product Code':
                entry.config(validate="key", validatecommand=vcmd)
            else:
                entry.bind("<KeyRelease>", lambda e: to_uppercase(e.widget))
            entry.grid(row=i, column=1, padx=2, pady=3)
            self.entries[label] = entry
        self.entries['New Min Stock Level'].bind("<Return>", lambda e: post_btn.focus_set())
        post_btn = tk.Button(self.window, text="Post Restock", width=15, command=self.submit, bg="dodgerblue")
        post_btn.grid(row=len(self.labels), column=0, columnspan=2, padx=20, pady=5)
        post_btn.bind("<Return>", lambda e: self.submit())
        auto_manage_focus(self.window)

    def submit(self):
        try:
            code = str(self.entries['Product Code'].get().strip().upper())
            added_quantity = int(self.entries['Quantity'].get().strip())
            def safe_float(val): return float(val.strip()) if val.strip() else None
            cost = safe_float(self.entries['New Cost'].get())
            wholesale_price = safe_float(self.entries['New Wholesale Price'].get())
            retail_price = safe_float(self.entries['New Retail Price'].get())
            min_stock_level = safe_float(self.entries['New Min Stock Level'].get())
            result = add_to_existing_product(self.conn, code, added_quantity, cost, wholesale_price, retail_price, min_stock_level)
            if result:
                if messagebox.askyesno("Success", f"{result}\nDo you want to add Another?", default='yes'):
                    for entry in self.entries.values():
                        entry.delete(0, tk.END)
                    self.entries['Product Code'].focus_set()
                else:
                    self.refresh_callback()
                    self.window.destroy()
            else:
                messagebox.showerror("Error", str(result))
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values where required.")



class DeleteProductPopup(BaseWindow):
    def __init__(self, master, conn, refresh_callback):
        self.window = tk.Toplevel(master)
        self.window.title("Delete Product")
        self.center_window(self.window, 270, 200)
        self.window.configure(bg="skyblue")
        self.window.transient(master)
        self.window.grab_set()

        self.product_code_var = tk.StringVar()
        self.refresh = refresh_callback
        self.conn = conn
        self.entry = None
        self.delete_btn = None
        self.listbox = tk.Listbox(self.window, bg="lightgray", width=25)

        self.products = None

        self.setup_widgets()

    def setup_widgets(self):
        # Label and Entry
        l_text = "Deleting a product is irreversible. Make sure you want to remove the product Completely. You can add it latter."
        tk.Label(self.window, text=l_text, fg="red", bg="skyblue",
                 font=("Arial", 11, "italic"), wraplength=250).pack(pady=3, padx=5)
        entry_frame = tk.Frame(self.window, bg="skyblue")
        entry_frame.pack(padx=5)
        tk.Label(entry_frame, text="Enter Product Code:", bg="skyblue").pack(pady=(5, 0), padx=3)
        self.entry = tk.Entry(entry_frame, textvariable=self.product_code_var, width=25)
        self.entry.pack(padx=3)
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self.uppercase_and_search)
        # Listbox
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.pack(padx=3)
        self.listbox.pack_forget()
        # Delete button (initially hidden)
        self.delete_btn = tk.Button(self.window, text="Delete Product", bg="dodgerblue", command=self.delete_selected)

    def uppercase_and_search(self, event=None):
        content = self.entry.get().upper()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, content)
        self.search_product()

    def search_product(self):
        self.listbox.delete(0, tk.END)
        product_code = self.product_code_var.get().strip()
        if not product_code:
            self.listbox.pack_forget()
            return
        try:
            results = search_product(self.conn, "product_code", product_code)
            if results:
                for product in results:
                    display = f"{product['product_code']} - {product['product_name']}"
                    self.products = results
                    self.listbox.insert(tk.END, display)
                self.listbox.config(height=min(len(results), 12))
                self.listbox.pack()
            else:
                self.listbox.pack_forget()
        except Exception as err:
            messagebox.showerror("Database Error", str(err))

    def on_select(self, event):
        if self.listbox.curselection():
            index = self.listbox.curselection()[0]
            product = self.products[index]
            product_code = product["product_code"]
            self.product_code_var.set(product_code)
            self.listbox.pack_forget()
            self.delete_btn.pack(pady=10)

    def delete_selected(self):
        product_code = self.product_code_var.get().strip()
        if not product_code:
            messagebox.showerror("No Product", "Please Enter a Valid Product Code.")
            return
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure to delete '{product_code}'?",
                                      default="no")
        if confirm:
            try:
                result = delete_product(product_code)
                if "deleted successfully" in result.lower():
                    messagebox.showinfo("Deleted", f"Product {product_code} has been deleted successfully.")
                    self.product_code_var.set("")
                    self.refresh()
                    self.window.destroy()
                else:
                    messagebox.showerror("Error", result)
                    self.entry.focus_set()
            except Exception as err:
                messagebox.showerror("Database Error", str(err))


class ProductUpdateWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Product Details")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 400, 500, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        # Variables
        self.search_var = tk.StringVar()
        # Frames
        self.top_frame = tk.Frame(self.window, bg="lightblue")
        self.details_frame = tk.Frame(self.window, bg="lightblue")
        self.entry = tk.Entry(self.top_frame, textvariable=self.search_var, width=40)
        self.suggestion_box = tk.Listbox(self.top_frame, width=40)
        self.search_btn = tk.Button(
            self.top_frame, text="Search", command=self.search, width=10
        )
        self.title = tk.Label(
            self.details_frame, text="", bg="lightblue", fg="dodgerblue",
            font=("Arial", 11, "bold", "underline")
        )
        self.entries = {}
        self.entry_order = []
        self.fields = {
            "Product Code:": tk.StringVar(),
            "Product Name:": tk.StringVar(),
            "Description:": tk.StringVar(),
            "Quantity:": tk.StringVar(),
            "Cost:": tk.StringVar(),
            "Retail Price:": tk.StringVar(),
            "Wholesale Price:": tk.StringVar(),
        }

        self.build_ui()

    def build_ui(self):
        self.top_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(
            self.top_frame, text="Enter Product Name / Code:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), anchor="w", padx=10)
        self.entry.pack(anchor="w", padx=10)
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self.on_keypress)
        # Suggestion listbox (initially hidden)
        self.suggestion_box.pack_forget()
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_select)
        self.search_btn.pack(pady=(5, 0))
        # Details Frame
        self.details_frame.pack(fill="both", expand=True, pady=10, padx=10)
        self.title.pack(anchor="center", padx=5)
        # 2 Columns Layout
        col1 = tk.Frame(self.details_frame, bg="lightblue")
        col2 = tk.Frame(self.details_frame, bg="lightblue")
        col1.pack(side="left", fill="both", expand=True, padx=5)
        col2.pack(side="left", fill="both", expand=True, padx=5)
        keys = list(self.fields.keys())
        mid = (len(keys) // 2) + 1
        for key in keys[:mid]:
            tk.Label(
                col1, text=key, bg="lightblue", font=("Arial", 10, "bold")
            ).pack()
            entry = tk.Entry(
                col1, textvariable=self.fields[key], width=30
            )
            entry.pack(pady=5)
            self.entries[key] = entry
            self.entry_order.append(entry)
        for key in keys[mid:]:
            tk.Label(
                col2, text=key, bg="lightblue", font=("Arial", 10, "bold")
            ).pack()
            entry = tk.Entry(
                col2, textvariable=self.fields[key], width=30
            )
            entry.pack(pady=5)
            self.entries[key] = entry
            self.entry_order.append(entry)
        for i, entry in enumerate(self.entry_order):
            entry.bind("<Return>", lambda e, idx=i: self.focus_next(idx))

    def focus_next(self, idx):
        """Focus next entry and highlight text."""
        if idx < len(self.entry_order) - 1:
            next_entry = self.entry_order[idx + 1]
            next_entry.focus_set()
            next_entry.selection_range(0, tk.END)
        return "break"

    def on_keypress(self, event):
        """Show suggestion box under entry."""
        keyword = self.search_var.get().strip()
        self.suggestion_box.delete(0, tk.END)
        self.search_btn.pack_forget()
        if not keyword:
            self.suggestion_box.pack_forget()
            self.search_btn.pack(pady=(5, 0))
            return
        results = search_product_codes(self.conn, keyword)
        if isinstance(results, str):
            messagebox.showerror("Error", results, parent=self.window)
            return
        if results:
            # Adjust height dynamically (max 8)
            height = min(len(results), 8)
            self.suggestion_box.config(height=height)
            self.suggestion_box.pack(anchor="w", fill="x", padx=10)
            for row in results:
                self.suggestion_box.insert(
                    tk.END, f"{row['product_code']} - {row['product_name']}"
                )
        else:
            self.suggestion_box.pack_forget()
            self.search_btn.pack(pady=(5, 0))

    def on_select(self, event):
        """Fill entry with selected value when chosen."""
        if not self.suggestion_box.curselection():
            return
        value = self.suggestion_box.get(self.suggestion_box.curselection())
        code, name = value.split(" - ", 1)
        # Auto-complete entry with product code (or name)
        self.search_var.set(code)
        self.suggestion_box.pack_forget()
        self.search_btn.pack(pady=(5, 0))

    def search(self):
        """Search button handler."""
        keyword = self.search_var.get().strip()
        if not keyword:
            messagebox.showwarning(
                "Warning", "Please Enter a Keyword.", parent=self.window
            )
            return
        self.load_product_details(keyword)

    def load_product_details(self, keyword):
        """Populate details form with product details."""
        row, err = search_product_details(self.conn, keyword)
        if err:
            messagebox.showerror("Error", err, parent=self.window)
            return
        if not row:
            messagebox.showinfo(
                "Not Found", "No Product Found.", parent=self.window
            )
            return
        # Map DB keys -> form Keys
        product_id = row["product_id"]
        mapping = {
            "Product Code:": "product_code",
            "Product Name:": "product_name",
            "Description:": "description",
            "Quantity:": "quantity",
            "Cost:": "cost",
            "Retail Price:": "retail_price",
            "Wholesale Price:": "wholesale_price",
        }
        # Autofill fields
        for form_key, db_key in mapping.items():
            if form_key in self.fields and db_key in row:
                self.fields[form_key].set(row[db_key])
        self.title.configure(text=f"Details For Product ID: {product_id}.")
        # Focus first entry and highlight text
        first_entry = self.entries["Product Code:"]
        first_entry.focus_set()
        first_entry.selection_range(0, tk.END)








if __name__ == "__main__":
    from connect_to_db import connect_db
    conn = connect_db()
    root = tk.Tk()
    app=ProductUpdateWindow(root, conn, "sniffy")
    root.mainloop()