import re
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
from base_window import BaseWindow
from working_on_orders import search_product_codes
from accounting_export import ReportExporter
from stock_popups1 import DeleteProductPopup, RestoreProductPopup
from authentication import VerifyPrivilegePopup, DescriptionFormatter
from window_functionality import auto_manage_focus, to_uppercase, only_digits
from stock_table_action_gui import (
    UpdateQuantityPopup, UpdatePriceWindow, UpdateDescriptionPopup
)
from working_on_stock import (
    fetch_all_products, insert_new_product, fetch_product_control_logs,
    fetch_distinct_years, fetch_deleted_products, search_product_codes,
    update_product_details, search_product_details,
)


class NewProductPopup(BaseWindow):
    def __init__(self, parent, conn, user, refresh_callback=None):
        self.popup = tk.Toplevel(parent)
        self.popup.title("New Product")
        self.popup.configure(bg="lightgreen")
        self.center_window(self.popup, 265, 300, parent)
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
        code_entry = tk.Entry(
            self.popup, font=("Arial", 11), width=15, bd=2, relief="raised"
        )
        code_entry.grid(row=0, column=1, pady=(0, 2))
        code_entry.bind("<KeyRelease>", self.check_product_code)
        code_entry.bind("<Return>", self.on_enter_code)
        tk.Label(
            self.popup, text="Product Code:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, pady=2, sticky="e")
        self.entries["Product Code"] = code_entry
        self.warning_label.grid(row=1, column=0, columnspan=2, padx=5)
        self.warning_label.grid_remove()
        # Other entries
        for i, label_text in enumerate(self.labels[1:], start=1):
            tk.Label(
                self.popup, text=f"{label_text}:", bg="lightgreen",
                font=("Arial", 11, "bold")
            ).grid(row=i + 1, column=0, pady=2, sticky="e")
            if label_text in self.digit_fields:
                entry = tk.Entry(
                    self.popup, width=15, validate="key", font=("Arial", 11),
                    validatecommand=(self.validate_cmd, "%S"),
                    bd=2, relief="raised"
                )
            else:
                entry = tk.Entry(self.popup, width=15, bd=2, relief="raised",
                                 font=("Arial", 11))
            entry.grid(row=i + 1, column=1, pady=2)
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
        self.center_window(self.window, 1200, 650, master)
        self.window.configure(bg="lightblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.search_by_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.data = fetch_all_products(self.conn)
        self.current_products = self.data
        self.product_code = None
        # Search Frame
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.search_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.search_label = tk.Label(
            self.search_frame, text="Enter Product Name:", bg="lightblue",
            font=("Arial", 12, "bold")
        )
        self.columns = [
            "No", "Product Code", "Product Name", "Description", "Quantity",
            "Retail Price", "Wholesale Price", "Restocked"
        ]
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings", height=20
        )

        self.setup_widgets()
        self.populate_table()

    def setup_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Title
        action_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="flat"
        )
        action_frame.pack(side="top", fill="x")
        self.search_frame.pack(side="top", fill="x")
        label_text = "Available Products To Reconcile"
        tk.Label(
            action_frame, text=label_text, bd=4, relief="groove",
            bg="lightblue", font=("Arial", 16, "bold", "underline")
        ).pack(side="left", padx=20)
        tk.Label(
            action_frame, text="Select Product to Edit", fg="blue",
            font=("Arial", 13, "italic", "underline"), bg="lightblue",
            bd=2, relief="flat"
        ).pack(side="left", padx=20)  # italic Note
        export_btns = {
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
            "Print": self.on_print,
        }
        for text, action in export_btns.items():
            tk.Button(
                action_frame, text=text, bd=2, relief="groove", fg="white",
                bg="dodgerblue", command=action, font=("Arial", 10, "bold")
            ).pack(side="right")
        tk.Label(
            self.search_frame, text="Search by:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0))
        search_options = ttk.Combobox(
            self.search_frame, width=6, textvariable=self.search_by_var,
            values=["Name", "Code"], state="readonly", font=("Arial", 11)
        )
        search_options.current(0)
        search_options.pack(side="left", padx=(0, 5))
        search_options.bind("<<ComboboxSelected>>", self.update_search_label)
        self.search_label.pack(side="left", padx=(5, 0))
        search_entry = tk.Entry(
            self.search_frame, textvariable=self.search_var, width=15, bd=2,
            relief="raised", font=("Arial", 11)
        )
        search_entry.pack(side="left", padx=(0, 5))
        search_entry.bind("<KeyRelease>", self.filter_table)

        btn_frame = tk.Frame(self.search_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=5)
        action_btn = {
            "Update Quantity": self.update_quantity,
            "Update Price": self.update_price,
            "Update Description": self.update_description,
            "Delete Product": self.delete_product,
            "Refresh": self.refresh,
        }
        for text, action in action_btn.items():
            tk.Button(
                btn_frame, text=text, bd=4, relief="groove", bg="lightgreen",
                command=action, font=("Arial", 10, "bold")
            ).pack(side="right")


        # Table Frame
        self.table_frame.pack(fill=tk.BOTH, expand=True)
        # Style
        style = ttk.Style()
        style.configure(
            "Treeview.Heading", font=("Arial", 12, "bold", "underline")
        )
        style.configure("Treeview", rowheight=20, font=("Arial", 10))
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

    def populate_table(self, products=None):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if products is None:
            self.current_products = self.data[:]
        else:
            self.current_products = products[:]
        alt_colors = ("#ffffff", "#e6f2ff")  # White and light blueish
        self.tree.tag_configure("evenrow", background=alt_colors[0])
        self.tree.tag_configure("oddrow", background=alt_colors[1])
        formatter = DescriptionFormatter()
        for index, row in enumerate(self.current_products, start=1):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            desc = formatter.format(row["description"])
            name = re.sub(r"\s+", " ", str(row["product_name"])).strip()
            self.tree.insert("", "end", values=(
                index,
                row["product_code"],
                name,
                desc,
                row["quantity"],
                f"{row["retail_price"]:,}",
                f"{row["wholesale_price"]:,}",
                row["date_replenished"]
            ), tags=(tag,))
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
            self.tree.column(col, width=max_width)

    def filter_table(self, event=None):
        keyword = self.search_var.get().lower()
        search_field = self.search_by_var.get()
        search_field = (
            "product_name" if search_field == "Name" else "product_code"
        )
        filtered = [r for r in self.data if keyword in str(r[search_field]).lower()]
        self.populate_table(filtered)

    def get_selected_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "No Selection", "Please select a product from the table."
            )
            return None
        self.product_code = self.tree.item(selected[0])["values"][1]
        return self.tree.item(selected[0])["values"]

    def refresh(self):
        data = fetch_all_products(self.conn)
        self.populate_table(data)

    def has_privilege(self, privilege: str) -> bool:
        """Check if the current user has the required privilege."""
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You do not have permission to {privilege}.",
                parent=self.window
            )
            return False
        return True

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append(
                {
                    "No": vals[0],
                    "Product Code": vals[1],
                    "Product Name": vals[2],
                    "Description": vals[3],
                    "Quantity": vals[4],
                    "Retail Price": vals[5],
                    "Wholesale Price": vals[6],
                    "Restocked": vals[7],
                }
            )
        return rows

    def _make_exporter(self):
        title = "Available Products To Reconcile."
        columns = [
            "No", "Product Code", "Product Name", "Description", "Quantity",
            "Retail Price", "Wholesale Price", "Restocked"
        ]
        rows = self._collect_rows()
        return ReportExporter(self.window, title, columns, rows)

    def on_export_excel(self):
        if not self.has_privilege("Export Products Records"):
            return
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_export_pdf(self):
        if not self.has_privilege("Export Products Records"):
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self.has_privilege("Export Products Records"):
            return
        exporter = self._make_exporter()
        exporter.print()

    def update_quantity(self):
        item = self.get_selected_item()
        if not item:
            messagebox.showerror(
                "No Selection",
                "Please Select Item to Update Quantity.", parent=self.window
            )
            return
        UpdateQuantityPopup(
            self.window, self.conn, self.user, item, self.refresh
        )

    def update_price(self):
        item = self.get_selected_item()
        if not item:
            messagebox.showerror(
                "No Selection",
                "Please Select Item to Update Price.", parent=self.window
            )
            return
        UpdatePriceWindow(
            self.window, self.conn, self.user, item, self.refresh
        )

    def update_description(self):
        item = self.get_selected_item()
        if not item:
            messagebox.showerror(
                "No Selection",
                "Please select Item to update Description.",
                parent=self.window
            )
            return
        UpdateDescriptionPopup(
            self.window, self.conn, item, self.refresh, self.user
        )

    def delete_product(self):
        if not self.has_privilege("Delete Product"):
            return
        if not self.product_code:
            messagebox.showinfo(
                "Advice",
                "Optionally, Select Product to Delete.", parent=self.window
            )
            DeleteProductPopup(
                self.window, self.conn, self.user, self.refresh
            )
        else:
            code = self.product_code
            DeleteProductPopup(
                self.window, self.conn, self.user, self.refresh, code
            )


class ProductLogsWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.top = tk.Toplevel(parent)
        self.top.title("Stock Products Logs")
        self.top.configure(bg="lightblue")
        self.center_window(self.top, 1200, 700, parent)
        self.top.transient(parent)
        self.top.grab_set()

        self.conn = conn
        self.user = user
        years, error = fetch_distinct_years(conn)
        if error:
            messagebox.showerror("Database Error", error, parent=self.top)
        self.years = years
        self.selected_year = tk.StringVar()
        self.filter_month_var = tk.BooleanVar(value=False)
        self.selected_month = tk.StringVar()
        self.title = None
        self.months = [
            ("", None), ("January", 1), ("February", 2), ("March", 3),
            ("April", 4), ("May", 5), ("June", 6), ("July", 7), ("August", 8),
            ("September", 9), ("October", 10), ("November", 11),
            ("December", 12),
        ]
        self.columns = [
            "No", "User", "Date", "Item Code", "Product Name", "Operation",
            "Quantity", "Amount"
        ]
        style = ttk.Style(self.top)
        style.configure(
            "Treeview.Heading", font=("Arial", 12, "bold", "underline")
        )
        style.configure("Treeview", font=("Arial", 10))
        self.main_frame = tk.Frame(self.top, bg="lightblue", bd=4, relief="solid")
        self.top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.filter_frame = tk.Frame(self.top_frame, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.filter_frame, textvariable=self.selected_year, width=10,
            state="readonly", values=self.years,
        )
        self.month_cb = ttk.Combobox(
            self.filter_frame, values=[name for name, _num in self.months],
            width=12, state="readonly",
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.title_label = tk.Label(
            self.top_frame, text="", bg="lightblue", bd=4, relief="flat",
            font=("Arial", 16, "bold", "underline"), fg="dodgerblue"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.refresh_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.top_frame.pack(fill="x")
        # Title
        self.title_label.pack(anchor="center", fill="x")
        # Filter Frame
        self.filter_frame.pack(fill="x", padx=5)
        # Year Selector
        tk.Label(
            self.filter_frame, text="Select Year:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.year_cb.pack(side="left", padx=(0, 10))
        if self.years:
            self.year_cb.set(self.years[0])
        else:
            messagebox.showinfo(
                "Info", "No Order Logs Found.", parent=self.top
            )
        self.year_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.refresh_table()
        )

        # Month Filter
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 5))
        tk.Button(
            self.filter_frame, text="Refresh", bd=4, relief="raised",
            command=self.refresh_table, bg="dodgerblue", fg="white"
        ).pack(side="left")
        btn_frame = tk.Frame(self.filter_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=10)
        action_btn = {
            "Export PDF": self.on_export_pdf,
            "Print Logs": self.on_print
        }
        for text, command in action_btn.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="raised",
                bg="dodgerblue", fg="white",
            ).pack(side="left")
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.table_frame.pack(fill="both", expand=True)
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        alt_colors = ("#ffffff", "#e6f2ff")  # White and light blueish
        self.tree.tag_configure("evenrow", background=alt_colors[0])
        self.tree.tag_configure("oddrow", background=alt_colors[1])


    def refresh_table(self):
        year_str = self.selected_year.get()
        if not year_str:
            return
        year = int(year_str)
        month = None
        title = "Stock Items Logs In"
        if self.month_cb.get():
            month = dict(self.months).get(self.month_cb.get())
            title += f" {self.month_cb.get()}"
        title += f" {year}."
        self.title_label.configure(text=title)
        self.title = title

        success, logs = fetch_product_control_logs(self.conn, year, month)
        if not success:
            messagebox.showerror("Error", logs, parent=self.top)
            return
        # Clear current rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, log in enumerate(logs, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            name = re.sub(r"\s+", " ", str(log["product_name"])).strip()
            self.tree.insert("", "end", values=(
                i,
                log["user"],
                log["log_date"],
                log["product_code"],
                name,
                log["description"],
                log["quantity"],
                f"{log['total']:,.2f}"
            ), tags=(tag,))
        self.auto_resize()

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0],
                "User": vals[1],
                "Date": vals[2],
                "Item Code": vals[3],
                "Product Name": vals[4],
                "Operation": vals[5],
                "Quantity": vals[6],
                "Amount": vals[7]
            })
        return rows

    def _make_exporter(self):
        title = self.title
        columns = [
            "No", "User", "Date", "Item Code", "Product Name", "Operation",
            "Quantity", "Amount"
        ]
        rows = self._collect_current_rows()
        return ReportExporter(self.top, title, columns, rows)

    def _check_privilege(self):
        priv = "View Logs"
        verify = VerifyPrivilegePopup(self.top, self.conn, self.user, priv)
        return getattr(verify, "result", None) == "granted"

    def on_export_pdf(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Export PDF.", parent=self.top
            )
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self._check_privilege():
            messagebox.showwarning(
                "Access Denied",
                "You Don't Permission to Print Logs.", parent=self.top
            )
            return
        exporter = self._make_exporter()
        exporter.print()

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
            self.tree.column(col, width=max_width)


