import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from window_functionality import auto_manage_focus, only_digits
from working_on_stock import (
    update_quantity, get_product_codes, add_to_existing_product
)


class UpdateQuantityWindow(BaseWindow):
    def __init__(self, master, conn, user, product_code=None):
        self.popup = tk.Toplevel(master)
        self.popup.title("Update Quantity")
        self.center_window(self.popup, 250, 200, master)
        self.popup.configure(bg="lightgreen")
        self.popup.grab_set()
        self.popup.transient(master)
        # Label and Entry widgets
        self.conn = conn
        self.user = user
        self.main_frame = tk.Frame(
            self.popup, bg="lightgreen", bd=4, relief="solid"
        )
        self.code_entry = tk.Entry(
            self.main_frame, width=15, bd=2, relief="raised",
            font=("Arial", 11)
        )
        if product_code:  # Pre-fill code if provided
            self.code_entry.insert(0, product_code)
        validate_cmd = self.popup.register(only_digits)
        self.quantity_entry = tk.Entry(
            self.main_frame, width=10, validate="key", bd=2, relief="raised",
            validatecommand=(validate_cmd, "%S"), font=("Arial", 11)
        )
        # Label for feedback initially hidden
        self.label = tk.Label(
            self.main_frame, text="", bg="lightgreen", fg="red",
            font=("Arial", 9, "italic", "underline")
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tk.Label(
            self.main_frame, text="Product Code:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0))
        self.code_entry.pack()
        self.code_entry.focus_set()
        self.code_entry.bind("<KeyRelease>", self.check_product_code)
        self.code_entry.bind(
            "<Return>", lambda e: self.quantity_entry.focus_set()
        )
        self.label.pack(pady=(2, 0))
        tk.Label(
            self.main_frame, text="New Quantity:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0))
        self.quantity_entry.pack(pady=(0, 5))
        self.quantity_entry.bind("<Return>", lambda e: self.perform_update())
        # Update Button
        tk.Button(
            self.main_frame, text="Update", bg="dodgerblue", width=10, bd=2,
            relief="groove", command=self.perform_update
        ).pack(pady=10)
        auto_manage_focus(self.popup)
        self.code_entry.focus_set()

    def check_product_code(self, event):
        current_text = self.code_entry.get()
        uppercase_text = current_text.upper()
        if current_text != uppercase_text:
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, uppercase_text)
        code = uppercase_text.strip()
        self.code_entry.configure(bg="white")
        self.label.configure(text="")
        if not code:
            return # Empty input, reset look

        success, result = get_product_codes(self.conn, code)
        # Handle DB or Logic errors
        if not success:
            self.label.configure(text=result, fg="red")
            return
        # Check if code exists among fetched items
        found = any(item["product_code"].startswith(code) for item in result)
        if not found:
            # Show Error feedback
            self.code_entry.configure(bg="#ffcccc") # Light red
            self.label.configure(text="Product Code Not Found.", fg="red")
        else:
            self.code_entry.configure(bg="white")
            self.label.configure(text="")

    def perform_update(self):
        # Verify Privilege
        priv = "Update Product Quantity"
        verify_dialog = VerifyPrivilegePopup(self.popup, self.conn, self.user,
                                             priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied",
                                   f"You do not have permission to {priv}.")
            return
        product_code = self.code_entry.get().strip().upper()
        quantity = self.quantity_entry.get().strip()
        if not product_code or not quantity.isdigit():
            messagebox.showerror(
                "Invalid Input", "Enter a valid product code and quantity."
            )
            return
        qty = int(quantity)
        result = update_quantity(self.conn, product_code, qty, self.user)
        if result:
            messagebox.showinfo("Result", result)
            self.popup.destroy()


class AddStockPopup(BaseWindow):
    def __init__(self, master, conn, user, refresh_callback=None):
        self.window = tk.Toplevel(master)
        self.window.title("Restocking Products")
        self.center_window(self.window, 300, 300, master)
        self.window.configure(bg="skyblue")
        self.window.transient(master)
        self.window.grab_set()

        self.user = user
        self.conn = conn
        if refresh_callback:
            self.refresh_callback = refresh_callback
        else:
            self.refresh_callback = None

        self.labels = [
            "Product Code", "Quantity", "Cost", "Wholesale Price",
            "Retail Price", "Min Stock Level"
        ]
        self.entries = {}
        self.main_frame = tk.Frame(
            self.window, bg="skyblue", bd=4, relief="solid"
        )
        self.code_entry = tk.Entry(
            self.main_frame, bd=2, relief="raised", width=15,
            font=("Arial", 11)
        )
        # Label for feedback initially hidden
        self.label = tk.Label(
            self.main_frame, text="", bg="skyblue", fg="red",
            font=("Arial", 9, "italic", "underline")
        )

        self.build_ui()

    def build_ui(self):
        """Creating and placing widgets in two columns."""
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tk.Label(
            self.main_frame, bg="skyblue", text="Product Code:",
            font=("Arial", 10, "bold")
        ).pack(pady=(5, 0))
        self.code_entry.pack(pady=(0, 2))
        self.code_entry.focus_set()
        self.code_entry.bind("<KeyRelease>", self.check_product_code)
        self.label.pack(pady=(2, 0))
        entry_frame = tk.Frame(self.main_frame, bg="skyblue")
        entry_frame.pack(expand=True)
        vcmd = (self.window.register(only_digits), '%S')
        col1_labels = self.labels[1:4]
        col2_labels = self.labels[4:]

        # left column
        for i, label in enumerate(col1_labels):
            tk.Label(
                entry_frame, bg="skyblue", text=f"{label}:",
                font=("Arial", 10, "bold")
            ).grid(row=i*2, column=0, sticky="w", pady=(5, 0), padx=5)
            entry = tk.Entry(
                entry_frame, bd=2, relief="raised", width=10,
                font=("Arial", 11)
            )
            entry.config(validate="key", validatecommand=vcmd)
            entry.grid(row=i*2+1, column=0, padx=10, pady=(0, 5), sticky="w")
            self.entries[label] = entry

        # Right Column
        for i, label in enumerate(col2_labels):
            tk.Label(
                entry_frame, bg="skyblue", text=f"{label}:",
                font=("Arial", 10, "bold")
            ).grid(row=i*2, column=1, sticky="w", pady=(5, 0), padx=5)
            entry = tk.Entry(
                entry_frame, bd=2, relief="raised", width=10,
                font=("Arial", 11)
            )
            entry.config(validate="key", validatecommand=vcmd)
            entry.grid(row=i*2+1, column=1, padx=10, pady=(0, 5), sticky="w")
            self.entries[label] = entry
        self.entries['Min Stock Level'].bind(
            "<Return>", lambda e: self.submit()
        )
        # Button centered across both columns
        post_btn = tk.Button(
            entry_frame, text="Post Restock", width=15, command=self.submit,
            bg="dodgerblue"
        )
        post_btn.grid(row=6, column=0, columnspan=2, pady=(10, 5))
        post_btn.bind("<Return>", lambda e: self.submit())
        # Expand nicely
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        auto_manage_focus(self.window)


    def check_product_code(self, event):
        current_text = self.code_entry.get()
        uppercase_text = current_text.upper()
        if current_text != uppercase_text:
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, uppercase_text)
        code = uppercase_text.strip()
        self.code_entry.configure(bg="white")
        self.label.configure(text="")
        if not code:
            return # Empty input, reset look

        success, result = get_product_codes(self.conn, code)
        # Handle DB or Logic errors
        if not success:
            self.label.configure(text=result, fg="red")
            return
        # Check if code exists among fetched items
        found = any(item["product_code"].startswith(code) for item in result)
        if not found:
            # Show Error feedback
            self.code_entry.configure(bg="#ffcccc") # Light red
            self.label.configure(text="Product Code Not Found.", fg="red")
        else:
            self.code_entry.configure(bg="white")
            self.label.configure(text="")

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
                if messagebox.askyesno(
                        "Add Another", "Do you want to add Another?",
                        default='yes', parent=self.window):
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

