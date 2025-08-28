import tkinter as tk
from tkinter import messagebox
from base_window import BaseWindow
from  working_on_employee import fetch_password, get_assigned_privileges

class VerifyPrivilegePopup(BaseWindow):
    def __init__(self, master, conn, username, required_privilege):
        self.window = tk.Toplevel(master)
        self.window.title("User Verification")
        self.window.configure(bg="blue")
        self.center_window(self.window, 300, 150)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.username = username
        self.required_privilege = required_privilege
        self.result = None # Will be granted or denied
        self.username_var = tk.StringVar(value=username)
        self.password_var = tk.StringVar()

        self.build_ui()
        self.window.wait_window() # Wait until this window is closed

    def build_ui(self):
        tk.Label(self.window, text="Username:", bg="blue").pack(pady=(5, 0))
        username_entry = tk.Entry(self.window, textvariable=self.username_var)
        username_entry.pack()
        username_entry.select_range(0, tk.END)
        username_entry.icursor(tk.END)
        tk.Label(self.window, text="Password:", bg="blue").pack(pady=(5, 0))
        password_entry = tk.Entry(self.window, textvariable=self.password_var, show="*")
        password_entry.pack()
        password_entry.bind("<Return>", self.verify_user)
        password_entry.focus_set()

    def verify_user(self, event=None):
        password = self.password_var.get()
        stored_pass = fetch_password(self.conn, self.username)
        if not stored_pass or password != stored_pass[0]:
            messagebox.showerror("Access Denied", "Incorrect Password.")
            self.result = "denied"
            self.window.destroy()
            return
        status, privileges = get_assigned_privileges(self.conn, self.username)
        if status is None:
            messagebox.showerror("Access Denied", "User not found.")
            self.result = "denied"
        elif status.lower() != "active":
            messagebox.showerror("Account Disabled",
                                 "Your Account is currently Disabled.\nConsult System Admin or Manager.")
            self.result = "denied"
        if self.required_privilege.lower() not in [p.lower() for p in privileges]:
            messagebox.showwarning("Access Denied",
                                   f"You don't have privilege to '{self.required_privilege}'.")
            self.result = "denied"
        else:
            self.result = "granted"
        self.window.destroy()

# if __name__ == "__main__":
#     from connect_to_db import connect_db
#     conn = connect_db()
#     root = tk.Tk()
#     username = "johnie"
#     required_privilege = "add user"
#     popup = VerifyPrivilegePopup(master=root, conn=conn, username=username, required_privilege=required_privilege)
#     # root.wait_window(popup.window)
#     print("Popup Returned:", popup.result)
#     conn.close()