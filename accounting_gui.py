import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from working_on_accounting import fetch_chart_of_accounts
from account_popups import (
    ViewJournalWindow, OpeningBalancePopup, JournalEntryPopup, InsertAccountPopup, ReverseJournalPopup,
    TrialBalanceWindow, IncomeStatementWindow, CashFlowStatementWindow, BalanceSheetWindow, CloseYearPopup
)

class AccountWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Account Management")
        self.center_window(self.window, 1000, 500, parent)
        self.window.configure(bg="lightblue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.left_frame = tk.Frame(self.window, width=200, bg="lightblue")
        self.right_frame = tk.Frame(self.window, bg="lightblue")
        self.table_frame = tk.Frame(self.right_frame, bg="lightblue")
        self.columns = ("No", "Code", "Account Name", "Account Type", "Description")
        self.tree = ttk.Treeview(self.table_frame, columns=self.columns, show="headings")

        self.build_ui()
        self.populate_accounts()

    def build_ui(self):
        # Frames
        self.left_frame.pack(side="left", fill="y")
        self.right_frame.pack(side="right", fill="both", expand=True)
        title_label = tk.Label(self.right_frame, text="Available Journal Accounts", font=("Arial", 16, "bold"),
                               bg="lightblue")
        title_label.pack(pady=(5, 0), anchor="center")
        self.table_frame.pack(fill="both", expand=True, padx=(0, 5), pady=(0, 5))
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=50, anchor="center")
        # Scrollbars
        y_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        # Bind Mousewheel for scrolling
        self.tree.bind("<MouseWheel>", lambda event: self.tree.yview_scroll(int(-1 * (event.delta/120)), "units"))
        # Buttons
        buttons = [
            ("Create Journal Account", self.new_journal_account),
            ("Initial Account Balances", self.initial_balances),
            ("Write Journal Entry", self.write_journal_entry),
            ("Reverse/Delete Journal", self.reverse_journal),
            ("View Journals", self.view_journal),
            ("Cash Flow Statement", self.view_cash_flow),
            ("Income Statement", self.view_income_statement),
            ("View Trial Balance", self.view_trial_balance),
            ("Balance Sheet", self.view_balance_sheet),
            ("Close Accounting Period", self.year_end)
        ]
        tk.Label(self.left_frame, text="", bg="lightblue").pack(pady=10)
        for text, command in buttons:
            btn = tk.Button(self.left_frame, text=text, command=command, width=20)
            btn.pack(pady=5, padx=2)

    def populate_accounts(self):
        accounts, _ = fetch_chart_of_accounts(self.conn)
        if isinstance(accounts, str):
            messagebox.showerror("Error", accounts)
            return
        for i, acc in enumerate(accounts, start=1):
            self.tree.insert("", "end", values=(
                i,
                acc["code"],
                acc["account_name"],
                acc["account_type"],
                acc["description"]
            ))
        self.auto_resize_columns()
    def auto_resize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            self.tree.column(col, width=font.measure(col) + 10)
        for col_index in range(len(self.columns)):
            max_width = 50
            for child in self.tree.get_children():
                val = self.tree.set(child, self.columns[col_index])
                width = font.measure(str(val)) + 10
                if width > max_width:
                    max_width = width
            self.tree.column(self.columns[col_index], width=max_width)

    def new_journal_account(self):
        priv = "Initial Balances"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        InsertAccountPopup(self.window, self.conn, self.user)

    def initial_balances(self):
        priv = "Initial Balances"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        OpeningBalancePopup(self.window, self.conn, self.user)
    def write_journal_entry(self):
        priv = "Insert Journal"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        JournalEntryPopup(self.window, conn, self.user)
    def reverse_journal(self):
        priv = "Reverse Journal"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        ReverseJournalPopup(self.window, self.conn, self.user)
    def view_journal(self):
        # Verify Access
        priv = "View Journal"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        ViewJournalWindow(self.window, self.conn)
    def view_cash_flow(self):
        # Verify Access
        priv = "View Cash Flow"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        CashFlowStatementWindow(self.window, self.conn)
    def view_income_statement(self):
        # Verify Access
        priv = "View Income Statement"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        IncomeStatementWindow(self.window, self.conn)
    def view_trial_balance(self):
        # Verify Access
        priv = "View Trial Balance"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        TrialBalanceWindow(self.window, self.conn, self.user)
    def view_balance_sheet(self):
        # Verify Access
        priv = "View Balance Sheet"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        BalanceSheetWindow(self.window, self.conn)
    def year_end(self):
        # Verify Access
        priv = "Close Accounting Books"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        CloseYearPopup(self.window, self.conn, self.user)

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root = tk.Tk()
    AccountWindow(root, conn, "sniffy")
    root.mainloop()