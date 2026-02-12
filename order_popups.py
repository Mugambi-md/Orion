import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from windows_utils import to_uppercase, DateEntryFormatter
from authentication import VerifyPrivilegePopup
from working_on_orders import (
    fetch_order_product, add_order_item, update_order_item,
    search_product_codes, update_order_details,
)


class AddItemWindow(BaseWindow):
    def __init__(self, parent, conn, order_id, refresh_callback, user):
        self.top = tk.Toplevel(parent)
        self.top.title(f"Add Item To Order No.{order_id}")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 300, 200, parent)
        self.top.transient(parent)
        self.top.grab_set()

        self.order_id = order_id
        self.conn = conn
        self.user = user
        self.refresh_callback = refresh_callback
        self.code = None
        self.product_name = None
        self.wholesale_price = None
        self.retail_price = None
        # Grid Layout
        self.main_frame = tk.Frame(self.top, bg="lightblue", bd=4, relief="solid")
        self.code_entry = tk.Entry(
            self.main_frame, bd=2, relief="raised", font=("Arial", 11), width=15
        )
        self.suggestions_listbox = tk.Listbox(
            self.main_frame, height=5, bg="lightgray", bd=2, relief="raised"
        )
        self.search_btn = tk.Button(
            self.main_frame, text="Search", bd=2, relief="solid", width=10,
            command=self.search_product,
        )
        self.qty_entry = tk.Entry(
            self.main_frame, font=("Arial", 11), bd=2, relief="raised", width=10
        )
        self.add_button = tk.Button(
            self.main_frame, text="Add to Order", bd=2, relief="solid",
            width=10, command=self.add_to_order,
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        tk.Label(
            self.main_frame, text="Product Code:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(10, 0), padx=10)
        self.code_entry.focus_set()
        self.code_entry.grid(row=1, column=0, pady=(0, 10), padx=10)
        self.suggestions_listbox.grid(row=2, column=0, sticky="we", padx=5)
        self.suggestions_listbox.bind(
            "<<ListboxSelect>>", self.fill_selected_code
        )
        self.suggestions_listbox.grid_remove()
        self.code_entry.bind(
            "<KeyRelease>", lambda e: to_uppercase(self.code_entry)
        )
        self.code_entry.bind("<KeyRelease>", self.update_suggestions)
        self.code_entry.bind("<Return>", lambda e: self.search_product())
        self.search_btn.grid(row=2, column=0, pady=5)
        self.search_btn.bind("<Return>", lambda e: self.search_product())
        tk.Label(
            self.main_frame, text="Quantity:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).grid(row=0, column=1, sticky="w", padx=10, pady=(10, 0))
        self.qty_entry.grid(row=1, column=1, padx=10, pady=(0, 10))
        self.qty_entry.bind("<Return>", lambda e: self.add_to_order())
        self.add_button.grid(row=2, column=1, pady=10)
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
            self.suggestions_listbox.grid(row=2, column=0, sticky="we")
        else:
            self.search_btn.grid(row=2, column=0, pady=5)
            self.suggestions_listbox.grid_remove()

    def fill_selected_code(self, event=None):
        try:
            selection = self.suggestions_listbox.get(
                self.suggestions_listbox.curselection()
            )
            code = selection.split(" - ")[0]
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, code)
            self.suggestions_listbox.delete(0, tk.END)
            self.suggestions_listbox.grid_remove()
            self.search_btn.grid(row=2, column=0, pady=5)
            self.search_btn.focus_set()
        except:
            pass

    def search_product(self):
        self.code = self.code_entry.get().strip().upper()
        if not self.code:
            messagebox.showerror(
                "Input Error", "Product Code is Required.", parent=self.top
            )
            return
        result = fetch_order_product(self.conn, self.code)
        if result:
            self.product_name = result["product_name"]
            self.wholesale_price = float(result["wholesale_price"])
            self.retail_price = float(result["retail_price"])
            answer = messagebox.askyesno(
                "Confirm",
                f"Add '{self.product_name}' to order?", parent=self.top
            )
            if answer:
                self.qty_entry.focus_set()
            else:
                self.code_entry.delete(0, tk.END)
                self.code_entry.focus_set()
        else:
            messagebox.showinfo(
                "Not Found",
                f"No Product Found With Code: {self.code}", parent=self.top
            )
            self.code_entry.select_range(0, tk.END)
            self.code_entry.focus_set()

    def add_to_order(self):
        if not hasattr(self, "product_name"):
            messagebox.showerror(
                "Error",
                "Search and select a valid product first.", parent=self.top
            )
            return
        try:
            qty = int(self.qty_entry.get().strip())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Input Error",
                "Quantity must be a positive integer.", parent=self.top
            )
            return
        unit_price = self.wholesale_price if qty >= 10 else self.retail_price
        total_price = unit_price * qty
        product_data = {
            "product_code": self.code,
            "product_name": self.product_name,
            "quantity": qty,
            "unit_price": unit_price,
            "total_price": total_price,
        }
        # Verify user privilege
        priv = "Edit Order"
        verify = VerifyPrivilegePopup(self.top, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied", f"Access Denied to {priv}.", parent=self.top
            )
            return
        success, message = add_order_item(
            self.conn, self.order_id, product_data, self.user
        )
        if success:
            messagebox.showinfo("Success", message, parent=self.top)
            self.refresh_callback()
            self.top.destroy()
        else:
            messagebox.showerror("Failed ", message, parent=self.top)


class EditQuantityWindow(BaseWindow):
    def __init__(self, parent, conn, item_data, refresh_items_callback, user):
        self.top = tk.Toplevel(parent)
        self.top.title("Edit Order Quantity")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 300, 250, parent)
        self.top.transient(parent)
        self.top.grab_set()

        self.conn = conn
        self.item_data = item_data
        self.refresh_items_callback = refresh_items_callback
        self.user = user
        self.code = None
        self.product_name = None
        self.wholesale_price = None
        self.retail_price = None
        self.main_frame = tk.Frame(
            self.top, bg="lightblue", bd=2, relief="solid"
        )
        # Product Code
        self.product_code_entry = tk.Entry(
            self.main_frame, bd=2, relief="raised", width=15,
            font=("Arial", 11)
        )
        # Search Button (can be expanded later)
        self.search_button = tk.Button(
            self.main_frame, text="Search", command=self.search_product,
            width=10, bd=2, relief="groove", bg="dodgerblue", fg="white",
        )
        # Quantity Entry
        self.quantity_entry = tk.Entry(
            self.main_frame, bd=2, relief="raised", font=("Arial", 11), width=5
        )
        # Update Button
        self.post_btn = tk.Button(
            self.main_frame, text="Update Order", command=self.update_order,
            width=10, bd=2, relief="groove", bg="dodgerblue", fg="white",
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        name = f"Update Quantity For: {str(self.item_data["product"])}"
        tk.Label(
            self.main_frame, text=name, bg="lightblue",
            font=("Arial", 11, "bold", "underline"),
        ).pack(pady=5, anchor="center")
        tk.Label(
            self.main_frame, text="Product Code:", font=("Arial", 11, "bold"),
            bg="lightblue",
        ).pack(pady=(5, 0), anchor="w")
        self.product_code_entry.pack(pady=(0, 5), padx=20, anchor="w")
        self.product_code_entry.bind(
            "<KeyRelease>", lambda e: to_uppercase(self.product_code_entry)
        )
        self.product_code_entry.insert(0, self.item_data["code"])
        self.search_button.pack(pady=5)
        self.search_button.focus_set()
        self.search_button.bind("<Return>", lambda e: self.search_product())
        tk.Label(
            self.main_frame, text="New Quantity:", bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(pady=(5, 0), anchor="w")
        self.quantity_entry.pack(pady=(0, 5), padx=20)
        self.quantity_entry.insert(0, str(self.item_data["quantity"]))
        self.quantity_entry.bind(
            "<Return>", lambda e: self.post_btn.focus_set()
        )
        self.post_btn.pack(pady=5)
        self.post_btn.bind("<Return>", lambda e: self.update_order())

    def search_product(self):
        self.code = self.product_code_entry.get().strip().upper()
        result = fetch_order_product(self.conn, self.code)
        order = self.item_data["order"]
        if result:
            self.product_name = result["product_name"]
            self.wholesale_price = float(result["wholesale_price"])
            self.retail_price = float(result["retail_price"])
            name = self.product_name
            answer = messagebox.askyesno(
                "Confirm",
                f"Update '{name}' Quantity in Order, {order}?",
                parent=self.top,
            )
            if answer:
                self.quantity_entry.focus_set()
            else:
                self.search_button.focus_set()
        else:
            messagebox.showinfo(
                "Not Found",
                f"No Product Found With Code: {self.code}", parent=self.top
            )
            self.product_code_entry.focus_set()

    def update_order(self):
        try:
            new_quantity = int(self.quantity_entry.get())
            if new_quantity <= 0:
                raise ValueError("Quantity Must Be Positive.")
            product_code = str(self.item_data["code"])
            order_id = int(self.item_data["order"])
            current_total_price = float(self.item_data["total"])
            unit_price = (
                self.wholesale_price if new_quantity >= 10 else self.retail_price
            )
            new_total_price = unit_price * new_quantity
            adjustment = new_total_price - current_total_price
            product_data = {
                "product_code": product_code,
                "quantity": new_quantity,
                "unit_price": unit_price,
                "total_price": new_total_price,
                "adjustment": adjustment,
            }
            # Verify user privilege
            priv = "Edit Order"
            verify = VerifyPrivilegePopup(
                self.top, self.conn, self.user, priv
            )
            if verify.result != "granted":
                messagebox.showwarning(
                    "Access Denied",
                    f"Access Denied to {priv}.", parent=self.top
                )
                return
            answer = messagebox.askyesno(
                "Confirm",
                f"Post '{self.product_name}' To Order?", parent=self.top
            )
            if answer:
                success, message = update_order_item(
                    self.conn, order_id, product_data, self.user
                )
                if success:
                    messagebox.showinfo("Success", message, parent=self.top)
                    self.refresh_items_callback()
                    self.top.destroy()
                else:
                    messagebox.showerror("Error", message, parent=self.top)
            else:
                self.quantity_entry.focus_set()
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e), parent=self.top)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"An unexpected error occurred:\n{e}", parent=self.top
            )


