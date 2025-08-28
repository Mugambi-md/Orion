import tkinter as tk
import re
import string
from tkinter import messagebox
from PIL import Image, ImageTk
from windows_utils import DateFormatter
from dashboard import OrionDashboard
from connect_to_db import connect_db
from base_window import BaseWindow
from datetime import date, datetime, timedelta
from working_on_employee import fetch_logins_by_username, update_login_password

class MugambiPOSApp(BaseWindow):
    def __init__(self, master):
        self.master = master
        self.conn = connect_db()
        self.master.title("POS System")
        self.center_window(self.master, 600, 400)
        self.master.resizable(False, False)
        # Load background image
        self.original_bg = Image.open("ground.jpg")
        self.bg_image = ImageTk.PhotoImage(self.original_bg)
        # Background Label

        self.bg_label = tk.Label(master)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.master.bind("<Configure>", self.resize_background) # Bind resizing
        self.title_label = tk.Label(
            master, text="MUGAMBI\nPoint of Sale System",
            font=("Arial", 18, "bold"), fg="white", bg="black"
        ) # Title Label
        self.title_label.pack(pady=10, anchor="center")
        self.date_frame = tk.Frame(master, bg="lightblue")
        day = DateFormatter.get_today_formatted()
        self.date_label = tk.Label(
            self.date_frame, text=day, font=("Arial", 14, "bold"),
            fg="dodgerblue", anchor="center"
        )
        self.date_label.pack(anchor="center")
        self.version_frame = tk.Frame(master, bg="#222222")
        self.version_frame.pack(fill='x', pady=(10, 0), side="bottom")
        self.version_label = tk.Label(
            self.version_frame, text="POS System V1.0",
            font=("Arial", 10, "italic"), fg="white", bg="black"
        )
        self.version_label.pack(padx=10, anchor="center") # Version Label
        self.bottom_frame = tk.Frame(
            self.version_frame, bg="lightgray", bd=2, relief="ridge"
        ) # Buttons Frame
        self.bottom_frame.pack(side="bottom", fill="x", ipady=20)
        self.login_btn = tk.Button(
            self.bottom_frame, text="LOGIN", font=("Arial", 14),
            command=self.login
        )
        self.login_btn.pack(side="left", expand=True, fill='both')
        self.admin_btn = tk.Button(self.bottom_frame, text="MAINTENANCE",
                                   font=("Arial", 14), command=self.admin)
        self.admin_btn.pack(side="left", expand=True, fill='both')
        self.exit_btn = tk.Button(
            self.bottom_frame, text="EXIT", font=("Arial", 14),
            command=self.master.quit
        )
        self.exit_btn.pack(side="left", expand=True, fill='both')
        self.date_frame.pack(pady=(10, 5), padx=10, side="bottom")

    def resize_background(self, event):
        resized = self.original_bg.resize((event.width, event.height), Image.Resampling.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(resized)
        self.bg_label.config(image=self.bg_image) # type: ignore
        self.bg_image.image = self.bg_image

    def login(self):
        login_window = tk.Toplevel(self.master)
        login_window.title("Login")
        self.center_window(login_window, 200, 150)
        login_window.resizable(False, False)
        login_window.configure(bg="lightgray")
        login_window.transient(self.master)
        label_frame = tk.Frame(login_window, bg="lightgray")
        label_frame.grid(row=0, column=0, columnspan=2)
        tk.Label(
            label_frame, text="Enter Username and Password.", bg="lightgray",
            font=("Arial", 10, "italic"), fg="blue"
        ).pack(anchor="center")
        # Username
        username_label = tk.Label(
            login_window, text="Username:",bg="lightgray"
        )
        username_label.grid(row=1, column=0, padx=2, pady=5, sticky="e")
        username_entry = tk.Entry(login_window)
        username_entry.grid(row=1, column=1, padx=2, pady=5)
        username_entry.focus_set()
        username_entry.bind("<Return>", lambda e: pass_entry.focus_set())
        # Password
        pass_label = tk.Label(login_window, text="Password:", bg="lightgray")
        pass_label.grid(row=2, column=0, pady=5, padx=2, sticky="e")
        pass_entry = tk.Entry(login_window, show="*")
        pass_entry.grid(row=2, column=1, padx=2, pady=5)
        pass_entry.bind("<Return>", lambda e: login_btn.focus_set())
        def has_six_consecutive_same_chars(password):
            return re.search(r'(.)\1{5}', password) is not None
        def handle_login():
            username = username_entry.get().strip().lower()
            typed_password = pass_entry.get()
            login_info = fetch_logins_by_username(self.conn, username)
            access = login_info['access']
            password = login_info['password']
            if not login_info:
                messagebox.showwarning("Invalid",
                                       "Invalid Username or Password")
                username_entry.delete(0, tk.END)
                pass_entry.delete(0, tk.END)
                username_entry.focus_set()
                return
            if typed_password != login_info['password']:
                messagebox.showwarning("Invalid",
                                       "Invalid Username or Password")
                username_entry.delete(0, tk.END)
                pass_entry.delete(0, tk.END)
                username_entry.focus_set()
                return
            if login_info['status'] == 'disabled':
                messagebox.showwarning("Access Denied",
                                       "Please Consult System Administrator.")
                return
            date_created = datetime.strptime(login_info['date_created'], "%Y-%m-%d").date()
            if date.today() - date_created > timedelta(days=30):
                messagebox.showinfo("Password Expired", "Please Update Your Password.")
                self.update_pass_window(username, password)
                login_window.destroy()
            if has_six_consecutive_same_chars(password):
                messagebox.showinfo("Password Expired", "Please Update Your Password.")
                self.update_pass_window(username, password)
                login_window.destroy()
            else:
                messagebox.showinfo("Success", f"Welcome {username}.")
                login_window.destroy()
                OrionDashboard(self.master, username, access)

        login_btn = tk.Button(login_window, text="Login", width=20, command=handle_login)
        login_btn.grid(row=3, column=0, columnspan=2, pady=5)
        login_btn.bind("<Return>", lambda e: handle_login())
    def admin(self):
        login_window = tk.Toplevel(self.master)
        tk.Label(login_window, text="Maintenance window coming soon.", font=("Arial", 12, "italic"), bg="lightgreen").pack()
        messagebox.showinfo("Admin", "Admin Button Clicked.")

    def update_pass_window(self, username, current_password):
        window = tk.Toplevel(self.master)
        window.title("Update Password")
        self.center_window(window, 250, 150)
        window.configure(bg="lightgray")
        window.resizable(False, False)
        window.transient(self.master)
        # Labels and entries
        labels = ["Current Password:", "New Password:", "Confirm Password:"]
        entries = []
        for i, text in enumerate(labels):
            tk.Label(window, text=text, bg="lightgray").grid(row=i, column=0, pady=5, padx=2, sticky="e")
            entry = tk.Entry(window, show="*")
            entry.grid(row=i, column=1, padx=2, pady=5)
            entries.append(entry)
        current_entry, new_entry, confirm_entry = entries
        current_entry.focus_set()
        current_entry.bind("<Return>", lambda e: new_entry.focus_set())
        new_entry.bind("<Return>", lambda e: confirm_entry.focus_set())
        confirm_entry.bind("<Return>", lambda e: update_action())
        def is_strong_password(password):
            return (
                len(password) >= 6 and any(c.isupper() for c in password) and any(c.isdigit() for c in password) and
                any(c in string.punctuation for c in password)
            )
        def update_action():
            current = current_entry.get()
            new_pass = new_entry.get()
            confirm = confirm_entry.get()
            if current != current_password:
                messagebox.showerror("Error", "Invalid Current Password.")
                return
            if not is_strong_password(new_pass):
                messagebox.showwarning("Weak Password", "Password Must be At Least 6 characters long and include:\n- At least one uppercase\n- One number\n- One punctuation mark.")
                return
            if new_pass != confirm:
                messagebox.showerror("Mismatch", "New Password do not match.")
                return
            msg = update_login_password(self.conn, username, new_pass)
            if msg == "Password updated successfully.":
                messagebox.showinfo("Success", f"{msg} For {username}")
                window.destroy()
                self.login()
        tk.Button(window, text="Update Password",bg="blue", width=20,
                  command=update_action).grid(row=3, column=0, columnspan=2, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = MugambiPOSApp(root)
    root.mainloop()