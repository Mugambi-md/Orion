import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime, timedelta
import string
from base_window import BaseWindow
from windows_utils import PasswordSecurity
from working_on_employee import (
    fetch_logins_by_username, update_login_password
)
from dashboard import SystemDashboard
from admin_gui import AdminWindow


class LoginWindow(BaseWindow):
    def __init__(self, master, conn, update_pass_callback=None):
        self.master = master
        self.window = tk.Toplevel(master)
        self.window.title("Employee Login")
        self.window.configure(bg="lightgray")
        self.center_window(self.window, 270, 150, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.update_pass = update_pass_callback
        self.username_entry = tk.Entry(
            self.window, bd=4, relief="raised", font=("Arial", 11), width=20
        )
        self.pass_entry = tk.Entry(
            self.window, bd=4, relief="raised", font=("Arial", 11), show="*",
            width=20
        )
        self.login_btn = tk.Button(
            self.window, text="Login", width=10, bg="blue", fg="white", bd=4,
            relief="groove", font=("Arial", 10, "bold"),
            command=self.handle_login
        )

        self.build_ui()

    def build_ui(self):
        # Info label
        label_frame = tk.Frame(self.window, bg="lightgray")
        label_frame.grid(row=0, column=0, columnspan=2)
        label_text = "Enter Valid Username and Password."
        tk.Label(
            label_frame, text=label_text, fg="blue", bg="lightgray",
            font=("Arial", 12, "italic", "underline")
        ).pack(anchor="center", pady=(3, 0))
        tk.Label(
            self.window, text="Username:", bg="lightgray",
            font=("Arial", 12, "bold")
        ).grid(row=1, column=0, padx=(5, 0), pady=5, sticky="e")
        self.username_entry.grid(row=1, column=1, padx=(0, 5), pady=5)
        self.username_entry.focus_set()
        tk.Label(
            self.window, text="Password:", bg="lightgray",
            font=("Arial", 12, "bold")
        ).grid(row=2, column=0, padx=(5, 0), pady=5, sticky="e")
        self.pass_entry.grid(row=2, column=1, pady=5, padx=(0, 5))
        self.username_entry.bind(
            "<Return>", lambda e: self.pass_entry.focus_set()
        )
        self.pass_entry.bind("<Return>", lambda e: self.login_btn.focus_set())
        self.login_btn.grid(row=3, column=0, columnspan=2, pady=5)
        self.login_btn.bind("<Return>", lambda e: self.handle_login())

    def handle_login(self):
        username = self.username_entry.get().strip().lower()
        typed_password = self.pass_entry.get()
        login_info = fetch_logins_by_username(self.conn, username)

        if not login_info:
            messagebox.showwarning(
                "Invalid", "Invalid Username or Password.", parent=self.window
            )
            self.reset_fields()
            return

        password = login_info["password"]
        if not password:
            messagebox.showwarning(
                "Invalid", "Invalid Username or Password.", parent=self.window
            )
            self.reset_fields()
            return
        if not PasswordSecurity.verify_password(typed_password, password):
            messagebox.showwarning(
                "Invalid", "Invalid Username or Password.", parent=self.window
            )
            self.reset_fields()
            return

        if login_info["status"] == "disabled":
            messagebox.showwarning(
                "Access Denied",
                "Please Consult System Administrator.", parent=self.window
            )
            return

        date_created = datetime.strptime(
            login_info["date_created"], "%Y-%m-%d"
        ).date()  # Password expiry (30 days)
        expired = date.today() - date_created > timedelta(days=30)
        weak_password = login_info["reset_pass"] == "true"
        # Weak Password and Expired Password
        if expired or weak_password:
            messagebox.showinfo(
                "Password Expired",
                "Please Update Your Password.", parent=self.window
            )
            self.update_pass(username, password)
            self.window.destroy()
            return

        # Success
        messagebox.showinfo(
            "Success", f"Welcome {username}.", parent=self.window
        )
        SystemDashboard(self.conn, username)
        self.window.destroy()

    def reset_fields(self):
        """Clear input and Refocus Username."""
        self.username_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)
        self.username_entry.focus_set()


