import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from working_sales import search_product
from authentication import VerifyPrivilegePopup
from working_on_stock import (
    restore_deleted_product, delete_product, search_deleted_product_codes
)


class DeleteProductPopup(BaseWindow):
    def __init__(self, master, conn, user, refresh=None, item_code=None):
        self.window = tk.Toplevel(master)
        self.window.title("Delete Product")
        self.center_window(self.window, 270, 200, master)
        self.window.configure(bg="skyblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.product_code_var = tk.StringVar()
        self.refresh = refresh if refresh else None
        self.products = None
        self.product_name = None
        self.main_frame = tk.Frame(
            self.window, bg="skyblue", bd=4, relief="solid"
        )
        self.entry_frame = tk.Frame(self.main_frame, bg="skyblue")
        self.entry = tk.Entry(
            self.entry_frame, textvariable=self.product_code_var, width=20,
            bd=2, relief="raised", font=("Arial", 11)
        )
        self.listbox = tk.Listbox(
            self.entry_frame, bg="lightgray", width=20, bd=2, relief="ridge",
            font=("Arial", 11)
        )
        # Delete button (initially hidden)
        self.delete_btn = tk.Button(
            self.main_frame, text="Delete Product", bd=4, relief="groove",
            bg="dodgerblue", fg="white", command=self.delete_selected,
            font=("Arial", 10, "bold")
        )


        self.setup_widgets()
        if item_code:
            self.product_code_var.set(item_code.upper())
            self.search_product()
            self.entry.icursor(tk.END)

    def setup_widgets(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Label and Entry
        l_text = "Deleting Product From Stock."
        tk.Label(
            self.main_frame, text=l_text, bg="skyblue", fg="red",
            font=("Arial", 12, "italic", "underline"), wraplength=250
        ).pack(pady=(10, 0), anchor="center")
        self.entry_frame.pack(padx=5)
        tk.Label(
            self.entry_frame, text="Enter Product Code:", bg="skyblue",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), padx=5)
        self.entry.pack(padx=5)
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self.uppercase_and_search)
        self.entry.bind("<Return>", lambda e: self.delete_selected())
        # Listbox
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.pack(padx=5)
        self.listbox.pack_forget()

    def uppercase_and_search(self, event=None):
        content = self.entry.get().upper()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, content)
        self.search_product()

    def search_product(self):
        self.listbox.delete(0, tk.END)
        product_code = self.product_code_var.get().strip()
        if not product_code:
            self.listbox.pack_forget()
            return
        try:
            results = search_product(self.conn, "product_code", product_code)
            if results:
                for product in results:
                    code = product['product_code']
                    name = product['product_name']
                    display = f"{code} - {name}"
                    self.products = results
                    self.listbox.insert(tk.END, display)
                self.listbox.config(height=min(len(results), 4))
                self.listbox.pack(padx=5)
            else:
                self.listbox.pack_forget()
        except Exception as err:
            messagebox.showerror(
                "Database Error", str(err), parent=self.window
            )

    def on_select(self, event):
        if self.listbox.curselection():
            index = self.listbox.curselection()[0]
            product = self.products[index]
            product_code = product["product_code"]
            self.product_code_var.set(product_code)
            self.product_name = product["product_name"]
            self.listbox.pack_forget()
            self.entry.icursor(tk.END)
            self.delete_btn.pack(pady=10)

    def delete_selected(self):
        # Verify Privilege
        priv = "Admin Delete Product"
        verify = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv
        )
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.window
            )
            return
        code = self.product_code_var.get().strip()
        if not code:
            messagebox.showerror(
                "No Product",
                "Please Enter a Valid Product Code.", parent=self.window
            )
            return
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete '{self.product_name}'; {code}?", default="no",
            parent=self.window
        )
        if confirm:
            try:
                success, msg = delete_product(self.conn, code, self.user)
                if success:
                    messagebox.showinfo("Deleted", msg, parent= self.window)
                    self.product_code_var.set("")
                    if self.refresh:
                        self.refresh()
                    self.window.destroy()
                else:
                    messagebox.showerror("Error", msg, parent=self.window)
                    self.entry.focus_set()
            except Exception as err:
                messagebox.showerror("Database Error", str(err))


