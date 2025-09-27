import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from working_sales import search_product
from working_on_stock2 import add_to_existing_product
from authentication import VerifyPrivilegePopup
from window_functionality import to_uppercase, only_digits, auto_manage_focus
from working_on_stock import (
    delete_product, search_product_codes, update_product_details,
    search_product_details
)

class AddStockPopup(BaseWindow):
    def __init__(self, master, conn, user, refresh_callback=None):
        self.window = tk.Toplevel(master)
        self.window.title("Restocking Products")
        self.center_window(self.window, 300, 200, master)
        self.window.configure(bg="skyblue")
        self.window.transient(master)
        self.window.grab_set()

        self.user = user
        self.conn = conn
        if refresh_callback:
            self.refresh_callback = refresh_callback
        else:
            self.refresh_callback = None

        self.labels = ["Product Code", "Quantity", "Cost", "Wholesale Price",
                       "Retail Price", "Min Stock Level"]
        self.entries = {}

        self.build_ui()

    def build_ui(self):
        """Creating and placing widgets in two columns."""
        vcmd = (self.window.register(only_digits), '%S')
        col1_labels = self.labels[:3]
        col2_labels = self.labels[3:]

        # left column
        for i, label in enumerate(col1_labels):
            tk.Label(
                self.window, bg="skyblue", text=f"{label}:",
                font=("Arial", 11, "bold")
            ).grid(row=i*2, column=0, sticky="w", pady=(5, 0), padx=5)
            entry = tk.Entry(self.window, bd=2, relief="raised", width=15)
            if label != 'Product Code':
                entry.config(validate="key", validatecommand=vcmd)
            else:
                entry.bind("<KeyRelease>", lambda e: to_uppercase(e.widget))
            entry.grid(row=i*2+1, column=0, padx=10, pady=(0, 5), sticky="w")
            self.entries[label] = entry

        # Right Column
        for i, label in enumerate(col2_labels):
            tk.Label(
                self.window, bg="skyblue", text=f"{label}:",
                font=("Arial", 11, "bold")
            ).grid(row=i*2, column=1, sticky="w", pady=(5, 0), padx=5)
            entry = tk.Entry(self.window, bd=2, relief="raised", width=15)
            entry.config(validate="key", validatecommand=vcmd)
            entry.grid(row=i*2+1, column=1, padx=10, pady=(0, 5), sticky="w")
            self.entries[label] = entry
        self.entries['Min Stock Level'].bind("<Return>", lambda e: self.submit())
        # Button centered across both columns
        post_btn = tk.Button(self.window, text="Post Restock", width=15,
                             command=self.submit, bg="dodgerblue")
        post_btn.grid(row=6, column=0, columnspan=2, pady=(10, 5))
        post_btn.bind("<Return>", lambda e: self.submit())
        # Expand nicely
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        auto_manage_focus(self.window)


    def submit(self):
        # Verify Privilege
        priv = "Add Stock"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.window
            )
            return
        try:
            code = str(self.entries['Product Code'].get().strip().upper())
            added_quantity = int(self.entries['Quantity'].get().strip())
            def safe_float(val):
                return float(val.strip()) if val.strip() else None
            cost = safe_float(self.entries['Cost'].get())
            wholesale = safe_float(self.entries['Wholesale Price'].get())
            retail = safe_float(self.entries['Retail Price'].get())
            min_stock = safe_float(self.entries['Min Stock Level'].get())
            data = {
                "product_code": code,
                "quantity": added_quantity,
                "cost": cost,
                "wholesale_price": wholesale,
                "retail_price": retail,
                "min_stock_level": min_stock
            }
            success, msg = add_to_existing_product(self.conn, data, self.user)
            if success:
                messagebox.showinfo("Success", msg, parent=self.window)
                if messagebox.askyesno("Add Another", "Do you want to add Another?", default='yes'):
                    for entry in self.entries.values():
                        entry.delete(0, tk.END)
                    self.entries['Product Code'].focus_set()
                else:
                    self.window.destroy()
                    if self.refresh_callback is not None:
                        self.refresh_callback()
            else:
                messagebox.showerror("Error", msg)
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter valid numeric values where required.",
                parent=self.window
            )



