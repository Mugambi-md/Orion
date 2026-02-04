import tkinter as tk
from base_window import BaseWindow
from tkinter import ttk, messagebox
from datetime import datetime
from authentication import VerifyPrivilegePopup
from accounting_export import ReportExporter
from table_utils import TreeviewSorter
from windows_utils import CurrencyFormatter, SentenceCapitalizer
from working_on_accounting import (
    count_accounts_by_type, check_account_name_exists, insert_account,
    get_account_name_and_code, insert_opening_balance, insert_journal_entry,
    fetch_journal_lines_by_account_code, get_account_by_name_or_code,
    reverse_journal_entry, fetch_all_journal_lines_with_names,
    get_balance_sheet, fetch_trial_balance, get_income_statement,
    CashFlowStatement, delete_journal_entry, insert_finance_log
)


class InsertAccountPopup(BaseWindow):
    def __init__(self, parent, conn, user):
        self.popup = tk.Toplevel(parent)
        self.popup.title("New Account")
        self.popup.configure(bg="blue")
        self.center_window(self.popup, 300, 350, parent)
        self.popup.transient(parent)
        self.popup.grab_set()

        self.conn = conn
        self.user = user
        self.account_type_var = tk.StringVar()
        self.code_var = tk.StringVar()
        style = ttk.Style(self.popup)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.popup, bg="blue", bd=4, relief="solid"
        )
        self.name_entry = tk.Entry(
            self.main_frame, width=15, bd=4, relief="raised",
            font=("Arial", 12)
        )
        self.label = tk.Label(
            self.main_frame, text="", bg="blue", fg="dodgerblue",
            font=("Arial", 10, "italic", "underline")
        )
        self.frame = tk.Frame(self.main_frame, bg="blue")
        self.type_combo = ttk.Combobox(
            self.frame, textvariable=self.account_type_var, width=10,
            state="readonly", font=("Arial", 12),
        )
        self.type_combo["values"] = [
            "Asset",
            "Liability",
            "Equity",
            "Revenue",
            "Expense",
        ]
        self.code_entry = tk.Entry(
            self.frame, textvariable=self.code_var, state="readonly",
            width=10, bd=4, relief="raised", font=("Arial", 12),
        )
        self.desc_entry = tk.Text(
            self.main_frame, height=3, bd=4, relief="ridge", wrap="word",
            font=("Arial", 12)
        )

        self.create_widgets()

    def create_widgets(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        t_label = "Create Journal Account"
        tk.Label(
            self.main_frame, text=t_label, bg="blue", fg="white", bd=4,
            relief="ridge", font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="center", fill="x", ipady=5)
        tk.Label(
            self.main_frame, text="Account Name:", bg="blue", fg="white",
            font=("Arial", 12, "bold"),
        ).pack()  # Account Name
        self.name_entry.pack(pady=(0, 2))
        self.name_entry.focus_set()
        self.name_entry.bind("<KeyRelease>", self.on_name_change)
        self.name_entry.bind(
            "<Return>", lambda e: self.type_combo.focus_set()
        )
        self.label.pack()
        self.frame.pack(fill="x", padx=5)
        tk.Label(
            self.frame, text="Account Type:", bg="blue", fg="white",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, pady=(5, 0), padx=10)  # Account Type
        self.type_combo.grid(row=1, column=0, pady=(0, 5), padx=10)
        self.type_combo.bind("<<ComboboxSelected>>", self.generate_code)
        # Generated Code
        tk.Label(
            self.frame, text="Account Code:", bg="blue", fg="white",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=1, pady=(5, 0), padx=10)
        self.code_entry.grid(row=1, column=1, pady=(0, 5), padx=10)
        tk.Label(
            self.main_frame, text="Description:", bg="blue", fg="white",
            font=("Arial", 11, "bold"),
        ).pack(pady=(5, 0))  # Description
        self.desc_entry.pack(pady=(0, 5), fill="x", padx=2)
        # Submit Button
        tk.Button(
            self.main_frame, text="Add Account", bg="dodgerblue",
            fg="white", bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.submit_account
        ).pack(pady=5)

    def on_name_change(self, event=None):
        current_text = self.name_entry.get()
        cursor_pos = self.name_entry.index(tk.INSERT)
        # Preserve trailing space if the user is typing
        if current_text.endswith(" "):
            return  # Let the user finish typing
        # Auto-capitalize each word
        capitalized = " ".join(
            word.capitalize() for word in current_text.split()
        )
        if current_text != capitalized:
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, capitalized)
            self.name_entry.icursor(cursor_pos)
        # Check for existing accounts
        if capitalized:
            existing_names = check_account_name_exists(self.conn, current_text)
            if current_text in existing_names:
                self.name_entry.config(fg="red")
                self.label.config(
                    text="❌ Account Name Already Taken", fg="red"
                )
            else:
                self.name_entry.config(fg="black")
                self.label.configure(
                    text="\u2713 Account Name Available", fg="green"
                )

    def generate_code(self, event=None):
        acc_type = self.account_type_var.get()
        if not acc_type:
            return
        try:
            count = count_accounts_by_type(self.conn, acc_type)
            prefix = {
                "Asset": 1,
                "Liability": 2,
                "Equity": 3,
                "Revenue": 4,
                "Expense": 5,
            }[acc_type]
            new_code = str(prefix * 10) + str(count + 1)
            self.code_var.set(new_code)
            self.desc_entry.focus_set()
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to generate code:\n{e}.", parent=self.popup
            )

    def submit_account(self):
        name = self.name_entry.get().strip()
        acc_type = self.account_type_var.get()
        code = self.code_var.get()
        desc = self.desc_entry.get("1.0", tk.END).strip()
        if not (name and acc_type and code):
            messagebox.showwarning(
                "Missing Data", "Please fill in all fields.",
                parent=self.popup
            )
            return
        # Verify user privilege
        priv = "Admin Create Journal"
        verify_dialog = VerifyPrivilegePopup(
            self.popup, self.conn, self.user, priv
        )
        if verify_dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Privilege on Requested Module.",
                parent=self.popup,
            )
            return

        try:
            success, msg = insert_account(
                self.conn, name, acc_type, code, desc, self.user
            )
            if success:
                messagebox.showinfo("Success", msg, parent=self.popup)
                self.popup.destroy()
            else:
                messagebox.showerror("Error", msg, parent=self.popup)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to insert account:\n{e}.", parent=self.popup
            )