class UpdatePasswordWindow(BaseWindow):
    def __init__(self, master, conn, username, password, callback):
        self.window = tk.Toplevel(master)
        self.window.title("Update Password")
        self.window.configure(bg="lightgray")
        self.center_window(self.window, 310, 180, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.username = username
        self.current_password = password
        self.callback = callback

        self.entries = {}

        self.build_ui()

    def build_ui(self):
        """Build UI for Password Update form."""
        labels = ["Current Password:", "New Password:", "Confirm Password:"]
        tk.Label(
            self.window, text="Update Password", bg="lightgray", fg="blue",
            font=("Arial", 12, "italic", "underline")
        ).pack(anchor="center", pady=(3, 0))
        input_frame = tk.Frame(
            self.window, bg="lightgray", bd=2, relief="groove"
        )
        input_frame.pack()
        for i, text in enumerate(labels):
            tk.Label(
                input_frame, text=text, font=("Arial", 12, "bold"),
                bg="lightgray"
            ).grid(row=i, column=0, padx=(3, 0), pady=5, sticky="e")
            entry = tk.Entry(
                input_frame, show="*", bd=4, relief="raised", width=19,
                font=("Arial", 12)
            )
            entry.grid(row=i, column=1, padx=(0, 3), pady=5)
            self.entries[text] = entry
        # Unpack for bindings
        current_entry = self.entries["Current Password:"]
        new_entry = self.entries["New Password:"]
        confirm_entry = self.entries["Confirm Password:"]
        current_entry.focus_set()
        current_entry.bind("<Return>", lambda e: new_entry.focus_set())
        new_entry.bind("<Return>", lambda e: confirm_entry.focus_set())
        confirm_entry.bind("<Return>", lambda e: self.update_action())

        tk.Button(
            input_frame, text="Update Password", bg="dodgerblue", fg="white",
            width=15, bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.update_action
        ).grid(row=3, column=0, columnspan=2, pady=(5, 0))

    @staticmethod
    def is_strong_password(password):
        """Check if password is strong."""
        return (
            len(password) >= 6 and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in string.punctuation for c in password)
        )
    def update_action(self):
        current = self.entries["Current Password:"].get()
        new_pass = self.entries["New Password:"].get()
        confirm = self.entries["Confirm Password:"].get()

        if not PasswordSecurity.verify_password(current, self.current_password):
            messagebox.showerror(
                "Error", "Invalid Current Password.", parent=self.window
            )
            return
        if PasswordSecurity.verify_password(new_pass, self.current_password):
            messagebox.showwarning(
                "No Changes",
                "Create New Password, Don't Use Existing Password.",
                parent=self.window
            )
            self.entries["New Password:"].focus_set()
            self.entries["New Password:"].selection_range(0, tk.END)
            self.entries["New Password:"].icursor(tk.END)
            return
        if new_pass != confirm:
            messagebox.showerror(
                "Mismatch", "New Password do not Match", parent=self.window
            )
            return

        if not self.is_strong_password(new_pass):
            messagebox.showwarning(
                "Weak Password",
                "Password must be at least 6 Characters long and include:\n"
                "- At Least one Uppercase letter\n"
                "- One Number\n"
                "- One Punctuation Mark.",
                parent=self.window
            )
            return
        success, msg = update_login_password(
            self.conn, self.username, new_pass
        )
        if success:
            messagebox.showinfo(
                "Success", f"{msg} for {self.username}", parent=self.window
            )
            self.callback()
            self.window.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self.window)