class DeleteProductPopup(BaseWindow):
    def __init__(self, master, conn, user, refresh_callback=None):
        self.window = tk.Toplevel(master)
        self.window.title("Delete Product")
        self.center_window(self.window, 270, 200, master)
        self.window.configure(bg="skyblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.product_code_var = tk.StringVar()
        if refresh_callback is not None:
            self.refresh = refresh_callback
        else:
            self.refresh = None
        self.entry_frame = tk.Frame(self.window, bg="skyblue")
        self.entry = tk.Entry(
            self.entry_frame, textvariable=self.product_code_var, width=25,
            bd=2, relief="solid"
        )
        # Delete button (initially hidden)
        self.delete_btn = tk.Button(
            self.window, text="Delete Product", bg="dodgerblue", width=10,
            command=self.delete_selected, bd=4, relief="raised"
        )
        self.listbox = tk.Listbox(self.window, bg="lightgray", width=25)

        self.products = None

        self.setup_widgets()

    def setup_widgets(self):
        # Label and Entry
        l_text = "Deleting Product Completely."
        tk.Label(
            self.window, text=l_text, bg="skyblue", fg="red",
            font=("Arial", 12, "italic", "underline"), wraplength=250
        ).pack(pady=(10, 0), anchor="center")
        self.entry_frame.pack(padx=5)
        tk.Label(
            self.entry_frame, text="Enter Product Code:", bg="skyblue",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), padx=3)
        self.entry.pack(padx=3)
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self.uppercase_and_search)
        # Listbox
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.pack(padx=3)
        self.listbox.pack_forget()

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
            self.entry.icursor(tk.END)
            self.delete_btn.pack(pady=10)

    def delete_selected(self):
        # Verify Privilege
        priv = "Delete Product"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.window
            )
            return
        code = self.product_code_var.get().strip()
        if not code:
            messagebox.showerror(
                "No Product",
                "Please Enter a Valid Product Code.", parent=self.window
            )
            return
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"You want to delete '{code}'?", default="no", parent=self.window
        )
        if confirm:
            try:
                success, msg = delete_product(self.conn, code)
                if success:
                    messagebox.showinfo("Deleted", msg, parent= self.window)
                    self.product_code_var.set("")
                    if self.refresh is not None:
                        self.refresh()
                    self.window.destroy()
                else:
                    messagebox.showerror("Error", msg, parent=self.window)
                    self.entry.focus_set()
            except Exception as err:
                messagebox.showerror("Database Error", str(err))


class ProductUpdateWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Product Details")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 300, 500, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        # Variables
        self.search_var = tk.StringVar()
        self.product_id = None
        # Frames
        self.top_frame = tk.Frame(self.window, bg="lightblue")
        self.details_frame = tk.Frame(self.window, bg="lightblue", bd=4,
                                      relief="groove")
        self.entry = tk.Entry(self.top_frame, textvariable=self.search_var, width=30)
        self.suggestion_box = tk.Listbox(self.top_frame, bg="light grey", width=30)
        self.search_btn = tk.Button(
            self.top_frame, text="Search", command=self.search, width=10,
            bd=4, relief="groove"
        )
        self.title = tk.Label(
            self.details_frame, text="", bg="lightblue", fg="dodgerblue",
            font=("Arial", 11, "italic", "underline")
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
            "Min Stock Level:": tk.StringVar(),
        }

        self.build_ui()
        self.set_fields_state("disabled")

    def build_ui(self):
        self.top_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(
            self.top_frame, text="Enter Product Name/ Code:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), anchor="w", padx=10)
        self.entry.pack(pady=(0, 5), padx=10)
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self.on_keypress)
        # Suggestion listbox (initially hidden)
        self.suggestion_box.pack_forget()
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_select)
        self.search_btn.pack(pady=(5, 0))
        # Details Frame
        self.details_frame.pack(pady=(5, 0), expand=True, fill="both")
        self.title.pack(anchor="center", padx=5)
        # Product Name and Description (increased width)
        for key in ["Product Name:", "Description:"]:
            tk.Label(
                self.details_frame, text=key, bg="lightblue",
                font=("Arial", 11, "bold")
            ).pack(anchor="w", pady=(5, 0), padx=5)
            entry = tk.Entry(
                self.details_frame, textvariable=self.fields[key], width=40,
                bd=2, relief="raised"
            )
            entry.pack(pady=(0, 5), padx=5)
            self.entries[key] = entry
            self.entry_order.append(entry)
        # 2 Columns Layout
        col1 = tk.Frame(self.details_frame, bg="lightblue")
        col2 = tk.Frame(self.details_frame, bg="lightblue")
        col1.pack(side="left", padx=(10, 5))
        col2.pack(side="left", padx=(5, 10))
        keys = ["Product Code:", "Quantity:", "Cost:", "Retail Price:",
                "Wholesale Price:", "Min Stock Level:"]
        mid = len(keys) // 2
        for key in keys[:mid]:
            tk.Label(
                col1, text=key, bg="lightblue", font=("Arial", 11, "bold")
            ).pack(anchor="w", pady=(5, 0))
            entry = tk.Entry(col1, textvariable=self.fields[key], width=15,
                             bd=2, relief="raised")
            entry.pack(anchor="w", pady=(0, 5), padx=5)
            self.entries[key] = entry
            self.entry_order.append(entry)
        for key in keys[mid:]:
            tk.Label(
                col2, text=key, bg="lightblue", font=("Arial", 11, "bold")
            ).pack(anchor="w", pady=(5, 0))
            entry = tk.Entry(col2, textvariable=self.fields[key], width=15,
                             bd=2, relief="raised")
            entry.pack(anchor="w", pady=(0, 5), padx=5)
            self.entries[key] = entry
            self.entry_order.append(entry)
        code_entry = self.entries["Product Code:"]
        code_entry.bind("<KeyRelease>", lambda e: to_uppercase(code_entry))
        for i, entry in enumerate(self.entry_order):
            entry.bind("<Return>", lambda e, idx=i: self.focus_next(idx))

        tk.Button(
            self.window, text="Update Product", bg="dodgerblue",
            command=self.post_updates, bd=4, relief="raised", width=20
        ).pack(pady=10, anchor="center")

    def focus_next(self, idx):
        """Focus next entry and highlight text."""
        if idx < len(self.entry_order) - 1:
            next_entry = self.entry_order[idx + 1]
            next_entry.focus_set()
            next_entry.selection_range(0, tk.END)
            next_entry.icursor(tk.END)
        return "break"

    def on_keypress(self, event):
        """Show suggestion box under entry."""
        to_uppercase(self.entry)
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
            height = min(len(results), 5)
            self.suggestion_box.config(height=height)
            self.suggestion_box.pack(padx=10)
            for row in results:
                self.suggestion_box.insert(
                    tk.END, f"{row['product_code']}  --  {row['product_name']}"
                )
        else:
            self.suggestion_box.pack_forget()
            self.search_btn.pack(pady=(5, 0))

    def on_select(self, event):
        """Fill entry with selected value when chosen."""
        if not self.suggestion_box.curselection():
            return
        value = self.suggestion_box.get(self.suggestion_box.curselection())
        code, name = value.split(" -- ", 1)
        # Auto-complete entry with product code (or name)
        self.search_var.set(code)
        self.suggestion_box.pack_forget()
        self.search_btn.pack(pady=(5, 0))
        self.entry.focus_set()
        self.entry.icursor(tk.END)

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
        self.product_id = row["product_id"]
        name = row["product_name"]
        mapping = {
            "Product Code:": "product_code",
            "Product Name:": "product_name",
            "Description:": "description",
            "Quantity:": "quantity",
            "Cost:": "cost",
            "Retail Price:": "retail_price",
            "Wholesale Price:": "wholesale_price",
            "Min Stock Level:": "min_stock_level",
        }
        # Autofill fields
        for form_key, db_key in mapping.items():
            if form_key in self.fields and db_key in row:
                self.fields[form_key].set(row[db_key])
        self.set_fields_state("normal")
        self.title.configure(text=f"Details For Product: {name}.")
        # Focus first entry and highlight text
        first_entry = self.entries["Product Name:"]
        first_entry.focus_set()
        first_entry.selection_range(0, tk.END)
        first_entry.icursor(tk.END)

    def post_updates(self):
        """Collect all product details and pass to update function.
        Post all fields both Updated and un updated."""
        priv = "Update Product Details"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn,
                                             self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.window
            )
            return
        try:
            product = {
                "product_id": self.product_id,
                "product_code": self.fields["Product Code:"].get().strip(),
                "product_name": self.fields["Product Name:"].get().strip(),
                "description": self.fields["Description:"].get().strip(),
                "quantity": int(self.fields["Quantity:"].get().strip() or 0),
                "cost": float(self.fields["Cost:"].get().strip() or 0.0),
                "retail_price": float(
                    self.fields["Retail Price:"].get().strip() or 0.0
                ),
                "wholesale_price": float(
                    self.fields["Wholesale Price:"].get().strip() or 0.0
                ),
                "min_stock_level": int(
                    self.fields["Min Stock Level:"].get().strip() or 0
                ),
            }
        except Exception as e:
            messagebox.showerror(
                "Error", f"Invalid Input: {str(e)}", parent=self.window
            )
            return
        success, message = update_product_details(self.conn, product, self.user)
        if success:
            messagebox.showinfo("Success", message, parent=self.window)
            self.set_fields_state("disabled")
            self.search_var.set("")
            self.title.configure(text="")
            self.product_id = None
            for var in self.fields.values():
                var.set("")
            self.entry.focus_set()
        else:
            messagebox.showerror("Error", message, parent=self.window)

    def set_fields_state(self, state="disabled"):
        """Enable / disable all detail entry widgets."""
        for entry in self.entries.values():
            entry.config(state=state)




if __name__ == "__main__":
    from connect_to_db import connect_db
    conn = connect_db()
    root = tk.Tk()
    app=DeleteProductPopup(root, conn, "sniffy")
    root.mainloop()