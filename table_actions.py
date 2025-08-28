import tkinter as tk
from tkinter import messagebox
from  base_window import BaseWindow
from working_on_stock import update_quantity, delete_product, update_price, update_description
from window_functionality import auto_manage_focus

class UpdatePriceWindow(BaseWindow):
    def __init__(self, master, conn, item, refresh_callback):
        self.conn = conn
        self.item = item
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(master)
        self.window.title("Update Price")
        self.window.configure(bg="lightgray")
        self.center_window(self.window, 400, 250)
        self.window.transient(master)
        self.window.grab_set()
        # Extract Values
        self.product_code = item[1]
        self.product_name = item[2]
        self.old_retail_price = item[5]
        self.old_wholesale_price = item[6]
        # Label showing current prices
        current_label = f"""Current price for {self.product_code} ({self.product_name}) is:
                        Retail Price: {self.old_retail_price}  Wholesale Price: {self.old_wholesale_price}."""
        tk.Label(self.window, text=current_label, bg="lightgray", fg="blue", font=("Arial", 10, "bold")).pack(pady=(2, 5))
        tk.Label(self.window, text="Enter New Retail Price:", bg="lightgray").pack()
        self.retail_entry = tk.Entry(self.window, width=10)
        self.retail_entry.pack(pady=(0, 5))
        self.retail_entry.focus_set()
        self.retail_entry.bind("<Return>", lambda e: self.wholesale_entry.focus_set())
        tk.Label(self.window, text="Enter New Wholesale Price:", bg="lightgray").pack()
        self.wholesale_entry = tk.Entry(self.window, width=10)
        self.wholesale_entry.pack(pady=(0, 5))
        self.wholesale_entry.bind("<Return>", lambda e: update_btn.focus_set())
        update_btn = tk.Button(self.window, text="Update Price", command=self.update_price)
        update_btn.pack()
        update_btn.bind("<Return>", lambda e: self.update_price())
    def update_price(self):
        try:
            new_retail = float(self.retail_entry.get())
            new_wholesale = float(self.wholesale_entry.get())
            product_code = str(self.product_code)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter Valid numeric prices")
            return
        result = update_price(self.conn, product_code, new_retail, new_wholesale)
        if result:
            messagebox.showinfo("Success",f"Price Updated successfully for {self.product_name}")
            self.refresh_callback()
            self.window.destroy()
        else:
            messagebox.showerror("Error", str(result))


def delete_product_popup(product_code, on_success=None):
    if not product_code:
        messagebox.showwarning("No Selection", "No Product Selected.")
        return
    confirm = messagebox.askquestion(
        "Confirm Deletion",
        f"Are you sure you want to delete product:\n\n CODE: {product_code}\n\nThis action cannot be undone.",
        icon="warning",
        default="no"
    )
    if confirm.lower() == "yes":
        result = delete_product(product_code)
        if "deleted successfully" in result.lower():
            messagebox.showinfo("Deleted", result)
            if on_success:
                on_success()
        elif "no product found" in result.lower():
            messagebox.showwarning("Not Found", result)
        elif "database connection failed" in result.lower():
            messagebox.showerror("Connection Error", result)
        else:
            messagebox.showerror("Error", result)

class UpdateQuantityPopup(BaseWindow):
    def __init__(self, parent, conn, product_data, refresh_callback):
        self.conn = conn
        self.product_data = product_data
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)
        self.window.title("Update Quantity")
        self.center_window(self.window, 300, 180)
        self.window.configure(bg="lightgray")
        self.window.transient(parent)
        self.window.grab_set()

        name = product_data[2]
        current_qty = product_data[4]

        tk.Label(self.window, text=f"Current Quantity for {name}\nIs: {current_qty}", font=("Arial", 10, "italic"),
                 bg="lightgray").pack(pady=(5, 4))
        tk.Label(self.window, text="Enter New Current Quantity:", font=("Arial", 10, "bold"),
                 bg="lightgray").pack(pady=(3, 0))
        self.new_qty_var = tk.StringVar()
        tk.Entry(self.window, textvariable=self.new_qty_var, width=20).pack(pady=(0, 5))
        post_btn = tk.Button(self.window, text="Update Quantity", command=self.update_quantity)
        post_btn.pack()

    def update_quantity(self):
        new_qty = self.new_qty_var.get().strip()
        if not new_qty.isdigit():
            messagebox.showerror("Invalid Input", "Please enter a valid number.")
            return
        product_code = str(self.product_data[1])
        qty = int(new_qty)
        try:
            result = update_quantity(product_code, qty)
            if result:
                messagebox.showinfo("Success", "Quantity Updated Successfully.")
                self.refresh_callback()
                self.window.destroy()
            else:
                messagebox.showerror("Error Updating", result)
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

class UpdateDescriptionPopup(BaseWindow):
    def __init__(self, master, conn, item, refresh_callback):
        self.conn = conn
        self.item = item
        self.refresh_callback = refresh_callback
        self.product_code = item[1]
        self.product_name = item[2]
        self.old_description = item[3]

        self.window = tk.Toplevel(master)
        self.window.title("Update Description")
        self.center_window(self.window, 400, 220)
        self.window.configure(bg="lightgray")
        self.window.transient(master)
        self.window.grab_set()
        # Label with current description
        current_label = f"""Current description for {self.product_code} ({self.product_name}):
                        \n{self.old_description}"""
        tk.Label(self.window, text=current_label, bg="lightgray", wraplength=380,
                 font=("Arial", 10, "bold")).pack(pady=(3, 5))
        # Entry for new description
        tk.Label(self.window, text="Enter New Description:", bg="lightgray").pack()
        self.desc_entry = tk.Entry(self.window, width=30)
        self.desc_entry.pack(pady=(0, 5))
        # Button to update
        update_btn = tk.Button(self.window, text="Update Description", command=self.update_description)
        update_btn.pack()

    def update_description(self):
        new_description = self.desc_entry.get().strip()
        if not new_description:
            messagebox.showerror("Invalid Input", "Description Cannot be Empty.")
            return
        product_code = str(self.product_code)
        result = update_description(self.conn, product_code, new_description)
        if result:
            messagebox.showinfo("Success", f"Description updated for {self.product_name}")
            self.refresh_callback()
            self.window.destroy()
        else:
            messagebox.showerror("Error Updating", str(result))