class AdminLoginWindow(BaseWindow):
    def __init__(self, master, conn, update_pass_callback=None):
        self.window = tk.Toplevel(master)
        self.window.title("Login")
        self.window.configure(bg="lightgray")
        self.center_window(self.window, 270, 150, master)
        self.window.transient(master)
        self.window.grab_set()

        self.parent = master
        self.conn = conn
        self.update_pass = update_pass_callback
        self.username_entry = tk.Entry(
            self.window, bd=4, relief="raised", font=("Arial", 12), width=20
        )
        self.pass_entry = tk.Entry(
            self.window, bd=4, relief="raised", font=("Arial", 12), show="*",
            width=20
        )
        self.login_btn = tk.Button(
            self.window, text="Login", bg="dodgerblue", fg="white", width=10,
            bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.handle_login
        )

        self.build_ui()

    def build_ui(self):
        # Info label
        label_frame = tk.Frame(self.window, bg="lightgray")
        label_frame.grid(row=0, column=0, columnspan=2)
        tk.Label(
            label_frame, text="Enter Valid Admin Logins.", bg="lightgray",
            font=("Arial", 13, "italic", "underline"), fg="blue"
        ).pack(anchor="center", pady=(3, 0))
        tk.Label(
            self.window, text="Username:", bg="lightgray",
            font=("Arial", 12, "bold")
        ).grid(row=1, column=0, padx=(5, 0), pady=5, sticky="e")
        self.username_entry.grid(row=1, column=1, padx=(0, 5), pady=5)
        self.username_entry.focus_set()
        tk.Label(
            self.window, text="Password:", bg="lightgray",
            font=("Arial", 12, "bold")
        ).grid(row=2, column=0, padx=(5, 0), pady=5, sticky="e")
        self.pass_entry.grid(row=2, column=1, pady=5, padx=(0, 5))
        self.username_entry.bind(
            "<Return>", lambda e: self.pass_entry.focus_set()
        )
        self.pass_entry.bind("<Return>", lambda e: self.login_btn.focus_set())
        self.login_btn.grid(row=3, column=0, columnspan=2, pady=(5, 0))
        self.login_btn.bind("<Return>", lambda e: self.handle_login())

    def handle_login(self):
        username = self.username_entry.get().strip().lower()
        typed_password = self.pass_entry.get()
        login_info = fetch_logins_by_username(self.conn, username)

        if not login_info:
            messagebox.showwarning(
                "Invalid", "Invalid Username or Password.", parent=self.window
            )
            self.reset_fields()
            return

        role = login_info["designation"]
        password = login_info["password"]
        if not PasswordSecurity.verify_password(typed_password, password):
            messagebox.showwarning(
                "Invalid", "Invalid Username or Password.", parent=self.window
            )
            self.reset_fields()
            return
        granted_roles = ["admin", "manager", "administrator"]
        if role.lower() not in granted_roles:
            messagebox.showwarning(
                "Restricted",
                "Login Only For Admin and Managers Only.\n"
                "Consult Admin or Your Supervisor.", parent=self.window
            )
            self.window.destroy()
            return
        if login_info["status"] == "disabled":
            messagebox.showwarning(
                "Access Denied",
                "Please Consult System Administrator.", parent=self.window
            )
            return

        date_created = datetime.strptime(
            login_info["date_created"], "%Y-%m-%d"
        ).date()  # Password expiry (30 days)
        expired = date.today() - date_created > timedelta(days=30)
        weak_password = login_info["reset_pass"] == "true"

        # Weak Password and Expired Password
        if expired or weak_password:
            messagebox.showinfo(
                "Password Expired",
                "Please Update Your Password.", parent=self.window
            )
            self.update_pass(username, password)
            self.window.destroy()
            return

        # Success
        messagebox.showinfo(
            "Success", f"Welcome {username}.", parent=self.window
        )
        AdminWindow(self.conn, username)
        self.window.destroy()


    def reset_fields(self):
        """Clear input and Refocus Username."""
        self.username_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)
        self.username_entry.focus_set()