class JournalEntryPopup(BaseWindow):
    def __init__(self, parent, conn, user):
        self.popup = tk.Toplevel(parent)
        self.popup.title("Payments")
        self.center_window(self.popup, 500, 400, parent)
        self.popup.configure(bg="lightblue")
        self.popup.transient(parent)
        self.popup.grab_set()

        self.conn = conn
        self.user = user
        # [{'name':..., 'code':...}, ...]
        self.accounts = get_account_name_and_code(conn)
        self.account_names = [acc["account_name"] for acc in self.accounts]
        self.account_codes = [acc["code"] for acc in self.accounts]
        CREDIT_KEYWORDS = ("cash", "bank", "mpesa")
        self.credit_acc = [
            acc for acc in self.accounts
            if any(k in acc["account_name"].lower() for k in CREDIT_KEYWORDS)
        ]
        self.credit_acc_names = [
            acc["account_name"] for acc in self.credit_acc
        ]
        self.credit_acc_codes = [acc["code"] for acc in self.credit_acc]
        self.debit_name_var = tk.StringVar()
        self.debit_code_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.credit_name_var = tk.StringVar()
        self.credit_code_var = tk.StringVar()
        self.ref_var = tk.StringVar()
        style = ttk.Style(self.popup)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.popup, bg="lightblue", bd=4, relief="solid"
        )
        self.data_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.payment_frame = tk.Frame(
            self.data_frame, bg="lightblue", bd=4, relief="flat"
        )
        self.bottom_frame = tk.Frame(
            self.data_frame, bg="lightblue", bd=4, relief="flat"
        )
        self.debit_name_combo = ttk.Combobox(
            self.payment_frame, textvariable=self.debit_name_var, width=15,
            values=self.account_names, state="readonly", font=("Arial", 11)
        )
        self.debit_code_combo = ttk.Combobox(
            self.payment_frame, textvariable=self.debit_code_var, width=5,
            values=self.account_codes, state="readonly", font=("Arial", 11),
        )
        self.credit_name_combo = ttk.Combobox(
            self.payment_frame, textvariable=self.credit_name_var, width=10,
            state="readonly", values=self.credit_acc_names,
            font=("Arial", 11),
        )
        self.credit_code_combo = ttk.Combobox(
            self.payment_frame, textvariable=self.credit_code_var, width=5,
            state="readonly", values=self.credit_acc_codes,
            font=("Arial", 11),
        )
        self.desc_entry = tk.Text(
            self.bottom_frame, width=30, height=3, bd=4, relief="ridge",
            font=("Arial", 12), wrap="word"
        )
        self.amount_entry = tk.Entry(
            self.bottom_frame, textvariable=self.amount_var, width=10,
            bd=4, relief="raised", font=("Arial", 12),
        )

        self.build_gui()

    def build_gui(self):
        self.main_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        tk.Label(
            self.main_frame, text="Accounts Payment", bg="lightblue",
            fg="blue", font=("Arial", 18, "bold", "underline")
        ).pack(side="top", anchor="center", fill="x", pady=(5, 0))
        self.data_frame.pack(fill="both", expand=True)
        self.payment_frame.pack(fill="x", expand=True)
        # Bottom Frame
        self.bottom_frame.pack(fill="x", expand=True)
        self.bottom_frame.columnconfigure(0, weight=0)
        self.bottom_frame.columnconfigure(1, weight=1)
        self.bottom_frame.columnconfigure(2, weight=0)
        self.bottom_frame.rowconfigure(1, weight=1)
        # Credit Part
        tk.Label(
            self.payment_frame, text="Make Payment From", bg="lightblue",
            fg="blue", font=("Arial", 13, "bold", "underline"),
        ).grid(row=0, column=0, columnspan=4, pady=(5, 0))
        tk.Label(
            self.payment_frame, text="Account Name:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).grid(row=1, column=0, sticky="e", padx=(2, 0), pady=3)
        self.credit_name_combo.grid(
            row=1, column=1, padx=(0, 2), pady=3, sticky="w"
        )
        self.credit_name_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.sync_account_fields("credit", "name")
        )
        tk.Label(
            self.payment_frame, text="Account Code:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).grid(row=1, column=2, sticky="e", padx=(2, 0), pady=3)
        self.credit_code_combo.grid(row=1, column=3, padx=(0, 2), pady=3)
        # Debit Part
        tk.Label(
            self.payment_frame, text="Make Payment To", bg="lightblue",
            fg="blue", font=("Arial", 13, "bold", "underline"),
        ).grid(row=2, column=0, columnspan=4, pady=(5, 0))
        tk.Label(
            self.payment_frame, text="Account Name:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).grid(row=3, column=0, sticky="w", padx=(2, 0), pady=3)
        self.debit_name_combo.grid(row=3, column=1, padx=(0, 2), pady=3)
        self.debit_name_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.sync_account_fields("debit", "name")
        )
        tk.Label(
            self.payment_frame, text="Account Code:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).grid(row=3, column=2, sticky="e", padx=(2, 0), pady=3)
        self.debit_code_combo.grid(row=3, column=3, padx=(0, 2), pady=3)
        self.debit_code_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.sync_account_fields("debit", "code")
        )
        self.credit_code_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.sync_account_fields("credit", "code")
        )
        tk.Label(
            self.bottom_frame, text="Amount:", font=("Arial", 12, "bold"),
            bg="lightblue"
        ).grid(row=0, column=0, sticky="e", pady=3)
        self.amount_entry.grid(row=0, column=1, pady=3, sticky="w")
        tk.Label(
            self.bottom_frame, text="Reference No:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=2, pady=3, sticky="e", padx=(5, 0))
        ref_entry = tk.Entry(
            self.bottom_frame, textvariable=self.ref_var, width=15, bd=4,
            relief="raised", font=("Arial", 12),
        )
        ref_entry.grid(row=0, column=3, pady=3, padx=(0, 5), sticky="w")
        self.amount_entry.bind(
            "<Return>",
            lambda e: ref_entry.focus_set() if self.account_selected()
            else self.credit_name_combo.focus_set()
        )
        ref_entry.bind("<Return>", self.focus_description)
        tk.Label(
            self.bottom_frame, text="Description:", bg="lightblue",
            font=("Arial", 12, "bold"),
        ).grid(row=1, column=0, columnspan=4, pady=(3, 0), sticky="w")
        self.desc_entry.grid(
            row=2, column=1, columnspan=3, pady=(0, 5), sticky="nw"
        )
        self.desc_entry.bind("<Return>", self.submit_from_desc)
        self.desc_entry.bind("<Shift-Return>", lambda e: None)
        SentenceCapitalizer.bind(self.desc_entry)
        tk.Button(
            self.bottom_frame, text="Post Payment", bd=4, relief="groove",
            bg="dodgerblue", fg="white", font=("Arial", 11, "bold"),
            command=self.submit_journal,
        ).grid(row=3, column=0, columnspan=4, pady=(5, 0))
        CurrencyFormatter.add_currency_trace(
            self.amount_var, self.amount_entry
        )

    def sync_account_fields(self, side, changed_field):
        name_var = self.debit_name_var if side == "debit" else self.credit_name_var
        code_var = self.debit_code_var if side == "debit" else self.credit_code_var
        value = name_var.get() if changed_field == "name" else code_var.get()
        source = self.accounts if side == "debit" else self.credit_acc
        account = next(
            (acc for acc in source
             if acc["account_name"] == value or acc["code"] == value), None
        )
        if account:
            name_var.set(account["account_name"])
            code_var.set(account["code"])
        else:
            messagebox.showwarning(
                "Not Found", f"No Matching Account For {value}.",
                parent=self.popup
            )
        if side == "debit":
            if self.account_selected():
                self.amount_entry.focus_set()
            else:
                self.credit_name_combo.focus_set()

    def focus_description(self, event=None):
        if not self.account_selected():
            self.credit_name_combo.focus_set()
            return "break"
        self.desc_entry.focus_set()
        self.desc_entry.mark_set("insert", "1.0")
        return "break"

    def submit_from_desc(self, event=None):
        if not self.account_selected():
            self.credit_name_combo.focus_set()
            return "break"
        self.submit_journal()
        return "break"

    def submit_journal(self):
        debit_code = self.debit_code_var.get()
        credit_code = self.credit_code_var.get()
        debit_amt = self.amount_var.get().replace(",", "").strip()
        desc = self.desc_entry.get("1.0", tk.END).strip()
        ref_no = self.ref_var.get().strip()
        try:
            debit_val = float(debit_amt) if debit_amt else 0.00
            credit_val = float(debit_amt) if debit_amt else 0.00
            if debit_val == 0 or credit_val == 0:
                messagebox.showwarning(
                    "Input Error", "Enter Valid Amount.", parent=self.popup
                )
                return
            if not debit_code or not credit_code:
                messagebox.showwarning(
                    "Input Error",
                    "Select Debit and Credit Accounts.",
                    parent=self.popup,
                )
                return
            # Verify user privilege
            priv = "Make Payment"
            verify = VerifyPrivilegePopup(
                self.popup, self.conn, self.user, priv
            )
            if verify.result != "granted":
                messagebox.showwarning(
                    "Access Denied",
                    f"You Don't Have Permission To {priv}.",
                    parent=self.popup,
                )
                return
            lines = [
                {
                    "account_code": debit_code,
                    "description": desc,
                    "debit": debit_val,
                    "credit": 0.00,
                },
                {
                    "account_code": credit_code,
                    "description": desc,
                    "debit": 0.00,
                    "credit": credit_val,
                },
            ]
            success, msg = insert_journal_entry(self.conn, ref_no, lines, self.user)
            if success:
                messagebox.showinfo("Success", msg, parent=self.popup)
                self.credit_name_var.set("")
                self.credit_code_var.set("")
                self.debit_name_var.set("")
                self.debit_code_var.set("")
                self.amount_var.set("")
                self.ref_var.set("")
                self.desc_entry.delete("1.0", tk.END)
            else:
                messagebox.showerror("Error", msg, parent=self.popup)
        except ValueError:
            messagebox.showerror(
                "Invalid", "Amount Must Be Numeric.", parent=self.popup
            )

    def account_selected(self):
        return (
            bool(self.credit_name_var.get()) and
            bool(self.debit_name_var.get())
        )


class OpeningBalancePopup(BaseWindow):
    def __init__(self, parent, conn, user):
        self.popup = tk.Toplevel(parent)
        self.popup.title("Accounts Balances")
        self.popup.configure(bg="lightblue")
        self.center_window(self.popup, 500, 450, parent)
        self.popup.transient(parent)
        self.popup.grab_set()

        self.conn = conn
        self.user = user
        self.accounts = get_account_name_and_code(conn)
        self.account_names = [acc["account_name"] for acc in self.accounts]
        self.account_code = [acc["code"] for acc in self.accounts]
        self.line_items = []  # Stores added opening entries
        self.display_rows = [] # Stores treeview rows
        self.account_name_var = tk.StringVar()
        self.account_code_var = tk.StringVar()
        self.debit_var = tk.StringVar()
        self.credit_var = tk.StringVar()
        self.columns = ("No.", "Account Name", "Code", "Debit", "Credit")
        style = ttk.Style(self.popup)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.popup, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No.")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_gui()
        self.sorter.autosize_columns()

    def build_gui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(
            self.main_frame, text="Account Opening Balance", bg="lightblue",
            fg="blue", font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="center")
        form_frame = tk.Frame(self.main_frame, bg="lightblue")
        form_frame.pack(pady=(5, 0), fill="x")
        tk.Label(
            form_frame, text="Account Name:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, padx=(5, 0), sticky="e")
        name_combo = ttk.Combobox(
            form_frame, textvariable=self.account_name_var, width=15,
            values=self.account_names, state="readonly", font=("Arial", 11),
        )
        name_combo.grid(row=0, column=1, padx=(0, 5))
        name_combo.bind(
            "<<ComboboxSelected>>", lambda e: self.sync_account("name")
        )
        name_combo.focus_set()
        tk.Label(
            form_frame, text="Account Code:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=2, padx=(5, 0), sticky="e")
        code_combo = ttk.Combobox(
            form_frame, textvariable=self.account_code_var, width=5,
            values=self.account_code, state="readonly", font=("Arial", 11)
        )
        code_combo.grid(row=0, column=3, padx=(0, 5))
        code_combo.bind(
            "<<ComboboxSelected>>", lambda e: self.sync_account("code")
        )
        tk.Label(
            form_frame, text="Debit:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=1, column=0, sticky="e")
        debit_entry = tk.Entry(
            form_frame, textvariable=self.debit_var, width=8, bd=4,
            relief="raised", font=("Arial", 11),
        )
        debit_entry.grid(row=1, column=1, sticky="w")
        tk.Label(
            form_frame, text="Credit:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=1, column=2, sticky="e")
        credit_entry = tk.Entry(
            form_frame, textvariable=self.credit_var, width=8, bd=4,
            relief="raised", font=("Arial", 11),
        )
        credit_entry.grid(row=1, column=3, sticky="w")
        # Buttons
        btn_frame = tk.Frame(self.main_frame, bg="lightblue")
        btn_frame.pack(pady=(5, 0))
        tk.Button(
            btn_frame, text="Add Line", bg="dodgerblue", fg="white", bd=4,
            relief="groove", font=("Arial", 10, "bold"),
            command=self.add_line,
        ).pack(side="left")
        tk.Button(
            btn_frame, text="Remove Line", bg="tomato", fg="white", bd=4,
            relief="groove", font=("Arial", 10, "bold"),
            command=self.remove_selected,
        ).pack(side="left")
        # Treeview
        self.table_frame.pack(fill="both", expand=True)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.pack(expand=True, fill="both")
        # Submit Button
        tk.Button(
            self.main_frame, text="Post Balances", bg="green", fg="white",
            bd=4, relief="groove", font=("Arial", 11, "bold"),
            command=self.post_opening_balances
        ).pack(pady=(5, 0))
        CurrencyFormatter.add_currency_trace(self.debit_var, debit_entry)
        CurrencyFormatter.add_currency_trace(self.credit_var, credit_entry)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def sync_account(self, changed):
        value = (
            self.account_name_var.get()
            if changed == "name"
            else self.account_code_var.get()
        )
        acc = get_account_by_name_or_code(self.conn, value)
        if acc:
            self.account_name_var.set(acc["account_name"])
            self.account_code_var.set(acc["code"])

    def find_row_index(self, name, code):
        for i, row in enumerate(self.display_rows):
            if row["account_code"] == code or row["account_name"] == name:
                return i
        return None

    def add_line(self):
        name = self.account_name_var.get()
        code = self.account_code_var.get()
        debit = self.debit_var.get().replace(",", "").strip()
        credit = self.credit_var.get().replace(",", "").strip()
        try:
            debit_val = float(debit) if debit else 0.00
            credit_val = float(credit) if credit else 0.00
            if not name or not code:
                messagebox.showwarning(
                    "Missing Info",
                    "Please Select Account Name Or Code.",
                    parent=self.popup,
                )
                return
            if debit_val == 0.00 and credit_val == 0.00:
                messagebox.showwarning(
                    "Invalid",
                    "Enter at Least Debit or Credit Amount.",
                    parent=self.popup,
                )
                return
            item_index = self.find_row_index(name, code)
            if item_index is not None:
                # Update display rows
                self.display_rows[item_index]["debit"] += debit_val
                self.display_rows[item_index]["credit"] += credit_val
                # Update posting row
                self.line_items[item_index]["debit"] += debit_val
                self.line_items[item_index]["credit"] += credit_val
            else:
                # New display row
                self.display_rows.append({
                    "account_name": name,
                    "account_code": code,
                    "debit": debit_val,
                    "credit": credit_val,
                })
                # New posting row
                self.line_items.append({
                    "account_code": code,
                    "description": f"Opening balance for {name}",
                    "debit": debit_val,
                    "credit": credit_val,
                })

            self.load_table()
            # Clear entries
            self.account_name_var.set("")
            self.account_code_var.set("")
            self.debit_var.set("")
            self.credit_var.set("")
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Debit and Credit Must be Numeric.", parent=self.popup
            )

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        for sel in selected:
            index = self.tree.index(sel)
            del self.display_rows[index]
            del self.line_items[index]
        self.load_table()

    def load_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, row in enumerate(self.display_rows, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                row["account_name"],
                row["account_code"],
                f"{row['debit']:,.2f}",
                f"{row['credit']:,.2f}"
            ), tags=(tag,))
        self.sorter.autosize_columns()

    def post_opening_balances(self):
        if not self.line_items:
            messagebox.showwarning(
                "Empty", "No Lines Added.", parent=self.popup
            )
            return
        # Verify user privilege
        priv = "Admin Initial Journal Balances"
        verify = VerifyPrivilegePopup(self.popup, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Privilege on Requested Module.",
                parent=self.popup,
            )
            return
        success, msg = insert_opening_balance(
            self.conn, self.line_items, self.user
        )
        if success:
            messagebox.showinfo("Success", msg, parent=self.popup)
            self.popup.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self.popup)


class ReverseJournalPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Reverse Journal")
        self.center_window(self.window, 1150, 700, master)
        self.window.configure(bg="lightblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.code = None
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.columns = (
            "No", "Date", "ID", "Account Name", "Acc Code", "Description",
            "Debit", "Credit",
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        top_frame = tk.Frame(self.main_frame, bg="lightblue")
        top_frame.pack(side="top", fill="x")
        tk.Label(
            top_frame, text="Reverse/Delete Journal Entry", bg="lightblue",
            fg="blue", font=("Arial", 20, "bold", "underline")
        ).pack(side="left")
        tk.Label(
            top_frame, text="Select Entry to Reverse.", bg="lightblue",
            font=("Arial", 12, "italic", "underline"), fg="blue", width=50
        ).pack(side="left", anchor="s")
        tk.Button(
            top_frame, text="Reverse Entry", bg="green", fg="white", bd=4,
            relief="groove", font=("Arial", 10, "bold"), height=1,
            command=self.reverse_selected
        ).pack(side="right")
        tk.Button(
            top_frame, text="Delete Entry", bg="green", fg="white", bd=4,
            relief="groove", font=("Arial", 10, "bold"), height=1,
            command=self.delete_selected
        ).pack(side="right")
        self.table_frame.pack(fill="both", expand=True)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def populate_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = fetch_all_journal_lines_with_names(self.conn)
        if isinstance(rows, str):
            messagebox.showerror("Error", rows)
            return
        for i, row in enumerate(rows, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                row["entry_date"].strftime("%d/%m/%Y"),
                row["journal_id"],
                row["account_name"],
                row["account_code"],
                row["description"],
                f"{row['debit']:,.2f}",
                f"{row['credit']:,.2f}",
            ), tags=(tag,))
        self.sorter.autosize_columns()

    def _handle_selected_entry(self, action_name, priv_name, action_func):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning(
                "No Selection",
                f"Please Select Journal Entry to {action_name.lower()}.",
                parent=self.window
            )
            return
        journal_id = self.tree.set(selected, "Journal ID")
        self.code = self.tree.set(selected, "Account Code")
        if not journal_id:
            messagebox.showerror(
                "Error", "No Journal ID Found.", parent=self.window
            )
            return
        confirm = messagebox.askyesno(
            "Confirm",
            f"{action_name.title()} journal #{journal_id}?",
            parent=self.window
        )
        if not confirm:
            return
        verify = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv_name
        )
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Permission to {priv_name}.",
                parent=self.window
            )
            return

        # Perform the action
        success, msg = action_func(journal_id)
        if success:
            messagebox.showinfo("Success", msg, parent=self.window)
            self.populate_table()
        else:
            messagebox.showerror("Error", msg, parent=self.window)

    def delete_selected(self):
        self._handle_selected_entry(
            action_name="Delete",
            priv_name="Admin Delete Journal Entry",
            action_func=lambda jid: delete_journal_entry(
                self.conn, jid, self.code, self.user
            ),
        )

    def reverse_selected(self):
        self._handle_selected_entry(
            action_name="Reverse",
            priv_name="Reverse Journal",
            action_func=lambda jid: reverse_journal_entry(
                self.conn, jid, self.user
            ),
        )


class ViewJournalWindow(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Journal Viewer")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 1000, 700, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.accounts = get_account_name_and_code(conn)
        self.accounts_names = [acc["account_name"] for acc in self.accounts]
        self.accounts_codes = [acc["code"] for acc in self.accounts]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.name_cb = ttk.Combobox(
            self.top_frame, width=18, values=self.accounts_names,
            state="readonly", font=("Arial", 12)
        )
        self.code_cb = ttk.Combobox(
            self.top_frame, width=7, values=self.accounts_codes,
            state="readonly", font=("Arial", 12)
        )
        self.title_var = tk.StringVar()
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.columns = (
            "No.", "Date", "Journal ID", "Description", "Debit", "Credit",
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No.")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(
            self.main_frame, text="View Finance Journals", bg="lightblue",
            fg="blue", font=("Arial", 20, "bold", "underline")
        ).pack(side="top", anchor="center")
        self.top_frame.pack(fill="x")
        tk.Label(
            self.top_frame, text="Select Account To Show;", bg="lightblue",
            fg="blue", font=("Arial", 14, "italic", "underline")
        ).pack(side="left", padx=(0, 5))
        tk.Label(
            self.top_frame, text="Account Name:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0), anchor="s")
        self.name_cb.pack(side="left", padx=(0, 5), anchor="s")
        self.name_cb.current(0)
        tk.Label(
            self.top_frame, text="Code:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=(5, 0), anchor="s")
        self.code_cb.pack(side="left", padx=(0, 5), anchor="s")
        self.name_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.sync_account_fields("name")
        )
        self.code_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.sync_account_fields("code")
        )
        btn_frame = tk.Frame(self.top_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=5, anchor="s")
        buttons = {
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
        }
        for text, command in buttons.items():
            tk.Button(
                btn_frame, text=text, bd=4, relief="groove", bg="blue",
                fg="white", command=command, font=("Arial", 10, "bold")
            ).pack(side="left")
        tk.Label(
            self.table_frame, textvariable=self.title_var, bg="lightblue",
            fg="blue", bd=4, relief="ridge",
            font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="center", fill="x")
        self.table_frame.pack(fill="both", expand=True)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        vsb = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        self.tree.tag_configure("totalrow", font=("Arial", 11, "bold"))
        self.tree.tag_configure(
            "total", font=("Arial", 12, "bold", "underline"),
            background="#c5cae9"
        )
        self.sync_account_fields("name")

    def sync_account_fields(self, changed_field):
        value = self.name_cb.get() if changed_field == "name" else self.code_cb.get()
        account = get_account_by_name_or_code(self.conn, value)
        if account:
            self.name_cb.set(account["account_name"])
            self.code_cb.set(account["code"])
            self.display_journal_lines(
                account["code"], account["account_name"]
            )
        else:
            messagebox.showwarning(
                "Not Found", f"No Matching Account For '{value}'.",
                parent=self.window
            )

    def display_journal_lines(self, account_code, account_name):
        for row in self.tree.get_children():
            self.tree.delete(row)
        lines = fetch_journal_lines_by_account_code(self.conn, account_code)
        if not lines:
            return
        total_debit = 0
        total_credit = 0

        self.title_var.set(f"{account_name}({account_code})")
        for idx, line in enumerate(lines, start=1):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                idx,
                line["entry_date"].strftime("%d/%m/%Y"),
                line["journal_id"],
                line["description"],
                f"{line['debit']:,.2f}",
                f"{line['credit']:,.2f}",
            ), tags=(tag,))
            total_debit += line["debit"]
            total_credit += line["credit"]
        # Insert balance carried down if necessary
        today = datetime.now().date().strftime("%d/%m/%Y")
        balancing = max(total_debit, total_credit)
        if total_debit > total_credit:
            desc = f"Balance C/d as at {today}"
            balance = total_debit - total_credit
            self.tree.insert("", "end", values=(
                "", "", "", desc, 0.00, f"{balance:,}"
            ), tags=("totalrow",))
        elif total_credit > total_debit:
            desc = f"Balance C/d as at {today}"
            balance = total_credit - total_debit
            self.tree.insert("", "end", values=(
                "", "", "", desc, f"{balance:,}", 0.00
            ), tags=("totalrow",))
        self.tree.insert("", "end", values=(
            "", "", "", "Total", f"{balancing:,}", f"{balancing:,}"
        ), tags=("total",))
        self.sorter.autosize_columns()

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append(
                {
                    "No.": vals[0],
                    "Date": vals[1],
                    "Journal ID": vals[2],
                    "Description": vals[3],
                    "Debit": vals[4],
                    "Credit": vals[5],
                }
            )
        return rows

    def _make_exporter(self):
        name = self.name_cb.get()
        code = self.code_cb.get()
        title = f"Journal Account {name.capitalize()} Code {code}"
        columns = [
            "No.", "Date", "Journal ID", "Description", "Debit", "Credit",
        ]
        rows = self._collect_current_rows()
        return ReportExporter(self.window, title, columns, rows)

    def check_privilege(self) -> bool:
        privilege = "View Journal"
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Privilege To {privilege}.",
                parent=self.window
            )
            return False
        return True

    def on_export_excel(self):
        if not self.check_privilege():
            return
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_export_pdf(self):
        if not self.check_privilege():
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self.check_privilege():
            return
        exporter = self._make_exporter()
        exporter.print()


class TrialBalanceWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Trial Balance")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 1100, 700, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        # Define columns
        self.columns = (
            "No", "Acc Code", "Account Name", "Acc Type", "Debit", "Credit",
            "Balance"
        )
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Top frame (title + button)
        top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        top_frame.pack(fill="x")
        year = datetime.now().date().year
        title_text = f"Trial Balance For Year Ended December {year}."
        tk.Label(
            top_frame, text=title_text, bg="lightblue", fg="blue", bd=4,
            relief="ridge", font=("Arial", 20, "bold", "underline"), width=40
        ).pack(side="left", anchor="s")
        # action buttons
        btn_frame = tk.Frame(top_frame, bg="lightblue")
        btn_frame.pack(side="right")
        buttons = {
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
        }
        for text, command in buttons.items():
            tk.Button(
                btn_frame, text=text, bd=4, relief="groove", bg="blue",
                fg="white", command=command, font=("Arial", 11, "bold")
            ).pack(side="left")

        self.table_frame.pack(fill="both", expand=True)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        self.tree.tag_configure(
            "total", font=("Arial", 12, "bold", "underline"),
            background="#c5cae9"
        )

    def populate_table(self):
        data = fetch_trial_balance(self.conn)
        if isinstance(data, str):
            messagebox.showerror("Error", data, parent=self.window)
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        total_debit = 0
        total_credit = 0
        total_balance = 0
        for i, row in enumerate(data, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            debit = row["total_debit"] or 0.00
            credit = row["total_credit"] or 0.00
            balance = row["balance"] or 0.00
            self.tree.insert("", "end", values=(
                i,
                row["code"],
                row["account_name"],
                row["account_type"],
                f"{debit:,.2f}",
                f"{credit:,.2f}",
                f"{balance:,.2f}",
            ), tags=(tag,))
            total_debit += float(debit)
            total_credit += float(credit)
            total_balance += float(balance)
        if data:
            self.tree.insert("", "end", values=(
                "", "", "", "Total", f"{total_debit:,}", f"{total_credit:,}",
                f"{total_balance}"
            ), tags=("total",))
        self.sorter.autosize_columns()

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append(
                {
                    "No": vals[0],
                    "Acc Code": vals[1],
                    "Account Name": vals[2],
                    "Acc Type": vals[3],
                    "Debit": vals[4],
                    "Credit": vals[5],
                    "Balance": vals[6],
                }
            )
        return rows

    def _make_exporter(self):
        year = datetime.now().date().year
        title = f"Trial Balance For Year Ended December {year}."
        columns = [
            "No", "Acc Code", "Account Name", "Acc Type", "Debit", "Credit",
            "Balance",
        ]
        rows = self._collect_current_rows()
        return ReportExporter(self.window, title, columns, rows)

    def check_privilege(self) -> bool:
        privilege = "View Trial Balance"
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Privilege To {privilege}.",
                parent=self.window
            )
            return False
        return True

    def on_export_excel(self):
        if not self.check_privilege():
            return
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_export_pdf(self):
        if not self.check_privilege():
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self.check_privilege():
            return
        exporter = self._make_exporter()
        exporter.print()


