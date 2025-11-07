import tkinter as tk
from tkinter import messagebox, Menu
from base_window import BaseWindow
from employee_gui_popup import ChangePasswordPopup

class OrionDashboard:
    def __init__(self, conn, user):
        self.window = tk.Toplevel()
        self.window.title("ORION STAR SYSTEM")
        self.window.iconbitmap("myicon.ico")
        self.window.configure(bg="#007BFF") # Blue Background
        # self.center_window(self.window, 1300, 650, master)
        self.window.state("zoomed")
        # self.window.transient(master)
        self.window.grab_set()

        self.user = user
        self.conn = conn

        self.create_widgets()

    def create_widgets(self):
        button_frame = tk.Frame(self.window, bg="#28A745") # Header Frame for Buttons
        button_frame.pack(side="top", fill="x")
        # Button Labels and their corresponding command
        buttons = {
            "Sales": self.sales_window,
            "Stock": self.stock_window,
            "Reports": self.reports_window,
            "Accounts": self.accounts_window,
            "Marketing": self.marketing_window,
            "Human Resource": self.hr_window
        }
        for text, command in buttons.items():
            tk.Button(
                button_frame, text=text, font=("Arial", 12, "bold"),
                width=len(text), height=1, fg="black",
                command=command, relief="raised", bd=4
            ).pack(side="left")
        btn_frame = tk.Frame(button_frame, bg="blue", height=1)
        btn_frame.pack(side="left")
        power_btn = tk.Button(
            btn_frame, text="⭕", font=("Arial", 16, "bold"), bg="blue",
            fg="red", width=2, height=1, relief="flat",
            command=self.window.destroy
        )
        power_btn.pack(side="left")
        arrow_btn = tk.Menubutton(
            btn_frame, text="▽", font=("Arial", 10), relief="flat", bg="blue", anchor="sw", fg="#FF6666")
        arrow_menu = Menu(arrow_btn, tearoff=0)
        arrow_menu.add_command(label="Log Out", command=self.window.destroy)
        arrow_menu.add_command(label="Change Password", command=self.change_password)
        arrow_btn.config(menu=arrow_menu)
        arrow_btn.pack(side="bottom")
        foot_frame = tk.Frame(self.window, bg="white")
        foot_frame.pack(side="bottom", fill="x")
        tk.Label(foot_frame, text=f"User: {self.user}", bg="white", fg="#007BFF").pack(side="left", padx=5)
        footer = tk.Label(foot_frame, text="ORION SYSTEM v1.0", bg="white", fg="#007BFF")
        footer.pack(side="left", padx=5)
    # Command methods
    def sales_window(self):
        messagebox.showinfo("Sales", "Sales Button Clicked.")
    def stock_window(self):
        messagebox.showinfo("Stock", "Stock Button Clicked.")
    def reports_window(self):
        messagebox.showinfo("Reports", "Reports Button Clicked.")
    def accounts_window(self):
        messagebox.showinfo("Accounts", "Accounts Button Clicked.")
    def marketing_window(self):
        messagebox.showinfo("Marketing", "Marketing Button Clicked.")
    def hr_window(self):
        messagebox.showinfo("Human Resource", "Human Resource Button Clicked.")
    def change_password(self):
        ChangePasswordPopup(self.window, self.conn, self.user)

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root = tk.Tk()
    root.withdraw()
    app = OrionDashboard(conn, "sniffy")
    root.mainloop()



