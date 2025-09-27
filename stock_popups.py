import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
from base_window import BaseWindow
from table_actions import UpdateQuantityPopup, UpdatePriceWindow, UpdateDescriptionPopup
from working_on_orders import search_product_codes
from authentication import VerifyPrivilegePopup
from working_on_stock import fetch_product_data, insert_new_product, update_quantity
from window_functionality import auto_manage_focus, to_uppercase, only_digits


class UpdateQuantityWindow(BaseWindow):
    def __init__(self, master, conn, user, product_code=None):
        self.popup = tk.Toplevel(master)
        self.popup.title("Update Quantity")
        self.center_window(self.popup, 200, 150, master)
        self.popup.configure(bg="lightgreen")
        self.popup.grab_set()
        self.popup.transient(master)
        # Label and Entry widgets
        self.conn = conn
        self.user = user
        self.code_entry = tk.Entry(self.popup, width=20)
        if product_code:  # Pre-fill code if provided
            self.code_entry.insert(0, product_code)
        validate_cmd = self.popup.register(only_digits)
        self.quantity_entry = tk.Entry(
            self.popup, width=20, validate="key", validatecommand=(validate_cmd, "%S")
        )

        self.build_ui()

    def build_ui(self):
        tk.Label(
            self.popup, text="Product Code:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0))
        self.code_entry.pack()
        self.code_entry.bind("<KeyRelease>", lambda e: to_uppercase(self.code_entry))
        tk.Label(
            self.popup, text="New Quantity:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0))
        self.quantity_entry.pack()
        # Update Button
        tk.Button(
            self.popup, text="Update", bg="lightblue", command=self.perform_update
        ).pack(pady=10)
        auto_manage_focus(self.popup)
        self.code_entry.focus_set()

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


class NewProductPopup(BaseWindow):
    def __init__(self, parent, conn, user, refresh_callback=None):
        self.popup = tk.Toplevel(parent)
        self.popup.title("New Product")
        self.popup.configure(bg="lightgreen")
        self.center_window(self.popup, 250, 300, parent)
        self.popup.grab_set()
        self.popup.transient(parent)

        if refresh_callback is not None:
            self.refresh = refresh_callback
        self.conn = conn
        self.user = user
        self.entries = {}
        self.labels = [
            "Product Code", "Product Name", "Description", "Quantity",
            "Cost", "Wholesale Price", "Retail Price", "Min Stock Level",
        ]
        self.digit_fields = {
            "Quantity", "Cost", "Wholesale Price", "Retail Price",
            "Min Stock Level",
        }
        self.validate_cmd = self.popup.register(only_digits)
        self.warning_label = tk.Label(
            self.popup, text="Product Code is not Available", bg="lightgreen",
            fg="red", font=("Arial", 9, "italic"), anchor="center",
        )
        self.build_form()
        auto_manage_focus(self.popup)

    def build_form(self):
        code_entry = tk.Entry(self.popup, width=20)
        code_entry.grid(row=0, column=1, padx=5, pady=(0, 2))
        code_entry.bind("<KeyRelease>", self.check_product_code)
        code_entry.bind("<Return>", self.on_enter_code)
        tk.Label(self.popup, text="Product Code:", bg="lightgreen").grid(
            row=0, column=0, padx=5, pady=2, sticky="e"
        )
        self.entries["Product Code"] = code_entry
        self.warning_label.grid(row=1, column=0, columnspan=2, padx=5)
        self.warning_label.grid_remove()
        # Other entries
        for i, label_text in enumerate(self.labels[1:], start=1):
            tk.Label(
                self.popup, text=f"{label_text}:", bg="lightgreen",
                font=("Arial", 11, "bold")
            ).grid(row=i + 1, column=0, padx=5, pady=2, sticky="e")
            if label_text in self.digit_fields:
                entry = tk.Entry(
                    self.popup, width=20, validate="key",
                    validatecommand=(self.validate_cmd, "%S"),
                )
            else:
                entry = tk.Entry(self.popup, width=20)
            entry.grid(row=i + 1, column=1, padx=5, pady=2)
            self.entries[label_text] = entry
        # Submit Button
        submit_btn = tk.Button(
            self.popup, text="Post Item", bg="lightblue", width=15,
            command=self.submit_product,
        )
        submit_btn.grid(row=len(self.labels) + 1, column=0, columnspan=2, pady=10)

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
            self.warning_label.grid(row=1, column=0, columnspan=2, padx=5)
        else:
            entry.config(bg="white")
            self.warning_label.grid_remove()

    def on_enter_code(self, event):
        code = self.entries["Product Code"].get().upper()
        if search_product_codes(self.conn, code):
            self.entries["Product Code"].focus_set()
            messagebox.showwarning(
                "Duplicate", "Product Code Already Exists. Choose Another."
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
            messagebox.showwarning("Duplicate", "Product Code Already Taken.")
            return
        priv = "Add New Product"
        verify_dialog = VerifyPrivilegePopup(self.popup, self.conn, self.user,
                                             priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied",
                                   f"You do not have permission to {priv}.")
            return
        code = self.entries["Product Code"].get().upper()
        name = self.entries["Product Name"].get()
        desc = self.entries["Description"].get().capitalize()
        quantity = int(self.entries["Quantity"].get())
        cost = float(self.entries["Cost"].get())
        wholesale = float(self.entries["Wholesale Price"].get())
        retail = float(self.entries["Retail Price"].get())
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
            result = insert_new_product(self.conn, data, self.user)
            if result.startswith("New Product"):
                messagebox.showinfo("Success", result)
                if self.refresh:
                    self.refresh()
                self.popup.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid Input: {e}")


class ReconciliationWindow(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Product Reconciliation")
        self.center_window(self.window, 1100, 600)
        self.window.configure(bg="lightblue")
        self.window.grab_set()
        self.window.transient(master)

        self.conn = conn
        self.user = user
        self.search_by_var = tk.StringVar()
        # Search Frame
        self.search_frame = tk.Frame(self.window, bg="lightblue")
        self.search_label = tk.Label(
            self.search_frame,
            text="Enter Product Name:",
            bg="lightblue",
            font=("Arial", 11, "bold"),
        )
        self.search_var = tk.StringVar()
        self.data = None
        self.columns = [
            "No",
            "Product Code",
            "Product Name",
            "Description",
            "Quantity",
            "Retail Price",
            "Wholesale Price",
        ]
        self.table_frame = tk.Frame(self.window, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings", height=20
        )

        self.setup_widgets()
        self.populate_table()

    def setup_widgets(self):
        tk.Label(
            self.window,
            text="Available Products",
            bg="lightblue",
            font=("Arial", 15, "bold", "underline"),
        ).pack(
            pady=(5, 0), padx=5
        )  # Title
        self.search_frame.pack(side="top", fill="x", padx=5)

        tk.Label(
            self.search_frame,
            text="Search by:",
            bg="lightblue",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=(5, 0))
        search_options = ttk.Combobox(
            self.search_frame,
            textvariable=self.search_by_var,
            values=["Name", "Code"],
            state="readonly",
            width=6,
        )
        search_options.current(0)
        search_options.pack(side="left", padx=(0, 5))
        search_options.bind("<<ComboboxSelected>>", self.update_search_label)
        self.search_label.pack(side="left", padx=(5, 0))
        search_entry = tk.Entry(
            self.search_frame, textvariable=self.search_var, width=20
        )
        search_entry.pack(side="left", padx=(0, 5))
        search_entry.bind("<KeyRelease>", self.filter_table)
        tk.Label(
            self.search_frame,
            text="Select Product to Edit",
            fg="blue",
            font=("Arial", 13, "italic"),
            bg="lightblue",
        ).pack(
            side="left", padx=5
        )  # italic Note
        btn_frame = tk.Frame(self.search_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=5)
        action_btn = {
            "Update Quantity": self.update_quantity,
            "Update Price": self.update_price,
            "Update Description": self.update_description,
            "Refresh": self.refresh,
        }
        for text, action in action_btn.items():
            tk.Button(
                btn_frame,
                text=text,
                bd=4,
                bg="white",
                relief="solid",
                fg="black",
                width=len(text),
                command=action,
            ).pack(side="right")
        # Table Frame
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Style
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), anchor="center")
        style.configure("Treeview", rowheight=30, font=("Arial", 10))
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        # Columns config

        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.bind(
            "<MouseWheel>",
            lambda e: self.tree.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

    def update_search_label(self, event=None):
        selected = self.search_by_var.get()
        if selected == "Name":
            label = "Enter Product Name:"
        else:
            label = "Enter Product Code:"
        self.search_label.config(text=label)

    def populate_table(self):
        self.data = fetch_product_data(self.conn)
        self.tree.delete(*self.tree.get_children())
        alt_colors = ("#ffffff", "#e6f2ff")  # White and light blueish
        self.tree.tag_configure("evenrow", background=alt_colors[0])
        self.tree.tag_configure("oddrow", background=alt_colors[1])
        for index, row in enumerate(self.data, start=1):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                values=(
                    index,
                    row["product_code"],
                    row["product_name"],
                    row["description"],
                    row["quantity"],
                    row["retail_price"],
                    row["wholesale_price"],
                ),
                tags=(tag,),
            )
        self.auto_resize()

    def auto_resize(self):
        """Resize columns to fit content."""
        font = tkFont.Font()
        for col in self.columns:
            # Start with the column header width
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            # Add Padding for readability
            self.tree.column(col, width=max_width + 3)

    def filter_table(self, event=None):
        keyword = self.search_var.get().lower()
        search_field = self.search_by_var.get()
        search_field = (
            "product_name" if search_field == "Product Name" else "product_code"
        )
        self.tree.delete(*self.tree.get_children())
        alt_colors = ("#ffffff", "#e6f2ff")  # White and light blueish
        filtered = [r for r in self.data if keyword in str(r[search_field]).lower()]
        for i, row in enumerate(filtered, start=1):
            self.tree.insert("", "end", values=(
                i,
                row["product_code"],
                row["product_name"],
                row["description"],
                row["quantity"],
                row["retail_price"],
                row["wholesale_price"],
            ), tags=(alt_colors[i % 2],))

    def get_selected_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "No Selection", "Please select a product from the table."
            )
            return None
        return self.tree.item(selected[0])["values"]

    def update_quantity(self):
        item = self.get_selected_item()
        if item:
            UpdateQuantityPopup(self.window, self.conn, self.user, item, self.refresh)
        else:
            messagebox.showerror(
                "No Selection", "Please Select Item to Update Quantity."
            )

    def update_price(self):
        item = self.get_selected_item()
        if item:
            UpdatePriceWindow(self.window, self.conn, item, self.refresh, self.user)
        else:
            messagebox.showerror("No Selection", "Please Select Item to Update Price.")

    def update_description(self):
        item = self.get_selected_item()
        if item:
            UpdateDescriptionPopup(self.window, self.conn, item, self.refresh)
        else:
            messagebox.showerror(
                "No Selection", "Please select Item to update Description."
            )

    def refresh(self):
        self.populate_table()


if __name__ == "__main__":
    from connect_to_db import connect_db

    conn = connect_db()
    root = tk.Tk()
    # root.withdraw()
    app = UpdateQuantityWindow(root, conn, "sniffy", None)
    root.mainloop()
