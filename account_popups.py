import tkinter as tk
import tkinter.font as tkFont
from base_window import BaseWindow
from tkinter import ttk, messagebox
from datetime import datetime
from authentication import VerifyPrivilegePopup
from accounting_export import ReportExporter
from working_on_accounting import (
    count_accounts_by_type, check_account_name_exists,
    get_account_name_and_code, insert_account, insert_opening_balance,
    fetch_journal_lines_by_account_code, insert_journal_entry,
    get_account_by_name_or_code, reverse_journal_entry,
    fetch_all_journal_lines_with_names, fetch_trial_balance,
    get_income_statement, CashFlowStatement, get_balance_sheet,
    delete_journal_entry
)
from connect_to_db import connect_db

class InsertAccountPopup(BaseWindow):
    def __init__(self, parent, conn, user):
        self.popup = tk.Toplevel(parent)
        self.popup.title("New Account")
        self.popup.configure(bg="blue")
        self.center_window(self.popup, 350, 270)
        self.popup.transient(parent)
        self.popup.grab_set()

        self.conn = conn
        self.user = user
        self.account_type_var = tk.StringVar()
        self.code_var = tk.StringVar()
        self.name_entry = tk.Entry(self.popup, width=30)
        self.label = tk.Label(self.popup, text="Account Name Available", bg="blue", fg="dodgerblue")
        self.type_combo = ttk.Combobox(self.popup, textvariable=self.account_type_var, width=30, state="readonly")
        self.type_combo['values'] = ['Asset', 'Liability', 'Equity', 'Revenue', 'Expense']
        self.code_entry = tk.Entry(self.popup, textvariable=self.code_var, state="readonly", width=30)
        self.desc_entry = tk.Entry(self.popup, width=40)

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.popup, text="Account Name:", bg="blue", fg="white").pack(pady=(5, 0)) # Account Name
        self.name_entry.pack()
        self.name_entry.focus_set()
        self.name_entry.bind("<KeyRelease>", self.on_name_change)
        self.name_entry.bind("<Return>", lambda e: self.type_combo.focus_set())
        self.label.pack()
        tk.Label(self.popup, text="Account Type:", bg="blue", fg="white").pack(pady=(5, 0)) # Account Type
        self.type_combo.pack()
        self.type_combo.bind("<<ComboboxSelected>>", self.generate_code)
        # Generated Code
        tk.Label(self.popup, text="Generated Account Code:", bg="blue", fg="white").pack(pady=(5, 0))
        self.code_entry.pack()
        tk.Label(self.popup, text="Description:", bg="blue", fg="white").pack(pady=(5, 0)) # Description
        self.desc_entry.pack()
        self.desc_entry.bind("<Return>", lambda e: post_btn.focus_set())
        # Submit Button
        post_btn = tk.Button(self.popup, text="Add Account", command=self.submit_account, bg="dodgerblue", width=15,
                  fg="white")
        post_btn.pack(pady=20)

    def on_name_change(self, event=None):
        current_text = self.name_entry.get()
        cursor_pos = self.name_entry.index(tk.INSERT)
        if current_text.endswith(" "): # Preserve trailing space if the user is typing
            return # Let the user finish typing
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
                "Expense": 5
            }[acc_type]
            new_code = str(prefix * 10) + str(count + 1)
            self.code_var.set(new_code)
            self.desc_entry.focus_set()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate code:\n{e}")

    def submit_account(self):
        # Verify user privilege
        priv = "Create Journal Account"
        verify_dialog = VerifyPrivilegePopup(self.popup, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        name = self.name_entry.get().strip()
        acc_type = self.account_type_var.get()
        code = self.code_var.get()
        desc = self.desc_entry.get().strip()
        if not (name and acc_type and code):
            messagebox.showwarning("Missing Data", "Please fill in all fields.")
            return
        try:
            result = insert_account(self.conn, name, acc_type, code, desc)
            if "successfully" in result.lower():
                messagebox.showinfo("Success", result)
                self.popup.destroy()
            else:
                messagebox.showerror("Error", result)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to insert account:\n{e}")

class JournalEntryPopup(BaseWindow):
    def __init__(self, parent, conn, user):
        self.popup = tk.Toplevel(parent)
        self.popup.title("Journal Entry")
        self.center_window(self.popup, 820, 200)
        self.popup.configure(bg="lightblue")
        self.popup.transient(parent)
        self.popup.grab_set()

        self.conn = conn
        self.user = user
        self.accounts = get_account_name_and_code(conn) # [{'name':..., 'code':...}, ...]
        self.account_names = [acc['account_name'] for acc in self.accounts]
        self.account_codes = [acc['code'] for acc in self.accounts]
        self.main_frame = tk.Frame(self.popup, bg="lightblue")
        self.debit_frame = tk.LabelFrame(self.main_frame, text="Debit Account", bg="lightblue")
        self.debit_name_var = tk.StringVar()
        self.debit_code_var = tk.StringVar()
        self.debit_amount_var = tk.StringVar()
        self.debit_name_combo = ttk.Combobox(self.debit_frame, textvariable=self.debit_name_var,
                                             values=self.account_names, state="readonly", width=20)
        self.debit_code_combo = ttk.Combobox(self.debit_frame, textvariable=self.debit_code_var,
                                             values=self.account_codes, state="readonly", width=7)
        self.debit_amount_entry = tk.Entry(self.debit_frame, textvariable=self.debit_amount_var, width=10)
        self.credit_frame = tk.LabelFrame(self.main_frame, text="Credit Account", bg="lightblue")
        self.credit_name_var = tk.StringVar()
        self.credit_code_var = tk.StringVar()
        self.credit_amount_var = tk.StringVar()
        self.credit_name_combo = ttk.Combobox(self.credit_frame, textvariable=self.credit_name_var, width=20,
                                              state="readonly", values=self.account_names)
        self.credit_code_combo = ttk.Combobox(self.credit_frame, textvariable=self.credit_code_var, width=7,
                                              values=self.account_codes, state="readonly")
        self.credit_amount_entry = tk.Entry(self.credit_frame, textvariable=self.credit_amount_var, width=10)
        self.bottom_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.ref_var = tk.StringVar()
        self.desc_entry = tk.Entry(self.bottom_frame, width=40)

        self.build_gui()

    def build_gui(self):
        self.main_frame.pack(padx=(5, 0), pady=5, fill="both", expand=True)
        self.debit_frame.grid(row=0, column=0, pady=5, sticky="n")
        tk.Label(self.debit_frame, text="Account Name:", bg="lightblue").grid(row=0, column=0, sticky="w", padx=2)
        self.debit_name_combo.grid(row=0, column=1, padx=(0, 5))
        self.debit_name_combo.bind("<<ComboboxSelected>>", lambda e: self.sync_account_fields('debit',
                                                                                              'name'))
        tk.Label(self.debit_frame, text="Account Code:", bg="lightblue").grid(row=0, column=2, sticky="w", padx=2)
        self.debit_code_combo.grid(row=0, column=3, padx=2)
        self.debit_code_combo.bind("<<ComboboxSelected>>", lambda e: self.sync_account_fields('debit',
                                                                                              'code'))
        tk.Label(self.debit_frame, text="Amount:", bg="lightblue").grid(row=1, column=2, sticky="w", pady=5)
        self.debit_amount_entry.grid(row=1, column=3, pady=5)
        self.credit_frame.grid(row=0, column=1, pady=5, padx=5, sticky="n")
        tk.Label(self.credit_frame, text="Account Name:", bg="lightblue").grid(row=0, column=0, sticky="w", padx=(2, 0))
        self.credit_name_combo.grid(row=0, column=1, padx=(0, 2))
        self.credit_name_combo.bind("<<ComboboxSelected>>", lambda e: self.sync_account_fields('credit',
                                                                                               'name'))
        tk.Label(self.credit_frame, text="Account Code:", bg="lightblue").grid(row=0, column=2, sticky="w", padx=(2, 0))
        self.credit_code_combo.grid(row=0, column=3, padx=(0, 2))
        self.credit_code_combo.bind("<<ComboboxSelected>>", lambda e: self.sync_account_fields('credit',
                                                                                               'code'))
        tk.Label(self.credit_frame, text="Amount:", bg="lightblue").grid(row=1, column=2, sticky="w", pady=5)
        self.credit_amount_entry.grid(row=1, column=3, sticky="w", padx=(0, 2), pady=5)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, pady=(0, 5), sticky="se")
        tk.Label(self.bottom_frame, text="Ref No:", bg="lightblue").grid(row=0, column=0, pady=(0, 5), padx=(5, 0))
        tk.Entry(self.bottom_frame, textvariable=self.ref_var, width=20).grid(row=0, column=1, pady=(0, 5), padx=(0, 5))
        tk.Label(self.bottom_frame, text="Description:", bg="lightblue").grid(row=0, column=2, pady=(0, 5), padx=(5, 0))
        self.desc_entry.grid(row=0, column=3, padx=(0, 5), pady=(0, 5))
        post_btn = tk.Button(self.bottom_frame, text="Post", bg="dodgerblue", fg="white", width=10,
                             command=self.submit_journal)
        post_btn.grid(row=1, column=2, columnspan=2, padx=15)

    def sync_account_fields(self, side, changed_field):
        name_var = self.debit_name_var if side == 'debit' else self.credit_name_var
        code_var = self.debit_code_var if side == 'debit' else self.credit_code_var
        value = name_var.get() if changed_field == 'name' else code_var.get()
        account = get_account_by_name_or_code(self.conn, value)
        if account:
            name_var.set(account['account_name'])
            code_var.set(account['code'])
        else:
            messagebox.showwarning("Not Found", f"No matching account for '{value}'")

    def submit_journal(self):
        # Verify user privilege
        priv = "Write Journal"
        verify_dialog = VerifyPrivilegePopup(self.popup, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        debit_code = self.debit_code_var.get()
        credit_code = self.credit_code_var.get()
        debit_amt = self.debit_amount_var.get()
        credit_amt = self.credit_amount_var.get()
        desc = self.desc_entry.get().strip()
        ref_no = self.ref_var.get().strip()
        try:
            debit_val = float(debit_amt) if debit_amt else 0.00
            credit_val = float(credit_amt) if credit_amt else 0.00
            if debit_val == 0 and credit_val == 0:
                messagebox.showwarning("Input Error", "Enter at least one amount.")
                return
            if not debit_code or not credit_code:
                messagebox.showwarning("Input Error", "Select both debit and credit accounts.")
                return
            lines = [
                {"account_code": debit_code, "description": desc, "debit": debit_val, "credit": 0.00},
                {"account_code": credit_code, "description": desc, "debit": 0.00, "credit": credit_val}
            ]
            success, msg = insert_journal_entry(self.conn, ref_no, lines)
            if success:
                messagebox.showinfo("Success", msg)
                self.popup.destroy()
            else:
                messagebox.showerror("Error", msg)
        except ValueError:
            messagebox.showerror("Invalid Input", "Amount must be Numeric.")

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
        self.account_names = [acc['account_name'] for acc in self.accounts]
        self.account_code = [acc['code'] for acc in self.accounts]
        self.line_items = [] # Stores added opening entries
        self.account_name_var = tk.StringVar()
        self.account_code_var = tk.StringVar()
        self.debit_var = tk.StringVar()
        self.credit_var = tk.StringVar()
        self.columns = ("Account Name", "Code", "Debit", "Credit")
        self.tree = ttk.Treeview(self.popup, columns=self.columns, show="headings", height=8)

        self.build_gui()

    def build_gui(self):
        form_frame = tk.Frame(self.popup, bg="lightblue")
        form_frame.pack(pady=(5, 0), fill="x")
        tk.Label(form_frame, text="Account Name:", bg="lightblue").grid(row=0, column=0, padx=(5, 0), sticky="e")
        name_combo = ttk.Combobox(form_frame, textvariable=self.account_name_var, values=self.account_names, width=25,
                                  state="readonly")
        name_combo.grid(row=0, column=1, padx=(0, 5))
        name_combo.bind("<<ComboboxSelected>>", lambda e: self.sync_account("name"))
        tk.Label(form_frame, text="Account Code:", bg="lightblue").grid(row=0, column=2, padx=(5, 0), sticky="e")
        code_combo = ttk.Combobox(form_frame, textvariable=self.account_code_var, values=self.account_code, width=10,
                                  state="readonly")
        code_combo.grid(row=0, column=3, padx=(0, 5))
        code_combo.bind("<<ComboboxSelected>>", lambda e: self.sync_account("code"))
        tk.Label(form_frame, text="Debit:", bg="lightblue").grid(row=1, column=0, sticky="e")
        tk.Entry(form_frame, textvariable=self.debit_var, width=10).grid(row=1, column=1, sticky="w")
        tk.Label(form_frame, text="Credit:", bg="lightblue").grid(row=1, column=2, sticky="e")
        tk.Entry(form_frame, textvariable=self.credit_var, width=10).grid(row=1, column=3, sticky="w")
        # Buttons
        btn_frame = tk.Frame(self.popup, bg="lightblue")
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="+ Add Line", command=self.add_line, bg="dodgerblue", fg="white").pack(side="left",
                                                                                                         padx=10)
        tk.Button(btn_frame, text="Remove Selected", command=self.remove_selected, bg="tomato",
                  fg="white").pack(side="left")
        # Treeview
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.pack(pady=5, padx=5, expand=True, fill="both")
        # Submit Button
        tk.Button(self.popup, text="Post Opening Balances", command=self.post_opening_balances, bg="green", fg="white",
                  width=20).pack(pady=10)

    def sync_account(self, changed):
        value = self.account_name_var.get() if changed == "name" else self.account_code_var.get()
        acc = get_account_by_name_or_code(self.conn, value)
        if acc:
            self.account_name_var.set(acc['account_name'])
            self.account_code_var.set(acc['code'])
    def add_line(self):
        name = self.account_name_var.get()
        code = self.account_code_var.get()
        debit = self.debit_var.get()
        credit = self.credit_var.get()
        try:
            debit_val = float(debit) if debit else 0.00
            credit_val = float(credit) if credit else 0.00
            if not name or not code:
                messagebox.showwarning("Missing Info", "Please select account name and code.")
                return
            if debit_val == 0.00 and credit_val == 0.00:
                messagebox.showwarning("Invalid", "Enter at least a debit or credit amount.")
                return
            self.line_items.append({
                "account_code": code,
                "description": f"Opening balance for {name}",
                "debit": debit_val,
                "credit": credit_val
            })
            self.tree.insert("", "end", values=(name, code, f"{debit_val:,.2f}", f"{credit_val:,.2f}"))
            self.autosize_columns()
            # Clear entries
            self.account_name_var.set("")
            self.account_code_var.set("")
            self.debit_var.set("")
            self.credit_var.set("")
        except ValueError:
            messagebox.showerror("Invalid Input", "Debit and Credit must be numeric.")

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        for sel in selected:
            index = self.tree.index(sel)
            self.tree.delete(sel)
            del self.line_items[index]
    def post_opening_balances(self):
        # Verify user privilege
        priv = "Insert Initial Journal Balance"
        verify_dialog = VerifyPrivilegePopup(self.popup, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        if not self.line_items:
            messagebox.showwarning("Empty", "No lines added.")
            return
        success, msg = insert_opening_balance(self.conn, self.line_items)
        if success:
            messagebox.showinfo("Success", msg)
            self.popup.destroy()
        else:
            messagebox.showerror("Error", msg)

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.tree["columns"]:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_text = str(self.tree.set(item, col))
                cell_width = font.measure(cell_text)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 10)

