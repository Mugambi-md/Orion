import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import messagebox
from stock_details_window import open_products_details_window
from table_actions import quantity_update_popup, delete_product_popup
from stock_popups1 import open_add_stock_popup,delete_product_popup
from stock_popups import open_update_quantity_window, open_new_product_popup, show_update_popup
from stock_access_tables import get_products_table, get_replenishments_table, get_stock_table

class OrionStock:
    def __init__(self, parent):
        self.master = tk.Toplevel(parent)
        self.master.title("ORION STOCK")
        self.master.geometry("1300x700")
        self.master.minsize(900, 500)
        self.master.configure(bg="white")
        self.master.grab_set()

        self.top_frame = tk.Frame(self.master, bg="#007BFF", height=50) # Blue top frame for navigation buttons
        self.top_frame.pack(side="top", fill="x")

        self.active_section = None
        self.section_button_widgets = {}
        self.section_buttons = ["Stock", "Products", "Replenishments", "Products Report"]
        for section in self.section_buttons:
            if section == "Products Report":
                btn = tk.Button(self.top_frame,text=section, font=("Arial", 12, "bold"), command=open_products_details_window)
            else:
                btn = tk.Button(self.top_frame, text=section, font=("Arial", 12, "bold"),
                                command=lambda s=section: self.update_table(s),
                                bg="white", fg="black")
            btn.pack(side="left", padx=10, pady=10)
            self.section_button_widgets[section] = btn
        
        button_actions = {"New Product": open_new_product_popup,
                          "Add Stock": open_add_stock_popup,
                          "Update Quantity": open_update_quantity_window,
                          "Update Details": show_update_popup,
                          "Delete Product": delete_product_popup
                          }
        self.right_frame = tk.Frame(self.master, bg="#28A745", width=150) # Right green frame for actions
        self.right_frame.pack(side="right", fill="y")
        for text, action in button_actions.items():
            btn = tk.Button(self.right_frame, text=text, font=("Arial", 11),
                            bg="white", fg="black", width=15, command=action)
            btn.pack(pady=7, padx=6)
        
        self.center_frame = tk.Frame(self.master, bg="white") # Center frame for table and tittle
        self.center_frame.pack(side="left", fill="both", expand=True)
        self.top_control_frame = tk.Frame(self.center_frame, bg="skyblue")
        self.top_control_frame.pack(fill="x", padx=10, pady=5)
        self.search_frame = tk.Frame(self.top_control_frame, bg="skyblue")
        self.search_frame.pack(side="left")
        self.search_type = tk.StringVar(value="Name")
        self.search_option = ttk.Combobox(self.search_frame, textvariable=self.search_type, values=["Name", "Code"], state="readonly", width=10)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var, width=30)
        search_btn = tk.Button(self.search_frame, text="Search", command=self.perform_search)
        reset_btn = tk.Button(self.search_frame, text="Reset", command=lambda: self.update_table(self.current_section))
        self.search_option.pack(side="left", padx=5, pady=4)
        self.search_entry.pack(side="left", padx=5, pady=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self.perform_search())
        search_btn.pack(side="left", padx=5, pady=4)
        reset_btn.pack(side="left", padx=5, pady=4)
        self.action_button_container = tk.Frame(self.top_control_frame, bg="skyblue")
        self.action_button_container.pack(side="right")
        self.table_title = tk.Label(self.center_frame, text="", font=("Arial", 14, "bold"), bg="white")
        self.table_title.pack(pady=4)
        self.tree_frame = tk.Frame(self.center_frame)
        self.tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree_scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_item)
        self.selected_product_code = None # Initialize
        self.tree_scroll.config(command=self.tree.yview)
        self.tree.tag_configure("row1", background="#d1ecf1") # Cyan tint # Define alternating row styles
        self.tree.tag_configure("row2", background="#f8d7da") # Pink/red tint
        self.tree.tag_configure("row3", background="#fff3cd") # Yellow tint
        self.update_table("Stock") # Default view
   
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

    def update_action_buttons(self, section):
        for widget in self.action_button_container.winfo_children():
            widget.destroy()
        if section in ["Stock", "Products", "Replenishments"]:
            def with_selected_code(action_func):
                return lambda: action_func() if self.selected_product_code else messagebox.showwarning("No Selection", "Please Select a Product First.")
            button_actions = {
                "Update Quantity": with_selected_code(quantity_update_popup),
                "Update Details": with_selected_code(show_update_popup)
            }
            for text, action in button_actions.items():
                btn = tk.Button(self.action_button_container, text=text, font=("Arial", 10), bg="lightgrey", fg="black", width=15, command=action)
                btn.pack(side="left", padx=4)
            

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
            self.tree.column(col, anchor=tk.W, width=100)
            self.tree.heading(col, text=col, anchor=tk.W)

        for i, row in enumerate(rows, start=1):
            tag = f"row{(i % 3) + 1}"
            self.tree.insert("", "end", values=row, tags=(tag,))
        if section in ["Stock", "Products", "Replenishments"]:
            self.update_action_buttons(section)
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
                if query.lower() in name.lower(): # Case- insensitive match for names
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
    def on_select_item(self, event):
        selected_item = self.tree.focus()
        if selected_item:
            values = self.tree.item(selected_item, "values")
            if values:
                self.selected_product_code = values[1] #2nd column (index 1)
            else:
                self.selected_product_code = None


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app=OrionStock(root)
    root.mainloop()