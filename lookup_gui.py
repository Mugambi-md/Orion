import tkinter as tk
from tkinter import StringVar
from tkinter import ttk
from base_window import BaseWindow
from working_sales import search_products

class ProductSearchWindow(BaseWindow, tk.Toplevel):
    def __init__(self, master, conn):
        super().__init__(master)
        self.title("Search Products")
        self.configure(bg="lightblue")
        self.center_window(self, 750, 350)
        self.transient(master)
        self.grab_set()
        self.conn = conn
        self.combo = None
        self.entry = None
        self.tree = None
        self.search_label = None
        self.search_var = None

        self.create_widgets()

    def create_widgets(self):
        top_frame = tk.Frame(self, bg="lightblue", padx=5) # Top Frame
        top_frame.pack(fill="x")
        tk.Label(top_frame, text="Search By:", bg="lightblue", font=("Arial", 10)).pack(side="left") # Search Label
        self.combo = ttk.Combobox(top_frame, values=["Name", "Code"], state="readonly") # Combobox
        self.combo.current(0)
        self.combo.pack(side="left", padx=5)
        self.combo.bind("<<ComboboxSelected>>", self.update_search_label) #Bind to update function
        self.search_label = tk.Label(top_frame, text="Enter Product Name:", bg="lightblue", font=("Arial", 10))
        self.search_label.pack(side="left", padx=5)
        self.search_var = StringVar() # Entry
        self.entry = ttk.Entry(top_frame, textvariable=self.search_var, width=20)
        self.entry.pack(side="left", padx=5)
        self.entry.bind("<KeyRelease>", self.perform_search)
        bottom_frame = tk.Frame(self, bg="lightblue", padx=5)
        bottom_frame.pack(fill="both", expand=True, pady=(0, 3))
        self.tree = ttk.Treeview(bottom_frame, columns=("code", "name", "qty", "wholesale", "retail"), show="headings")
        for col, text in zip(["code", "name", "qty", "wholesale", "retail"],
            ["Product Code", "Product Name", "Quantity", "Wholesale Price", "Retail Price"]):
            self.tree.heading(col, text=text)
            self.tree.column(col, anchor="center", width=50)
        self.tree.pack(fill="both", expand=True)
    def update_size(self):
        row_count = len(self.tree.get_children())
        row_height = self.tree.winfo_reqheight() // (row_count or 1)
        base_height= 150
        new_height = base_height + (row_count * row_height)
        max_height = 600
        self.geometry(f"800x{min(new_height, max_height)}")
    def perform_search(self, event=None):
        keyword = self.search_var.get().strip()
        search_field = "product_name" if self.combo.get() == "Name" else "product_code"
        if not keyword:
            self.tree.delete(*self.tree.get_children())
            return
        result = search_products(self.conn, search_field, keyword)
        # Clear and insert results
        self.tree.delete(*self.tree.get_children())
        for row in result:
            self.tree.insert("", "end", values=(
                row['product_code'],
                row['product_name'],
                row['quantity'],
                row['wholesale_price'],
                row['retail_price']
            ))
        self.update_idletasks()
        self.update_size()
    def update_search_label(self, event=None):
        """Update search label based on selected combo option."""
        selected_option = self.combo.get()
        self.search_label.config(text="Enter Product Name:" if selected_option == "Name" else "Enter Product Code:")

# if __name__ == "__main__":
#     from connect_to_db import connect_db
#     root = tk.Tk()
#     # root.withdraw()
#     conn = connect_db()
#     ProductSearchWindow(root, conn)
#     root.mainloop()