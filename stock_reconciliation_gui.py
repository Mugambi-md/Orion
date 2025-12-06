import re
import tkinter as tk
import tkinter.font as tkFont
from tkinter import messagebox, ttk
from base_window import BaseWindow
from accounting_export import ReportExporter
from authentication import VerifyPrivilegePopup, DescriptionFormatter
from working_on_stock import fetch_all_products
from stock_update_popups import UpdateQuantityWindow
from stock_windows import DeletedItemsWindow
from stock_popups import (
    ProductUpdateWindow, DeleteProductPopup, UpdateStockLevelPopup
)
from stock_table_action_gui import (
    UpdateQuantityPopup, UpdatePriceWindow, UpdateDescriptionPopup
)

class ReconciliationWindow(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Product Reconciliation")
        self.center_window(self.window, 1200, 700, master)
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
        # Style
        style = ttk.Style()
        style.theme_use("alt")
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"))
        style.configure("Treeview", font=("Arial", 11))
        # Search Frame
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.search_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.search_label = tk.Label(
            self.search_frame, text="Product Name:", bg="lightblue",
            font=("Arial", 12, "bold")
        )
        self.columns = [
            "No", "Product Code", "Product Name", "Description", "Quantity",
            "Retail Price", "Wholesale Price", "Restocked"
        ]
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.setup_widgets()
        self.populate_table()

    def setup_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Title
        tk.Label(
            self.main_frame, text="Available Products To Reconcile", bd=4,
            relief="ridge", bg="lightblue", fg="blue",
            font=("Arial", 16, "bold", "underline")
        ).pack(anchor="center", ipadx=20)
        # Buttons Frame
        action_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        action_frame.pack(side="top", fill="x")
        export_btns = {
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
            "Print": self.on_print,
        }
        for text, action in export_btns.items():
            tk.Button(
                action_frame, text=text, bd=2, relief="raised", fg="white",
                bg="blue", command=action, font=("Arial", 9, "bold")
            ).pack(side="right")
        button_actions = {
            "Update Item Details": self.update_products,
            "Update Quantity": self.open_update_quantity_window,
            "Update Min Stock Level": self.min_stock_level_window,
            "Deleted Products": self.deleted_products
        }
        for text, action in button_actions.items():
            tk.Button(
                action_frame, text=text, bd=4, relief="groove", fg="white",
                bg="dodgerblue", command=action, font=("Arial", 11, "bold")
            ).pack(side="left")
        self.search_frame.pack(side="top", fill="x")
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
        tk.Label(
            self.search_frame, text="Select Product to Edit", fg="blue",
            font=("Arial", 12, "italic", "underline"), bg="lightblue",
            bd=2, relief="flat"
        ).pack(side="left", padx=5)  # italic Note
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
                btn_frame, text=text, bd=4, relief="ridge", bg="green",
                fg="white", command=action, font=("Arial", 9, "bold")
            ).pack(side="right")
        # Table Frame
        self.table_frame.pack(fill=tk.BOTH, expand=True)
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
            label = "Product Name:"
        else:
            label = "Product Code:"
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
        formatter = DescriptionFormatter(50, 10)
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
                row["date_replenished"].strftime("%d/%m/%Y")
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
                "No Selection", "Please select a product from the table.",
                parent=self.window
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

    def open_update_quantity_window(self):
        if not self.has_privilege("Change Product Quantity"):
            return
        UpdateQuantityWindow(self.window, self.conn, self.user)

    def update_products(self):
        if not self.has_privilege("Admin Product Details"):
            return
        ProductUpdateWindow(self.window, self.conn, self.user)

    def min_stock_level_window(self):
        if not self.has_privilege("Stock Level"):
            return
        UpdateStockLevelPopup(self.window, self.conn, self.user)

    def deleted_products(self):
        if not self.has_privilege("Manage Stock"):
            return
        DeletedItemsWindow(self.window, self.conn, self.user)

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
        if not self.has_privilege("Admin Product Quantity"):
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
        if not self.has_privilege("Admin Product Price"):
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
        if not self.has_privilege("Update Product Details"):
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

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root=tk.Tk()
    ReconciliationWindow(root, conn, "Sniffy")
    root.mainloop()