import tkinter as tk
from tkinter import ttk
from selling_gui import MakeSaleWindow
import tkinter.messagebox as messagebox

class SalesGUI:
    def __init__(self, parent):
        import tkinter as tk
        from tkinter import ttk
        import tkinter.font as tkFont
        from sales_access import get_products_for_sales_table
        self.master = tk.Toplevel(parent)
        self.master.title("Sales Module")
        self.master.geometry("1300x700")
        self.master.minsize(900, 500)
        self.master.configure(bg="green")
        self.master.grab_set() # Blocks interaction with main window
        # Left Frame Nav Buttons
        self.left_frame = tk.Frame(self.master, bg="blue", width=150)
        self.left_frame.pack(side="left", fill="y")
        self.buttons = {
            "Sell": self.open_sell_window,
            "Look Up Product": self.lookup_product,
            "Sales Records": self.sales_records,
            "Orders": self.orders,
            "Invoices": self.invoices,
            "Customers": self.customers,
            "Sales Analysis": self.sales_analysis
            }
        for text, command in self.buttons.items():
            if text == "Sell":
                tk.Button(
                    self.left_frame,
                    text=text,
                    width=20,
                    command=command
                    ).pack(pady=5, padx=10)
            else:
                tk.Button(
                    self.left_frame,
                    text=text,
                    width=20,
                    state="disabled"
                ).pack(padx=10, pady=5)
            
        # Right Frame Action buttons
        self.right_frame = tk.Frame(self.master, bg="blue", width=150)
        self.right_frame.pack(side="right", fill="y")
        action_buttons = ["Change Price", "Change Code", "Change Description"] # Add more Later
        for btn in action_buttons:
            tk.Button(self.right_frame, text=btn, width=20).pack(padx=10, pady=5)
        # Center Frame Products table Area
        self.center_frame = tk.Frame(self.master, bg="green")
        self.center_frame.pack(expand=True, fill="both")
        # Top Frame search and sort controls
        self.top_controls = tk.Frame(self.center_frame, bg="blue")
        self.top_controls.pack(fill="x", padx=5, pady=5)
        tk.Label(self.top_controls, text="Search Products:", bg="blue", fg="white").pack(side="left", padx=5)
        self.search_entry = tk.Entry(self.top_controls, width=25)
        self.search_entry.pack(side="left", padx=5)

        tk.Label(self.top_controls, text="Sort By:", bg="blue", fg="white").pack(side="left", padx=5)
        self.sort_colunm = ttk.Combobox(self.top_controls, values=["Product Name", "Product Code", "Quantity"], width=15)
        self.sort_colunm.pack(side="left", padx=5)
        self.sort_colunm.set("Product Name")

        self.sort_order = ttk.Combobox(self.top_controls, values=["Ascending", "Descending"])
        self.sort_order.pack(side="left", padx=5)
        self.sort_order.set("Ascending")
        # Table Title
        tk.Label(self.center_frame, text="Available Products In Stock", bg="green", font=("Arial", 12, "bold")).pack(pady=5)
        # Table Treeview
        self.table_frame = tk.Frame(self.center_frame)
        self.table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        columns, rows = get_products_for_sales_table()
        self.product_table = ttk.Treeview(self.table_frame, columns=columns, show="headings")
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)
        style.configure("Treeview.Heading", font="Arial 12 bold")
        for col in columns: # Set up headings
            self.product_table.heading(col, text=col)
            self.product_table.column(col, anchor="center")
        for idx, row in enumerate(rows): # Insert data rows
            if idx % 3 == 0:
                tag = "evenrow"
            elif idx % 3 == 1:
                tag = "oddrow"
            else:
                tag = "thirdrow"
            self.product_table.insert("", "end", values=row, tags=(tag,))
        self.product_table.tag_configure("evenrow", background='#add8e6') # Light Blue
        self.product_table.tag_configure("oddrow", background='#ffffff') # white
        self.product_table.tag_configure("thirdrow", background='#d3d3d3') # Light grey
        font = tkFont.Font() # Auto-size columns
        for col in columns:
            max_width = font.measure(col) # Start with header width
            for item in self.product_table.get_children():
                cell_text = self.product_table.set(item, col)
                max_width = max(max_width, font.measure(str(cell_text)))
                self.product_table.column(col, width=max_width + 10)
        self.product_table.pack(fill="both", expand=True)
    def open_sell_window(self):
        MakeSaleWindow(self.master)
    def lookup_product(self):
        messagebox.showinfo("Coming Soon", "Look Up Product window coming soon!")
    def sales_records(self):
        messagebox.showinfo("Coming Soon", "Sale Records window coming soon!")    
    def orders(self):
        messagebox.showinfo("Coming Soon", "Orders window coming soon!")
    def invoices(self):
        messagebox.showinfo("Coming Soon", "Invoices window coming soon!")
    def customers(self):
        messagebox.showinfo("Coming Soon", "Customers window coming soon!")
    def sales_analysis(self):
        messagebox.showinfo("Coming Soon", "Sales Analysis window coming soon!")
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app=SalesGUI(root)
    root.mainloop()