class DeletedItemsWindow(BaseWindow):
    def __init__(self, root, conn, user):
        self.top = tk.Toplevel(root)
        self.top.title("Deleted Products")
        self.center_window(self.top, 1200, 650, root)
        self.top.configure(bg="lightblue")
        self.top.transient(root)
        self.top.grab_set()

        self.conn = conn
        self.user = user
        style = ttk.Style()
        style.configure("Treeview", rowheight=20, font=("Arial", 10))
        style.configure(
            "Treeview.Heading", font=("Arial", 12, "bold", "underline")
        )
        self.columns = [
            "No", "Code", "Name", "Description", "Quantity", "Cost",
            "Wholesale Price", "Retail Price", "Min Stock", "Restocked"
        ]
        self.main_frame = tk.Frame(
            self.top, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )


        self.build_ui()
        self.load_data()

    def build_ui(self):
        """UI set up."""
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="groove"
        )
        top_frame.pack(side="top", fill="x")
        tk.Label(
            top_frame, text="Previously Deleted Products", bg="lightblue",
            bd=4, relief="groove", font=("Arial", 16, "bold", "underline")
        ).pack(side="left", padx=20)
        btn_frame = tk.Frame(top_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=10)
        # btn_frame.pack_propagate(False)
        buttons = {
            "Restore": self.restore_product,
            "Export PDF": self.on_export_pdf,
            "Print": self.on_print
        }
        for text, command in buttons.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="raised",
                height=1, width=len(text)
            ).pack(side="left")
        self.table_frame.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        # Set Headings
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        alt_colors = ("#ffffff", "#e6f2ff")  # White and light blueish
        self.tree.tag_configure("evenrow", background=alt_colors[0])
        self.tree.tag_configure("oddrow", background=alt_colors[1])

    def load_data(self):
        """Load data into table."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        items = fetch_deleted_products(self.conn)

        formatter = DescriptionFormatter()
        for i, row in enumerate(items, start=1):
            name = re.sub(r"\s+", " ", str(row["product_name"])).strip()
            desc = formatter.format(row["description"])
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                row["product_code"],
                name,
                desc,
                row["quantity"],
                f"{row["cost"]:,}",
                f"{row["wholesale_price"]:,}",
                f"{row["retail_price"]:,}",
                row["min_stock_level"],
                row["date_replenished"]
            ), tags=(tag,))
        self.autosize_columns()

    def has_privilege(self, privilege: str) -> bool:
        """Check if the current user has the required privilege."""
        dialog = VerifyPrivilegePopup(
            self.top, self.conn, self.user, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You do not have permission to {privilege}.",
                parent=self.top
            )
            return False
        return True

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0],
                "Code": vals[1],
                "Name": vals[2],
                "Description": vals[3],
                "Quantity": vals[4],
                "Cost": vals[5],
                "Wholesale Price": vals[6],
                "Retail Price": vals[7],
                "Min Stock": vals[8],
                "Restocked": vals[9]
            })
        return rows

    def _make_exporter(self):
        title = "Stock Items Report."
        columns = [
            "No", "Code", "Name", "Description", "Quantity", "Cost",
            "Wholesale Price", "Retail Price", "Min Stock", "Restocked"
        ]
        rows = self._collect_current_rows()
        return ReportExporter(self.top, title, columns, rows)

    def on_export_pdf(self):
        if not self.has_privilege("View Products"):
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self.has_privilege("View Products"):
            return
        exporter = self._make_exporter()
        exporter.print()

    def restore_product(self):
        if not self.has_privilege("Restore Product"):
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Advice",
                "Optionally, Select Item to Restore.", parent=self.top
            )
            RestoreProductPopup(
                self.top, self.conn, self.user, self.load_data
            )
            return
        code = self.tree.item(selected[0])["values"][1]
        RestoreProductPopup(
            self.top, self.conn, self.user, self.load_data, code
        )

    def autosize_columns(self):
        """Auto-resize columns based on the content."""
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                width = font.measure(text)
                if width > max_width:
                    max_width = width
            self.tree.column(col, width=max_width)


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
        self.entry = tk.Entry(
            self.top_frame, textvariable=self.search_var, width=30,
            font=("Arial", 11)
        )
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
                font=("Arial", 10, "bold")
            ).pack(anchor="w", pady=(5, 0), padx=5)
            entry = tk.Entry(
                self.details_frame, textvariable=self.fields[key], width=40,
                bd=2, relief="raised", font=("Arial", 11)
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
                col1, text=key, bg="lightblue", font=("Arial", 10, "bold")
            ).pack(anchor="w", pady=(5, 0))
            entry = tk.Entry(
                col1, textvariable=self.fields[key], width=15, bd=2,
                font=("Arial", 11), relief="raised"
            )
            entry.pack(anchor="w", pady=(0, 5), padx=5)
            self.entries[key] = entry
            self.entry_order.append(entry)
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
                code = row['product_code']
                name = row['product_name']
                self.suggestion_box.insert(
                    tk.END, f"{code}  --  {name}"
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
        dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if dialog.result != "granted":
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
        success, message = update_product_details(self.conn, product,
                                                  self.user)
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
    conn=connect_db()
    root=tk.Tk()
    ReconciliationWindow(root, conn, "sniffy")
    root.mainloop()