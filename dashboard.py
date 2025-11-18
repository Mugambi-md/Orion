import tkinter as tk
from tkinter import messagebox, Menu
from authentication import VerifyPrivilegePopup
from sales_report_gui import SalesGUI

from employee_gui_popup import ChangePasswordPopup

class OrionDashboard:
    def __init__(self, conn, user):
        self.window = tk.Toplevel()
        self.window.title("ORION STAR SYSTEM")
        self.window.iconbitmap("myicon.ico")
        self.window.configure(bg="blue")
        self.window.state("zoomed")
        # self.window.transient(master)
        self.window.grab_set()

        self.user = user
        self.conn = conn
        self.main_frame = tk.Frame(
            self.window, bg="blue", bd=4, relief="solid"
        )

        self.create_widgets()

    def create_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10)
        button_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        button_frame.pack(side="top", fill="x", padx=5, ipady=5, ipadx=5)
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
                button_frame, text=text, command=command, bg="dodgerblue",
                fg="white", bd=4, relief="groove", width=len(text), height=1,
                font=("Arial", 12, "bold")
            ).pack(side="left", ipadx=5)
        btn_frame = tk.Frame(button_frame, height=1)
        btn_frame.pack(side="left")
        power_btn = tk.Button(
            btn_frame, text="⭕", font=("Arial", 16, "bold"),
            fg="red", width=2, height=1, relief="ridge",
            command=self.window.destroy
        )
        power_btn.pack(side="left")
        arrow_btn = tk.Menubutton(
            btn_frame, text="▽", font=("Arial", 11), relief="ridge",
            anchor="sw", fg="#FF6666"
        )
        arrow_menu = Menu(arrow_btn, tearoff=0)
        arrow_menu.add_command(
            label="Log Out", command=self.window.destroy
        )
        arrow_menu.add_command(
            label="Change Password", command=self.change_password
        )
        arrow_btn.config(menu=arrow_menu)
        arrow_btn.pack(side="bottom")
        foot_frame = tk.Frame(self.window, bg="white", bd=2, relief="ridge")
        foot_frame.pack(side="bottom", fill="x", padx=10)
        tk.Label(
            foot_frame, text=f"User: {self.user}", bg="white",
            fg="#007BFF", font=("Arial", 9)
        ).pack(side="left", padx=(5, 40))
        footer = tk.Label(
            foot_frame, text="ORION SYSTEM v1.0", bg="white", fg="#007BFF",
            font=("Arial", 11)
        )
        footer.pack(side="left", padx=40)

    def has_privilege(self, privilege: str) -> bool:
        """Check if the current user has the required privilege."""
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You do not have permission to {privilege}.",
                parent=self.window
            )
            return False
        return True

    def sales_window(self):
        if not self.has_privilege("Export Products Records"):
            return
        SalesGUI(self.window, self.conn, self.user)

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
    app = OrionDashboard(conn, "Sniffy")
    root.mainloop()



