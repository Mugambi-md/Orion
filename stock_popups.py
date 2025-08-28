import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
# from connect_to_db import connect_db
from base_window import BaseWindow
from table_actions import UpdateQuantityPopup, UpdatePriceWindow, UpdateDescriptionPopup
from working_on_orders import search_product_codes
from working_on_stock import fetch_product_data, insert_new_product, update_quantity
from window_functionality import auto_manage_focus, to_uppercase, only_digits

class UpdateQuantityWindow(BaseWindow):
        def __init__(self, master=None, product_code=None):
                self.popup = tk.Toplevel(master)
                self.popup.title("Update Quantity")
                self.center_window(self.popup, 200, 150)
                self.popup.configure(bg="lightgreen")
                self.popup.grab_set()
                self.popup.transient(master)
                # Label and Entry widgets
                tk.Label(self.popup, text="Product Code:", bg="lightgreen").pack(pady=(5, 0))
                self.code_entry = tk.Entry(self.popup, width=20)
                self.code_entry.pack()
                self.code_entry.bind("<KeyRelease>", lambda e: to_uppercase(self.code_entry))
                if product_code: # Pre-fill code if provided
                        self.code_entry.insert(0, product_code)
                tk.Label(self.popup, text="New Quantity:", bg="lightgreen").pack(pady=(5, 0))
                validate_cmd = self.popup.register(only_digits)
                self.quantity_entry = tk.Entry(self.popup, width=20, validate="key", validatecommand=(validate_cmd, '%S'))
                self.quantity_entry.pack()
                # Update Button
                tk.Button(self.popup, text="Update", bg="lightblue", command=self.perform_update).pack(pady=10)
                auto_manage_focus(self.popup)
                self.code_entry.focus_set()
        def perform_update(self):
                product_code = self.code_entry.get().strip().upper()
                quantity = self.quantity_entry.get().strip()
                if not product_code or not quantity.isdigit():
                        messagebox.showerror("Invalid Input", "Enter a valid product code and quantity.")
                        return
                result = update_quantity(product_code, int(quantity))
                if result:
                        messagebox.showinfo("Result", result)
                        self.popup.destroy()

class NewProductPopup(BaseWindow):
        def __init__(self, parent, conn, refresh_callback):
                self.popup = tk.Toplevel(parent)
                self.popup.title("New Product")
                self.popup.configure(bg="lightgreen")
                self.center_window(self.popup, 250,300)
                self.popup.grab_set()
                self.popup.transient(parent)

                self.refresh = refresh_callback
                self.conn = conn
                self.entries = {}
                self.labels = ["Product Code", "Product Name", "Description", "Quantity", "Cost",
                        "Wholesale Price", "Retail Price", "Min Stock Level"]
                self.digit_fields = {"Quantity", "Cost", "Wholesale Price", "Retail Price", "Min Stock Level"}
                self.validate_cmd = self.popup.register(only_digits)
                self.warning_label = None
                self.build_form()
                auto_manage_focus(self.popup)
        def build_form(self):
                code_entry = tk.Entry(self.popup, width=20)
                code_entry.grid(row=0, column=1, padx=5, pady=(0, 2))
                code_entry.bind("<KeyRelease>", self.check_product_code)
                code_entry.bind("<Return>", self.on_enter_code)
                tk.Label(self.popup, text="Product Code:", bg="lightgreen").grid(row=0, column=0, padx=5, pady=2, sticky="e")
                self.entries["Product Code"] = code_entry
                self.warning_label = tk.Label(
                        self.popup, text="Product Code is not Available", bg="lightgreen", fg="red",
                        font=("Arial", 9, "italic"), anchor="center")
                self.warning_label.grid(row=1, column=0, columnspan=2, padx=5)
                self.warning_label.grid_remove()
                # Other entries
                for i, label_text in enumerate(self.labels[1:], start=1):
                        tk.Label(self.popup, text=f"{label_text}:", bg="lightgreen").grid(row=i+1, column=0, padx=5, pady=2, sticky="e")
                        if label_text in self.digit_fields:
                                entry = tk.Entry(self.popup, width=20, validate="key",
                                                 validatecommand=(self.validate_cmd, '%S'))
                        else:
                                entry = tk.Entry(self.popup, width=20)
                        entry.grid(row=i+1, column=1, padx=5, pady=2)
                        self.entries[label_text] = entry
                # Submit Button
                submit_btn = tk.Button(self.popup, text="Post Item", bg="lightblue", width=15, command=self.submit_product)
                submit_btn.grid(row=len(self.labels)+1, column=0, columnspan=2, pady=10)
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
                        messagebox.showwarning("Duplicate", "Product Code Already Exists. Choose Another.")
                        self.entries["Product Code"].config(bg="#ffcdd2")
                        self.warning_label.grid(row=1, column=0, columnspan=2, padx=5)
                else:
                        self.warning_label.grid_remove()
                        self.entries["Product Code"].config(bg="white")
                        self.entries["Product Name"].focus_set()
        def submit_product(self):
                code = self.entries["Product Code"].get().upper()
                if search_product_codes(self.conn, code):
                        messagebox.showwarning("Duplicate", "Product Code Already Exists. Choose Another.")
                        return
                try:
                        result = insert_new_product(
                                self.entries["Product Code"].get().upper(),
                                self.entries["Product Name"].get(),
                                self.entries["Description"].get(),
                                int(self.entries["Quantity"].get()),
                                float(self.entries["Cost"].get()),
                                float(self.entries["Wholesale Price"].get()),
                                float(self.entries["Retail Price"].get()),
                                int(self.entries["Min Stock Level"].get())
                        )
                        if result.startswith("New Product"):
                                messagebox.showinfo("Success", result)
                                self.refresh()
                                self.popup.destroy()
                except Exception as e:
                        messagebox.showerror("Error", f"Invalid Input: {e}")