class EditOrderWindow(BaseWindow):
    def __init__(self, parent, conn, order_data, user):
        """Initialize the Edit Order Window."""
        self.master = tk.Toplevel(parent)
        self.master.title("Edit Order Information")
        self.master.configure(bg="lightblue")
        self.center_window(self.master, 330, 210, parent)
        self.master.transient(parent)
        self.master.grab_set()

        self.conn = conn
        self.user = user
        self.order_data = order_data
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.entry_name = tk.Entry(
            self.main_frame, bd=4, relief="raised", width=25,
            font=("Arial", 12)
        )
        self.entry_contact = tk.Entry(
            self.main_frame, bd=4, relief="raised", width=12,
            font=("Arial", 12)
        )
        self.entry_deadline = tk.Entry(
            self.main_frame, bd=4, relief="raised", width=10,
            font=("Arial", 12)
        )
        self.date_formatter = DateEntryFormatter(self.entry_deadline)

        self.build_ui()

    def build_ui(self):
        """Build the edit Order UI."""
        order_id = self.order_data["order_id"]
        customer_name = self.order_data["customer_name"]
        contact = self.order_data["contact"]
        deadline = self.order_data["deadline"]
        amount = float(self.order_data["total_amount"])
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        tk.Label(
            self.main_frame, text=f"Details For Order. {order_id}", fg="blue",
            bg="lightblue", font=("Arial", 16, "bold", "underline"),
        ).grid(row=0, column=0, columnspan=2, pady=(3, 0), sticky="ew")
        tk.Label(
            self.main_frame, text="Customer Name:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).grid(row=1, column=0, pady=(3, 0), sticky="sw")
        self.entry_name.grid(
            row=2, column=0, columnspan=2, pady=(0, 3), sticky="n"
        )
        self.entry_name.insert(0, customer_name)
        self.entry_name.bind("<KeyRelease>", self.capitalize_customer_name)
        self.entry_name.bind(
            "<Return>", lambda e: self.focus_select(self.entry_contact)
        )
        self.entry_name.focus_set()
        self.entry_name.select_range(0, tk.END)
        # Contact
        tk.Label(
            self.main_frame, text="Contact:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).grid(row=3, column=0, padx=(0, 3), pady=(3, 0), sticky="sw")
        self.entry_contact.grid(
            row=4, column=0, pady=(0, 3), sticky="n"
        )
        self.entry_contact.insert(0, contact)
        self.entry_contact.bind(
            "<Return>", lambda e: self.focus_select(self.entry_deadline)
        )
        # Deadline
        tk.Label(
            self.main_frame, text="Deadline(ddmmyyyy):", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).grid(row=3, column=1, pady=(3, 0), padx=(3, 0), sticky="sw")
        self.entry_deadline.grid(
            row=4, column=1, pady=(0, 3), sticky="n"
        )
        self.entry_deadline.insert(0, deadline)
        self.entry_deadline.bind(
            "<Return>", lambda e: self.post_update(order_id, amount)
        )
        # Post Button
        tk.Button(
            self.main_frame, text="Post Update", bg="blue", fg="white", bd=4,
            relief="raised", font=("Arial", 10, "bold"),
            command=lambda: self.post_update(order_id, amount),
        ).grid(row=5, column=0, columnspan=2, pady=(10, 0))

    def focus_select(self, widget):
        """Focus the next widget and select all text."""
        widget.focus_set()
        widget.select_range(0, tk.END)

    def capitalize_customer_name(self, event):
        """Auto-Capitalize Customer name while typing."""
        entry = event.widget
        value = entry.get()
        entry.delete(0, tk.END)
        entry.insert(0, value.title())

    def post_update(self, order_id, total_amount):
        """Handle posting of order updates."""
        name = self.entry_name.get().strip()
        contact = self.entry_contact.get().strip()
        deadline_row = self.entry_deadline.get().strip()

        try:
            deadline = DateEntryFormatter.to_mysql(deadline_row)
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Date must be in DD/MM/YYYY Format.", parent=self.master
            )
            self.entry_deadline.focus_set()
            self.entry_deadline.select_range(0, tk.END)
            return 

        if not name or not contact or not deadline:
            messagebox.showwarning(
                "Incomplete", "Please Fill in all Fields.", parent=self.master
            )
            return
        # Verify user privilege
        priv = "Edit Order"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        order_data = {
            "order_id": order_id,
            "customer_name": name,
            "contact": contact,
            "deadline": deadline,
            "total_amount": total_amount
        }
        result = update_order_details(self.conn, order_data, self.user)
        if isinstance(result, str) and result.lower().startswith("error"):
            messagebox.showerror("Error", result, parent=self.master)
        else:
            messagebox.showinfo(
                "Success",
                f"Order {order_id} Updated Successfully.", parent=self.master
            )
            self.master.destroy()