class ViewJournalWindow(BaseWindow):
    def __init__(self, master, conn):
        self.window = tk.Toplevel(master)
        self.window.title("Journal Viewer")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 900, 500, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.accounts = get_account_name_and_code(conn)
        self.accounts_names = [acc['account_name'] for acc in self.accounts]
        self.accounts_codes = [acc['code'] for acc in self.accounts]
        self.top_frame = tk.Frame(self.window, bg="lightblue")
        self.name_cb = ttk.Combobox(self.top_frame, width=25, values=self.accounts_names, state="readonly")
        self.code_cb = ttk.Combobox(self.top_frame, width=10, values=self.accounts_codes, state="readonly")
        self.title_var = tk.StringVar()
        self.table_frame = tk.Frame(self.window, bg="lightblue")
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        self.columns = ("No", "Journal ID", "Account Code", "Description", "Debit", "Credit")
        self.tree = ttk.Treeview(self.table_frame, columns=self.columns, show="headings")

        self.build_ui()

    def build_ui(self):
        self.top_frame.pack(fill='x', pady=5)
        tk.Label(self.top_frame, text="Select Account Name:", bg="lightblue").pack(side="left", padx=(5, 0))
        self.name_cb.pack(side="left", padx=(0, 5))
        tk.Label(self.top_frame, text="Select Account Code:", bg="lightblue").pack(side="left", padx=(5, 0))
        self.code_cb.pack(side="left", padx=(0, 5))
        self.name_cb.bind("<<ComboboxSelected>>", lambda e: self.sync_account_fields('name'))
        self.code_cb.bind("<<ComboboxSelected>>", lambda e: self.sync_account_fields('code'))
        title_frame = tk.Frame(self.window, bg="lightblue")
        title_frame.pack(fill="x", padx=10)
        tk.Label(title_frame, textvariable=self.title_var, font=("Arial", 13, "bold"),
                 bg="lightblue").pack(anchor="center")
        self.table_frame.pack(fill="both", expand=True, padx=(0, 5), pady=10)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        # MouseWheel binding
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(int(-1*(e.delta/120)), "units"))

    def sync_account_fields(self, changed_field):
        value = self.name_cb.get() if changed_field == 'name' else self.code_cb.get()
        account = get_account_by_name_or_code(self.conn, value)
        if account:
            self.name_cb.set(account['account_name'])
            self.code_cb.set(account['code'])
            self.display_journal_lines(account['code'], account['account_name'])
        else:
            messagebox.showwarning("Not Found", f"No matching account for '{value}'")

    def display_journal_lines(self, account_code, account_name):
        for row in self.tree.get_children():
            self.tree.delete(row)
        lines = fetch_journal_lines_by_account_code(self.conn, account_code)
        if not lines:
            return
        total_debit = 0
        total_credit = 0

        self.title_var.set(account_name)
        for idx, line in enumerate(lines, start=1):
            self.tree.insert("", "end", values=(
                idx,
                line['journal_id'],
                line['account_code'],
                line['description'],
                f"{line['debit']:,.2f}",
                f"{line['credit']:,.2f}"
            ))
            total_debit += line['debit']
            total_credit += line['credit']
        # Insert balance carried down if necessary
        if total_debit > total_credit:
            balance = total_debit - total_credit
            self.tree.insert("", "end", values=(
                "-", "-", account_code, "Balance c/d", 0.00, f"{balance:,.2f}"
            ))
        elif total_credit > total_debit:
            balance = total_credit -  total_debit
            self.tree.insert("", "end", values=(
                "-", "-", account_code, "Balance c/d", f"{balance:,.2f}", 0.00
            ))
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
            self.tree.column(col, width=max_width + 10)

class ReverseJournalPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Reverse Journal Entry")
        self.center_window(self.window, 1000, 600, master)
        self.window.configure(bg="lightblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.table_frame = tk.Frame(self.window, bg="lightblue")
        self.columns = ("No", "Date", "Journal ID", "Account Code",
                        "Account Name", "Description", "Debit", "Credit")
        self.tree = ttk.Treeview(self.table_frame, columns=self.columns, show="headings")
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        top_frame = tk.Frame(self.window, bg="lightblue")
        top_frame.pack(fill="x", pady=(5, 0), padx=5)
        tk.Label(top_frame, text="Select Entry to Reverse", bg="lightblue",
                 font=("Arial", 12, "italic"), fg="dodgerblue").pack(side="left", padx=(20, 0))
        tk.Button(top_frame, text="Reverse Entry", bg="green", fg="white",
                  command=self.reverse_selected).pack(side="right")
        tk.Button(top_frame, text="Delete Entry", bg="green", fg="white",
                  command=self.delete_selected).pack(side="right")
        self.table_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        y_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(int(-1 * (e.delta/120)), "units"))

    def populate_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = fetch_all_journal_lines_with_names(self.conn)
        if isinstance(rows, str):
            messagebox.showerror("Error", rows)
            return
        for i, row in enumerate(rows, start=1):
            self.tree.insert("", "end", values=(
                i,
                row["entry_date"].strftime("%Y/%m/%d"),
                row["journal_id"],
                row["account_code"],
                row["account_name"],
                row["description"],
                f"{row['debit']:,.2f}",
                f"{row['credit']:,.2f}"
            ))
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
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn,
                                             self.user, priv_name)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied",
                                   f"You do not have permission to {priv_name}.")
            return
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning(
                "No Selection",
                f"Please select journal entry to {action_name.lower()}.")
            return
        journal_id = self.tree.set(selected, "Journal ID")
        if not journal_id:
            messagebox.showerror("Error", "No journal ID Found.")
            return
        confirm = messagebox.askyesno(
            "Confirm",
            f"Are you sure to {action_name.lower()} journal #{journal_id}?")
        if not confirm:
            return
        # Perform the action
        result = action_func(journal_id)
        # Handle return type (tuple or string)
        if isinstance(result, tuple): # reverse_journal_entry returns (success, msg)
            success, msg = result
        else:
            success = "successfully" in result.lower()
            msg = result
        if success:
            messagebox.showinfo("Success", msg)
            self.populate_table()
        else:
            messagebox.showerror("Error", msg)

    def delete_selected(self):
        self._handle_selected_entry(
            action_name="Delete",
            priv_name="Delete Journal",
            action_func=lambda jid: delete_journal_entry(self.conn, jid)
        )

    def reverse_selected(self):
        self._handle_selected_entry(
            action_name="Reverse",
            priv_name="Reverse Journal",
            action_func=lambda jid: reverse_journal_entry(self.conn, jid)
        )

