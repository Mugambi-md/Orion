import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from windows_utils import SentenceCapitalizer
from working_on_stock import (
    update_quantity, update_price, update_description
)


class UpdatePriceWindow(BaseWindow):
    def __init__(self, master, conn, user, item, refresh_callback):
        self.window = tk.Toplevel(master)
        self.window.title("Update Price")
        self.window.configure(bg="lightgray")
        self.center_window(self.window, 350, 250, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.item = item
        self.refresh_callback = refresh_callback
        # Extract Values
        self.product_code = item[1]
        self.product_name = item[2]
        self.old_retail_price = item[5]
        self.old_wholesale_price = item[6]
        self.retail_var = tk.StringVar()
        self.wholesale_var = tk.StringVar()
        # Label showing current prices
        self.main_frame = tk.Frame(
            self.window, bg="lightgray", bd=4, relief="groove"
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        label_frame = tk.Frame(self.main_frame, bg="lightgray")
        label_frame.pack(side="top", fill="x", pady=(5, 0), padx=5)
        current_label = f"""
            Current price for {self.product_name}:
            Retail Price: {self.old_retail_price}
            Wholesale Price: {self.old_wholesale_price}.
        """
        tk.Label(
            label_frame, text=current_label, bg="lightgray", fg="blue",
            font=("Arial", 13, "bold")
        ).pack(padx=5, side="left")
        center_frame = tk.Frame(self.main_frame, bg="lightgray")
        center_frame.pack(pady=5)
        tk.Label(
            center_frame, text="Retail Price:", bg="lightgray",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, pady=(5, 0), sticky="e")
        retail_entry = tk.Entry(
            center_frame, textvariable=self.retail_var, font=("Arial", 11),
            width=10, bd=2, relief="raised"
        )
        retail_entry.grid(row=1, column=0, pady=(0, 5), padx=(5, 0))
        retail_entry.focus_set()
        retail_entry.bind(
            "<Return>", lambda e: wholesale_entry.focus_set()
        )
        tk.Label(
            center_frame, text="Wholesale Price:", bg="lightgray",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=1, pady=(5, 0), sticky="e")
        wholesale_entry = tk.Entry(
            center_frame, textvariable=self.wholesale_var, width=10, bd=2,
            font=("Arial", 11), relief="raised"
        )
        wholesale_entry.grid(row=1, column=1, pady=(0, 5), padx=(0, 5))
        wholesale_entry.bind("<Return>", lambda e: self.update_price())
        tk.Button(
            self.main_frame, text="Update Price", command=self.update_price
        ).pack()
        self.add_currency_trace(self.retail_var, retail_entry)
        self.add_currency_trace(self.wholesale_var, wholesale_entry)

    def add_currency_trace(self, var, entry):
        def callback(var_name, index, mode):
            self.format_currency(var, entry)
        var.trace_add("write", callback)

    def format_currency(self, var, entry):
        """Automatically format entry into money format."""
        # Temporarily remove trace to avoid recursion
        traces = var.trace_info()
        if traces:
            for mode, cbname in traces:
                var.trace_remove(mode, cbname)
        value = var.get().replace(",", "").strip()
        cleaned = ''.join(ch for ch in value if ch.isdigit())
        if not cleaned:
            # Reattach trace and return
            self.add_currency_trace(var, entry)
            return
        formatted = f"{int(cleaned):,}"
        var.set(formatted)
        entry.after_idle(lambda : entry.icursor(tk.END))
        # Reattach trace
        self.add_currency_trace(var, entry)

    def update_price(self):
        try:
            retail_var = self.retail_var.get().replace(",", "").strip()
            w_sale_var = self.wholesale_var.get().replace(",", "").strip()
            retail = retail_var if retail_var else None
            wholesale = w_sale_var if w_sale_var else None
            code = str(self.product_code)
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter Valid numeric prices", parent=self.window
            )
            return
        priv = "Admin Product Price"
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You do not have permission to {priv}.", parent=self.window
            )
            return
        success, message = update_price(
            self.conn, code, retail, wholesale, self.user
        )
        if success:
            messagebox.showinfo(
                "Success",
                f"Price Updated for {self.product_name}.", parent=self.window
            )
            self.refresh_callback()
            self.window.destroy()
        else:
            messagebox.showerror("Error", message, parent=self.window)


