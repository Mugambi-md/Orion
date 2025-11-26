import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from working_on_accounting import fetch_chart_of_accounts
from log_popups_gui import FinanceLogsWindow
from account_popups import (
    ViewJournalWindow, OpeningBalancePopup, JournalEntryPopup,
    CloseYearPopup, InsertAccountPopup, ReverseJournalPopup,
    TrialBalanceWindow, IncomeStatementWindow, BalanceSheetWindow,
    CashFlowStatementWindow
)

class AccountWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Account Management")
        self.center_window(self.window, 1100, 650, parent)
        self.window.configure(bg="lightblue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 10))
        self.columns = (
            "No", "Code", "Account Name", "Account Type", "Description"
        )
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.left_frame = tk.Frame(
            self.main_frame, width=200, bg="lightblue"
        )
        self.right_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.table_frame = tk.Frame(self.right_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.populate_accounts()

    def build_ui(self):
        # Frames
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.left_frame.pack(side="left", fill="y")
        self.right_frame.pack(side="right", fill="both", expand=True)
        text = "Available Journal Accounts."
        tk.Label(
            self.right_frame, text=text, bg="lightblue", bd=2, relief="ridge",
            font=("Arial", 16, "bold", "underline")
        ).pack(pady=(5, 0), anchor="center", ipadx=10)
        self.table_frame.pack(fill="both", expand=True)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=30, anchor="center")
        # Scrollbars
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        # Bind Mousewheel for scrolling
        self.tree.bind("<MouseWheel>", lambda event: self.tree.yview_scroll(
            int(-1 * (event.delta/120)), "units"
        ))
        # Buttons
        buttons = [
            ("Create Journal\nAccount", self.new_journal_account),
            ("Initial Account\nBalances", self.initial_balances),
            ("Write Journal\nEntry", self.write_journal_entry),
            ("Reverse/Delete\nJournal", self.reverse_journal),
            ("View Journals", self.view_journal),
            ("Cash Flow\nStatement", self.view_cash_flow),
            ("Income Statement", self.view_income_statement),
            ("Trial Balance", self.view_trial_balance),
            ("Balance Sheet", self.view_balance_sheet),
            ("Close Accounting\nPeriod", self.year_end),
            ("Finance Logs", self.finance_logs_window)
        ]
        for text, command in buttons:
            tk.Button(
                self.left_frame, text=text, command=command, width=15, bd=2,
                relief="groove", bg="blue", fg="white",
                font=("Arial", 11, "bold")
            ).pack(ipady=5, padx=5)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def populate_accounts(self):
        accounts, _ = fetch_chart_of_accounts(self.conn)
        if isinstance(accounts, str):
            messagebox.showerror("Error", accounts)
            return
        for i, acc in enumerate(accounts, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                acc["code"],
                acc["account_name"],
                acc["account_type"],
                acc["description"]
            ), tags=(tag,))
        self.auto_resize_columns()

    def auto_resize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            self.tree.column(col, width=max_width + 5)

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

    def new_journal_account(self):
        # Verify user privilege
        if not self.has_privilege("Admin Create Journal"):
            return
        InsertAccountPopup(self.window, self.conn, self.user)

    def initial_balances(self):
        # Verify user privilege
        privilege = "Admin Initial Journal Balances"
        if not self.has_privilege(privilege):
            return
        OpeningBalancePopup(self.window, self.conn, self.user)

    def write_journal_entry(self):
        privilege = "Write Journal"
        if not self.has_privilege(privilege):
            return
        JournalEntryPopup(self.window, conn, self.user)

    def reverse_journal(self):
        privilege = "Reverse Journal"
        if not self.has_privilege(privilege):
            return
        ReverseJournalPopup(self.window, self.conn, self.user)

    def view_journal(self):
        # Verify Access
        privilege = "View Journal"
        if not self.has_privilege(privilege):
            return
        ViewJournalWindow(self.window, self.conn, self.user)

    def view_cash_flow(self):
        # Verify Access
        privilege = "View Cash Flow"
        if not self.has_privilege(privilege):
            return
        CashFlowStatementWindow(self.window, self.conn)

    def view_income_statement(self):
        # Verify Access
        privilege = "View Income Statement"
        if not self.has_privilege(privilege):
            return
        IncomeStatementWindow(self.window, self.conn)

    def view_trial_balance(self):
        # Verify Access
        privilege = "View Trial Balance"
        if not self.has_privilege(privilege):
            return
        TrialBalanceWindow(self.window, self.conn, self.user)

    def view_balance_sheet(self):
        # Verify Access
        privilege = "View Balance Sheet"
        if not self.has_privilege(privilege):
            return
        BalanceSheetWindow(self.window, self.conn)

    def year_end(self):
        # Verify Access
        privilege = "Admin Close Books"
        if not self.has_privilege(privilege):
            return
        CloseYearPopup(self.window, self.conn, self.user)

    def finance_logs_window(self):
        # Verify Access
        privilege = "View Finance Logs"
        if not self.has_privilege(privilege):
            return
        FinanceLogsWindow(self.window, self.conn, self.user)


if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root = tk.Tk()
    AccountWindow(root, conn, "sniffy")
    root.mainloop()