class IncomeStatementWindow(BaseWindow):
    def __init__(self, parent, conn):
        self.window = tk.Toplevel(parent)
        self.window.title("Income Statement")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 900, 700, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.columns = (
            "No", "Category", "Account Name", "Code", "Amount"
        )
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Table Frame
        top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        top_frame.pack(fill="x")
        year = datetime.now().date().year
        title_text = f"Income Statement For Year Ended {year}."
        tk.Label(
            top_frame, text=title_text, bg="lightblue", fg="blue", bd=4,
            relief="flat", font=("Arial", 20, "bold", "underline")
        ).pack(side="left", ipadx=10, anchor="s")
        # Buttons Frame
        btn_frame = tk.Frame(top_frame, bg="lightblue")
        btn_frame.pack(side="right", anchor="s")
        buttons = {
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
        }
        for text, command in buttons.items():
            tk.Button(
                btn_frame, text=text, bd=4, relief="groove", bg="blue",
                fg="white", command=command, font=("Arial", 11, "bold")
            ).pack(side="left")
        # Table Area
        self.table_frame.pack(fill="both", expand=True)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        self.tree.tag_configure(
            "total", font=("Arial", 12, "bold", "underline"),
            background="#c5cae9"
        )

    def populate_table(self):
        success, result = get_income_statement(self.conn)
        if not success:
            messagebox.showerror("Error", result, parent=self.window)
            return
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)
        total = 0.00
        for idx, row in enumerate(result, start=1):
            amount = row.get("amount") or 0.00
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                idx,
                row.get("category", ""),
                row.get("account_name", ""),
                row.get("account_code", ""),
                f"{amount:,.2f}"
            ), tags=(tag,))
            if row["category"] == "Revenue":
                total += float(amount)
            else:
                total -= float(amount)
        if result:
            status = "Net Profit" if total >= 0 else "Net Loss"
            self.tree.insert("", "end", values=(
                "", "", status, "", f"{total:,.2f}"
            ), tags=("total",))
        self.sorter.autosize_columns(10)

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append(
                {
                    "No": vals[0],
                    "Category": vals[1],
                    "Account Name": vals[2],
                    "Code": vals[3],
                    "Amount": vals[4],
                }
            )
        return rows

    def _make_exporter(self):
        year = datetime.now().date().year
        title = f"Income Statement For Year Ended {year}."
        columns = [
            "No", "Category", "Account Name", "Code", "Amount"
        ]
        rows = self._collect_rows()
        return ReportExporter(self.window, title, columns, rows)

    def on_export_excel(self):
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_export_pdf(self):
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        exporter = self._make_exporter()
        exporter.print()


