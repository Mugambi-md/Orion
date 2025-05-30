def open_add_stock_popup(master=None):
    import tkinter as tk
    from tkinter import messagebox
    from working_on_stock2 import add_to_existing_product
    from stock_popups import open_new_product_popup
    from window_functionality import to_uppercase, only_digits, auto_manage_focus

    popup = tk.Toplevel()
    popup.title("Add Stock To Products")
    popup.geometry("400x350")
    popup.configure(bg="skyblue")
    popup.grab_set()

    labels = ["Product Code", "Quantity", "New Cost", "New Wholesale Price", "New Retail Price", "New Min Stock Level"]
    entries = {}

    vcmd = (popup.register(only_digits), '%S') # Validator for numeric input
    for i, label in enumerate(labels):
        tk.Label(popup, bg="skyblue", text=label).grid(row=i, column=0, sticky="e", padx=10, pady=5)
        entry = tk.Entry(popup, bg="white")
        if label != 'Product Code': # Only allow digits for numeric fields
            entry.config(validate="key", validatecommand=vcmd)
        else:
            entry.bind("<FocusOut>", lambda e: to_uppercase(e.widget)) # Auto-uppercase
        entry.grid(row=i, column=1, padx=10, pady=5)
        entries[label] = entry

    def submit():
        try:
            product_code = entries['Product Code'].get().strip().upper()
            added_quantity = int(entries['Quantity'].get().strip())
            def safe_float(val): return float(val.strip()) if val.strip() else None
            new_cost = safe_float(entries['New Cost'].get())
            new_wholesale_price = safe_float(entries['New Wholesale Price'].get())
            new_retail_price = safe_float(entries['New Retail Price'].get())
            new_min_stock_level = safe_float(entries['New Min Stock Level'].get())
            result = add_to_existing_product(
                product_code, added_quantity, new_cost,
                new_wholesale_price, new_retail_price, new_min_stock_level
                )
            if "not found in database" in result.lower():
                if messagebox.askyesno("Product Not Found", f"{result}\nDo you want to add new product?"):
                    popup.destroy()
                    open_new_product_popup(master)
                    return
            elif "not found" in result.lower():
                messagebox.showerror("Error", result)
                return
            else:
                if messagebox.askyesno("Success", f"{result}\nDo you want to add another product?", default='yes'):
                    for entry in entries.values():
                        entry.delete(0, tk.END)
                    entries['Product Code'].focus_set()
                else:
                    popup.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values where required.")
    submit_button = tk.Button(popup, text="Post", command=submit, bg="dodgerblue")
    submit_button.grid(row=len(labels), column=0, columnspan=2, pady=10, padx=20)
    auto_manage_focus(popup)

def delete_product_popup():
    import tkinter as tk
    from tkinter import messagebox
    from connect_to_db import connect_db
    from working_on_stock import delete_product

    popup = tk.Toplevel()
    popup.title("Delete Product")
    popup.geometry("300x350")
    popup.configure(bg="skyblue")
    popup.grab_set()

    search_type = tk.StringVar(value="Product Name") # Default to Product Name
    selected_product = tk.StringVar()
    entries = {}
    product_results = []


    def switch_search_type(*args):
        for widget in frame_search.winfo_children():
            widget.destroy()
        label_text = "Enter Product Code:" if search_type.get() == "Product Code" else "Enter Product Name:"
        label = tk.Label(frame_search, text=label_text, bg="skyblue", width=len(label_text))
        label.pack(side="left", padx=3)

        entry = tk.Entry(frame_search, bg="skyblue", width=25)
        entry.pack(side="left", padx=3)
        if search_type.get() == "Product Code":
            def on_keyrelease(event):
                content = entry.get().upper()
                entry.delete(0, tk.END)
                entry.insert(0, content)
            entry.bind("<KeyRelease>", on_keyrelease)
        entries["search"] = entry
    def search_product():
        listbox.delete(0, tk.END)
        product_results.clear()
        query_value = entries["search"].get().strip()
        if not query_value:
            messagebox.showerror("Error", "Please enter search term.")
            return
        try:
            conn = connect_db()
            cursor = conn.cursor()
            if search_type.get() == "Product Code":
                cursor.execute("SELECT product_code, product_name FROM products WHERE product_code=%s", (query_value,))
            else:
                cursor.execute("SELECT product_code, product_name FROM products WHERE product_name=%s", (query_value,))
            results = cursor.fetchall()
            conn.close()
            if results:
                for code, name in results:
                    display = f"{code} - {name}"
                    product_results.append((code, name))
                    listbox.insert(tk.END, display)
            else:
                messagebox.showinfo("Not Found", "No product(s) found.")
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
    def on_select(event):
        if listbox.curselection():
            index = listbox.curselection()[0]
            code, name = product_results[index]
            selected_product.set(f"Selected: {code} - {name}")
            delete_button.pack(pady=10)
    def delete_selected():
        index = listbox.curselection()
        if not index:
            return
        product_code, product_name = product_results[index[0]]
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{product_name}' from database?",
            default='no'
        )
        if confirm:
            try:
                result = delete_product(product_code)
                if "deleted successfully" in result.lower():
                    messagebox.showinfo("Deleted", f"'{product_name}' has been deleted successfully.")
                    listbox.delete(index[0])
                    delete_button.pack_forget()
                else:
                    messagebox.showerror("Error", result)
            except Exception as err:
                messagebox.showerror("Database Error", str(err))
    # Layout
    option_frame = tk.Frame(popup, bg="skyblue")
    option_frame.pack(pady=10)
    tk.Label(option_frame, text="Search by:", bg="skyblue").pack(side="left", padx=5)
    dropdown = tk.OptionMenu(option_frame, search_type, "Product Code", "Product Name")
    dropdown.pack(side="left", padx=5)
    search_type.trace_add("write", switch_search_type)
    frame_search = tk.Frame(popup, bg="skyblue")
    frame_search.pack()
    switch_search_type() # Set initial label/entry field
    search_btn = tk.Button(popup, bg="dodgerblue", text="Search", command=search_product)
    search_btn.pack(pady=10)

    listbox = tk.Listbox(popup, bg="grey", height=6, width=35)
    listbox.pack(pady=10)
    listbox.bind('<<ListboxSelect>>', on_select)
    selected_label = tk.Label(popup, textvariable=selected_product, bg="skyblue", font=("Arial", 10, "italic"))
    selected_label.pack(pady=5)
    delete_button = tk.Button(popup, text="Delete Product", bg="dodgerblue", command=delete_selected)