class UpdateQuantityPopup(BaseWindow):
    def __init__(self, parent, conn, user, product_data, refresh_callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Update Quantity")
        self.center_window(self.window, 300, 180, parent)
        self.window.configure(bg="lightgray")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.product_data = product_data
        self.refresh_callback = refresh_callback
        name = product_data[2]
        current_qty = product_data[4]
        self.label = f"Quantity for:\n{name} Is {current_qty}."
        self.new_qty_var = tk.StringVar()
        self.main_frame = tk.Frame(
            self.window, bg="lightgray", bd=4, relief="groove"
        )


        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(
            self.main_frame, text=self.label, bg="lightgray",
            font=("Arial", 14, "italic", "underline")
        ).pack(pady=5)
        entry_frame = tk.Frame(self.main_frame, bg="lightgray")
        entry_frame.pack(pady=10)
        tk.Label(
            entry_frame, text="New Quantity:", bg="lightgray",
            font=("Arial", 10, "bold")
        ).pack(pady=5, side="left")
        entry = tk.Entry(
            entry_frame, textvariable=self.new_qty_var, width=10, bd=2,
            relief="raised", font=("Arial", 11)
        )
        entry.pack(pady=5, side="left")
        entry.focus_set()
        entry.bind("<Return>", lambda e: self.update_quantity())
        post_btn = tk.Button(
            self.main_frame, text="Update Quantity", bd=2, relief="groove",
            command=self.update_quantity, bg="blue", fg="white"
        )
        post_btn.pack(pady=5, side="bottom")

    def update_quantity(self):
        new_qty = self.new_qty_var.get().strip()
        if not new_qty.isdigit():
            messagebox.showerror(
                "Invalid Input",
                "Please enter a valid number.", parent=self.window
            )
            return
        product_code = str(self.product_data[1])
        qty = int(new_qty)
        priv = "Update Product Quantity"
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You do not have permission to {priv}.", parent=self.window
            )
            return
        try:
            result = update_quantity(self.conn, product_code, qty, self.user)
            if result:
                messagebox.showinfo(
                    "Success",
                    "Quantity Updated Successfully.", parent=self.window
                )
                self.refresh_callback()
                self.window.destroy()
            else:
                messagebox.showerror(
                    "Error Updating", result, parent=self.window
                )
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self.window)

class UpdateDescriptionPopup(BaseWindow):
    def __init__(self, master, conn, item, refresh_callback, user):
        self.window = tk.Toplevel(master)
        self.window.title("Update Description")
        self.center_window(self.window, 400, 260, master)
        self.window.configure(bg="lightgray")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.item = item
        self.user = user
        self.refresh_callback = refresh_callback
        self.product_code = item[1]
        self.product_name = item[2]
        self.old_description = item[3]

        self.main_frame = tk.Frame(
            self.window, bg="lightgray", bd=4, relief="groove"
        )
        self.desc_text = tk.Text(
            self.main_frame, width=40, height=5, bd=2, relief="raised",
            font=("Arial", 11), wrap="word"
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Label with current description
        current_label = f"""
        Description For {self.product_name}:\n{self.old_description}."""
        tk.Label(
            self.main_frame, text=current_label, bg="lightgray",
            wraplength=380, font=("Arial", 10, "bold")
        ).pack(pady=(0, 5))
        # Entry for new description
        tk.Label(
            self.main_frame, text="New Description:", bg="lightgray",
            font=("Arial", 10, "bold")
        ).pack(pady=(5, 0))
        self.desc_text.pack(pady=(0, 5))
        self.desc_text.focus_set()
        SentenceCapitalizer.bind(self.desc_text)
        # Button to update
        update_btn = tk.Button(
            self.main_frame, text="Update Description", bd=2, relief="groove",
            command=self.update_description
        )
        update_btn.pack(pady=(0, 10))

    def update_description(self):
        description = self.desc_text.get("1.0", tk.END).strip()
        if not description:
            messagebox.showerror(
                "Invalid Input",
                "Description Cannot be Empty.", parent=self.window
            )
            return
        product_code = str(self.product_code)
        priv = "Update Product Details"
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You do not have permission to {priv}.", parent=self.window
            )
            return
        result = update_description(
            self.conn, product_code, description, self.user
        )
        if result:
            name = self.product_name
            messagebox.showinfo(
                "Success",
                f"Description updated for {name}", parent=self.window
            )
            self.refresh_callback()
            self.window.destroy()
        else:
            messagebox.showerror("Error", str(result), parent=self.window)