class CashFlowStatementWindow(BaseWindow):
    def __init__(self, parent, conn):
        self.window = tk.Toplevel(parent)
        self.window.title("Cash Flow Statement")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 1000, 650, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.columns = (
            "No", "Category", "Account Code", "Account Name", "Amount",
            "Total"
        )
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Title Frame
        top_frame = tk.Frame(self.main_frame, bg="lightblue")
        top_frame.pack(fill="x", padx=5)
        current_year = datetime.now().year
        title_text = f"Cash Flow Statement For Year {current_year}."
        tk.Label(
            top_frame, text=title_text, bg="lightblue", fg="blue", bd=4,
            relief="flat", font=("Arial", 20, "bold", "underline"),
        ).pack(side="left", anchor="s", ipadx=10)
        # Buttons Frame
        btn_frame = tk.Frame(top_frame, bg="lightblue")
        btn_frame.pack(side="right", anchor="s")
        buttons = {
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
        }
        for text, command in buttons.items():
            tk.Button(
                btn_frame, text=text, bd=4, relief="groove", bg="blue",
                fg="white", command=command, font=("Arial", 11, "bold")
            ).pack(side="left", anchor="s")
        # Table Area
        self.table_frame.pack(fill="both", expand=True)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="left", fill="y")
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def populate_table(self):
        fetch = CashFlowStatement(self.conn)
        result = fetch.get_cash_flow_statement()
        if isinstance(result, str):
            messagebox.showerror("Error", result, parent=self.window)
            return
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Insert Rows
        no = 1
        total_amount = 0
        for row in result["cash_inflows"]:
            amount = row["amount"] or 0.00
            total_amount += amount
            tag = "evenrow" if no % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                no,
                row["category"],
                row["account_code"],
                row["account_name"],
                f"{amount:,.2f}",
                f"{total_amount:,.2f}",
            ), tags=(tag,))
            no += 1
        for row in result["cash_outflows"]:
            amount = row["amount"] or 0.00
            total_amount += amount  # negative values subtract automatically
            tag = "evenrow" if no % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                no,
                row["category"],
                row["account_code"],
                row["account_name"],
                f"{amount:,.2f}",
                f"{total_amount:,.2f}",
            ), tags=(tag,))
            no += 1
        if total_amount >= 0:
            status = "Profit"
            total_figure = f"{total_amount:,.2f}"
            self.tree.tag_configure(
                "total", font=("Arial", 12, "bold", "underline"),
                background="blue", foreground="white"
            )
        else:
            status = "Loss"
            total_figure =f"({abs(total_amount):,.2f})"
            self.tree.tag_configure(
                "total", font=("Arial", 12, "bold", "underline"),
                background="red", foreground="black"
            )
        self.tree.insert("", "end", values=(
            "", "", "Net Income", status, "", total_figure
        ), tags=("total",))
        self.sorter.autosize_columns(10)

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append(
                {
                    "No": vals[0],
                    "Category": vals[1],
                    "Account Code": vals[2],
                    "Account Name": vals[3],
                    "Amount": vals[4],
                    "Total": vals[5],
                }
            )
        return rows

    def _make_exporter(self):
        title = f"Cash Flow Statement For Year {datetime.now().date().year}."
        columns = [
            "No", "Category", "Account Code", "Account Name", "Amount",
            "Total"
        ]
        rows = self._collect_rows()
        return ReportExporter(self.window, title, columns, rows)

    def on_export_excel(self):
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_export_pdf(self):
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        exporter = self._make_exporter()
        exporter.print()