class TrialBalanceWindow(BaseWindow):
    def __init__(self, root, conn, user):
        self.window = tk.Toplevel(root)
        self.window.title("Trial Balance")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 1000, 600, root)
        self.window.transient(root)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        # Define columns
        self.table_frame = tk.Frame(self.window, bg="lightblue")
        self.columns = ("No", "Account Code", "Account Name", "Account Type", "Debit", "Credit", "Balance")
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.tree = ttk.Treeview(self.table_frame, columns=self.columns, show="headings")

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        # Top frame (title + button)
        top_frame = tk.Frame(self.window, bg="lightblue")
        top_frame.pack(fill="x", padx=5, pady=(5, 0))
        tk.Label(top_frame, text="Trial Balance Report", bg="lightblue",
                 font=("Arial", 14, "bold")).pack(anchor="center", padx=20)
        self.table_frame.pack(fill="both", expand=True, padx=10)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        y_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        # Mouse Wheel scrolling
        self.tree.bind("<MouseWheel>", lambda e:
                       self.tree.yview_scroll(int(-1 * (e.delta/120)), "units"))
        # Bottom action buttons
        btn_frame = tk.Frame(self.window, bg="lightblue")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Button(btn_frame, text="Export Excel", width=10, bg="dodgerblue",
                  command=self.on_export_excel).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Export PDF", width=10, bg="dodgerblue",
                  command=self.on_export_pdf).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Print", width=10, bg="dodgerblue",
                  command=self.on_print).pack(side="right", padx=5)

    def populate_table(self):
        data = fetch_trial_balance(self.conn)
        if isinstance(data, str):
            messagebox.showerror("Error", data)
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, row in enumerate(data, start=1):
            self.tree.insert("", "end", values=(
                i,
                row["code"],
                row["account_name"],
                row["account_type"],
                f"{row['total_debit'] or 0.00:,.2f}",
                f"{row['total_credit'] or 0.00:,.2f}",
                f"{row['balance'] or 0.00:,.2f}"
            ))
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
            rows.append({
                "No": vals[0],
                "Account Code": vals[1],
                "Account Name": vals[2],
                "Account Type": vals[3],
                "Debit": vals[4],
                "Credit": vals[5],
                "Balance": vals[6]
            })
        return rows

    def _make_exporter(self):
        title = "Trial Balance"
        columns = ["No", "Account Code", "Account Name", "Account Type", "Debit", "Credit", "Balance"]
        rows = self._collect_current_rows()
        return ReportExporter(self.window, title, columns, rows)

    def _check_privilege(self):
        priv = "View Trial Balance"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        return getattr(verify_dialog, "result", None) == "granted"

    def on_export_excel(self):
        if not self._check_privilege():
            messagebox.showwarning("Access Denied",
                                   "You do not permission to export ")
            return
        exporter = self._make_exporter()
        exporter.export_excel()
    def on_export_pdf(self):
        if not self._check_privilege():
            messagebox.showwarning("Access Denied",
                                   "You do not permission to export ")
            return
        exporter = self._make_exporter()
        exporter.export_pdf()
    def on_print(self):
        if not self._check_privilege():
            messagebox.showwarning("Access Denied",
                                   "You do not permission to export ")
            return
        exporter = self._make_exporter()
        exporter.print()

