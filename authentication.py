import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from working_on_employee import fetch_password, get_assigned_privileges

class VerifyPrivilegePopup(simpledialog.Dialog):
    def __init__(self, master, conn, username, required_privilege):
        self.conn = conn
        self.username = username
        self.required_privilege = required_privilege
        self.result = None  # Will be 'granted' or 'denied'
        self.username_entry = None
        self.password_entry = None

        super().__init__(master, title="User Verification")

    def body(self, master):
        master.configure(bg="lightgreen")
        tk.Label(master, text="Username:", bg="lightgreen").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.username_entry = tk.Entry(master)
        self.username_entry.insert(0, self.username)
        self.username_entry.config(state="readonly")
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(master, text="Password:", bg="lightgreen").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.password_entry = tk.Entry(master, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        self.password_entry.bind("<Return>", self.check_credentials)
        self.password_entry.focus_set()

        return self.password_entry  # initial focus

    def check_credentials(self, event=None):
        entered_password = self.password_entry.get()
        stored_password = fetch_password(self.conn, self.username)
        if not stored_password or entered_password != stored_password[0]:
            messagebox.showerror("Access Denied", "Incorrect password.")
            self.result = "denied"
            self.cancel()
            return

        status, privileges, role, error = get_assigned_privileges(self.conn, self.username)
        if error:
            messagebox.showerror("Error", f"Failed to retrieve privileges:\n{error}")
            self.result = "denied"
            self.cancel()
            return
        if status is None:
            messagebox.showerror("Access Denied", "User not found.")
            self.result = "denied"
        elif status.lower() != "active":
            self.result = "denied"
        elif role is not None and role.lower() in ["admin", "manager"]:
            self.result = "granted"
        elif self.required_privilege.lower() not in [p.lower() for p in privileges]:
            self.result = "denied"
        else:
            self.result = "granted"
        self.cancel()  # Close the popup

    def apply(self):
        # When Ok button is clicked
        self.check_credentials()

    def cancel(self, event = None):
        if self.result is None:
            self.result = "denied"
        super().cancel(event)