class BalanceSheetWindow(BaseWindow):
    def __init__(self, parent, conn):
        self.window = tk.Toplevel(parent)
        self.window.title("Balance Sheet")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 1000, 700, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.columns = (
            "No", "Account Code", "Account Name", "Debit", "Credit"
        )
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.bind_mousewheel()

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Title Frame
        title_frame = tk.Frame(self.main_frame, bg="lightblue")
        title_frame.pack(fill="x", ipadx=5)
        year = datetime.now().year
        title_text = f"Balance Sheet For Year Ended {year}"
        tk.Label(
            title_frame, text=title_text, bg="lightblue", fg="blue", bd=2,
            relief="ridge", font=("Arial", 20, "bold", "underline"),
        ).pack(side="left", ipadx=10)
        # Buttons Frame
        btn_frame = tk.Frame(title_frame, bg="lightblue")
        btn_frame.pack(side="right", anchor="s")
        buttons = {
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
        }
        for text, command in buttons.items():
            tk.Button(
                btn_frame, text=text, bd=4, relief="groove", bg="blue",
                fg="white", command=command, font=("Arial", 11, "bold")
            ).pack(side="left")
        # Table Frame
        self.table_frame.pack(fill="both", expand=True)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        # Apply tag style
        self.tree.tag_configure(
            "total", font=("Arial", 12, "bold", "underline"),
            background="#FFFFFF", foreground="blue"
        ) # Pure White Background
        self.tree.tag_configure(
            "totalrow", font=("Arial", 12, "bold"), background="#FAFAFA",
            foreground="green"
        ) # Very light Gray
        self.tree.tag_configure(
            "grandtotalrow", font=("Arial", 12, "bold", "underline"),
            background="blue", foreground="white"
        )

    def populate_table(self):
        result = get_balance_sheet(self.conn)
        if isinstance(result, str):
            messagebox.showerror("Error", result)
            return
        # Clear table first
        self.tree.delete(*self.tree.get_children())
        no = 1
        total_assets = total_liabilities = total_equity = 0.00
        for category in ["assets", "liabilities", "equity"]:
            cat_data = result[category]
            # Heading row for category
            self.tree.insert("", "end", values=(
                "", category.capitalize(), "", "", ""
            ), tags=("total",))
            # Rows for each account
            for row in cat_data["items"]:
                if category == "assets":
                    debit = f"{row['amount']:,.2f}"
                    credit = ""
                else:
                    debit = ""
                    credit = f"{row['amount']:,.2f}"
                tag = "evenrow" if no % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=(
                    no,
                    row["account_code"],
                    row["account_name"],
                    debit,
                    credit,
                ), tags=(tag,))
                no += 1
            # Total row
            if category == "assets":
                total_assets = cat_data["total"]
                total_debit = f"{cat_data['total']:,.2f}"
                total_credit = ""
            elif category == "liabilities":
                total_liabilities = cat_data["total"]
                total_debit = ""
                total_credit = f"{cat_data['total']:,.2f}"
            else:  # Equity
                total_equity = cat_data["total"]
                total_debit = ""
                total_credit = f"{cat_data['total']:,.2f}"

            self.tree.insert("", "end", values=(
                "",
                "",
                f"Total {category.capitalize()}",
                total_debit,
                total_credit,
            ), tags=("totalrow",))
        # Grand total row (Assets vs Liabilities + Equity)
        grand_total_debit = total_assets
        grand_total_credit = (total_liabilities + total_equity)
        if grand_total_debit > grand_total_credit:
            balancing_figure = (grand_total_debit - grand_total_credit)
            self.tree.insert("", "end", values=(
                "", "", "Balance C/d", "", f"{balancing_figure:,.2f}"
            ), tags=("totalrow",))
        elif grand_total_credit > grand_total_debit:
            balancing_figure = (grand_total_credit-grand_total_debit)
            self.tree.insert("", "end", values=(
                "", "", "Balance C/d", f"{balancing_figure:,.2f}", ""
            ), tags=("totalrow",))
        else:
            # For Spacing
            self.tree.insert("", "end", values=("", "", "", "", ""))
        total = max(grand_total_debit, grand_total_credit)
        self.tree.insert("", "end", values=(
            "",
            "",
            "TOTAL",
            f"{total:,.2f}",
            f"{total:,.2f}"
        ), tags=("grandtotalrow",))

        self.sorter.autosize_columns(5)

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append(
                {
                    "No": vals[0],
                    "Account Code": vals[1],
                    "Account Name": vals[2],
                    "Debit": vals[3],
                    "Credit": vals[4],
                }
            )
        return rows

    def _make_exporter(self):
        year = datetime.now().year
        title = f"Balance Sheet For Year Ended {year}"
        columns = ["No", "Account Code", "Account Name", "Debit", "Credit"]
        rows = self._collect_rows()
        return ReportExporter(self.window, title, columns, rows)

    def on_export_excel(self):
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_export_pdf(self):
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        exporter = self._make_exporter()
        exporter.print()


