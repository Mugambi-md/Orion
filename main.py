import tkinter as tk
from PIL import Image, ImageTk
from windows_utils import DateFormatter
from connect_to_db import connect_db
from base_window import BaseWindow
from login_gui import LoginWindow, UpdatePasswordWindow, AdminLoginWindow


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
        """Open normal login window."""
        LoginWindow(
            self.master, self.conn,
            lambda username, current_password: self.update_password(
                username, current_password, "login"
            )
        )

    def admin(self):
        """Open admin login window."""
        AdminLoginWindow(
            self.master, self.conn,
            lambda username, current_password: self.update_password(
                username, current_password, "admin"
            )
        )

    def update_password(self, username, current_password, source):
        """
        Launch UpdatePasswordWindow with correct callback based on source.
        """
        if source == "login":
            callback = self.login
        elif source == "admin":
            callback = self.admin
        else:
            callback = None # Fallback
        UpdatePasswordWindow(
            self.master, self.conn, username, current_password, callback
        )



if __name__ == "__main__":
    root = tk.Tk()
    app = MugambiPOSApp(root)
    root.mainloop()