class ReconciliationWindow(BaseWindow):
        def __init__(self, master, conn):
                self.window = tk.Toplevel(master)
                self.window.title("Product Reconciliation")
                self.center_window(self.window, 1050, 600)
                self.window.configure(bg="lightblue")
                self.window.grab_set()
                self.window.transient(master)

                self.search_by_var = None
                self.search_label = None
                self.search_var = None
                self.data = None
                self.tree = None
                self.conn = conn

                self.setup_widgets()
        def setup_widgets(self):
                tk.Label(self.window, text="Available Products",
                         font=("Arial", 15, "bold"),bg="lightblue").pack(pady=(5, 0), padx=5) # Title
                tk.Label(self.window, text="Select Product to Edit", font=("Arial", 10, "italic"), fg="blue",
                         bg="lightblue").pack(padx=5) # italic Note
                #Search Frame
                search_frame = tk.Frame(self.window, bg="lightblue")
                search_frame.pack(side="top", fill="x", padx=5)
                tk.Label(search_frame, text="Search by:", bg="lightblue").pack(side="left", padx=(5, 0))
                self.search_by_var = tk.StringVar(value="Product Name")
                search_options = ttk.Combobox(search_frame,
                                              textvariable=self.search_by_var, values=["Product Name", "Product Code"],
                                              state="readonly", width=15)
                search_options.pack(side="left", padx=(0, 5))
                search_options.bind("<<ComboboxSelected>>", self.update_search_label)
                self.search_label = tk.Label(search_frame, text="Enter Product Name:", bg="lightblue")
                self.search_label.pack(side="left", padx=(5, 0))
                self.search_var = tk.StringVar()
                search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=20)
                search_entry.pack(side="left", padx=(0, 5))
                search_entry.bind("<KeyRelease>", self.filter_table)
                btn_frame = tk.Frame(search_frame, bg="lightblue")
                btn_frame.pack(side="right", padx=5)
                ttk.Button(btn_frame, text="Update Quantity", command=self.update_quantity).pack(side="left", padx=3)
                ttk.Button(btn_frame, text="Update Price", command=self.update_price).pack(side="left", padx=3)
                ttk.Button(btn_frame, text="Update Description", command=self.update_description).pack(padx=3, side="left")
                ttk.Button(btn_frame, text="Refresh", command=self.refresh_table).pack(padx=3, side="left")
                # Table Frame
                table_frame = tk.Frame(self.window, bg="lightblue")
                table_frame.pack(fill=tk.BOTH, expand=True, pady=3)
                self.tree = ttk.Treeview(table_frame, columns=("no", "code", "name", "desc", "qty", "retail",
                                                               "wholesale"), show="headings", height=20)
                # Style
                style = ttk.Style()
                style.configure("Treeview.Heading", font=("Arial", 10, "bold"), anchor="center")
                style.configure("Treeview", rowheight=30, font=("Arial", 10))
                # Scrollbar
                scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
                self.tree.configure(yscrollcommand=scrollbar.set)
                scrollbar.pack(side="right", fill="y")
                self.tree.pack(side="left", fill="both", expand=True)
                # Columns config
                headings = [("no", "No"), ("code", "Product Code"), ("name", "Product Name"), ("desc", "Description"),
                            ("qty", "Quantity"), ("retail", "Retail Price"), ("wholesale", "Wholesale Price")]
                for col_id, col_name in headings:
                        self.tree.heading(col_id, text=col_name)
                        self.tree.column(col_id, anchor="center", stretch=True)
                self.populate_table()
                self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(int(-1*(e.delta/120)), "units"))

        def update_search_label(self, event=None):
                selected = self.search_by_var.get()
                label = "Enter Product Name:" if selected == "Product Name" else "Enter Product Code:"
                self.search_label.config(text=label)

        def populate_table(self):
                self.data = fetch_product_data(self.conn)
                self.tree.delete(*self.tree.get_children())
                alt_colors = ("#ffffff", "#e6f2ff") # White and light blueish
                self.tree.tag_configure("evenrow", background=alt_colors[0])
                self.tree.tag_configure("oddrow", background=alt_colors[1])
                for index, row in enumerate(self.data, start=1):
                        display_row = (index, row["product_code"], row["product_name"], row["description"],
                                       row["quantity"], row["retail_price"], row["wholesale_price"])
                        tag = "evenrow" if index % 2 == 0 else "oddrow"
                        self.tree.insert("", "end", values=display_row, tags=(tag,))
                for col in self.tree["columns"]:
                        font = tkFont.Font()
                        self.tree.column(col, width=font.measure(col.title()) + 5)
                        for item in self.tree.get_children():
                                cell_text = str(self.tree.set(item, col))
                                pixel_width = font.measure(cell_text) + 5
                                if self.tree.column(col, 'width') < pixel_width:
                                        self.tree.column(col, width=pixel_width)

        def filter_table(self, event=None):
                keyword = self.search_var.get().lower()
                search_field = "product_name" if self.search_by_var.get() == "Product Name" else "product_code"
                self.tree.delete(*self.tree.get_children())
                alt_colors = ("#ffffff", "#e6f2ff") # White and light blueish
                filtered = [r for r in self.data if keyword in str(r[search_field]).lower()]
                for i, row in enumerate(filtered, start=1):
                        display_row = (i, row["product_code"], row["product_name"], row["description"],
                                       row["quantity"], row["retail_price"], row["wholesale_price"])
                        self.tree.insert("", "end", values=display_row, tags=(alt_colors[i % 2],))

        def get_selected_item(self):
                selected = self.tree.selection()
                if not selected:
                        messagebox.showwarning("No Selection", "Please select a product from the table.")
                        return None
                return self.tree.item(selected[0])["values"]
        def update_quantity(self):
                item = self.get_selected_item()
                if item:
                        UpdateQuantityPopup(self.window, self.conn, item, self.refresh_table)
                else:
                        messagebox.showerror("No Selection", "Please Select Item to Update Quantity.")

        def update_price(self):
                item = self.get_selected_item()
                if item:
                        UpdatePriceWindow(self.window, self.conn, item, self.refresh_table)
                else:
                        messagebox.showerror("No Selection", "Please Select Item to Update Price.")

        def update_description(self):
                item = self.get_selected_item()
                if item:
                        UpdateDescriptionPopup(self.window, self.conn, item, self.refresh_table)
                else:
                        messagebox.showerror("No Selection", "Please select Item to update Description.")
        def refresh_table(self):
                self.populate_table()

# if __name__ == "__main__":
#         conn = connect_db()
#         root = tk.Tk()
#         # root.withdraw()
#         app=ReconciliationWindow(root,conn)
#         root.mainloop()