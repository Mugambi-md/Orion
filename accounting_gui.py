import tkinter as tk
from tkinter import ttk, messagebox
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from working_on_accounting import fetch_chart_of_accounts
from log_popups_gui import FinanceLogsWindow
from table_utils import TreeviewSorter
from windows_utils import ScrollableFrame
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
        self.center_window(self.window, 1100, 700, parent)
        self.window.configure(bg="lightblue")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.columns = (
            "No.", "Code", "Account Name", "Account Type", "Description"
        )
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.right_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.table_frame = tk.Frame(self.right_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No.")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()
        self.populate_accounts()

    def build_ui(self):
        # Frames
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        left_frame = tk.Frame(self.main_frame, width=200, bg="lightblue")
        left_frame.pack(side="left", fill="y")
        tk.Label(
            left_frame, text="Accounting Actions.", bg="lightblue", fg="green",
            font=("Arial", 14, "bold", "underline")
        ).pack(side="top", anchor="w", pady=(10, 0))
        btn_frame = ScrollableFrame(left_frame, "lightblue", 180)
        btn_frame.pack(side="left", fill="y")
        btn_area = btn_frame.scrollable_frame
        self.right_frame.pack(side="right", fill="both", expand=True)
        tk.Label(
            self.right_frame, text="Current Journal Accounts.", fg="blue",
            bg="lightblue", font=("Arial", 18, "bold", "underline")
        ).pack(pady=(3, 0), anchor="center")
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
        # Buttons
        buttons = [
            ("New Journal Account", self.new_journal_account),
            ("Initial Balances", self.initial_balances),
            ("Record Payments", self.write_journal_entry),
            ("Reverse Journal", self.reverse_journal),
            ("View Journals", self.view_journal),
            ("Cash Flow Statement", self.view_cash_flow),
            ("View Income Statement", self.view_income_statement),
            ("View Trial Balance", self.view_trial_balance),
            ("View Balance Sheet", self.view_balance_sheet),
            ("Close/End Year", self.year_end),
            ("Finance Logs", self.finance_logs_window)
        ]
        for text, action in buttons:
            tk.Button(
                btn_area, text=text, command=action, width=20, bd=4,
                bg="blue", fg="white", relief="groove",
                font=("Arial", 11, "bold")
            ).pack(ipady=5)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def populate_accounts(self):
        accounts, _ = fetch_chart_of_accounts(self.conn)
        if isinstance(accounts, str):
            messagebox.showerror("Error", accounts, parent=self.window)
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
        self.sorter.autosize_columns(5)

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
        privilege = "Make Payment"
        if not self.has_privilege(privilege):
            return
        JournalEntryPopup(self.window, self.conn, self.user)

    def reverse_journal(self):
        privilege = "Reverse Payment"
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
