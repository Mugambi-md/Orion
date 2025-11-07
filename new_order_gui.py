import re
import tkinter as tk
from datetime import date
import tkinter.font as tkFont
from tkinter import ttk, messagebox
from base_window import BaseWindow
from lookup_gui import ProductSearchWindow
from windows_utils import to_uppercase, auto_format_date
from working_on_orders import (
    insert_order_data, fetch_order_product, search_product_codes
)


class NewOrderWindow(BaseWindow):
    def __init__(self, master, conn, user):
        self.master = tk.Toplevel(master)
        self.master.title("Receive New Order")
        self.center_window(self.master, 1200, 700, master)
        self.master.configure(bg="lightgreen")
        self.master.transient(master)
        self.master.grab_set()

        self.user = user
        self.conn = conn
        self.order_items = []
        self.total_amount = 0
        # Bold Table Headings and content font
        style = ttk.Style(self.master)
        style.configure("Treeview", font=("Arial", 10))
        style.configure(
            "Treeview.Heading", font=("Arial", 11, "bold", "underline")
        )
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.left_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.customer_name_entry = tk.Entry(
            self.left_frame, bd=2, relief="raised", font=("Arial", 11),
            width=23
        )
        self.contact_entry = tk.Entry(
            self.left_frame, bd=2, relief="raised", font=("Arial", 11),
            width=12
        )
        self.deadline_entry = tk.Entry(
            self.left_frame, bd=2, relief="raised", font=("Arial", 11),
            width=11
        )
        # Next Button
        self.next_button = tk.Button(
            self.left_frame, text="Next", command=self.handle_next, width=10,
            bd=4, relief="solid"
        )
        self.search_section = tk.Frame(self.left_frame, bg="lightblue")
        self.product_code_entry = tk.Entry(
            self.search_section, bd=2, relief="raised", font=("Arial", 11)
        )
        self.suggestions_listbox = tk.Listbox(self.search_section, bg="lightgray")
        self.search_button = tk.Button(
            self.search_section, text="Search", command=self.search_product
        )
        self.quantity_entry = tk.Entry(
            self.search_section, bd=2, relief="raised", font=("Arial", 11),
            width=8
        )
        self.add_button = tk.Button(
            self.search_section, text="Add to Order", bd=4, relief="solid",
            command=self.add_to_order
        )
        self.submit_button = tk.Button(
            self.search_section, text="Submit Order", bd=4, relief="solid",
            command=self.submit_order
        )
        self.product_name_var = tk.StringVar()
        self.wholesale_price_var = tk.StringVar()
        self.retail_price_var = tk.StringVar()
        self.right_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.button_frame = tk.Frame(self.right_frame, bg="lightblue")
        self.delete_btn = tk.Button(
            self.button_frame, text="Delete Item", bd=4, relief="solid",
            command=self.delete_selected_item
        )
        self.columns = [
            "No.", "Product Code", "Product Name", "Quantity", "Unit Price",
            "Total Price"
        ]
        self.tree = ttk.Treeview(self.right_frame, columns=self.columns,
                                 show="headings", selectmode="browse")
        self.total_label = tk.Label(
            self.right_frame, text="Total Cost: KES 0.00", fg="red",
            font=("Arial", 13, "bold")
        )
        (self.product_name, self.wholesale_price,
         self.retail_price) = None, None, None


        self.build_ui()
    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.left_frame.pack(side="left", fill="y")
        # Customer Info (2 - columns: label top, entry below)
        tk.Label(
            self.left_frame, text="Customer Name:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, padx=5, pady=(5, 2))
        self.customer_name_entry.grid(row=1, column=0, padx=(5, 0), pady=2)
        self.customer_name_entry.focus_set()
        self.customer_name_entry.bind(
            "<Return>", lambda e: self.contact_entry.focus_set()
        )
        self.customer_name_entry.bind(
            "<KeyRelease>", self.capitalize_customer_name
        )
        tk.Label(
            self.left_frame, text="Contact:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=1, padx=5, pady=(5, 2))
        self.contact_entry.grid(row=1, column=1, pady=2)
        self.contact_entry.bind(
            "<Return>", lambda e: self.deadline_entry.focus_set()
        )
        tk.Label(
            self.left_frame, text="Deadline:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=2, padx=5, pady=(5, 2))
        self.deadline_entry.grid(row=1, column=2, padx=(0, 5), pady=2)
        self.deadline_entry.bind("<KeyRelease>", auto_format_date)
        self.deadline_entry.bind("<Return>", lambda e: self.handle_next())
        self.next_button.grid(row=2, column=0, columnspan=3, padx=5, pady=2)
        tk.Label(self.left_frame, text="", bg="lightblue"
                 ).grid(row=3, column=0, columnspan=3, pady=5)
        # Product search section (initially hidden)
        self.search_section.columnconfigure(0, weight=1)
        self.search_section.columnconfigure(1, weight=1)
        tk.Label(
            self.search_section, text="Enter Product Code:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, padx=5, pady=2)
        self.product_code_entry.bind(
            "<KeyRelease>", lambda event: to_uppercase(self.product_code_entry)
        )
        self.product_code_entry.grid(row=1, column=0, padx=5, pady=2)
        self.suggestions_listbox.grid(row=2, column=0, sticky="we", padx=5)
        self.suggestions_listbox.bind(
            "<<ListboxSelect>>", self.fill_selected_code
        )
        self.suggestions_listbox.grid_remove()
        self.product_code_entry.bind("<KeyRelease>", self.update_suggestions)
        self.product_code_entry.bind(
            "<Return>", lambda e: self.search_product()
        )
        self.search_button.grid(row=2, column=0, pady=5)
        self.search_button.bind("<Return>", lambda e: self.search_product)
        tk.Label(
            self.search_section, text="Quantity:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=1, padx=5, pady=2)
        self.quantity_entry.grid(row=1, column=1, padx=5, pady=2)
        self.add_button.grid(row=2, column=1, pady=5)
        self.submit_button.grid(row=3, column=0, columnspan=2, pady=10)
        self.submit_button.grid_remove()
        tk.Button(
            self.left_frame, text="Look Up Products", bg="green",
            bd=4, relief="solid", command=self.lookup_items
        ).grid(row=7, column=0, columnspan=3)
        self.right_frame.pack(side="right", fill="both", expand=True)
        self.button_frame.pack(fill=tk.X, pady=(0, 2))
        tk.Label(
            self.button_frame, text="Order Items List.", bg="lightblue",
            font=("Arial", 15, "bold", "underline")
        ).pack(pady=5, anchor="center")
        self.delete_btn.pack(side=tk.RIGHT, padx=5)
        self.delete_btn.pack_forget()
        for col in self.columns:
            self.tree.heading(col, text=col)
            width = 30 if col == "No." else 50
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(expand=True, fill=tk.BOTH)
        self.total_label.pack(side=tk.RIGHT,padx=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_selection_change)
        
    def on_tree_selection_change(self, event=None):
        selected = self.tree.selection()
        if selected:
            self.delete_btn.pack(side=tk.RIGHT, padx=5)
        else:
            self.delete_btn.pack_forget()

    def delete_selected_item(self):
        selected = self.tree.selection()
        if not selected:
            return
        item_values = self.tree.item(selected[0], 'values')
        if not item_values:
            return
        code = item_values[0]
        try:
            item_cost = float(item_values[4].replace(",", ""))
            self.total_amount -= item_cost
        except (IndexError, ValueError):
            pass
        self.tree.delete(selected[0])
        self.order_items = [
            item for item in self.order_items if item['product_code'] != code
        ]
        self.delete_btn.pack_forget()
        self.total_label.config(
            text=f"Total Cost: KES {self.total_amount:,.2f}"
        )
        for i, iid in enumerate(self.tree.get_children(), start=1):
            values = list(self.tree.item(iid, "values"))
            if values:
                values[0] = i # update No.
                self.tree.item(iid, values=values)
        messagebox.showinfo(
            "Success",
            "Product Successfully Removed From Order.", parent=self.master
        )

    def capitalize_customer_name(self, event=None):
        widget = event.widget
        name = widget.get()
        cursor_position = widget.index(tk.INSERT)
        capitalized = ' '.join(word.capitalize() for word in name.split(' '))
        if name != capitalized:
            widget.delete(0, tk.END)
            widget.insert(0, capitalized)
            widget.icursor(cursor_position)

    def add_to_order(self):
        try:
            code = self.product_code_entry.get().upper()
            qty = int(self.quantity_entry.get())
            if not code or qty <=0:
                messagebox.showerror(
                    "Input Error",
                    "Enter Valid Item Code and Quantity.", parent=self.master
                )
                return
            existing_item = next(
                (item for item in self.order_items if item['product_code'] == code),
                None
            )
            if existing_item:
                for iid in self.tree.get_children():
                    values = self.tree.item(iid, 'values')
                    if values[0] == code:
                        self.tree.delete(iid)
                        break
                # Remove old item from list and update total
                self.total_amount -= existing_item['total_price']
                self.order_items.remove(existing_item)
                qty += existing_item['quantity']
            unit_price = self.wholesale_price if qty >= 10 else self.retail_price
            formated_price = f"{unit_price:,}"
            total = unit_price * qty
            formated_total = f"{total:,}"
            index_no = len(self.tree.get_children()) + 1
            # Add updated item
            name = re.sub(r"\s+", " ", str(self.product_name)).strip()
            self.tree.insert("", "end", values=(
                index_no, code, name, qty, formated_price, formated_total
            ))
            self.order_items.append({
                "product_code": code,
                "product_name": self.product_name,
                "quantity": qty,
                "unit_price": unit_price,
                "total_price": total
            })
            # Update total label
            self.total_amount += total
            self.total_label.config(
                text=f"Total Cost: KES {self.total_amount:,.2f}"
            )
            # Ask to add more
            another = messagebox.askyesno(
                "More", "Do You Want to Add Product?", parent=self.master
            )
            if another:
                self.product_code_entry.config(state="normal")
                self.quantity_entry.config(state="normal")
                self.product_code_entry.delete(0, tk.END)
                self.quantity_entry.delete(0, tk.END)
                self.product_code_entry.focus()
                self.product_code_entry.bind(
                    "<Return>", lambda e: self.search_product()
                )
                self.submit_button.grid_remove()
            else:
                self.search_button.config(state="disabled")
                self.product_code_entry.config(state="disabled")
                self.quantity_entry.config(state="disabled")
                self.add_button.config(state="disabled")
                self.submit_button.grid(row=4, column=0, columnspan=2,
                                        pady=10)
                self.submit_button.focus_set()
                self.submit_button.bind(
                    "<Return>", lambda e: self.submit_order()
                )
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.master)

    def update_suggestions(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return"):
            return
        text = self.product_code_entry.get().strip().upper()
        self.product_code_entry.delete(0, tk.END)
        self.product_code_entry.insert(0, text)
        if not text:
            self.suggestions_listbox.grid_remove()
            return
        results = search_product_codes(self.conn, text)
        self.suggestions_listbox.delete(0, tk.END)
        if results:
            for item in results:
                display = f"{item['product_code']} - {item['product_name']}"
                self.suggestions_listbox.insert(tk.END, display)
            # Set min and max height for usability
            height = min(len(results), 10)
            self.suggestions_listbox.configure(height=height)
            self.search_button.grid_remove()
            self.suggestions_listbox.grid(
                row=2, column=0, sticky="we", padx=5
            )
        else:
            self.suggestions_listbox.grid_remove()
            self.search_button.grid(row=2, column=0, pady=5)

    def fill_selected_code(self, event=None):
        try:
            selection = self.suggestions_listbox.get(
                self.suggestions_listbox.curselection())
            code = selection.split(" - ")[0]
            self.product_code_entry.delete(0, tk.END)
            self.product_code_entry.insert(0, code)
            self.suggestions_listbox.delete(0, tk.END)
            self.suggestions_listbox.grid_remove()
            self.search_button.grid(row=2, column=0, pady=5)
            self.search_button.focus_set()
        except:
            pass
    
    
    def handle_next(self):
        name = self.customer_name_entry.get()
        contact = self.contact_entry.get()
        deadline = self.deadline_entry.get()
        if not name or not contact or not deadline:
            messagebox.showwarning(
                "Missing Info",
                "Please fill all customer fields.", parent=self.master
            )
            return
        self.customer_name_entry.config(state="disabled")
        self.contact_entry.config(state="disabled")
        self.deadline_entry.config(state="disabled")
        self.next_button.config(state="disabled")
        self.search_section.grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=5
        )
        self.product_code_entry.focus_set()

    def search_product(self):
        code = self.product_code_entry.get().upper()
        try:
            result = fetch_order_product(code)
            self.product_name = result["product_name"]
            self.wholesale_price = float(result["wholesale_price"])
            self.retail_price = float(result["retail_price"])
            name = self.product_name
            answer = messagebox.askyesno(
                "Confirm", f"Add '{name}' to order?", parent=self.master
            )
            if answer:
                self.quantity_entry.focus_set()
                self.quantity_entry.bind(
                    "<Return>", lambda e: self.add_to_order()
                )
            else:
                self.product_code_entry.delete(0, tk.END)
                self.product_code_entry.focus_set()
        except ValueError as ve:
            messagebox.showerror(
                "Product Not Found", str(ve), parent=self.master
            )
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self.master)
    
    
    def submit_order(self):
        if not self.order_items:
            messagebox.showwarning(
                "Missing", "No items in Order List.", parent=self.master
            )
            return
        def continue_submission(paid_amount, cash, mpesa):
            balance = self.total_amount - paid_amount
            payment = {
                "total_amount": self.total_amount,
                "paid_amount": paid_amount,
                "balance": balance,
                "method": f"Cash: {cash}, Mpesa: {mpesa}"
            }
            customer_name = self.customer_name_entry.get()
            contact = self.contact_entry.get()
            deadline = self.deadline_entry.get()
            order_data = {
                "customer_name": customer_name,
                "contact": contact,
                "date_placed": str(date.today()),
                "deadline": deadline,
                "amount": self.total_amount
            }
            confirm_post = messagebox.askyesno(
                "Post Order",
                "Do you want to post this order?", parent=self.master
            )
            if confirm_post:
                result = insert_order_data(
                    self.conn, order_data, self.order_items, self.user,
                    payment
                )
                if result:
                    messagebox.showinfo("Result", result, parent=self.master)
                    self.customer_name_entry.config(state="normal")
                    self.contact_entry.config(state="normal")
                    self.deadline_entry.config(state="normal")
                    self.next_button.config(state="normal")
                    self.customer_name_entry.delete(0, tk.END)
                    self.contact_entry.delete(0, tk.END)
                    self.deadline_entry.delete(0, tk.END)
                    self.customer_name_entry.focus_set()
                    self.product_code_entry.config(state="normal")
                    self.quantity_entry.config(state="normal")
                    self.product_code_entry.delete(0, tk.END)
                    self.quantity_entry.delete(0, tk.END)
                    self.search_section.grid_remove()
                    self.submit_button.grid_remove()
                    # Delete all items from treeview
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                    self.order_items.clear()
                    self.total_amount = 0
                    self.total_label.config(text="Total Cost: KES 0.00")
                    # Hide delete button again
                    self.delete_btn.pack_forget()

        wants_to_pay = messagebox.askyesno(
            "Payment", "Do you want to pay the order?", parent=self.master
        )
        if wants_to_pay:
            self.payment_dialog(continue_submission)
        else:
            confirm = messagebox.askyesno(
                "Post Order",
                "Post this Order Without Payment?", parent=self.master
            )
            if confirm:
                continue_submission(0, 0, 0)

    def payment_dialog(self, on_complete_callback):
        """Custom dialog for entering Cash and Mpesa amounts."""
        dialog = tk.Toplevel(self.master)
        dialog.title("Payment Details")
        dialog.configure(bg="lightgreen")
        dialog.grab_set()
        self.center_window(dialog, 250, 200, self.master)

        # Labels and Entries
        tk.Label(
            dialog, text="Cash:", bg="lightgreen", font=("Arial", 11, "bold")
        ).grid(row=0, column=0, pady=5, padx=(5, 0), sticky="e")
        cash_entry = tk.Entry(dialog, bd=2, relief="raised",
                              font=("Arial", 11))
        cash_entry.grid(row=0, column=1, padx=(0, 5), pady=5)
        cash_entry.focus_set()
        tk.Label(
            dialog, text="Mpesa:", bg="lightgreen", font=("Arial", 11, "bold")
        ).grid(row=1, column=0, pady=5, padx=(5, 0), sticky="e")
        mpesa_entry = tk.Entry(dialog, bd=2, relief="raised",
                               font=("Arial", 11))
        mpesa_entry.grid(row=1, column=1, padx=(0, 5), pady=5)
        # Button Frame
        button_frame = tk.Frame(dialog, bg="lightgreen")
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        def on_ok():
            try:
                cash = float(cash_entry.get() or 0)
                mpesa = float(mpesa_entry.get() or 0)
                paid_amount = cash + mpesa
                dialog.destroy()
                on_complete_callback(paid_amount, cash, mpesa)
            except ValueError:
                messagebox.showerror(
                    "Error", "Please Enter Valid Amount.", parent=dialog
                )
        def on_cancel():
            dialog.destroy()

        tk.Button(
            button_frame, text="OK", width=8, command=on_ok
        ).pack(side="left", padx=10)
        tk.Button(
            button_frame, text="Cancel", width=8, command=on_cancel
        ).pack(side="right", padx=10)
        # Keyboard shortcuts
        cash_entry.bind("<Return>", lambda e: mpesa_entry.focus_set())
        mpesa_entry.bind("<Return>", lambda e: on_ok())

    def lookup_items(self):
        ProductSearchWindow(self.master, self.conn)

    def resize_columns(self):
        font = tkFont.Font()  # Auto-size columns
        for col in self.columns:
            max_width = font.measure(col)  # Start with header width
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                width = font.measure(text)
                if width > max_width:
                    max_width = width
            self.tree.column(col, width=max_width)



if __name__ == "__main__":
    from connect_to_db import connect_db
    conn = connect_db()
    root = tk.Tk()
    NewOrderWindow(root, conn, "Sniffy")
    root.mainloop()