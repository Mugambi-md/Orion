import tkinter as tk
from tkinter import messagebox

class OrionDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ORION STAR SYSTEM")
        self.geometry("1300x650")
        self.minsize(800, 500)
        self.iconbitmap("myicon.ico")
        self.configure(bg="#007BFF") # Blue Background

        self.create_widgets()

    def create_widgets(self):
        button_frame = tk.Frame(self, bg="#28A745") # Header Frame for Buttons
        button_frame.pack(side="top", fill="x", pady=5)
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
            btn = tk.Button(
                button_frame, text=text, font=("Arial", 12, "bold"),
                width=len(text)+1, height=1, bg="white", fg="black",
                activebackground="#218838", activeforeground="white",
                command=command
            )
            btn.pack(side="left", padx=5, pady=10)
        foot_frame = tk.Frame(self, bg="white")
        foot_frame.pack(side="bottom", fill="x", pady=5)
        footer = tk.Label(foot_frame, text="ORION SYSTEM v1.0", bg="white", fg="#007BFF")
        footer.pack(side="left", padx=3, pady=5)
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

if __name__ == "__main__":
    app = OrionDashboard()
    app.mainloop()



