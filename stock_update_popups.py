import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from window_functionality import auto_manage_focus, only_digits
from windows_utils import CurrencyFormatter
from working_on_stock import (
    update_quantity, get_product_codes
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
        product_code = self.code_entry.get().strip().upper()
        quantity = self.quantity_entry.get().strip()
        if not product_code or not quantity.isdigit():
            messagebox.showerror(
                "Invalid Input", "Enter a valid product code and quantity.",
                parent=self.popup
            )
            return
        # Verify Privilege
        priv = "Update Product Quantity"
        verify = VerifyPrivilegePopup(self.popup, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied", f"You Don't Have Permission to {priv}.",
                parent=self.popup
            )
            return

        qty = int(quantity)
        result = update_quantity(self.conn, product_code, qty, self.user)
        if result:
            messagebox.showinfo("Result", result, parent=self.popup)
            self.popup.destroy()


