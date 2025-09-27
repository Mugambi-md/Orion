import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import messagebox
from authentication import VerifyPrivilegePopup
from base_window import BaseWindow
from stock_details_window import ProductsDetailsWindow
from stock_popups1 import (AddStockPopup, DeleteProductPopup,
                           ProductUpdateWindow)
from stock_popups import UpdateQuantityWindow, NewProductPopup, ReconciliationWindow
from stock_access_tables import get_products_table, get_replenishments_table, get_stock_table

class OrionStock(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("ORION STOCK")
        self.center_window(self.master, 1350, 700, parent)
        # self.master.minsize(900, 500)
        self.master.configure(bg="lightblue")
        self.master.transient(parent)
        self.master.grab_set()
        self.conn = conn
        self.user = user
        self.current_data = None
        self.current_section = None

        # Blue top frame for navigation buttons
        self.top_frame = tk.Frame(self.master, bg="#007BFF", height=50)
        self.top_frame.pack(side="top", fill="x")

        self.active_section = None
        self.section_button_widgets = {}
        self.section_buttons = [
            "Stock", "Products", "Replenishments"
        ]
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)
        style.configure("Treeview.Heading", font="Arial 12 bold")
        for section in self.section_buttons:
            btn = tk.Button(
                self.top_frame, text=section, font=("Arial", 12, "bold"),
                command=lambda s=section: self.update_table(s), bg="white",
                fg="black", bd=4, relief="ridge"
            )
            btn.pack(side="left")
            self.section_button_widgets[section] = btn
        
        button_actions = {
            "Products Report": self.open_product_detail_window,
            "Stock Reconciliation": self.open_reconciliation,
            "Delete Product": self.delete_product,
            "Update Quantity": self.open_update_quantity_window,
            "Update Item Details": self.update_products,
            "Add Stock": self.open_add_stock_popup,
            "New Product": self.open_new_product_popup
        }
        # Top Right frame for actions
        self.action_frame = tk.Frame(self.top_frame, bg="lightblue")
        self.action_frame.pack(side="right", padx=10)
        for text, action in button_actions.items():
            tk.Button(
                self.action_frame, text=text, bd=4, bg="white", relief="solid",
                fg="black", width=len(text), command=action
            ).pack(side="right")
        
        self.center_frame = tk.Frame(self.master, bg="lightblue") # Center frame for table and tittle
        self.center_frame.pack(side="left", fill="both", expand=True)
        self.table_title = tk.Label(
            self.center_frame, text="", font=("Arial", 16, "bold"), bg="lightblue"
        )
        self.table_title.pack(padx=5)
        self.top_control_frame = tk.Frame(self.center_frame, bg="skyblue")
        self.top_control_frame.pack(fill="x")
        self.search_frame = tk.Frame(self.top_control_frame, bg="skyblue")
        self.search_frame.pack(side="left")
        self.search_type = tk.StringVar(value="Name")
        tk.Label(self.search_frame, bg="skyblue", text="Search By:").pack(side="left", padx=5)
        self.search_option = ttk.Combobox(self.search_frame, textvariable=self.search_type, values=["Name", "Code"], state="readonly", width=10)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var, width=30)
        search_btn = tk.Button(self.search_frame, text="Search", command=self.perform_search)
        reset_btn = tk.Button(self.search_frame, text="Refresh", command=lambda: self.refresh())
        self.search_option.pack(side="left", padx=5)
        tk.Label(self.search_frame, bg="skyblue", text="Search Item:").pack(side="left", padx=5)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.perform_search())
        search_btn.pack(side="left", padx=5)
        reset_btn.pack(side="left", padx=5)

        self.tree_frame = tk.Frame(self.center_frame)
        self.tree_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree_scroll.pack(side="right", fill="y")
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)
        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.tree.bind("<Button-4>", lambda e: self.tree.yview_scroll(-1, "units"))
        self.tree.bind("<Button-5>", lambda e: self.tree.yview_scroll(1, "units"))
        self.selected_product_code = None # Initialize
        self.tree_scroll.config(command=self.tree.yview)
        self.tree.tag_configure("row1", background="#d1ecf1") # Cyan tint # Define alternating row styles
        self.tree.tag_configure("row2", background="#f8d7da") # Pink/red tint
        self.tree.tag_configure("row3", background="#fff3cd") # Yellow tint
        self.build_ui()
        self.update_table("Stock") # Default view

    def build_ui(self):
        """Build user interface."""
        pass
   
    def autosize_columns(self):
        for col in self.tree["columns"]:
            font = tkFont.Font()
            max_width = font.measure(col)
            for item in self.tree.get_children():
                value =self.tree.set(item, col)
                width = font.measure(value)
                if width > max_width:
                    max_width = width
            self.tree.column(col, width=max_width) # Add padding

    def update_table(self, section):
        self.current_section = section
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = ()
        self.tree.heading("#0", text="")
        for sec, btn in self.section_button_widgets.items():
            btn.config(bg="lightblue") # Reset all buttons to grey
        self.section_button_widgets[section].config(bg="white") # Set clicked to white
        self.active_section = section
        data = []

        if section == "Stock":
            title, columns, rows, data = get_stock_table()
        elif section == "Products":
            title, columns, rows, data = get_products_table()
        elif section == "Replenishments":
            title, columns, rows, data = get_replenishments_table()
        else:
            title, columns, rows = "No section selected", [], []
        self.current_data = data
        self.table_title.config(text=title)

        self.tree["columns"] = columns
        self.tree.column('#0', width=0, stretch=tk.NO)
        for col in columns:
            self.tree.column(col, anchor="center", width=50)
            self.tree.heading(col, text=col, anchor="center")

        for i, row in enumerate(rows, start=1):
            tag = f"row{(i % 3) + 1}"
            self.tree.insert("", "end", values=row, tags=(tag,))
        self.autosize_columns()

    def perform_search(self):
        query = self.search_var.get().strip()
        search_by = self.search_type.get()
        self.tree.delete(*self.tree.get_children()) # Clear Table
        if not query:
            self.update_table(self.current_section)
            return 
        filtered_data = []
        for i, row in enumerate(self.current_data, start=1):
            if search_by == "Name":
                name = (row.get("name") or row.get("product_name") or "")
                if query.lower() in name.lower(): # Case: insensitive match for names
                    filtered_data.append((i, row))
            elif search_by == "Code":
                code = (row.get("code") or row.get("product_code") or "")
                if query.upper() in code: # Match code as uppercase
                    filtered_data.append((i, row))
        for index, row in filtered_data:
            tag = f"row{(index % 3) + 1}"
            if self.current_section == "Products":
                self.tree.insert("", "end", values=(
                    index,
                    row["product_code"],
                    row["product_name"],
                    row["description"],
                    row["quantity"],
                    row["cost"],
                    row["wholesale_price"],
                    row["retail_price"],
                    row["min_stock_level"]
                ), tags=(tag,))
            elif self.current_section == "Stock":
                self.tree.insert("", "end", values=(
                    index,
                    row["code"],
                    row["name"],
                    row["retail"],
                    row["wholesale"]
                ), tags=(tag,))
            elif self.current_section == "Replenishments":
                self.tree.insert("", "end", values=(
                    index,
                    row["product_code"],
                    row["product_name"],
                    row["quantity"],
                    row["cost_per_unit"],
                    row["total_cost"],
                    row["date_replenished"]
                ), tags=(tag,))
            
            self.autosize_columns()
    def refresh(self):
        self.update_table(self.current_section)
    def open_new_product_popup(self):
        priv = "Add New Product"
        verify_dialog = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        NewProductPopup(self.master, self.conn, self.user, self.refresh)
    def open_reconciliation(self):
        priv = "Manage Stock"
        verify_dialog = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        ReconciliationWindow(self.master, self.conn, self.user)
    def open_product_detail_window(self):
        priv = "View Products"
        verify_dialog = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        ProductsDetailsWindow(self.master, self.user, self.conn)
    def open_update_quantity_window(self):
        priv = "Change Product Quantity"
        verify_dialog = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        UpdateQuantityWindow(self.master, self.conn, self.user)

    def open_add_stock_popup(self):
        priv = "Add Stock"
        verify_dialog = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        AddStockPopup(self.master, self.user, self.conn, self.refresh)
    def delete_product(self):
        priv = "Delete Product"
        verify_dialog = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        DeleteProductPopup(self.master, self.conn, self.user, self.refresh)

    def update_products(self):
        priv = "Update Product Details"
        verify_dialog = VerifyPrivilegePopup(self.master, self.conn,
                                             self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied",
                                   f"You do not have permission to {priv}.")
            return
        ProductUpdateWindow(self.master, self.conn, self.user)


if __name__ == "__main__":
    from connect_to_db import connect_db
    conn = connect_db()
    root = tk.Tk()
    app=OrionStock(root, conn, "sniffy")
    root.mainloop()