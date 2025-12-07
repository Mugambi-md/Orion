import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from working_on_orders import search_product_codes
from working_sales import search_product
from authentication import VerifyPrivilegePopup
from window_functionality import (
    to_uppercase, only_digits, auto_manage_focus
)
from windows_utils import (
    CurrencyFormatter, capitalize_customer_name, SentenceCapitalizer
)
from working_on_stock import (
    insert_new_product, delete_product, restore_deleted_product,
    search_deleted_product_codes, add_to_existing_product, get_product_codes,
    search_product_codes, update_product_details, search_product_details,
    update_min_stock_level
)


class NewProductPopup(BaseWindow):
    def __init__(self, parent, conn, user):
        self.popup = tk.Toplevel(parent)
        self.popup.title("Add New Product")
        self.popup.configure(bg="lightgreen")
        self.center_window(self.popup, 300, 500, parent)
        self.popup.grab_set()
        self.popup.transient(parent)

        self.conn = conn
        self.user = user
        self.field_vars = {}
        self.entries = {}
        self.validate_cmd = self.popup.register(only_digits)
        self.entry_order = []
        self.digit_fields = {"Quantity", "Min Stock Level"}
        self.currency_fields = {"Cost", "Wholesale Price", "Retail Price"}
        self.main_frame = tk.Frame(
            self.popup, bg="lightgreen", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.bottom_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.warning_label = tk.Label(
            self.top_frame, text="Product Code is not Available", fg="red",
            bg="lightgreen", font=("Arial", 9, "italic"), anchor="center",
        )

        self.build_form()

    def build_form(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(
            self.main_frame, text="Add New Product.", bd=2, relief="ridge",
            bg="lightgreen", fg="blue", font=("Arial", 13, "bold", "underline")
        ).pack(anchor="center", ipadx=5, pady=(5, 0))
        self.top_frame.pack(fill="both", expand=True)
        tk.Label(
            self.top_frame, text="Product Code:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, pady=(5, 0), sticky="w", padx=5)
        code_entry = tk.Entry(
            self.top_frame, width=20, font=("Arial", 11), bd=2,
            relief="raised"
        )
        code_entry.grid(row=1, column=0, pady=(0, 2))
        code_entry.bind("<KeyRelease>", self.check_product_code)
        code_entry.bind("<Return>", self.on_enter_code)
        code_entry.focus_set()
        self.entries["Product Code"] = code_entry
        self.entry_order.append(code_entry)
        self.warning_label.grid(row=2, column=0, columnspan=2, padx=5)
        self.warning_label.grid_remove()
        tk.Label(
            self.top_frame, text="Product Name:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).grid(row=3, column=0, pady=(3, 0), sticky="w", padx=5)
        name_entry = tk.Entry(
            self.top_frame, width=20, font=("Arial", 11), bd=2,
            relief="raised"
        )
        name_entry.grid(row=4, column=0, pady=(0, 3))
        self.entries["Product Name"] = name_entry
        self.entry_order.append(name_entry)
        name_entry.bind("<KeyRelease>", capitalize_customer_name)
        tk.Label(
            self.top_frame, text="Description:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).grid(row=5, column=0, pady=(3, 0), sticky="w", padx=5)
        desc = tk.Text(
            self.top_frame, width=30, height=4, wrap="word", bd=2,
            relief="ridge", font=("Arial", 11)
        )
        desc.grid(row=6, column=0, columnspan=2, pady=(0, 3), padx=5)
        SentenceCapitalizer.bind(desc)
        self.entries["Description"] = desc
        self.entry_order.append(desc)
        # Other entries
        self.bottom_frame.pack(anchor="center", expand=True)
        fields = [
            ("Quantity", 0, 0),
            ("Cost", 0, 1),
            ("Wholesale Price", 2, 0),
            ("Retail Price", 2, 1),
            ("Min Stock Level", 4, 0),
        ]
        for label, row, col in fields:
            tk.Label(
                self.bottom_frame, text=label + ":", bg="lightgreen",
                font=("Arial", 11, "bold")
            ).grid(row=row, column=col, pady=(3, 0), sticky="w", padx=10)
            var = tk.StringVar()
            entry = tk.Entry(
                self.bottom_frame, textvariable=var, width=10, bd=2,
                relief="raised", font=("Arial", 11)
            )
            entry.grid(row=row+1, column=col, pady=(0, 5), padx=5)
            self.entries[label] = entry
            self.field_vars[label] = var
            self.entry_order.append(entry)
            # Validate digits only
            if label in self.digit_fields:
                entry.config(
                    validate="key", validatecommand=(self.validate_cmd, "%S")
                )
            # Auto currency format
            if label in self.currency_fields:
                CurrencyFormatter.add_currency_trace(var, entry)
        for i, entry in enumerate(self.entry_order):
            entry.bind("<Return>", lambda e, idx=i: self.focus_next(idx))
        self.entries["Min Stock Level"].bind("<Return>", lambda e: self.submit_product())
        # Submit Button
        submit_btn = tk.Button(
            self.main_frame, text="Post Item", bg="lightblue", width=10,
            bd=4, relief="groove", command=self.submit_product,
        )
        submit_btn.pack(anchor="center", pady=5)

    def check_product_code(self, event=None):
        entry = self.entries["Product Code"]
        current_code = entry.get().upper()
        to_uppercase(entry)
        if not current_code:
            entry.config(bg="white")
            self.warning_label.config(text="")
            return
        if search_product_codes(self.conn, current_code):
            entry.config(bg="#ffcdd2")
            self.warning_label.grid(row=2, column=0, padx=5)
        else:
            entry.config(bg="white")
            self.warning_label.grid_remove()

    def on_enter_code(self, event):
        code = self.entries["Product Code"].get().upper()
        if search_product_codes(self.conn, code):
            self.entries["Product Code"].focus_set()
            messagebox.showwarning(
                "Duplicate", "Product Code Already Exists. Choose Another.",
                parent=self.popup
            )
            self.entries["Product Code"].config(bg="#ffcdd2")
            self.warning_label.grid(row=1, column=0, columnspan=2, padx=5)
        else:
            self.warning_label.grid_remove()
            self.entries["Product Code"].config(bg="white")
            self.entries["Product Name"].focus_set()

    def submit_product(self):
        code = self.entries["Product Code"].get().upper()
        if search_product_codes(self.conn, code):
            messagebox.showwarning(
                "Duplicate", "Product Code Already Taken.",
                parent=self.popup
            )
            return
        priv = "Admin New Product"
        verify = VerifyPrivilegePopup(self.popup, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied", f"You Don't Have Permission to {priv}.",
                parent=self.popup
            )
            return
        code = self.entries["Product Code"].get().upper()
        name = self.entries["Product Name"].get()
        desc = self.entries["Description"].get("1.0", tk.END).strip()
        quantity = int(self.entries["Quantity"].get())
        cost = float(self.field_vars["Cost"].get().replace(",", ""))
        wholesale = float(
            self.field_vars["Wholesale Price"].get().replace(",", "")
        )
        retail = float(
            self.field_vars["Retail Price"].get().replace(",", "")
        )
        min_stock = int(self.entries["Min Stock Level"].get())

        data = {
            "product_code": code,
            "product_name": name,
            "description": desc,
            "quantity": quantity,
            "cost": cost,
            "wholesale_price": wholesale,
            "retail_price": retail,
            "min_stock_level": min_stock,
        }
        try:
            success, msg = insert_new_product(self.conn, data, self.user)
            if success:
                messagebox.showinfo("Success", msg, parent=self.popup)
                self.popup.destroy()
            else:
                messagebox.showerror("Error", msg, parent=self.popup)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Invalid Input: {str(e)}.", parent=self.popup
            )

    def focus_next(self, idx):
        """Focus next entry."""
        if idx < len(self.entry_order) - 1:
            next_entry = self.entry_order[idx + 1]
            next_entry.focus_set()
        return "break"





class ProductUpdateWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Product Details")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 350, 600, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        # Variables
        self.search_var = tk.StringVar()
        self.product_id = None
        # Frames
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.details_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.entry = tk.Entry(
            self.top_frame, textvariable=self.search_var, width=20,
            font=("Arial", 11)
        )
        self.suggestion_box = tk.Listbox(
            self.top_frame, bg="light grey", width=20, bd=4, relief="ridge",
            font=("Arial", 11)
        )
        self.search_btn = tk.Button(
            self.top_frame, text="Search", command=self.search, bg="blue",
            fg="white", bd=4, relief="groove", font=("Arial", 10, "bold")
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
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.top_frame.pack(fill="x", padx=10)
        tk.Label(
            self.top_frame, text="Enter Item's Name/Code:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), anchor="center", padx=10)
        self.entry.pack(pady=(0, 5), padx=10)
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self.on_keypress)
        # Suggestion listbox (initially hidden)
        self.suggestion_box.pack_forget()
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_select)
        self.search_btn.pack(pady=(5, 0))
        # Details Frame
        self.details_frame.pack(pady=(5, 0), fill="both")
        self.title.pack(anchor="center", padx=5)
        # Product Name and Description (increased width)
        tk.Label(
            self.details_frame, text="Product Name:", bg="lightblue",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(5, 0), padx=5)
        name_entry = tk.Entry(
            self.details_frame, textvariable=self.fields["Product Name:"], width=30,
            bd=2, relief="raised", font=("Arial", 11)
        )
        name_entry.bind("<KeyRelease>", capitalize_customer_name)
        name_entry.pack(pady=(0, 5), padx=5)
        self.entries["Product Name:"] = name_entry
        self.entry_order.append(name_entry)
        tk.Label(
            self.details_frame, text="Description:", bg="lightblue",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(5, 0), padx=5)
        desc_entry = tk.Text(
            self.details_frame, width=40, height=4, wrap="word", bd=2,
            relief="raised", font=("Arial", 11)
        )
        desc_entry.pack(pady=(0, 5), padx=5)
        SentenceCapitalizer.bind(desc_entry)
        self.entries["Description:"] = desc_entry
        self.entry_order.append(desc_entry)
        # 2 Columns Layout
        col1 = tk.Frame(self.details_frame, bg="lightblue")
        col2 = tk.Frame(self.details_frame, bg="lightblue")
        col1.pack(side="left", padx=(10, 5))
        col2.pack(side="left", padx=(5, 10))
        keys = ["Product Code:", "Quantity:", "Cost:", "Retail Price:",
                "Wholesale Price:", "Min Stock Level:"]
        currency_fields = {"Cost:", "Wholesale Price:", "Retail Price:"}
        mid = len(keys) // 2
        for key in keys[:mid]:
            tk.Label(
                col1, text=key, bg="lightblue", font=("Arial", 10, "bold")
            ).pack(anchor="w", pady=(5, 0))
            entry = tk.Entry(
                col1, textvariable=self.fields[key], width=15, bd=2,
                font=("Arial", 11), relief="raised"
            )
            entry.pack(anchor="w", pady=(0, 5), padx=5)
            self.entries[key] = entry
            self.entry_order.append(entry)
            if key in currency_fields:
                CurrencyFormatter.add_currency_trace(self.fields[key], entry)
        for key in keys[mid:]:
            tk.Label(
                col2, text=key, bg="lightblue", font=("Arial", 10, "bold")
            ).pack(anchor="w", pady=(5, 0))
            entry = tk.Entry(
                col2, textvariable=self.fields[key], width=15, bd=2,
                relief="raised", font=("Arial", 11)
            )
            entry.pack(anchor="w", pady=(0, 5), padx=5)
            self.entries[key] = entry
            self.entry_order.append(entry)
            if key in currency_fields:
                CurrencyFormatter.add_currency_trace(self.fields[key], entry)
        code_entry = self.entries["Product Code:"]
        code_entry.bind("<KeyRelease>", lambda e: to_uppercase(code_entry))
        for i, entry in enumerate(self.entry_order):
            entry.bind("<Return>", lambda e, idx=i: self.focus_next(idx))
        self.entries["Min Stock Level:"].bind(
            "<Return>", lambda e: self.post_updates()
        )
        tk.Button(
            self.main_frame, text="Update Product", bg="dodgerblue",
            fg="white", command=self.post_updates, bd=4, relief="raised",
            font=("Arial", 10, "bold")
        ).pack(side="bottom", pady=5, anchor="center")

    def focus_next(self, idx):
        """Focus next entry and highlight text."""
        if idx < len(self.entry_order) - 1:
            next_entry = self.entry_order[idx + 1]
            next_entry.focus_set()
            if isinstance(next_entry, tk.Entry):
                next_entry.selection_range(0, tk.END)
                next_entry.icursor(tk.END)
            # if it's a text widget -> select entire text differently
            elif isinstance(next_entry, tk.Text):
                next_entry.tag_add("sel", "1.0", tk.END)
                next_entry.mark_set("insert", tk.END)
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
            height = min(len(results), 4)
            self.suggestion_box.config(height=height)
            self.suggestion_box.pack(padx=5)
            for row in results:
                code = row['product_code']
                name = row['product_name']
                self.suggestion_box.insert(
                    tk.END, f"{code} - {name}"
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
        self.set_fields_state("normal")
        self.product_id = row["product_id"]
        name = row["product_name"]
        desc = self.entries["Description:"]
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
        desc.delete("1.0", tk.END)
        desc.insert("1.0", row["description"] or "")
        for form_key, db_key in mapping.items():
            if form_key in self.fields and db_key in row:
                self.fields[form_key].set(row[db_key])

        self.title.configure(text=f"Details For Product: {name}.")
        # Focus first entry and highlight text
        first_entry = self.entries["Product Name:"]
        first_entry.focus_set()
        first_entry.selection_range(0, tk.END)
        first_entry.icursor(tk.END)

    def post_updates(self):
        """Collect all product details and pass to update function.
        Post all fields both Updated and un updated."""
        priv = "Admin Product Details"
        dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.window
            )
            return
        desc = self.entries["Description:"].get("1.0", tk.END).strip()
        try:
            product = {
                "product_id": self.product_id,
                "product_code": self.fields["Product Code:"].get().strip(),
                "product_name": self.fields["Product Name:"].get().strip(),
                "description": desc,
                "quantity": int(self.fields["Quantity:"].get().strip() or 0),
                "cost": float(
                    self.fields["Cost:"].get().replace(",", "") or 0.0
                ),
                "retail_price": float(
                    self.fields["Retail Price:"].get().replace(",", "") or 0.0
                ),
                "wholesale_price": float(
                    self.fields["Wholesale Price:"].get().replace(",", "") or 0.0
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
        success, msg = update_product_details(self.conn, product, self.user)
        if success:
            messagebox.showinfo("Success", msg, parent=self.window)
            self.search_var.set("")
            self.title.configure(text="")
            self.product_id = None
            self.entries["Description:"].delete("1.0", tk.END)
            self.set_fields_state("disabled")
            for var in self.fields.values():
                var.set("")
            self.entry.focus_set()
        else:
            messagebox.showerror("Error", msg, parent=self.window)

    def set_fields_state(self, state="disabled"):
        """Enable / disable all detail entry widgets."""
        for entry in self.entries.values():
            entry.config(state=state)


class AddStockPopup(BaseWindow):
    def __init__(self, master, conn, user, refresh_callback=None):
        self.window = tk.Toplevel(master)
        self.window.title("Restocking Products")
        self.center_window(self.window, 270, 300, master)
        self.window.configure(bg="skyblue")
        self.window.transient(master)
        self.window.grab_set()

        self.user = user
        self.conn = conn
        if refresh_callback:
            self.refresh_callback = refresh_callback
        else:
            self.refresh_callback = None
        self.cost_var = tk.StringVar()
        self.wholesale_var = tk.StringVar()
        self.retail_var = tk.StringVar()
        self.labels = [
            "Product Code", "Quantity", "Cost", "Wholesale Price",
            "Retail Price"
        ]
        self.entries = {}
        self.entry_order = []
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
            self.main_frame, text="Restocking Product", fg="dodgerblue",
            bg="skyblue", font=("Arial", 14, "bold", "underline")
        ).pack(anchor="center", pady=5)
        tk.Label(
            self.main_frame, bg="skyblue", text="Product Code:",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0))
        self.code_entry.pack(pady=(0, 2))
        self.code_entry.focus_set()
        self.entries["Product Code"] = self.code_entry
        self.code_entry.bind("<KeyRelease>", self.check_product_code)
        self.entry_order.append(self.code_entry)
        self.label.pack(pady=(0, 2))
        entry_frame = tk.Frame(self.main_frame, bg="skyblue")
        entry_frame.pack(expand=True)
        vcmd = (self.window.register(only_digits), '%S')
        col1_labels = self.labels[1:3]
        col2_labels = self.labels[3:]

        # left column
        for i, label in enumerate(col1_labels):
            tk.Label(
                entry_frame, bg="skyblue", text=f"{label}:",
                font=("Arial", 11, "bold")
            ).grid(row=i*2, column=0, sticky="w", pady=(5, 0), padx=5)
            entry = tk.Entry(
                entry_frame, bd=2, relief="raised", width=10,
                font=("Arial", 11)
            )
            entry.config(validate="key", validatecommand=vcmd)
            entry.grid(row=i*2+1, column=0, padx=10, pady=(0, 5), sticky="w")
            self.entries[label] = entry
            self.entry_order.append(entry)
        # Right Column
        for i, label in enumerate(col2_labels):
            tk.Label(
                entry_frame, bg="skyblue", text=f"{label}:",
                font=("Arial", 11, "bold")
            ).grid(row=i*2, column=1, sticky="w", pady=(5, 0), padx=5)
            entry = tk.Entry(
                entry_frame, bd=2, relief="raised", width=10,
                font=("Arial", 11)
            )
            entry.config(validate="key", validatecommand=vcmd)
            entry.grid(row=i*2+1, column=1, padx=10, pady=(0, 5), sticky="w")
            self.entries[label] = entry
            self.entry_order.append(entry)
        self.entries["Cost"].config(textvariable=self.cost_var)
        self.entries["Wholesale Price"].config(textvariable=self.wholesale_var)
        self.entries["Retail Price"].config(textvariable=self.retail_var)
        CurrencyFormatter.add_currency_trace(
            self.cost_var, self.entries["Cost"]
        )
        CurrencyFormatter.add_currency_trace(
            self.wholesale_var, self.entries["Wholesale Price"]
        )
        CurrencyFormatter.add_currency_trace(
            self.retail_var, self.entries["Retail Price"]
        )
        for i, entry in enumerate(self.entry_order):
            entry.bind("<Return>", lambda e, idx=i: self.focus_next(idx))
        self.entries["Retail Price"].bind("<Return>", lambda e: self.submit())
        # Button centered across both columns
        post_btn = tk.Button(
            entry_frame, text="Post Restock", bg="dodgerblue", fg="white",
            bd=4, relief="groove", command=self.submit
        )
        post_btn.grid(row=6, column=0, columnspan=2, pady=(10, 5))
        post_btn.bind("<Return>", lambda e: self.submit())
        # Expand nicely
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        auto_manage_focus(self.window)

    def check_product_code(self, event):
        code = self.code_entry.get().strip().upper()
        self.code_entry.delete(0, tk.END)
        self.code_entry.insert(0, code)
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
        if len(code) < 3:
            return
        if not found:
            # Show Error feedback
            self.code_entry.configure(bg="#ffcccc") # Light red
            self.label.configure(text="Product Code Not Found.", fg="red")

    def focus_next(self, idx):
        """Focus next entry and highlight text."""
        if idx < len(self.entry_order) - 1:
            next_entry = self.entry_order[idx + 1]
            next_entry.focus_set()
            if isinstance(next_entry, tk.Entry):
                next_entry.selection_range(0, tk.END)
                next_entry.icursor(tk.END)
            # if it's a text widget -> select entire text differently
            elif isinstance(next_entry, tk.Text):
                next_entry.tag_add("sel", "1.0", tk.END)
                next_entry.mark_set("insert", tk.END)
        return "break"

    def submit(self):
        # Verify Privilege
        priv = "Add Stock"
        verify = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv
        )
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
            cost = safe_float(self.cost_var.get().replace(",", ""))
            wholesale = safe_float(self.wholesale_var.get().replace(",", ""))
            retail = safe_float(self.retail_var.get().replace(",", ""))
            data = {
                "product_code": code,
                "quantity": added_quantity,
                "cost": cost,
                "wholesale_price": wholesale,
                "retail_price": retail,
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

class UpdateStockLevelPopup(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Update Minimum Quantity")
        self.center_window(self.window, 350, 350, parent)
        self.window.configure(bg="lightblue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user

        self.search_var = tk.StringVar()
        self.new_qty_var = tk.StringVar()
        self.product_code = None
        self.validate_cmd = self.window.register(only_digits)
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.entry_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.entry = tk.Entry(
            self.entry_frame, textvariable=self.search_var, width=15, bd=4,
            relief="raised", font=("Arial", 11)
        )
        self.suggestion_box = tk.Listbox(
            self.entry_frame, bg="light grey", width=20, font=("Arial", 10),
            bd=4, relief="ridge"
        )
        self.search_btn = tk.Button(
            self.entry_frame, text="Search", command=self.search, bg="blue",
            fg="white", bd=4, relief="groove", font=("Arial", 10, "bold")
        )
        self.details_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.title = tk.Label(
            self.details_frame, text="", bg="lightblue", fg="blue",
            font=("Arial", 11, "italic", "underline"), wraplength=330
        )
        self.qty_entry = tk.Entry(
            self.details_frame, textvariable=self.new_qty_var, width=10,
            bd=4, relief="raised", font=("Arial", 11)
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        text_l = "Update Items' Min Stock Level."
        tk.Label(
            self.main_frame, text=text_l, bg="lightblue", fg="blue",
            font=("Arial", 14, "italic", "underline")
        ).pack(pady=(5, 0))
        self.entry_frame.pack()
        tk.Label(
            self.entry_frame, text="Name/Code to Search:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), padx=10)
        self.entry.pack(pady=(0, 5), padx=10)
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self.on_keypress)
        self.entry.bind("<Return>", lambda e: self.search())
        # Suggestion listbox (initially hidden)
        self.suggestion_box.pack_forget()
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_select)
        self.search_btn.pack(pady=(5, 0))
        # Details Frame
        self.details_frame.pack(expand=True, fill="both")
        self.title.pack(anchor="center", padx=5)
        tk.Label(
            self.details_frame, text="New Minimum Quantity:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), padx=5)
        self.qty_entry.pack(pady=(0, 5), padx=5)
        self.qty_entry.config(
            validate="key", validatecommand=(self.validate_cmd, "%S")
        )
        self.qty_entry.bind("<Return>", lambda e: self.update_quantity())
        post_btn = tk.Button(
            self.details_frame, text="Update Quantity", bg="dodgerblue",
            fg="white", bd=2, relief="groove", font=("Arial", 10, "bold"),
            command=self.update_quantity
        )
        post_btn.pack(pady=5)
        self.details_frame.pack_forget()

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
            height = min(len(results), 4)
            self.suggestion_box.config(height=height)
            self.suggestion_box.pack(padx=5)
            for row in results:
                code = row['product_code']
                name = row['product_name']
                self.suggestion_box.insert(
                    tk.END, f"{code} - {name}"
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
        name = row["product_name"]
        self.product_code = row["product_code"]
        p_code = self.product_code
        min_qty = row["min_stock_level"]
        text = f"Min Stock Level For {name} ({p_code}) Is {min_qty}."
        self.title.configure(text=text)
        self.details_frame.pack(expand=True, fill="both")
        self.qty_entry.focus_set()

    def update_quantity(self):
        new_qty = self.new_qty_var.get().strip()
        if not new_qty.isdigit():
            messagebox.showerror(
                "Invalid Input",
                "Please enter a valid number.", parent=self.window
            )
            return
        product_code = self.search_var.get()
        qty = int(new_qty)
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
        try:
            success, msg = update_min_stock_level(
                self.conn, product_code, qty, self.user
            )
            if success:
                messagebox.showinfo(
                    "Success",
                    "Quantity Updated Successfully.", parent=self.window
                )
                self.window.destroy()
            else:
                messagebox.showerror(
                    "Error Updating", msg, parent=self.window
                )
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self.window)

class DeleteProductPopup(BaseWindow):
    def __init__(self, master, conn, user, refresh=None, item_code=None):
        self.window = tk.Toplevel(master)
        self.window.title("Delete Product")
        self.center_window(self.window, 300, 220, master)
        self.window.configure(bg="skyblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.product_code_var = tk.StringVar()
        self.refresh = refresh if refresh else None
        self.products = None
        self.product_name = None
        self.main_frame = tk.Frame(
            self.window, bg="skyblue", bd=4, relief="solid"
        )
        self.entry_frame = tk.Frame(self.main_frame, bg="skyblue")
        self.entry = tk.Entry(
            self.entry_frame, textvariable=self.product_code_var, width=20,
            bd=4, relief="raised", font=("Arial", 11)
        )
        self.listbox = tk.Listbox(
            self.entry_frame, bg="lightgray", width=20, bd=2, relief="ridge",
            font=("Arial", 11)
        )
        # Delete button (initially hidden)
        self.delete_btn = tk.Button(
            self.entry_frame, text="Delete Product", bd=4, relief="groove",
            bg="dodgerblue", fg="white", command=self.delete_selected,
            font=("Arial", 10, "bold")
        )

        self.setup_widgets()
        if item_code:
            self.product_code_var.set(item_code.upper())
            self.search_product()
            self.entry.icursor(tk.END)

    def setup_widgets(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Label and Entry
        l_text = "Deleting Product From Stock."
        tk.Label(
            self.main_frame, text=l_text, bg="skyblue", fg="red",
            font=("Arial", 14, "italic", "underline")
        ).pack(pady=(5, 0), anchor="center")
        self.entry_frame.pack(fill="both", expand=True)
        tk.Label(
            self.entry_frame, text="Product Code:", bg="skyblue",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), padx=5)
        self.entry.pack(padx=5)
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self.uppercase_and_search)
        self.entry.bind("<Return>", lambda e: self.delete_selected())
        # Listbox
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.pack(padx=5, pady=(0, 5))
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
                    code = product['product_code']
                    name = product['product_name']
                    display = f"{code} - {name}"
                    self.products = results
                    self.listbox.insert(tk.END, display)
                self.listbox.config(height=min(len(results), 4))
                self.listbox.pack(padx=5, pady=(0, 5))
            else:
                self.listbox.pack_forget()
        except Exception as err:
            messagebox.showerror(
                "Database Error", str(err), parent=self.window
            )

    def on_select(self, event):
        if self.listbox.curselection():
            index = self.listbox.curselection()[0]
            product = self.products[index]
            product_code = product["product_code"]
            self.product_code_var.set(product_code)
            self.product_name = product["product_name"]
            self.listbox.pack_forget()
            self.entry.icursor(tk.END)
            self.delete_btn.pack(pady=5)

    def delete_selected(self):
        code = self.product_code_var.get().strip()
        if not code:
            messagebox.showerror(
                "No Product",
                "Please Enter a Valid Product Code.", parent=self.window
            )
            return
        # Verify Privilege
        priv = "Admin Delete Product"
        verify = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv
        )
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.window
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete '{self.product_name}'; {code}?", default="no",
            parent=self.window
        )
        if confirm:
            try:
                success, msg = delete_product(self.conn, code, self.user)
                if success:
                    messagebox.showinfo("Deleted", msg, parent= self.window)
                    self.product_code_var.set("")
                    if self.refresh:
                        self.refresh()
                    self.window.destroy()
                else:
                    messagebox.showerror("Error", msg, parent=self.window)
                    self.entry.focus_set()
            except Exception as err:
                messagebox.showerror("Database Error", str(err))

class RestoreProductPopup(BaseWindow):
    def __init__(self, master, conn, user, callback=None, item_code=None):
        self.window = tk.Toplevel(master)
        self.window.title("Restore Product")
        self.center_window(self.window, 300, 200, master)
        self.window.configure(bg="skyblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.product_code_var = tk.StringVar()
        self.refresh = callback if callback else None
        self.products = None
        self.product_name = None
        self.main_frame = tk.Frame(
            self.window, bg="skyblue", bd=4, relief="solid"
        )
        self.entry_frame = tk.Frame(self.main_frame, bg="skyblue")
        self.entry = tk.Entry(
            self.entry_frame, textvariable=self.product_code_var, width=20,
            bd=4, relief="raised", font=("Arial", 11)
        )
        self.listbox = tk.Listbox(
            self.entry_frame, bg="lightgray", width=20, bd=2, relief="raised",
            font=("Arial", 11)
        )
        # Delete button (initially hidden)
        self.delete_btn = tk.Button(
            self.entry_frame, text="Restore Product", bd=4, relief="raised",
            bg="dodgerblue", fg="white", command=self.restore_selected,
            font=("Arial", 10, "bold")
        )

        self.setup_widgets()
        if item_code:
            self.product_code_var.set(item_code.upper())
            self.search_product()
            self.entry.icursor(tk.END)

    def setup_widgets(self):
        """Widgets set up."""
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Label and Entry
        l_text = "Restore Deleted Product."
        tk.Label(
            self.main_frame, text=l_text, bg="skyblue", fg="red", bd=2,
            relief="groove", font=("Arial", 14, "italic", "underline")
        ).pack(pady=(5, 0), anchor="center")
        self.entry_frame.pack(fill="both", expand=True)
        tk.Label(
            self.entry_frame, text="Product Code:", bg="skyblue",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), padx=5)
        self.entry.pack(padx=5)
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self.uppercase_and_search)
        self.entry.bind("<Return>", lambda e: self.restore_selected())
        # Listbox
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.pack(padx=5, pady=(0, 5))
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
            results = search_deleted_product_codes(self.conn, product_code)
            if results:
                for product in results:
                    code = product['product_code']
                    name = product['product_name']
                    display = f"{code} - {name}"
                    self.products = results
                    self.listbox.insert(tk.END, display)
                self.listbox.config(height=min(len(results), 4))
                self.listbox.pack(padx=5, pady=(0, 5))
            else:
                self.listbox.pack_forget()
        except Exception as err:
            messagebox.showerror(
                "Database Error", str(err), parent=self.window
            )

    def on_select(self, event):
        if self.listbox.curselection():
            index = self.listbox.curselection()[0]
            product = self.products[index]
            product_code = product["product_code"]
            self.product_name = product["product_name"]
            self.product_code_var.set(product_code)
            self.listbox.pack_forget()
            self.entry.icursor(tk.END)
            self.delete_btn.pack(pady=5)

    def restore_selected(self):
        # Verify Privilege
        priv = "Admin Restore Product"
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
            "Confirm Restore",
            f"Restore '{code}'; {self.product_name}?", default="no",
            parent=self.window
        )
        if confirm:
            try:
                connect = self.conn
                user = self.user
                success, msg = restore_deleted_product(connect, code, user)
                if success:
                    messagebox.showinfo("Restored", msg, parent= self.window)
                    self.product_code_var.set("")
                    if self.refresh is not None:
                        self.refresh()
                    self.window.destroy()
                else:
                    messagebox.showerror("Error", msg, parent=self.window)
                    self.entry.focus_set()
            except Exception as err:
                messagebox.showerror(
                    "Database Error", str(err), parent=self.window
                )