from accounting_close_year import *


class CloseYearPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Close Accounting Year")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 300, 250, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.selected_year = None
        self.mode = "close"  # Default mode
        self.combo_var = tk.StringVar()
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.btn_close_year = tk.Button(
            self.top_frame, text="Close Year", bg="green", fg="white", bd=4,
            relief="groove", font=("Arial", 11, "bold"),
            command=self.show_close_year
        )
        self.btn_reverse_year = tk.Button(
            self.top_frame, text="Reverse Closed Year", bg="red", fg="white",
            bd=4, relief="groove", font=("Arial", 11, "bold"),
            command=self.show_reverse_year
        )
        # Middle content frame
        self.middle_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        # Dynamic title label (inside content area)
        self.mode_title_label = tk.Label(
            self.middle_frame, text="", bg="lightblue", fg="blue",
            font=("Arial", 14, "bold", "underline")
        )
        # Dynamic label + combobox
        self.select_label = tk.Label(
            self.middle_frame, text="", bg="lightblue", fg="blue",
            font=("Arial", 12, "bold")
        )
        self.combobox = ttk.Combobox(
            self.middle_frame, state="readonly", textvariable=self.combo_var,
            width=30, font=("Arial", 12)
        )
        # Bottom action button
        self.action_btn = tk.Button(
            self.middle_frame, text="", bg="blue", fg="white", bd=4,
            relief="groove", font=("Arial", 11, "bold"),
            command=self.perform_action,
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tk.Label(
            self.main_frame, text="Close Financial Year.", bg="lightblue",
            fg="blue", font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="center", pady=(5, 0))
        # Pack top frame + buttons
        self.top_frame.pack(fill="x", pady=(5, 0))
        self.btn_close_year.pack(side="left")
        self.btn_reverse_year.pack(side="left")
        # Middle Section
        self.middle_frame.pack(fill="both", expand=True)
        self.mode_title_label.pack(anchor="center", pady=(3, 0), ipadx=5)
        self.select_label.pack(anchor="w", pady=(5, 0))
        self.combobox.pack(anchor="w", fill="x", pady=(0, 5))
        self.action_btn.pack(pady=10)
        # Default to close year
        self.show_close_year()

    def show_close_year(self):
        self.mode = "close"
        self.mode_title_label.config(text="Close Accounting Period.")
        self.select_label.config(text="Select Period to Close:")
        self.action_btn.config(text="Close Year", bg="green")
        periods = get_available_periods_from_journal_entries(self.conn)
        if isinstance(periods, str):
            messagebox.showerror("Error", periods)
            periods = []
        self.combobox["values"] = periods
        self.combobox.set(periods[0] if periods else "")

    def show_reverse_year(self):
        self.mode = "reverse"
        self.mode_title_label.config(text="Reverse Closed Year")
        self.select_label.config(text="Select Year to Reverse:")
        self.action_btn.config(text="Reverse Year", bg="red")
        years = get_available_years_from_jornal_archive(self.conn)
        if isinstance(years, str):
            messagebox.showerror("Error", years)
            years = []
        self.combobox["values"] = years
        self.combobox.set(years[0] if years else "")

    def perform_action(self):
        # Verify user privilege
        priv = "Close Accounting Books"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied", f"You Don't Have Permission to {priv}.",
                parent=self.window
            )
            return
        selected = self.combo_var.get()
        if not selected:
            messagebox.showwarning(
                "No Selection", "Please Select Year First.",
                parent=self.window
            )
            return
        if self.mode == "close":
            try:
                closing_year = int(selected.split()[-1])
            except IndexError:
                messagebox.showinfo(
                    "Error", "Invalid Period Format.", parent=self.window
                )
                return
            confirm = messagebox.askyesno(
                "Confirm",
                f"Close Accounting Year: {closing_year}?", parent=self.window
            )
            if confirm:
                processor = YearEndProcessor(self.conn)
                success, msg = processor.close_year(closing_year)
                if success:
                    messagebox.showinfo(
                        "Success", f"Closed Year:\n{msg}", parent=self.window
                    )
                    receipt = date.today().strftime("%d/%m/%Y")
                    action = f"Closed Year {closing_year}."
                    success, status = insert_finance_log(
                        self.conn, self.user, f"Closing {receipt}", action
                    )
                    if success:
                        messagebox.showinfo(
                            "Success", status, parent=self.window
                        )
                    else:
                        messagebox.showerror(
                            "Failed", f"Failed to Log Action:\n{status}.",
                            parent=self.window
                        )
                else:
                    messagebox.showerror("Failed", msg, parent=self.window)
        else:
            try:
                reversing_year = int(selected)
            except ValueError:
                messagebox.showerror(
                    "Error", "Invalid Year Format.", parent=self.window
                )
                return
            confirm = messagebox.askyesno(
                "Confirm Reverse.",
                f"Reverse Closed Accounting Year: {reversing_year}?",
                parent=self.window
            )
            if confirm:
                reverser = YearEndReversalManager(self.conn)
                success, msg = reverser.reverse_year(reversing_year)
                if success:
                    messagebox.showinfo("Success", msg, parent=self.window)
                    receipt = date.today().strftime("%d/%m/%Y")
                    action = f"Reversed Closed Year {reversing_year}."
                    success, status = insert_finance_log(
                        self.conn, self.user, receipt, action
                    )
                    if success:
                        messagebox.showinfo(
                            "Success", status, parent=self.window
                        )
                    else:
                        messagebox.showerror(
                            "Failed", f"Failed to Log Action:\n{status}.",
                            parent=self.window
                        )
                else:
                    messagebox.showerror(
                        "Failed", f"Failed to Reverse Closed Year:\n{msg}.",
                        parent=self.window
                    )