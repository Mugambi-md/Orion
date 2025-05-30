def open_update_quantity_window():
        from window_functionality import auto_manage_focus, to_uppercase, only_digits
        import tkinter as tk
        from tkinter import messagebox
        from working_on_stock import update_quantity
        popup = tk.Toplevel()
        popup.title("Update Quantity")
        popup.geometry("300x150")
        popup.grab_set()
        popup.transient()
        # Label and Entry widgets
        label = tk.Label(popup, text="Product Code")
        label.pack()
        code_entry = tk.Entry(popup, width=30)
        code_entry.pack()
        code_entry.bind("<KeyRelease>", lambda event: to_uppercase(code_entry))
        validate_cmd = popup.register(only_digits)
        tk.Label(popup, text="New Quantity:").pack(pady=5)
        quantity_entry = tk.Entry(popup, width=30, validate="key", validatecommand=(validate_cmd, '%S'))
        quantity_entry.pack()
        # Update Button
        def perform_update():
                product_code = code_entry.get().strip()
                quantity = quantity_entry.get().strip()
                if not product_code or not quantity.isdigit():
                        messagebox.showerror("Invalid Input", "Enter a valid product code and quantity.")
                        return
                result = update_quantity(product_code, int(quantity))
                messagebox.showinfo("Result", result)
        tk.Button(popup, text="Update", command=perform_update).pack(pady=10)
        auto_manage_focus(popup)


def open_new_product_popup(window=None):
        import tkinter as tk
        from tkinter import messagebox
        from working_on_stock import insert_new_product
        from window_functionality import auto_manage_focus, to_uppercase, only_digits
        popup = tk.Toplevel()
        popup.title("New Product")
        popup.grab_set()
        popup.transient()
        labels = [
                "Product Code", "Product Name", "Description", "Quantity", "Cost", "Wholesale Price", "Retail Price", "Min Stock Level"
        ]
        entries = {}
        validate_cmd = popup.register(only_digits)
        product_code_entry = tk.Entry(popup, width=30)
        product_code_entry.grid(row=0, column=1, padx=10, pady=5)
        product_code_entry.bind("<KeyRelease>", lambda event: to_uppercase(product_code_entry))
        label = tk.Label(popup, text="Product Code")
        label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        entries["Product Code"] = product_code_entry
        digit_fields = {"Quantity", "Cost", "Wholesale Price", "Retail Price", "Min Stock Level"}
        for i, label_text in enumerate(labels[1:], start=1):
                label = tk.Label(popup, text=label_text)
                label.grid(row=i, column=0, padx=10, pady=5, sticky="e")
                if label_text in digit_fields:
                        entry = tk.Entry(popup, width=30, validate="key", validatecommand=(validate_cmd, '%S'))
                else:
                        entry = tk.Entry(popup, width=30)
                entry.grid(row=i, column=1, padx=10, pady=5)
                entries[label_text] = entry

        def submit_product():
                try:
                        result = insert_new_product(
                                entries["Product Code"].get().upper(),
                                entries["Product Name"].get(),
                                entries["Description"].get(),
                                int(entries["Quantity"].get()),
                                float(entries["Cost"].get()),
                                float(entries["Wholesale Price"].get()),
                                float(entries["Retail Price"].get()),
                                int(entries["Min Stock Level"].get())
                        )
                        messagebox.showinfo("Product Insert", result)
                        if result.startswith("New Product"):
                                popup.destroy()
                except Exception as e:
                        messagebox.showerror("Error", f"Invalid Input: {e}")
        
        submit_btn = tk.Button(popup, text="Post Item", command=submit_product)
        submit_btn.grid(row=len(labels), column=0, columnspan=2, pady=10)
        auto_manage_focus(popup)
def show_update_popup():
        import tkinter as tk
        from tkinter import messagebox
        from connect_to_db import connect_db
        from working_on_stock import update_product
        from window_functionality import auto_manage_focus, to_uppercase, only_digits
        popup = tk.Toplevel()
        popup.title("Update Product")
        popup.grab_set()
        popup.transient()
        labels = [
                "Product Code", "Product Name", "Description", "Add Quantity", "Cost", "Wholesale Price",
                "Retail Price", "Min Stock Level"
        ]
        entries = {}
        validate_cmd = popup.register(only_digits)
        product_code_entry = tk.Entry(popup, width=30)
        product_code_entry.grid(row=0, column=1, padx=10, pady=5)
        product_code_entry.bind("<KeyRelease>", lambda event: to_uppercase(product_code_entry))
        tk.Label(popup, text="Product Code").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        entries["Product Code"] = product_code_entry
        def populate_fields():
                product_code = product_code_entry.get().strip().upper()
                if not product_code:
                        messagebox.showerror("Error", "Please enter Product Code.")
                        return
                conn = connect_db()
                cursor = conn.cursor()
                try:
                        cursor.execute("SELECT * FROM products WHERE product_code = %s", (product_code,))
                        product = cursor.fetchone()
                        if not product:
                                messagebox.showerror("Not Found", f"No product with code '{product_code}' found.")
                                return
                        field_map = {
                                "Product Name": product[2],
                                "Description": product[3],
                                "Add Quantity": "0",
                                "Cost": product[5],
                                "Wholesale Price": product[6],
                                "Retail Price": product[7],
                                "Min Stock Level": product[8]
                        }
                        for i, (label_text, value) in enumerate(field_map.items(), start=1):
                                entry = entries[label_text]
                                entry.delete(0, tk.END)
                                try:
                                        entry.insert(0, str(value) if value is not None else "")
                                except Exception as e:
                                        print(f"Failed to insert value '{value}' for '{label_text}': {e}")
                                        entry.insert(0, "")
                                entry.select_range(0, tk.END)
                except Exception as e:
                        messagebox.showerror("Error", f"Failed to load product: {e}")
                finally:
                        cursor.close()
                        conn.close()
        tk.Button(popup, text="Search", command=populate_fields).grid(row=1, column=0, columnspan=2, padx=10)
        digit_fields = {"Add Quantity", "Cost", "Wholesale Price", "Retail Price", "Min Stock Level"}
        for i, label_text in enumerate(labels[1:], start=2):
                tk.Label(popup, text=label_text).grid(row=i, column=0, padx=10, pady=5, sticky="e")
                if label_text in digit_fields:
                        entry = tk.Entry(popup, width=30, validate="key",validatecommand=(validate_cmd, '%S'))
                else:
                        entry = tk.Entry(popup, width=30,)
                entry.grid(row=i, column=1, padx=10, pady=5)
                entries[label_text] = entry
        def handle_update():
                try:
                        result = update_product(
                                entries["Product Code"].get().strip().upper(),
                                entries["Product Name"].get().strip(),
                                entries["Description"].get().strip(),
                                int(entries["Add Quantity"].get().strip()),
                                float(entries["Cost"].get().strip()),
                                float(entries["Wholesale Price"].get().strip()),
                                float(entries["Retail Price"].get().strip()),
                                int(entries["Min Stock Level"].get().strip())
                        )
                        messagebox.showinfo("Product Update", result)
                        if result.startswith("Updated"):
                                popup.destroy()
                except Exception as e:
                        messagebox.showerror("Error", f"invalid Input: {e}")
        submit_btn = tk.Button(popup, text="Post Update", command=handle_update)
        submit_btn.grid(row=len(labels)+1, column=0, columnspan=2, pady=10)

        auto_manage_focus(popup)
