import tkinter as tk
import tkinter.font as tkFont
from base_window import BaseWindow
from tkinter import ttk, messagebox
from datetime import datetime
from authentication import VerifyPrivilegePopup
from accounting_export import ReportExporter
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
        self.main_frame = tk.Frame(
            self.popup, bg="blue", bd=4, relief="solid"
        )
        self.name_entry = tk.Entry(
            self.main_frame, width=15, bd=2, relief="raised",
            font=("Arial", 11)
        )
        self.label = tk.Label(
            self.main_frame, text="Account Name Available", bg="blue",
            fg="dodgerblue", font=("Arial", 9, "italic"),
        )
        self.type_combo = ttk.Combobox(
            self.main_frame, textvariable=self.account_type_var, width=10,
            state="readonly", font=("Arial", 11),
        )
        self.type_combo["values"] = [
            "Asset",
            "Liability",
            "Equity",
            "Revenue",
            "Expense",
        ]
        self.code_entry = tk.Entry(
            self.main_frame, textvariable=self.code_var, state="readonly",
            width=5, bd=4, relief="raised", font=("Arial", 11),
        )
        self.desc_entry = tk.Text(
            self.main_frame, width=30, height=3, bd=4, relief="raised",
            font=("Arial", 11), wrap="word",
        )

        self.create_widgets()

    def create_widgets(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tk.Label(
            self.main_frame, text="Account Name:", bg="blue", fg="white",
            font=("Arial", 11, "bold"),
        ).pack(pady=(5, 0))  # Account Name
        self.name_entry.pack(pady=(0, 2))
        self.name_entry.focus_set()
        self.name_entry.bind("<KeyRelease>", self.on_name_change)
        self.name_entry.bind("<Return>", lambda e: self.type_combo.focus_set())
        self.label.pack()
        tk.Label(
            self.main_frame,
            text="Account Type:",
            bg="blue",
            fg="white",
            font=("Arial", 11, "bold"),
        ).pack(
            pady=(5, 0)
        )  # Account Type
        self.type_combo.pack(pady=(0, 5))
        self.type_combo.bind("<<ComboboxSelected>>", self.generate_code)
        # Generated Code
        tk.Label(
            self.main_frame,
            text="Generated Account Code:",
            bg="blue",
            fg="white",
            font=("Arial", 11, "bold"),
        ).pack(pady=(5, 0))
        self.code_entry.pack(pady=(0, 5))
        tk.Label(
            self.main_frame,
            text="Description:",
            bg="blue",
            fg="white",
            font=("Arial", 11, "bold"),
        ).pack(
            pady=(5, 0)
        )  # Description
        self.desc_entry.pack(pady=(0, 5))
        # Submit Button
        tk.Button(
            self.main_frame,
            text="Add Account",
            command=self.submit_account,
            bg="dodgerblue",
            fg="white",
            width=15,
            bd=2,
            relief="groove",
        ).pack(pady=10)

    def on_name_change(self, event=None):
        current_text = self.name_entry.get()
        cursor_pos = self.name_entry.index(tk.INSERT)
        if current_text.endswith(" "):  # Preserve trailing space if the user is typing
            return  # Let the user finish typing
        # Auto-capitalize each word
        capitalized = " ".join(word.capitalize() for word in current_text.split())
        if current_text != capitalized:
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, capitalized)
            self.name_entry.icursor(cursor_pos)
        # Check for existing accounts
        if capitalized:
            existing_names = check_account_name_exists(self.conn, current_text)
            if current_text in existing_names:
                self.name_entry.config(fg="red")
                self.label.config(text="Account Name Already Taken", fg="red")
            else:
                self.name_entry.config(fg="black")
                self.label.configure(text="Account Name Available", fg="dodgerblue")

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
        # Verify user privilege
        priv = "Admin Create Journal"
        verify_dialog = VerifyPrivilegePopup(self.popup, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Privilege on Requested Module.",
                parent=self.popup,
            )
            return
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
        self.popup.title("Journal Entry")
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
        self.debit_name_var = tk.StringVar()
        self.debit_code_var = tk.StringVar()
        self.debit_amount_var = tk.StringVar()
        self.credit_name_var = tk.StringVar()
        self.credit_code_var = tk.StringVar()
        self.credit_amount_var = tk.StringVar()
        self.ref_var = tk.StringVar()
        style = ttk.Style(self.popup)
        style.theme_use("alt")
        self.main_frame = tk.Frame(self.popup, bg="lightblue", bd=4, relief="solid")
        self.debit_frame = tk.LabelFrame(
            self.main_frame, text="Debit Account", bg="lightblue", bd=4, relief="ridge"
        )
        self.debit_name_combo = ttk.Combobox(
            self.debit_frame,
            textvariable=self.debit_name_var,
            width=15,
            values=self.account_names,
            state="readonly",
            font=("Arial", 11),
        )
        self.debit_code_combo = ttk.Combobox(
            self.debit_frame,
            textvariable=self.debit_code_var,
            width=5,
            values=self.account_codes,
            state="readonly",
            font=("Arial", 11),
        )
        self.debit_amount_entry = tk.Entry(
            self.debit_frame,
            textvariable=self.debit_amount_var,
            width=8,
            bd=2,
            relief="raised",
            font=("Arial", 11),
        )
        self.credit_frame = tk.LabelFrame(
            self.main_frame, text="Credit Account", bg="lightblue", bd=4, relief="ridge"
        )
        self.credit_name_combo = ttk.Combobox(
            self.credit_frame,
            textvariable=self.credit_name_var,
            width=15,
            state="readonly",
            values=self.account_names,
            font=("Arial", 11),
        )
        self.credit_code_combo = ttk.Combobox(
            self.credit_frame,
            textvariable=self.credit_code_var,
            width=5,
            values=self.account_codes,
            state="readonly",
            font=("Arial", 11),
        )
        self.credit_amount_entry = tk.Entry(
            self.credit_frame,
            textvariable=self.credit_amount_var,
            width=8,
            bd=2,
            relief="raised",
            font=("Arial", 11),
        )
        self.bottom_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="flat"
        )
        self.desc_entry = tk.Text(
            self.bottom_frame, width=40, height=4, bd=2, relief="raised"
        )

        self.build_gui()

    def build_gui(self):
        self.main_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        # Allow row 2 (Bottom frame) to expand
        self.main_frame.rowconfigure(0, weight=0)
        self.main_frame.rowconfigure(1, weight=0)
        self.main_frame.rowconfigure(2, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        # Debit Frame
        self.debit_frame.grid(row=0, column=0, sticky="w")
        tk.Label(
            self.debit_frame,
            text="Account Name:",
            bg="lightblue",
            font=("Arial", 11, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(5, 0), pady=5)
        self.debit_name_combo.grid(row=0, column=1, padx=(0, 5), pady=5)
        self.debit_name_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.sync_account_fields("debit", "name")
        )
        tk.Label(
            self.debit_frame,
            text="Account Code:",
            bg="lightblue",
            font=("Arial", 11, "bold"),
        ).grid(row=0, column=2, sticky="e", padx=(5, 0), pady=5)
        self.debit_code_combo.grid(row=0, column=3, padx=(0, 5), pady=5)
        self.debit_code_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.sync_account_fields("debit", "code")
        )
        tk.Label(
            self.debit_frame, text="Amount:", font=("Arial", 11, "bold"),
            bg="lightblue"
        ).grid(row=1, column=2, sticky="e", pady=5, padx=(5, 0))
        self.debit_amount_entry.grid(row=1, column=3, pady=5, padx=(0, 5))
        # Credit Frame
        self.credit_frame.grid(row=1, column=0, sticky="w")
        tk.Label(
            self.credit_frame,
            text="Account Name:",
            bg="lightblue",
            font=("Arial", 11, "bold"),
        ).grid(row=0, column=0, sticky="e", padx=(5, 0), pady=5)
        self.credit_name_combo.grid(row=0, column=1, padx=(0, 5), pady=5)
        self.credit_name_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.sync_account_fields("credit", "name")
        )
        tk.Label(
            self.credit_frame,
            text="Account Code:",
            bg="lightblue",
            font=("Arial", 11, "bold"),
        ).grid(row=0, column=2, sticky="e", padx=(5, 0), pady=5)
        self.credit_code_combo.grid(row=0, column=3, padx=(0, 5), pady=5)
        self.credit_code_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.sync_account_fields("credit", "code")
        )
        tk.Label(
            self.credit_frame,
            text="Amount:",
            bg="lightblue",
            font=("Arial", 11, "bold"),
        ).grid(row=1, column=2, sticky="e", pady=5, padx=(5, 0))
        self.credit_amount_entry.grid(row=1, column=3, padx=(0, 5), pady=5)
        # Bottom Frame
        self.bottom_frame.grid(row=2, column=0, pady=5, sticky="nsew")
        self.bottom_frame.columnconfigure(0, weight=0)
        self.bottom_frame.columnconfigure(1, weight=1)
        self.bottom_frame.columnconfigure(2, weight=0)
        self.bottom_frame.rowconfigure(1, weight=1)
        tk.Label(
            self.bottom_frame,
            text="Reference No:",
            bg="lightblue",
            font=("Arial", 11, "bold"),
        ).grid(row=0, column=0, pady=5, padx=(5, 0), sticky="w")
        tk.Entry(
            self.bottom_frame,
            textvariable=self.ref_var,
            width=15,
            bd=2,
            relief="raised",
            font=("Arial", 11),
        ).grid(row=0, column=1, pady=5, padx=(0, 5), sticky="w")
        tk.Label(
            self.bottom_frame,
            text="Description:",
            bg="lightblue",
            font=("Arial", 11, "bold"),
        ).grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky="w")
        self.desc_entry.grid(row=2, column=0, columnspan=2, pady=(0, 5))
        SentenceCapitalizer.bind(self.desc_entry)
        tk.Button(
            self.bottom_frame,
            text="Post",
            bg="dodgerblue",
            fg="white",
            width=10,
            bd=2,
            relief="groove",
            command=self.submit_journal,
        ).grid(row=3, column=0, columnspan=2, pady=10)
        CurrencyFormatter.add_currency_trace(
            self.debit_amount_var, self.debit_amount_entry
        )
        CurrencyFormatter.add_currency_trace(
            self.credit_amount_var, self.credit_amount_entry
        )

    def sync_account_fields(self, side, changed_field):
        name_var = self.debit_name_var if side == "debit" else self.credit_name_var
        code_var = self.debit_code_var if side == "debit" else self.credit_code_var
        value = name_var.get() if changed_field == "name" else code_var.get()
        account = get_account_by_name_or_code(self.conn, value)
        if account:
            name_var.set(account["account_name"])
            code_var.set(account["code"])
        else:
            messagebox.showwarning(
                "Not Found", f"No Matching Account For {value}.",
                parent=self.popup
            )

    def submit_journal(self):
        # Verify user privilege
        priv = "Write Journal"
        verify = VerifyPrivilegePopup(self.popup, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Permission To {priv}.",
                parent=self.popup,
            )
            return
        debit_code = self.debit_code_var.get()
        credit_code = self.credit_code_var.get()
        debit_amt = self.debit_amount_var.get().replace(",", "").strip()
        credit_amt = self.credit_amount_var.get().replace(",", "").strip()
        desc = self.desc_entry.get("1.0", tk.END).strip()
        ref_no = self.ref_var.get().strip()
        try:
            debit_val = float(debit_amt) if debit_amt else 0.00
            credit_val = float(credit_amt) if credit_amt else 0.00
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
                self.popup.destroy()
            else:
                messagebox.showerror("Error", msg, parent=self.popup)
        except ValueError:
            messagebox.showerror(
                "Invalid", "Amount Must Be Numeric.", parent=self.popup
            )