class IncomeStatementWindow(BaseWindow):
    def __init__(self, parent, conn):
        self.window = tk.Toplevel(parent)
        self.window.title("Income Statement")
        self.window.configure(bg="lightblue")
        self.center_window(self.window, 900, 600, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.columns = ("No", "Category", "Account Code", "Account Name", "Amount")
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        self.table_frame = tk.Frame(self.window, bg="lightblue")
        self.tree = ttk.Treeview(self.table_frame, columns=self.columns,
                                 show="headings", selectmode="browse")
        self.build_ui()
        self.populate_table()

    def build_ui(self):
        # Table Frame
        top_frame = tk.Frame(self.window, bg="lightblue")
        top_frame.pack(fill="x", padx=5, pady=(5, 0))
        tk.Label(top_frame, text="Income Statement", bg="lightblue",
                 font=("Arial", 14, "bold")).pack(anchor="center", padx=20)
        # Table Area
        self.table_frame.pack(fill="both", expand=True, padx=10)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        y_scroll = ttk.Scrollbar(self.table_frame, orient="vertical",
                                 command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        # Mouse wheel support
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        # Bottom buttons
        btn_frame = tk.Frame(self.window, bg="lightblue")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Button(btn_frame, text="Export Excel", width=10, bg="dodgerblue",
                  command=self.on_export_excel).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Export PDF", width=10, bg="dodgerblue",
                  command=self.on_export_pdf).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Print", width=10, bg="dodgerblue",
                  command=self.on_print).pack(side="right", padx=5)

    def populate_table(self):
        success, result = get_income_statement(self.conn)
        if not success:
            messagebox.showerror("Error", result)
            return
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, row in enumerate(result, start=1):
            amount = row.get("amount") or 0.00
            self.tree.insert("", "end", values=(
                idx,
                row.get("category", ""),
                row.get("account_code", ""),
                row.get("account_name", ""),
                f"{amount:,.2f}"
            ))
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
            self.tree.column(col, width=max_width+5)

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0],
                "Category": vals[1],
                "Account Code": vals[2],
                "Account Name": vals[3],
                "Amount": vals[4]
            })
        return rows
    def _make_exporter(self):
        title = "Income Statement"
        columns = ["No", "Category", "Account Code", "Account Name", "Amount"]
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
        self.center_window(self.window, 900, 500, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.columns = ("No", "Category", "Account Code", "Account Name", "Amount", "Total")
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.table_frame = tk.Frame(self.window, bg="lightblue")
        self.tree = ttk.Treeview(self.table_frame, columns=self.columns,
                                 show="headings", selectmode="browse")

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        # Title Frame
        top_frame = tk.Frame(self.window, bg="lightblue")
        top_frame.pack(fill="x", pady=(5, 0), padx=5)
        current_year = datetime.now().year
        tk.Label(
            top_frame,
            text=f"Cash Flow Statement For Year {current_year}",
            bg="lightblue",
            font=("Arial", 14, "bold")
        ).pack(anchor="center", padx=20)
        # Table Area
        self.table_frame.pack(fill="both", expand=True, padx=10)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        y_scroll = ttk.Scrollbar(self.table_frame, orient="vertical",
                                 command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="left", fill="y")
        # Mouse Wheel scroll
        self.tree.bind("<MouseWheel>", lambda e:
                       self.tree.yview_scroll(int(-1 * (e.delta/120)), "units"))
        # Bottom Buttons Frame
        btn_frame = tk.Frame(self.window, bg="lightblue")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Button(btn_frame, text="Export Excel", width=10, bg="dodgerblue",
                  command=self.on_export_excel).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Export PDF", width=10, bg="dodgerblue",
                  command=self.on_export_pdf).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Print", width=10, bg="dodgerblue",
                  command=self.on_print).pack(side="right", padx=5)

    def populate_table(self):
        fetch = CashFlowStatement(self.conn)
        result = fetch.get_cash_flow_statement()
        if isinstance(result, str):
            messagebox.showerror("Error", result)
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
            self.tree.insert("", "end", values=(
                no,
                row["category"],
                row["account_code"],
                row["account_name"],
                f"{amount:,.2f}",
                f"{total_amount:,.2f}"
            ))
            no += 1
        for row in result["cash_outflows"]:
            amount = row["amount"] or 0.00
            total_amount += amount #negative values subtract automatically
            self.tree.insert("", "end", values=(
                no,
                row["category"],
                row["account_code"],
                row["account_name"],
                f"{amount:,.2f}",
                f"{total_amount:,.2f}"
            ))
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
            self.tree.column(col, width=max_width+5)

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0],
                "Category": vals[1],
                "Account Code": vals[2],
                "Account Name": vals[3],
                "Amount": vals[4],
                "Total": vals[5]
            })
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
        self.center_window(self.window, 900, 600, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.table_frame = tk.Frame(self.window, bg="lightblue")
        self.columns = ("No", "Account Code", "Account Name", "Debit", "Credit")
        self.tree = ttk.Treeview(self.table_frame, columns=self.columns,
                                 show="headings")

        self.build_ui()
        self.populate_table()

    def build_ui(self):
        # Title Frame
        title_frame = tk.Frame(self.window, bg="lightblue")
        title_frame.pack(pady=(10, 0), padx=5)
        year = datetime.now().year
        title_label = tk.Label(
            title_frame,
            text=f"Balance Sheet For Year Ended {year}",
            font=("Arial", 14, "bold"),
            bg="lightblue"
        )
        title_label.pack(anchor="center", padx=10)
        # Table Frame
        self.table_frame.pack(fill="both", expand=True, padx=5)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Mousewheel Scroll
        self.tree.bind("<MouseWheel>",
                       lambda e: self.tree.yview_scroll(int(-1 * (e.delta / 120)),
                                                        "units"))
        # Bottom Buttons Frame
        btn_frame = tk.Frame(self.window, bg="lightblue")
        btn_frame.pack(side="bottom", fill="x", pady=(0, 5))
        tk.Button(btn_frame, text="Export Excel", width=10, bg="dodgerblue",
                  command=self.on_export_excel).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Export PDF", width=10, bg="dodgerblue",
                  command=self.on_export_pdf).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Print", width=10, bg="dodgerblue",
                  command=self.on_print).pack(side="right", padx=5)

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
                "", category.capitalize(), "", "", ""),
                             tags=("category_header",)
                             )
            # Rows for each account
            for row in cat_data["items"]:
                if category == "assets":
                    debit = f"{row['amount']:,.2f}"
                    credit = ""
                else:
                    debit = ""
                    credit = f"{row['amount']:,.2f}"
                self.tree.insert("", "end", values=(
                    no,
                    row["account_code"],
                    row["account_name"],
                    debit,
                    credit
                ))
                no += 1
            # Total row
            if category == "assets":
                total_assets = cat_data['total']
                total_debit = f"{cat_data['total']:,.2f}"
                total_credit = ""
            elif category == "liabilities":
                total_liabilities = cat_data['total']
                total_debit = ""
                total_credit = f"{cat_data['total']:,.2f}"
            else: # Equity
                total_equity = cat_data['total']
                total_debit = ""
                total_credit = f"{cat_data['total']:,.2f}"
            self.tree.insert("", "end", values=(
                "",
                "",
                f"Total {category.capitalize()}",
                total_debit,
                total_credit
            ), tags=("total_row",))
            self.tree.insert("", "end", values=("", "", "","", "")) # For Spacing
        # Grand total row (Assets vs Liabilities + Equity)
        grand_total_debit = f"{total_assets:,.2f}"
        grand_total_credit = f"{(total_liabilities + total_equity):,.2f}"
        self.tree.insert("", "end", values=(
            "",
            "",
            "TOTAL",
            f"‗‗{grand_total_debit}‗‗",  # double underscore look
            f"‗‗{grand_total_credit}‗‗"
        ), tags=("grand_total_row",))
        # Apply tag style
        self.tree.tag_configure("category_header", font=("Arial", 11, "bold"))
        self.tree.tag_configure("total_row", font=("Arial", 10, "bold", "underline"))
        self.tree.tag_configure("grand_total_row", font=("Arial", 11, "bold", "underline"))
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
            self.tree.column(col, width=max_width+5)

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0],
                "Account Code": vals[1],
                "Account Name": vals[2],
                "Debit": vals[3],
                "Credit": vals[4]
            })
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
        self.center_window(self.window, 300, 200, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.selected_year = None
        self.mode = "close" # Default mode
        self.top_frame = tk.Frame(self.window, bg="lightblue")
        self.btn_close_year = tk.Button(
            self.top_frame, text="Close Year", bg="green", fg="white",
            command=self.show_close_year
        )
        self.btn_reverse_year = tk.Button(
            self.top_frame, text="Reverse Closed Year", bg="red", fg="white",
            command=self.show_reverse_year
        )
        # Middle content frame
        self.middle_frame = tk.Frame(self.window, bg="lightblue")
        # Dynamic title label (inside content area)
        self.mode_title_label = tk.Label(
            self.middle_frame, text="", bg="lightblue",
            font=("Arial", 12, "bold")
        )
        # Dynamic label + combobox
        self.select_label = tk.Label(
            self.middle_frame, text="", bg="lightblue",
            font=("Arial", 11, "bold")
        )
        self.combo_var = tk.StringVar()
        self.combobox = ttk.Combobox(self.middle_frame, state="readonly",
                                     textvariable=self.combo_var, width=25)
        # Bottom action button
        self.action_btn = tk.Button(
            self.middle_frame, text="", bg="blue", fg="white", width=10,
            font=("Arial", 11, "bold"), command=self.perform_action
        )

        self.build_ui()

    def build_ui(self):
        # Pack top frame + buttons
        self.top_frame.pack(anchor="center", pady=5)
        self.btn_close_year.pack(side="left", padx=10)
        self.btn_reverse_year.pack(side="left", padx=10)
        # Middle Section
        self.middle_frame.pack(pady=(0, 10), padx=10)
        self.mode_title_label.pack(anchor="center", pady=3)
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
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        selected = self.combo_var.get()
        if not selected:
            messagebox.showwarning("No Selection",
                                   "Please select year first.")
            return
        if self.mode == "close":
            try:
                closing_year = int(selected.split()[-1])
            except IndexError:
                messagebox.showinfo("Error", "Invalid period format.")
                return
            confirm = messagebox.askyesno(
                "Confirm Close Year",
                f"Do you want to close accounting year: {closing_year}"
            )
            if confirm:
                processor = YearEndProcessor(self.conn)
                result = processor.close_year(closing_year)
                messagebox.showinfo("Close Year", result)
        else:
            try:
                reversing_year = int(selected)
            except ValueError:
                messagebox.showerror("Error", "Invalid year format.")
                return
            confirm = messagebox.askyesno(
                "Confirm Reverse Year",
                f"Do you want to reverse accounting year: {reversing_year}"
            )
            if confirm:
                reverser = YearEndReversalManager(self.conn)
                result = reverser.reverse_year(reversing_year)
                messagebox.showinfo("Close Year", result)

