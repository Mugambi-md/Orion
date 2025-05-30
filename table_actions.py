def quantity_update_popup(product_code):
    import tkinter as tk
    from tkinter import messagebox
    from working_on_stock import update_quantity
    from window_functionality import auto_manage_focus
    if not product_code:
        messagebox.showwarning("No Selection", "No Product Selected.")
        return
    popup = tk.Toplevel()
    popup.title("Update Quantity")
    popup.geometry("300x150")
    popup.grab_set()
    label = tk.Label(popup,text=f"Product Code: {product_code}", font=("Arial", 12))
    label.pack(pady=10)
    quantity_var = tk.StringVar()
    entry_label = tk.Label(popup, text="New Quantity:")
    entry_label.pack()
    quantity_entry = tk.Entry(popup, textvariable=quantity_var)
    quantity_entry.pack(pady=5)
    def submit():
        try:
            new_quantity = int(quantity_var.get())
        except ValueError:
            messagebox.showerror("Invalid Iput", "Please enter a valid integer.")
            return
        confirm = messagebox.askquestion(
            "Confirm Update",
            f"Are you sure you want to update the quantity of product {product_code} to {new_quantity}",
            icon="warning", default='no'
        )
        if confirm == "yes":
            update_quantity(product_code, new_quantity)
            messagebox.showinfo("Success", f"Quantity updated to {new_quantity}.")
            popup.destroy()
    post_button = tk.Button(popup, text="Post", command=submit, bg="green", fg="white")
    post_button.pack(pady=10)
    auto_manage_focus(popup)

def delete_product_popup(product_code, on_success=None):
    from tkinter import messagebox
    from working_on_stock import delete_product
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