class RestoreProductPopup(BaseWindow):
    def __init__(self, master, conn, user, callback=None, item_code=None):
        self.window = tk.Toplevel(master)
        self.window.title("Restore Product")
        self.center_window(self.window, 300, 200, master)
        self.window.configure(bg="skyblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.product_code_var = tk.StringVar()
        self.refresh = callback if callback else None
        self.products = None
        self.product_name = None
        self.main_frame = tk.Frame(
            self.window, bg="skyblue", bd=4, relief="solid"
        )
        self.entry_frame = tk.Frame(self.main_frame, bg="skyblue")
        self.entry = tk.Entry(
            self.entry_frame, textvariable=self.product_code_var, width=20,
            bd=2, relief="raised", font=("Arial", 11)
        )
        self.listbox = tk.Listbox(
            self.entry_frame, bg="lightgray", width=20, bd=2, relief="raised",
            font=("Arial", 11)
        )
        # Delete button (initially hidden)
        self.delete_btn = tk.Button(
            self.main_frame, text="Restore Product", bd=4, relief="raised",
            bg="dodgerblue", fg="white", command=self.restore_selected,
            font=("Arial", 10, "bold")
        )


        self.setup_widgets()
        if item_code:
            self.product_code_var.set(item_code.upper())
            self.search_product()
            self.entry.icursor(tk.END)

    def setup_widgets(self):
        """Widgets set up."""
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Label and Entry
        l_text = "Restore Deleted Product."
        tk.Label(
            self.main_frame, text=l_text, bg="skyblue", fg="red", bd=2,
            relief="groove", font=("Arial", 12, "italic", "underline")
        ).pack(pady=(10, 0), anchor="center")
        self.entry_frame.pack(padx=5)
        tk.Label(
            self.entry_frame, text="Enter Product Code:", bg="skyblue",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 0), padx=5)
        self.entry.pack(padx=5)
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self.uppercase_and_search)
        self.entry.bind("<Return>", lambda e: self.restore_selected())
        # Listbox
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.pack(padx=5)
        self.listbox.pack_forget()

    def uppercase_and_search(self, event=None):
        content = self.entry.get().upper()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, content)
        self.search_product()

    def search_product(self):
        self.listbox.delete(0, tk.END)
        product_code = self.product_code_var.get().strip()
        if not product_code:
            self.listbox.pack_forget()
            return
        try:
            results = search_deleted_product_codes(self.conn, product_code)
            if results:
                for product in results:
                    code = product['product_code']
                    name = product['product_name']
                    display = f"{code} - {name}"
                    self.products = results
                    self.listbox.insert(tk.END, display)
                self.listbox.config(height=min(len(results), 5))
                self.listbox.pack()
            else:
                self.listbox.pack_forget()
        except Exception as err:
            messagebox.showerror(
                "Database Error", str(err), parent=self.window
            )

    def on_select(self, event):
        if self.listbox.curselection():
            index = self.listbox.curselection()[0]
            product = self.products[index]
            product_code = product["product_code"]
            self.product_name = product["product_name"]
            self.product_code_var.set(product_code)
            self.listbox.pack_forget()
            self.entry.icursor(tk.END)
            self.delete_btn.pack(pady=10)

    def restore_selected(self):
        # Verify Privilege
        priv = "Admin Restore Product"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.window
            )
            return
        code = self.product_code_var.get().strip()
        if not code:
            messagebox.showerror(
                "No Product",
                "Please Enter a Valid Product Code.", parent=self.window
            )
            return
        confirm = messagebox.askyesno(
            "Confirm Restore",
            f"Restore '{code}'; {self.product_name}?", default="no",
            parent=self.window
        )
        if confirm:
            try:
                connect = self.conn
                user = self.user
                success, msg = restore_deleted_product(connect, code, user)
                if success:
                    messagebox.showinfo("Restored", msg, parent= self.window)
                    self.product_code_var.set("")
                    if self.refresh is not None:
                        self.refresh()
                    self.window.destroy()
                else:
                    messagebox.showerror("Error", msg, parent=self.window)
                    self.entry.focus_set()
            except Exception as err:
                messagebox.showerror(
                    "Database Error", str(err), parent=self.window
                )

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root=tk.Tk()
    RestoreProductPopup(root, conn, "sniffy")
    root.mainloop()