class OpeningBalancePopup(BaseWindow):
    def __init__(self, parent, conn, user):
        self.popup = tk.Toplevel(parent)
        self.popup.title("Creating Opening Balances")
        self.popup.configure(bg="lightblue")
        self.center_window(self.popup, 500, 350, parent)
        self.popup.transient(parent)
        self.popup.grab_set()

        self.conn = conn
        self.user = user
        self.accounts = get_account_name_and_code(conn)
        self.account_names = [acc["account_name"] for acc in self.accounts]
        self.account_code = [acc["code"] for acc in self.accounts]
        self.line_items = []  # Stores added opening entries
        self.account_name_var = tk.StringVar()
        self.account_code_var = tk.StringVar()
        self.debit_var = tk.StringVar()
        self.credit_var = tk.StringVar()
        self.columns = ("Account Name", "Code", "Debit", "Credit")
        style = ttk.Style()
        style.theme_use("alt")
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.configure("Treeview", font=("Arial", 10))
        self.main_frame = tk.Frame(self.popup, bg="lightblue", bd=4, relief="solid")
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings", height=8
        )

        self.build_gui()

    def build_gui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        form_frame = tk.Frame(self.main_frame, bg="lightblue")
        form_frame.pack(pady=(5, 0), fill="x")
        tk.Label(
            form_frame, text="Account Name:", bg="lightblue", font=("Arial", 11, "bold")
        ).grid(row=0, column=0, padx=(5, 0), sticky="e")
        name_combo = ttk.Combobox(
            form_frame,
            textvariable=self.account_name_var,
            width=15,
            values=self.account_names,
            state="readonly",
            font=("Arial", 11),
        )
        name_combo.grid(row=0, column=1, padx=(0, 5))
        name_combo.bind("<<ComboboxSelected>>", lambda e: self.sync_account("name"))
        name_combo.focus_set()
        tk.Label(
            form_frame, text="Account Code:", bg="lightblue", font=("Arial", 11, "bold")
        ).grid(row=0, column=2, padx=(5, 0), sticky="e")
        code_combo = ttk.Combobox(
            form_frame,
            textvariable=self.account_code_var,
            width=5,
            values=self.account_code,
            state="readonly",
            font=("Arial", 11),
        )
        code_combo.grid(row=0, column=3, padx=(0, 5))
        code_combo.bind("<<ComboboxSelected>>", lambda e: self.sync_account("code"))
        tk.Label(
            form_frame, text="Debit:", bg="lightblue", font=("Arial", 11, "bold")
        ).grid(row=1, column=0, sticky="e")
        debit_entry = tk.Entry(
            form_frame,
            textvariable=self.debit_var,
            width=8,
            bd=2,
            relief="raised",
            font=("Arial", 11),
        )
        debit_entry.grid(row=1, column=1, sticky="w")
        tk.Label(
            form_frame, text="Credit:", bg="lightblue", font=("Arial", 11, "bold")
        ).grid(row=1, column=2, sticky="e")
        credit_entry = tk.Entry(
            form_frame,
            textvariable=self.credit_var,
            width=8,
            bd=2,
            relief="raised",
            font=("Arial", 11),
        )
        credit_entry.grid(row=1, column=3, sticky="w")
        # Buttons
        btn_frame = tk.Frame(self.main_frame, bg="lightblue")
        btn_frame.pack(pady=5)
        tk.Button(
            btn_frame,
            bd=2,
            relief="groove",
            text="Add Line",
            command=self.add_line,
            bg="dodgerblue",
            fg="white",
        ).pack(side="left")
        tk.Button(
            btn_frame,
            bd=2,
            relief="groove",
            text="Remove Line",
            command=self.remove_selected,
            bg="tomato",
            fg="white",
        ).pack(side="left")
        # Treeview
        self.table_frame.pack(fill="both", expand=True, pady=(0, 10))
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.pack(expand=True, fill="both")
        # Submit Button
        tk.Button(
            self.main_frame,
            bg="green",
            fg="white",
            bd=4,
            relief="groove",
            text="Post Opening Balances",
            command=self.post_opening_balances,
        ).pack(pady=5)
        CurrencyFormatter.add_currency_trace(self.debit_var, debit_entry)
        CurrencyFormatter.add_currency_trace(self.credit_var, credit_entry)

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
            self.line_items.append(
                {
                    "account_code": code,
                    "description": f"Opening balance for {name}",
                    "debit": debit_val,
                    "credit": credit_val,
                }
            )
            self.tree.insert(
                "",
                "end",
                values=(name, code, f"{debit_val:,.2f}", f"{credit_val:,.2f}"),
            )
            self.autosize_columns()
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
            self.tree.delete(sel)
            del self.line_items[index]

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

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.tree["columns"]:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_text = str(self.tree.set(item, col))
                cell_width = font.measure(cell_text)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width)


class ReverseJournalPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Reverse Journal Entry")
        self.center_window(self.window, 1100, 700, master)
        self.window.configure(bg="lightblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 10))
        self.code = None
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.columns = (
            "No", "Date", "Journal ID", "Account Code", "Account Name",
            "Description", "Debit", "Credit",
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        top_frame = tk.Frame(self.main_frame, bg="lightblue")
        top_frame.pack(fill="x", pady=(5, 0), padx=5)
        tk.Label(
            top_frame, text="Select Entry to Reverse.", bg="lightblue", bd=4,
            font=("Arial", 14, "italic", "underline"), fg="dodgerblue",
            relief="ridge"
        ).pack(side="left", padx=20, ipadx=5)
        tk.Button(
            top_frame, text="Reverse Entry", bg="green", fg="white", bd=2,
            relief="groove", command=self.reverse_selected,
            font=("Arial", 10)
        ).pack(side="right")
        tk.Button(
            top_frame, text="Delete Entry", bg="green", fg="white", bd=2,
            relief="groove", command=self.delete_selected, font=("Arial", 10)
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
        self.tree.bind(
            "<MouseWheel>",
            lambda e: self.tree.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )
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
                row["account_code"],
                row["account_name"],
                row["description"],
                f"{row['debit']:,.2f}",
                f"{row['credit']:,.2f}",
            ), tags=(tag,))
        self.autosize_columns()

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_text = str(self.tree.set(item, col))
                cell_width = font.measure(cell_text)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 5)

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
        self.center_window(self.window, 1000, 650, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.accounts = get_account_name_and_code(conn)
        self.accounts_names = [acc["account_name"] for acc in self.accounts]
        self.accounts_codes = [acc["code"] for acc in self.accounts]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 10))
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.name_cb = ttk.Combobox(
            self.top_frame, width=20, values=self.accounts_names,
            state="readonly", font=("Arial", 11)
        )
        self.code_cb = ttk.Combobox(
            self.top_frame, width=5, values=self.accounts_codes,
            state="readonly", font=("Arial", 11)
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

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.top_frame.pack(fill="x")
        tk.Label(
            self.top_frame, text="Select Account Name:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(5, 0))
        self.name_cb.pack(side="left", padx=(0, 5))
        self.name_cb.current(0)
        tk.Label(
            self.top_frame, text="Select Account Code:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(5, 0))
        self.code_cb.pack(side="left", padx=(0, 5))
        self.name_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.sync_account_fields("name")
        )
        self.code_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.sync_account_fields("code")
        )
        btn_frame = tk.Frame(self.top_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=5)
        buttons = {
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
        }
        for text, command in buttons.items():
            tk.Button(
                btn_frame, text=text, bd=2, relief="groove", bg="blue", fg="white",
                command=command, font=("Arial", 10, "bold")
            ).pack(side="left")
        tk.Label(
            self.table_frame, textvariable=self.title_var, bg="lightblue",
            fg="blue", bd=2, relief="raised",
            font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="center", ipadx=10)
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
        # MouseWheel binding
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        self.tree.tag_configure("balance", font=("Arial", 11, "bold"))
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

        self.title_var.set(f"{account_name} : {account_code}")
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
        today = date.today().strftime("%d/%m/%Y")
        balancing = max(total_debit, total_credit)
        if total_debit > total_credit:
            desc = f"Balance C/d as at {today}"
            balance = total_debit - total_credit
            self.tree.insert("", "end", values=(
                "", "", "", desc, 0.00, f"{balance:,}"
            ), tags=("balance",))
        elif total_credit > total_debit:
            desc = f"Balance C/d as at {today}"
            balance = total_credit - total_debit
            self.tree.insert("", "end", values=(
                "", "", "", desc, f"{balance:,}", 0.00
            ), tags=("balance",))
        self.tree.insert("", "end", values=(
            "", "", "", "Total", f"{balancing:,}", f"{balancing:,}"
        ), tags=("total",))
        self.auto_resize_columns()

    def auto_resize_columns(self):
        font = tkFont.Font()
        for col in self.tree["columns"]:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_text = str(self.tree.set(item, col))
                cell_width = font.measure(cell_text)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 2)

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
        self.center_window(self.window, 1100, 650, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        # Define columns
        self.columns = (
            "No", "Account Code", "Account Name", "Account Type", "Debit",
            "Credit", "Balance"
        )
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 11))
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Top frame (title + button)
        top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        top_frame.pack(fill="x")
        year = date.today().year
        title_text = f"Trial Balance For Year Ended December {year}."
        tk.Label(
            top_frame, text=title_text, bg="lightblue", fg="blue",
            font=("Arial", 18, "bold", "underline"), bd=2, relief="flat"
        ).pack(side="left", padx=20)
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
                btn_frame, text=text, bd=2, relief="groove", bg="blue",
                fg="white", command=command, font=("Arial", 10, "bold")
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
        # Mouse Wheel scrolling
        self.tree.bind(
            "<MouseWheel>", lambda e: self.tree.yview_scroll(
                int(-1 * (e.delta / 120)), "units"
            ),
        )
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
        self.autosize_columns()

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_text = str(self.tree.set(item, col))
                cell_width = font.measure(cell_text)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 5)

    def _collect_current_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append(
                {
                    "No": vals[0],
                    "Account Code": vals[1],
                    "Account Name": vals[2],
                    "Account Type": vals[3],
                    "Debit": vals[4],
                    "Credit": vals[5],
                    "Balance": vals[6],
                }
            )
        return rows

    def _make_exporter(self):
        year = date.today().year
        title = f"Trial Balance For Year Ended December {year}."
        columns = [
            "No", "Account Code", "Account Name", "Account Type", "Debit",
            "Credit", "Balance",
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
        self.center_window(self.window, 900, 550, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.columns = (
            "No", "Category", "Account Name", "Code", "Amount"
        )
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"))
        style.configure("Treeview", font=("Arial", 11))
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Table Frame
        top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        top_frame.pack(fill="x")
        year = date.today().year
        title_text = f"Income Statement For Year Ended {year}."
        tk.Label(
            top_frame, text=title_text, bg="lightblue", fg="blue", bd=2,
            relief="ridge", font=("Arial", 18, "bold", "underline"),
        ).pack(side="left", ipadx=10)
        # Buttons Frame
        btn_frame = tk.Frame(top_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=5)
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
        # Mouse wheel support
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))
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
        self.autosize_columns()

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_text = str(self.tree.set(item, col))
                cell_width = font.measure(cell_text)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 5)

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
        year = date.today().year
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
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 11))
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

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
            top_frame, text=title_text, bg="lightblue", fg="blue", bd=2,
            relief="ridge", font=("Arial", 18, "bold", "underline"),
        ).pack(side="left", ipadx=10)
        # Buttons Frame
        btn_frame = tk.Frame(top_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=5)
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
        # Mouse Wheel scroll
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))
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
        self.autosize_columns()

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_text = str(self.tree.set(item, col))
                cell_width = font.measure(cell_text)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 5)

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
        title = f"Cash Flow Statement For Year {datetime.now().year}."
        columns = ["No", "Category", "Account Code", "Account Name", "Amount", "Total"]
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
        style.theme_use("classic")
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"))
        style.configure("Treeview", font=("Arial", 11))
        self.columns = (
            "No", "Account Code", "Account Name", "Debit", "Credit"
        )
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Title Frame
        title_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        title_frame.pack(fill="x", padx=5)
        year = datetime.now().year
        title_text = f"Balance Sheet For Year Ended {year}"
        title_label = tk.Label(
            title_frame, text=title_text, bg="lightblue", bd=2,
            relief="ridge", font=("Arial", 18, "bold", "underline"),
        )
        title_label.pack(side="left", ipadx=10)
        # Buttons Frame
        btn_frame = tk.Frame(title_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=5)
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
        # Mousewheel Scroll
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        # Apply tag style
        self.tree.tag_configure(
            "category_header", font=("Arial", 12, "bold", "underline"),
            background="#FFFFFF"
        ) # Pure White Background
        self.tree.tag_configure(
            "total_row", font=("Arial", 11, "bold"), background="#FAFAFA"
        ) # Very light Gray
        self.tree.tag_configure(
            "balance", font=("Arial", 12, "bold"), background="#FCE4EC"
        ) # Light Pink Background
        self.tree.tag_configure(
            "grand_total_row", font=("Arial", 12, "bold", "underline"),
            background="#c5cae9"
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
            ), tags=("category_header",))
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
            ), tags=("total_row",))
        # Grand total row (Assets vs Liabilities + Equity)
        grand_total_debit = total_assets
        grand_total_credit = (total_liabilities + total_equity)
        if grand_total_debit > grand_total_credit:
            balancing_figure = (grand_total_debit - grand_total_credit)
            self.tree.insert("", "end", values=(
                "", "", "Balance C/d", "", f"{balancing_figure:,.2f}"
            ), tags=("balance",))
        elif grand_total_credit > grand_total_debit:
            balancing_figure = (grand_total_credit-grand_total_debit)
            self.tree.insert("", "end", values=(
                "", "", "Balance C/d", f"{balancing_figure:,.2f}", ""
            ), tags=("balance",))
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
        ), tags=("grand_total_row",))

        self.autosize_columns()

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_text = str(self.tree.set(item, col))
                cell_width = font.measure(cell_text)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 5)

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
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.btn_close_year = tk.Button(
            self.top_frame, text="Close Year", bg="green", fg="white", bd=2,
            relief="groove", command=self.show_close_year,
        )
        self.btn_reverse_year = tk.Button(
            self.top_frame, text="Reverse Closed Year", bg="red", fg="white",
            bd=2, relief="groove", command=self.show_reverse_year,
        )
        # Middle content frame
        self.middle_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="ridge"
        )
        # Dynamic title label (inside content area)
        self.mode_title_label = tk.Label(
            self.middle_frame, text="", bg="lightblue", bd=2, relief="ridge",
            font=("Arial", 14, "bold", "underline")
        )
        # Dynamic label + combobox
        self.select_label = tk.Label(
            self.middle_frame, text="", bg="lightblue",
            font=("Arial", 12, "bold")
        )
        self.combobox = ttk.Combobox(
            self.middle_frame, state="readonly", textvariable=self.combo_var,
            width=27, font=("Arial", 11)
        )
        # Bottom action button
        self.action_btn = tk.Button(
            self.middle_frame, text="", bg="blue", fg="white", bd=2,
            relief="groove", font=("Arial", 11, "bold"),
            command=self.perform_action,
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Pack top frame + buttons
        self.top_frame.pack(fill="x", padx=5, ipady=5)
        self.btn_close_year.pack(side="left", padx=10)
        self.btn_reverse_year.pack(side="left", padx=10)
        # Middle Section
        self.middle_frame.pack(fill="both", expand=True)
        self.mode_title_label.pack(anchor="center", pady=3, ipadx=5)
        self.select_label.pack(anchor="w", pady=5)
        self.combobox.pack(anchor="w", fill="x", padx=10)
        self.action_btn.pack(pady=15)
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



# if __name__ == "__main__":
#     from connect_to_db import connect_db
#
#     conn = connect_db()
#     root = tk.Tk()
#     CloseYearPopup(root, conn, "Sniffy")
#     root.mainloop()