import tkinter as tk
import string
from tkinter import ttk, messagebox
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup, DescriptionFormatter
from table_utils import TreeviewSorter
from windows_utils import (
    only_digits, capitalize_customer_name, is_valid_email,
    CurrencyFormatter, SentenceCapitalizer, PasswordSecurity
)
from working_on_employee import (
    get_departments, username_exists, insert_privilege, get_user_info,
    insert_user_privilege, EmployeeManager, fetch_departments,
    get_login_status_and_name, update_login_status, fetch_all_users,
    get_user_privileges, fetch_password, fetch_unassigned_privileges,
    remove_user_privilege, reset_user_password, update_employee_info,
    update_login_password, fetch_user_identity, insert_into_departments,
    fetch_user_details_and_privileges, fetch_employee_login_info,
    get_all_privileges
)

class EmployeePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Employee Account")
        self.center_window(self.window, 350, 370, master)
        self.window.configure(bg="lightgreen")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.manager = EmployeeManager(self.conn, user)
        self.departments = get_departments(self.conn)
        self.username_var = tk.StringVar()
        self.username_entry = None
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.outer_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.main_frame = tk.Frame(
            self.outer_frame, bg="lightgreen", bd=2, relief="flat"
        )
        self.username_feedback = tk.Label(
            self.main_frame, text="", bg="lightgreen", fg="red"
        )
        self.entries = {}
        self.entry_order = []
        self.submit_btn = tk.Button(
            self.main_frame, text="Create Employee", bg="dodgerblue", bd=4,
            fg="white", relief="groove", font=("Arial", 10, "bold"),
            command=self.submit
        )

        self.build_form()

    def build_form(self):
        self.outer_frame.pack(
            fill="both", expand=True, padx=10, pady=(0, 10)
        )
        tk.Label(
            self.outer_frame, text="New Employee Details.", bg="lightgreen",
            fg="blue", font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="center")
        self.main_frame.pack(fill="both", expand=True)
        validate_cmd = self.window.register(only_digits)
        fields = [
            ("Name", "name", False),
            ("Username", "username", False),
            ("Department", "department", False),
            ("Designation", "designation", False),
            ("National ID", "national_id", True),
            ("Phone", "phone", True),
            ("Email", "email", False),
            ("Salary", "salary", False)
        ]
        departments = self.departments
        for idx, (label_text, field, digits_only) in enumerate(fields):
            label = tk.Label(
                self.main_frame, text=f"{label_text}:", bg="lightgreen",
                font=("Arial", 12, "bold")
            )
            label.grid(row=idx * 2, column=0, pady=3, sticky="e")
            if field == "department":
                cb = ttk.Combobox(
                    self.main_frame, values=departments, state="readonly",
                    font=("Arial", 11), width=10
                )
                cb.grid(row=idx * 2, column=1, pady=3, sticky="w")
                self.entries[field] = cb
                self.entry_order.append(cb)
            elif field == "username":
                entry = tk.Entry(
                    self.main_frame, textvariable=self.username_var, bd=4,
                    relief="raised", font=("Arial", 11), width=15
                )
                entry.grid(row=idx * 2, column=1, pady=3, sticky="w")
                entry.bind("<KeyRelease>", self.validate_username)
                entry.bind("<Return>", self.focus_next_entry)
                self.entries[field] = entry
                self.username_entry = entry
                self.entry_order.append(entry)

            else:
                entry = tk.Entry(
                    self.main_frame, bd=4, relief="raised",
                    font=("Arial", 11)
                )
                entry.grid(row=idx * 2, column=1, pady=3, sticky="w")
                if field == "name":
                    entry.bind("<KeyRelease>", capitalize_customer_name)
                if digits_only:
                    entry.config(
                        validate="key", validatecommand=(validate_cmd, "%S"),
                        width=15
                    )
                entry.bind("<Return>", self.focus_next_entry)
                self.entries[field] = entry
                self.entry_order.append(entry)
        self.entries["name"].config(width=25)
        self.entries["designation"].config(width=10)
        self.entries["salary"].config(width=10)
        self.entries["email"].config(width=25)
        amount_var = tk.StringVar()
        self.entries["salary"].config(textvariable=amount_var)
        CurrencyFormatter.add_currency_trace(
            amount_var, self.entries["salary"]
        )
        self.entries["name"].focus_set()
        self.entries["salary"].bind("<Return>", lambda e: self.submit())
        self.submit_btn.grid(
            row=len(fields) * 2, column=0, columnspan=2, pady=(5, 0)
        )

    def validate_username(self, event=None):
        keyword = self.username_var.get()
        if not keyword:
            self.username_feedback.grid_remove()
            self.username_entry.config(bg="white")
            return
        if not self.username_feedback.winfo_ismapped():
            self.username_feedback.grid(
                row=3, column=0, columnspan=2, padx=5
            )
        if username_exists(self.conn, keyword):
            self.username_feedback.config(
                text="❌ Username not available", fg="red"
            )
            self.username_entry.config(bg="misty rose")
        else:
            self.username_feedback.config(
                text="\u2713 Username Available", fg="green"
            )
            self.username_entry.config(bg="white")

    def focus_next_entry(self, event):
        widget = event.widget
        if widget in self.entry_order:
            current_index = self.entry_order.index(widget)
            if current_index + 1 <= len(self.entry_order):
                self.entry_order[current_index + 1].focus_set()

    def submit(self):
        data = {k: v.get() for k, v in self.entries.items()}
        missing_fields = [k for k, v in data.items() if not v]
        if missing_fields:
            messagebox.showerror(
                "Error", f"Missing Fields: {', '.join(missing_fields)}.",
                parent=self.window
            )
            return
        if self.username_entry["bg"] == "misty rose":
            messagebox.showerror(
                "Error", "Username is Already Taken.", parent=self.window
            )
            return
        if not is_valid_email(data["email"]):
            messagebox.showerror(
                "Error", "Invalid Email Format.", parent=self.window
            )
            return
        # Verify user privilege
        priv = "Admin Add User"
        verify_dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv
        )
        if verify_dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You don't Have Permission To {priv}.", parent=self.window
            )
            return

        try:
            emp_data = {
                "name": data["name"],
                "username": data["username"],
                "department": data["department"],
                "designation": data["designation"],
                "national_id": int(data["national_id"]),
                "phone": data["phone"],
                "email": data["email"],
                "salary": float(data["salary"].replace(",", ""))
            }
            success, message = self.manager.insert_employee(emp_data)
            if success:
                messagebox.showinfo("Success", message, parent=self.window)
                for entry in self.entries:
                    self.entries[entry].delete(0, tk.END)
            else:
                messagebox.showerror("Failed", message, parent=self.window)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Insert field: {str(e)}.", parent=self.window
            )


class LoginStatusPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Update Employee Login Status")
        self.center_window(self.window, 310, 300, master)
        self.window.configure(bg="lightgreen")
        self.window.transient(master)
        self.window.grab_set()
        self.conn = conn
        self.user = user

        self.current_status = None
        self.identifier_type = tk.StringVar(value="username")
        self.identifier_input = tk.StringVar()
        self.status_var = tk.StringVar()
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.search_by_combo = ttk.Combobox(
            self.main_frame, textvariable=self.identifier_type, width=10,
            values=["Username", "User Code"], state="readonly",
            font=("Arial", 12)
        )
        self.input_label = tk.Label(
            self.main_frame, text="Enter Username:", bg="lightgreen",
            font=("Arial", 12, "bold")
        )
        self.identifier_entry = tk.Entry(
            self.main_frame, textvariable=self.identifier_input, width=15,
            bd=4, relief="raised", font=("Arial", 11)
        )
        self.search_btn = tk.Button(
            self.main_frame, text="Search", bg="blue", fg="white", bd=4,
            relief="groove", font=("Arial", 10, "bold"),
            command=self.search_user
        )
        self.status_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=2, relief="flat"
        )
        self.info_label = tk.Label(
            self.status_frame, text="", bg="lightgreen", fg="blue",
            font=("Arial", 13, "italic", "underline")
        )
        self.status_label = tk.Label(
            self.status_frame, text="", font=("Arial", 12, "bold"),
            fg="blue", bg="lightgreen"
        )
        self.status_combo = ttk.Combobox(
            self.status_frame, textvariable=self.status_var, state="readonly",
            values=["active", "disabled"], width=8, font=("Arial", 11)
        )
        self.post_btn = tk.Button(
            self.status_frame, text="Post Status", bg="green", fg="white",
            bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.post_update
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(
            self.main_frame, text="Disable/Enable User", bg="lightgreen",
            fg="blue", font=("Arial", 16, "bold", "underline")
        ).grid(row=0, column=0, columnspan=2, pady=(5, 0))
        # Search by label and combobox
        tk.Label(
            self.main_frame, text="Search User By:", bg="lightgreen",
            font=("Arial", 12, "bold")
        ).grid(row=1, column=0, pady=5, padx=(5, 0), sticky="e")
        self.search_by_combo.grid(row=1, column=1, pady=5, sticky="w")
        # bind change in identifier type to update label
        self.search_by_combo.bind(
            "<<ComboboxSelected>>", self.update_input_label
        )
        # Entry field label and entry box
        self.input_label.grid(
            row=2, column=0, pady=5, padx=(5, 0), sticky="e"
        )
        self.identifier_entry.grid(
            row=2, column=1, pady=5, padx=(0, 5), sticky="w"
        )
        self.identifier_entry.focus_set()
        self.identifier_entry.bind(
            "<Return>", lambda e: self.search_btn.focus_set()
        )
        # Search Button
        self.search_btn.grid(row=3, column=0, columnspan=2, pady=5)
        self.search_btn.bind("<Return>", lambda e: self.search_user())
        # Label and status change combo (initially hidden)
        self.info_label.pack(pady=(5, 0), anchor="center")
        self.status_label.pack(pady=(5, 0), padx=5)
        self.status_combo.pack(pady=(0, 5), padx=5)
        self.post_btn.pack(anchor="center", pady=(5, 0))

    def update_input_label(self, event=None):
        label_text = f"Enter {self.identifier_type.get()}:"
        self.input_label.config(text=label_text)

    def search_user(self):
        identifier = self.identifier_input.get().strip()
        if not identifier:
            messagebox.showerror(
                "Input Error",
                "Please Enter a Valid Identifier.", parent=self.window
            )
            return
        result = get_login_status_and_name(self.conn, identifier)
        if not result:
            messagebox.showerror(
                "Not Found", f"No user with: {identifier}.",
                parent=self.window
            )
            return
        self.current_status = result[1]
        status = self.current_status.lower()
        label_color = "red" if status == "disabled" else "dodgerblue"
        self.info_label.config(
            text=f"{identifier} is Currently: {self.current_status}.",
            fg=label_color
        )
        # Show label
        set_status = "Active" if status == "disabled" else "Disabled"
        self.status_label.config(text=f"Set Status To {set_status}:")
        self.status_var.set(self.current_status) # Pre-fill current status
        self.status_frame.grid(
            row=4, column=0, columnspan=2, sticky="nsew"
        )

    def post_update(self):
        identifier = self.identifier_input.get().strip()
        new_status = self.status_var.get().lower()
        # Verify User privilege
        if new_status == "active":
            priv = "Admin Activate User"
        else:
            priv = "Admin Deactivate User"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Permission to: {priv}.", parent=self.window
            )
            return
        if new_status == self.current_status:
            messagebox.showerror(
                "Info", f"Status is Already '{self.current_status}'.",
                parent=self.window
            )
            return
        success, result = update_login_status(
            self.conn, identifier, new_status, self.user
        )
        if success:
            messagebox.showinfo("Success", result, parent=self.window)
            self.status_var.set("")
            self.identifier_input.set("")
        else:
            messagebox.showerror("Error", result, parent=self.window)


class PrivilegePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Privileges")
        self.center_window(self.window, 670, 700, master)
        self.window.configure(bg="lightblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.privilege_var = tk.StringVar()
        self.privileges = None
        self.columns = ["No.", "Id", "Privilege", "Clearance"]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="ridge"
        )
        self.table_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=1, relief="ridge"
        )
        self.entry = tk.Entry(
            self.top_frame, textvariable=self.privilege_var, width=20, bd=4,
            relief="raised", font=("Arial", 12)
        )
        self.desc_entry = tk.Text(
            self.top_frame, width=45, height=2, bd=4, relief="ridge",
            font=("Arial", 12)
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No.")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_form()
        self.load_privileges()

    def build_form(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(
            self.main_frame, text="Create User Privileges", bg="lightblue",
            fg="blue", font=("Arial", 18, "bold", "underline")
        ).pack(side="top", anchor="center", pady=(5, 0))
        self.top_frame.pack(side="top", fill="x")
        # Title Label
        tk.Label(
            self.top_frame, text="Privilege:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(5, 0))
        # Entry field
        self.entry.grid(row=1, column=0, pady=(0, 5), padx=5, sticky="nw")
        self.entry.bind("<KeyRelease>", self.on_entry_keyrelease)
        self.entry.bind("<Return>", self.focus_description)
        self.entry.focus_set()
        tk.Label(
            self.top_frame, text="Description (Actions Performed):",
            bg="lightblue", font=("Arial", 12, "bold")
        ).grid(row=0, column=1, sticky="w", pady=(5, 0))
        self.desc_entry.grid(row=1, column=1, pady=(0, 5), padx=(5, 0))
        SentenceCapitalizer.bind(self.desc_entry)
        self.desc_entry.bind("<Return>", self.submit)
        # Submit Button
        tk.Button(
            self.top_frame, text="Add Privilege", bd=4, relief="groove",
            bg="green", fg="white", command=self.submit,
            font=("Arial", 11, "bold")
        ).grid(row=2, column=0, columnspan=2, pady=5)
        self.table_frame.pack(fill="both", expand=True)
        tk.Label(
            self.table_frame, text="Current Privileges", fg="blue",
            bg="lightblue", font=("Arial", 14, "bold", "underline")
        ).pack(side="top", anchor="center", pady=(5, 0))
        scroll = tk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def focus_description(self, event):
        self.desc_entry.focus_set()
        self.desc_entry.mark_set("insert", "1.0")
        return "break"

    def on_entry_keyrelease(self, event):
        capitalize_customer_name(event)
        self.filter_privileges()

    def submit(self, event=None):
        privilege = self.privilege_var.get().strip()
        if not privilege:
            messagebox.showerror(
                "Input Error",
                "Privilege Cannot be Empty.", parent=self.window
            )
            return
        # Verify user privilege
        priv = "Admin Create Privilege"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Permission To {priv}.", parent=self.window
            )
            return
        # Proceed to insert if access is granted
        desc = self.desc_entry.get("1.0", tk.END).strip()
        success, result = insert_privilege(
            self.conn, privilege, desc, self.user
        )
        if not success:
            messagebox.showerror("Error", result, parent=self.window)
        else:
            messagebox.showinfo("Success", result, parent=self.window)
            self.privilege_var.set("") # Clear input
            self.desc_entry.delete("1.0", tk.END)
            self.entry.focus_set()
            self.load_privileges()

    def load_privileges(self):
        success, result = get_all_privileges(self.conn)
        if not success:
            messagebox.showerror("Error", result, parent=self.window)
            return
        self.privileges = result
        self.display_privileges(result)

    def display_privileges(self, data):
        for row in self.tree.get_children():
            self.tree.delete(row)

        formatter = DescriptionFormatter(35, 10)
        for i, row in enumerate(data, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            clearance = formatter.format(row["clearance"])
            self.tree.insert("", "end", values=(
                i,
                row["no"],
                row["privilege"],
                clearance
            ), tags=(tag,))
        self.sorter.autosize_columns()

    def filter_privileges(self, event=None):
        priv_text = self.privilege_var.get().strip().lower()
        if not priv_text:
            self.display_privileges(self.privileges)
            return
        filtered = []
        for row in self.privileges:
            privilege = row["privilege"].lower()
            clearance = (row["clearance"] or "").lower()
            if priv_text in privilege or priv_text in clearance:
                filtered.append(row)
        if filtered:
            self.display_privileges(filtered)
        else:
            self.display_privileges(self.privileges)


class AssignPrivilegePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Assign Privileges")
        self.center_window(self.window, 1100, 700, master)
        self.window.configure(bg="lightgreen")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.identifier_type = tk.StringVar(value="Username")
        self.identifier_input = tk.StringVar()
        self.selected_privileges = {} # {id: name}
        self.user_code = None
        self.employee_name = None
        # {id: name}
        self.all_privileges = None
        self.columns = ["No.", "Id", "Privilege", "Clearance"]
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.left_frame = tk.Frame(
            self.main_frame, bg="lightgreen", width=450
        )
        self.identifier_frame = tk.Frame(self.left_frame, bg="lightgreen")
        self.identifier_entry = tk.Entry(
            self.identifier_frame, textvariable=self.identifier_input,
            width=15, bd=4, relief="raised", font=("Arial", 11)
        )
        self.input_label = tk.Label(
            self.identifier_frame, text="Search Username:", bg="lightgreen",
            font=("Arial", 11, "bold")
        )
        self.selected_frame = tk.Frame(self.left_frame, bd=2, relief="ridge")
        self.middle_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.tree_frame = tk.Frame(self.middle_frame, bg="lightgreen")
        self.tree = ttk.Treeview(
            self.tree_frame, columns=self.columns, show="headings"
        )

        self.assign_label = tk.Label(
            self.left_frame, text="", bg="lightgreen", fg="blue",
            font=("Arial", 12, "italic", "underline")
        )
        self.post_btn = tk.Button(
            self.left_frame, text="Add Privileges", bg="green", fg="white",
            bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.post_privileges
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No.")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_layout()

    def build_layout(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tk.Label(
            self.main_frame, text="Assign Privilege To Users", fg="blue",
            bg="lightgreen", font=("Arial", 18, "bold", "underline"), bd=4,
            relief="ridge"
        ).pack(side="top", anchor="center")
        # Search Section
        self.left_frame.pack(side="left", fill="y", expand=False, anchor="w")
        self.left_frame.configure(width=450)
        self.left_frame.pack_propagate(False)
        self.identifier_frame.pack(side="top", fill="x")
        tk.Label(
            self.identifier_frame, text="Search User By:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, sticky="e")
        search_by = ttk.Combobox(
            self.identifier_frame, values=["Username", "User Code"],
            width=10, textvariable=self.identifier_type, state="readonly",
            font=("Arial", 11)
        )
        search_by.grid(row=0, column=1, sticky="w")
        search_by.bind("<<ComboboxSelected>>", self.update_input_label)
        self.input_label.grid(row=1, column=0, sticky="e", pady=5)
        self.identifier_entry.grid(row=1, column=1, sticky="w", pady=5)
        self.identifier_entry.focus_set()
        self.identifier_entry.bind("<Return>", self.search_user)
        tk.Button(
            self.left_frame, text="Search", bg="dodgerblue", fg="white",
            width=10, command=self.search_user, bd=2, relief="groove"
        ).pack(pady=5, padx=5, anchor="center")
        # Assign Header
        self.assign_label.pack(pady=5)
        # Privileges and Selection Area
        self.tree_frame.pack(fill="both", expand=True)
        tk.Label(
            self.tree_frame, text="Select Privileges to Assign", fg="blue",
            bg="lightgreen", font=("Arial", 12, "bold", "underline")
        ).pack(side="top", anchor="center")
        scroll = tk.Scrollbar(
            self.tree_frame, orient="vertical", command=self.tree.yview
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        self.tree.bind("<<TreeviewSelect>>", self.handle_tree_select)
        # Right Side: Selected privileges Display
        self.selected_frame.pack(fill="both", expand=True)
        self.selected_frame.pack_forget()

    def update_input_label(self, event=None):
        if self.identifier_type.get() == "Username":
            self.input_label.config(text="Search Username:")
        else:
            self.input_label.config(text="Search User Code:")

    def search_user(self, event=None):
        identifier = self.identifier_input.get().strip()
        if not identifier:
            messagebox.showerror(
                "Input Error","Please Enter Valid Identifier.",
                parent=self.window
            )
            return
        success, user_info = get_user_info(self.conn, identifier)
        if not success:
            messagebox.showerror("Not Found", user_info, parent=self.window)
            return
        self.user_code = user_info["user_code"]
        self.employee_name = user_info["name"]
        self.assign_label.config(
            text= f"Assign Privileges to: {self.employee_name.capitalize()}"
        )
        self.selected_privileges.clear()
        self.update_selected_display()
        self.selected_frame.pack(fill="both", expand=True)
        self.middle_frame.pack(side="left", fill="both", expand=True)
        self.post_btn.pack(side="bottom", anchor="center", pady=5)
        self.load_unassigned_privileges(identifier)

    def load_unassigned_privileges(self, username):
        for row in self.tree.get_children():
            self.tree.delete(row)
        success, result = fetch_unassigned_privileges(self.conn, username)
        if not success:
            messagebox.showerror("Error", result, parent=self.window)
            return
        formatter = DescriptionFormatter(30, 10)
        for i, row in enumerate(result, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            clearance = formatter.format(row["clearance"])
            self.tree.insert("", "end", iid=str(row["no"]), values=(
                i,
                row["no"],
                row["privilege"],
                clearance
            ), tags=(tag,))
        self.sorter.autosize_columns()

    def handle_tree_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        values = self.tree.item(item_id, "values")
        pid = int(item_id)
        privilege = values[2]
        if pid not in self.selected_privileges:
            self.selected_privileges[pid] = privilege
            self.update_selected_display()

    def update_selected_display(self):
        for widget in self.selected_frame.winfo_children():
            widget.destroy()
        self.selected_frame.update_idletasks()
        available_width = self.selected_frame.winfo_width()
        if available_width <= 1:
            # Frame may not have been drawn yet -fallback to default width
            available_width = 500
        current_width = 0
        row_frame = tk.Frame(self.selected_frame, bg="white")
        row_frame.pack(fill="x", anchor="w")
        for pid, pname in self.selected_privileges.items():
            item_frame = tk.Frame(
                row_frame, bg="lightblue", bd=1, relief="flat", padx=2
            )
            label = tk.Label(item_frame, text=pname, bg="lightblue")
            label.pack(side="left")
            remove_btn = tk.Label(
                item_frame, text="X", fg="red", bg="white", cursor="hand2"
            )
            remove_btn.pack(side="right")
            remove_btn.bind(
                "<Button-1>", lambda e, p=pid: self.remove_privilege(p)
            )
            item_frame.update_idletasks()
            item_width = item_frame.winfo_reqwidth() + 5
            # If adding this item exceeds available width add new line
            if current_width + item_width > available_width:
                row_frame = tk.Frame(self.selected_frame, bg="white")
                row_frame.pack(fill="x", anchor="w", pady=2)
                current_width = 0
            item_frame.pack(side="left", padx=2)
            current_width += item_width

    def remove_privilege(self, privilege_id):
        if privilege_id in self.selected_privileges:
            del self.selected_privileges[privilege_id]
            self.update_selected_display()

    def post_privileges(self):
        if not self.user_code or not self.selected_privileges:
            messagebox.showerror(
                "Error",
                "Please Search User and Select at Least 1 Privilege.",
                parent=self.window
            )
            return
        # Verify user privilege
        priv = "Admin Assign Privilege"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied", f"You Don't Have Permission To {priv}.",
                parent=self.window
            )
            return
        user_name = self.employee_name
        code = self.user_code
        success_count = 0
        fail_count = 0
        error_msg = []
        for pid, pname in self.selected_privileges.items():
            success, msg = insert_user_privilege(
                self.conn, code, pid, pname, user_name, self.user
            )
            if success:
                success_count += 1
            else:
                fail_count += 1
                error_msg.append(msg)
        if success_count > 0:
            messagebox.showinfo(
                "Success",
                f"{success_count} Privilege(s) Assigned to {user_name}.",
                parent=self.window
            )
        else:
            messagebox.showerror(
                "Error",
                f"Failed to Add Privilege(s) To {user_name}.\n{error_msg}",
                parent=self.window
            )
        self.selected_privileges.clear()
        self.assign_label.config(text="")
        self.identifier_entry.delete(0, tk.END)
        self.user_code = None
        self.employee_name = None
        self.selected_frame.pack_forget()
        self.middle_frame.pack_forget()
        self.post_btn.pack_forget()
        self.identifier_entry.focus_set()


class RemovePrivilegePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Remove Privileges")
        self.window.configure(bg="Lightgreen")
        self.center_window(self.window, 700, 550, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.identifier_type = tk.StringVar(value="Username")
        self.identifier_input = tk.StringVar()
        self.selected_privileges = {} # {access_id, privilege}
        self.user_code = None
        self.employee_name = None
        self.privileges_assigned = {} # {access_id: privilege_name}
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=4, relief="flat"
        )
        self.dynamic_label = tk.Label(
            self.top_frame, text="Search Username:", bg="lightgreen",
            font=("Arial", 11, "bold")
        )
        self.identifier_entry = tk.Entry(
            self.top_frame, textvariable=self.identifier_input, width=15,
            bd=4, relief="raised", font=("Arial", 11)
        )
        self.middle_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=4, relief="ridge", height=18
        )
        self.left_frame = tk.Frame(self.middle_frame, bg="lightgreen")
        self.listbox_frame = tk.Frame(self.left_frame, bg="lightgreen")
        self.priv_listbox = tk.Listbox(
            self.listbox_frame, height=15, width=23, font=("Arial", 12)
        )
        self.selected_frame = tk.Frame(
            self.middle_frame, bg="white", bd=4, relief="ridge", width=500,
            height=20
        )
        self.header_label = tk.Label(
            self.middle_frame, text="", bg="lightgreen", fg="blue",
            font=("Arial", 13, "italic", "underline")
        )
        self.remove_btn = tk.Button(
            self.main_frame, text="Remove Privileges", bg="red", fg="white",
            bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.remove_selected
        )


        self.build_gui()

    def build_gui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Top search Frame
        self.top_frame.pack(side="top", pady=(5, 0))
        tk.Label(
            self.top_frame, text="Remove Privilege(s) From User", fg="blue",
            bg="lightgreen", font=("Arial", 18, "bold", "underline")
        ).pack(side="top", pady=(5, 0), anchor="center")
        tk.Label(
            self.top_frame, text="Search User By:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(10, 0))
        search_by_cb = ttk.Combobox(
            self.top_frame, values=["Username", "User Code"], width=10,
            textvariable=self.identifier_type, state="readonly",
            font=("Arial", 12)
        )
        search_by_cb.pack(side="left", padx=(0, 10))
        search_by_cb.bind("<<ComboboxSelected>>", self.update_input_label)
        self.dynamic_label.pack(side="left", padx=(5, 0))
        self.identifier_entry.pack(side="left")
        self.identifier_entry.bind("<Return>", self.search_user)
        # Search Button
        tk.Button(
            self.main_frame, text="Search", bg="dodgerblue", fg="white",
            bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.search_user
        ).pack(pady=(5, 0))
        # Header
        self.header_label.pack(pady=(10, 5))
        # Privilege area
        tk.Label(
            self.left_frame, text="Select Privileges to Remove:",
            bg="lightgreen", font=("Arial", 12, "bold", "underline")
        ).pack(anchor="w")
        self.listbox_frame.pack(fill="both")
        scrollbar = tk.Scrollbar(
            self.listbox_frame, command=self.priv_listbox.yview
        )
        self.priv_listbox.config(yscrollcommand=scrollbar.set)
        self.priv_listbox.pack(side="left", fill="y")
        self.priv_listbox.pack_propagate(False)
        scrollbar.pack(side="right", fill="y")
        self.priv_listbox.bind(
            "<<ListboxSelect>>", self.handle_listbox_select
        )
        self.left_frame.pack(side="left", fill="y")
        self.selected_frame.pack(side="left", fill="both")
        self.selected_frame.pack_propagate(False)
        self.identifier_entry.focus_set()


    def update_input_label(self, event=None):
        selected = self.identifier_type.get()
        if selected == "Username":
            self.dynamic_label.config(text="Search Username:")
        else:
            self.dynamic_label.config(text="Search User Code:")

    def search_user(self, event=None):
        identifier = self.identifier_input.get().strip()
        if not identifier:
            messagebox.showerror(
                "Error", "Please enter valid identifier.", parent=self.window
            )
            return
        result = get_user_privileges(self.conn, identifier)
        if not result or isinstance(result, str):
            messagebox.showerror(
                "Not Found",
                f"No Privileges Found For {identifier}.", parent=self.window
            )
            return
        self.user_code = result[0][0]
        self.privileges_assigned = {aid: pname for _, aid, pname in result}
        self.header_label.config(
            text=f"Remove Privilege(s) From {identifier.capitalize()}."
        )
        self.priv_listbox.delete(0, tk.END)
        for pname in self.privileges_assigned.values():
            self.priv_listbox.insert("end", pname)
        self.selected_privileges.clear()
        self.update_selected_display()
        self.middle_frame.pack(fill="both", expand=False, pady=(0, 5))
        self.remove_btn.pack(pady=5)

    def handle_listbox_select(self, event=None):
        selection = event.widget.curselection()
        if not selection:
            return
        selected_name = event.widget.get(selection[0])
        for aid, pname in self.privileges_assigned.items():
            if pname == selected_name and aid not in self.selected_privileges:
                self.selected_privileges[aid] = pname
                break
        self.update_selected_display()

    def update_selected_display(self):
        for widget in self.selected_frame.winfo_children():
            widget.destroy()
        self.selected_frame.update_idletasks()
        available_width = self.selected_frame.winfo_width()
        if available_width <= 1:
            # Frame may not have been drawn yet -fallback to default width
            available_width = 500
        current_width = 0
        row_frame = tk.Frame(self.selected_frame, bg="white")
        row_frame.pack(fill="x", anchor="w")
        for aid, pname in self.selected_privileges.items():
            item_frame = tk.Frame(
                row_frame, bg="lightblue", bd=1, relief="flat", padx=2
            )
            label = tk.Label(item_frame, text=pname, bg="lightblue")
            label.pack(side="left")
            remove_btn = tk.Label(
                item_frame, text="X", fg="red", bg="white", cursor="hand2"
            )
            remove_btn.pack(side="right")
            remove_btn.bind(
                "<Button-1>", lambda e, a=aid: self.remove_privilege_from_list(a)
            )
            item_frame.update_idletasks()
            item_width = item_frame.winfo_reqwidth() + 5
            # If adding this item exceeds available width add new line
            if current_width + item_width > available_width:
                row_frame = tk.Frame(self.selected_frame, bg="white")
                row_frame.pack(fill="x", anchor="w", pady=2)
                current_width = 0
            item_frame.pack(side="left", padx=2)
            current_width += item_width

    def remove_privilege_from_list(self, access_id):
        if access_id in self.selected_privileges:
            del self.selected_privileges[access_id]
            self.update_selected_display()

    def remove_selected(self):
        if not self.user_code or not self.selected_privileges:
            messagebox.showwarning(
                "Error",
                "Please Search User and Select at Least 1 Privilege.", parent=self.window
            )
            return
        priv = "Admin Remove Privilege"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Permission To {priv}.", parent=self.window
            )
            return

        name = self.identifier_input.get().strip()
        code = self.user_code
        success_count = 0
        fail_count = 0
        for aid, pname in self.selected_privileges.items():
            success, msg = remove_user_privilege(
                self.conn, code, aid, pname, name, self.user
            )
            if success:
                success_count += 1
            else:
                fail_count += 1
        if success_count > 0:
            messagebox.showinfo(
                "Success",
                f"{success_count} Privilege(s) Removed From {name}.",
                parent=self.window
            )
        else:
            messagebox.showerror(
                "Error", f"Failed to Remove Privileges From {name}.",
                parent=self.window
            )
        self.window.destroy()


class ResetPasswordPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Reset Password")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 300, 260, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.user_code = None
        self.employee_name = None
        self.identifier_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.identifier_entry = tk.Entry(
            self.main_frame, textvariable=self.identifier_var, width=15,
            bd=4, relief="raised", font=("Arial", 12)
        )
        self.search_btn = tk.Button(
            self.main_frame, text="Search User", bg="dodgerblue", fg="white",
            bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.search_user
        )
        self.identifier_entry.bind("<Return>", self.search_user)
        # Bind to clear previous on type
        self.identifier_entry.bind("<Key>", self.clear_on_type)
        # Flag to clear entry next time user types
        self.replace_on_type = False
        self.pass_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=4, relief="ridge"
        )
        self.new_password_entry =tk.Entry(
            self.pass_frame, textvariable=self.new_password_var, width=8,
            bd=4, relief="raised", font=("Arial", 12)
        )
        self.reset_btn = tk.Button(
            self.pass_frame, text="Reset Password", bg="green", fg="white",
            bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.reset_password
        )
        self.new_password_entry.bind("<KeyRelease>", self.repeat_digit)
        self.new_password_entry.bind(
            "<Return>", lambda e: self.reset_btn.focus_set()
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(
            self.main_frame, text="Reset User Password", bg="lightgreen",
            fg="blue", font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="center")
        tk.Label(
            self.main_frame, text="Username or Code:", bg="lightgreen",
            fg="blue", font=("Arial", 12, "bold")
        ).pack()
        self.identifier_entry.pack(pady=(0, 5))
        self.identifier_entry.focus_set()
        self.search_btn.pack(pady=(5, 0))
        tk.Label(
            self.pass_frame, text="Digit to Set Password(Optional):",
            bg="lightgreen", fg="blue", font=("Arial", 12, "bold")
        ).pack(anchor="center")
        self.new_password_entry.pack(padx=5, pady=(0, 5))
        self.new_password_entry.bind("<Return>", self.reset_password)
        self.reset_btn.pack(pady=(5, 0))
        self.reset_btn.bind("<Return>", lambda e: self.reset_password())


    def repeat_digit(self, event=None):
        digit = self.new_password_var.get().strip()
        if digit.isdigit() and len(digit) == 1:
            self.new_password_var.set(digit * 6)
        elif len(digit) > 1:
            self.new_password_var.set(digit[0] * 6 if digit[0].isdigit() else "")
        elif not digit:
            self.new_password_var.set("")
        self.new_password_entry.icursor(tk.END)

    def focus_identifier_entry(self):
        self.identifier_entry.focus_set()
        self.identifier_entry.select_range(0, tk.END)
        self.replace_on_type =True

    def clear_on_type(self, event=None):
        if self.replace_on_type:
            self.identifier_var.set("")
            self.replace_on_type = False

    def search_user(self, event=None):
        if not self.identifier_var.get().strip():
            messagebox.showerror(
                "Input Error",
                "Please Enter valid Identifier.", parent=self.window
            )
            self.focus_identifier_entry()
            return
        identifier = self.identifier_var.get().strip()
        success, data = get_user_info(self.conn, identifier)
        if not success:
            messagebox.showerror("Not Found", data, parent=self.window)
            self.focus_identifier_entry()
            return
        self.user_code = data["user_code"]
        self.employee_name = data["name"]
        confirm = messagebox.askyesno(
            "Confirm.",
            f"Reset Password For: {self.employee_name}?", parent=self.window
        )
        if confirm:
            self.pass_frame.pack(fill="both", expand=True)
            self.new_password_entry.focus_set()
        else:
            self.pass_frame.pack_forget()
            self.focus_identifier_entry()

    def reset_password(self, event=None):
        # Verify user privilege
        priv = "Reset Password"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Permission to {priv}.", parent=self.window
            )
            return
        user_code = str(self.user_code)
        name = self.employee_name
        new_password = self.new_password_var.get().strip() or "000000"
        success, msg = reset_user_password(
            self.conn, user_code, name, self.user, new_password
        )
        if success:
            messagebox.showinfo("Success", msg, parent=self.window)
            messagebox.showinfo(
                "Advice",
                f"User to Use '{new_password}' Login Password.",
                parent=self.window
            )
            self.identifier_var.set("")
            self.new_password_var.set("")
        else:
            messagebox.showerror("Error", msg, parent=self.window)


class ChangePasswordPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Change Password")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 350, 300, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.username_var = tk.StringVar()
        self.username_var.set(user)
        self.password_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.strength_var = tk.IntVar(value=0)
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Slim.Horizontal.TProgressbar", thickness=2)
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.username_entry = tk.Entry(
            self.main_frame, textvariable=self.username_var, bd=2, width=10,
            relief="raised", font=("Arial", 12), state="readonly"
        )
        self.password_entry = tk.Entry(
            self.main_frame, textvariable=self.password_var, show="*", bd=2,
            relief="raised", width=15, font=("Arial", 12)
        )
        # New Password (Initially Hidden)
        self.new_frame = tk.Frame(self.main_frame, bg="spring green")
        self.new_password_entry = tk.Entry(
            self.new_frame, textvariable=self.new_password_var, show="*",
            bd=2, relief="raised", width=15, font=("Arial", 12)
        )
        self.password_error_label = tk.Label(
            self.new_frame, text="", fg="red", bg="spring green",
            font=("Arial", 9, "italic")
        )
        self.strength_bar = ttk.Progressbar(
            self.new_frame, maximum=100, variable=self.strength_var,
            length=180, mode="determinate",
            style="Slim.Horizontal.TProgressbar"
        )
        self.strength_label = tk.Label(
            self.new_frame, text="", bg="spring green",
            font=("Arial", 9, "bold")
        )

        self.confirm_password_entry = tk.Entry(
            self.new_frame, textvariable=self.confirm_password_var, show="*",
            bd=2, relief="raised", width=15, font=("Arial", 12)
        )
        self.change_btn = tk.Button(
            self.new_frame, text="Change Password", bg="dodgerblue", bd=4,
            relief="groove", fg="white", command=self.change_password,
            font=("Arial", 11, "bold"), state="disabled"
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Allow grind Expansion
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        # Username Entry
        tk.Label(
            self.main_frame, text="Password Update", bg="lightgreen",
            fg="blue", font=("Arial", 14, "bold", "underline")
        ).grid(row=0, column=0, columnspan=2, pady=5)
        tk.Label(
            self.main_frame, text="Username:", bg="lightgreen",
            font=("Arial", 12, "bold")
        ).grid(row=1, column=0, pady=5, sticky="e")
        self.username_entry.grid(row=1, column=1, pady=5, sticky="w")
        tk.Label(
            self.main_frame, text="Current Password:", bg="lightgreen",
            font=("Arial", 12, "bold")
        ).grid(row=2, column=0, pady=5, sticky="e")
        self.password_entry.grid(row=2, column=1, pady=5, sticky="w")
        self.password_entry.focus_set()
        self.password_entry.bind("<Return>", self.verify_password_and_status)
        self.new_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        self.new_frame.grid_rowconfigure(0, weight=1)
        self.new_frame.grid_rowconfigure(1, weight=0)
        self.new_frame.grid_rowconfigure(3, weight=1)
        self.new_frame.grid_columnconfigure(0, weight=1)
        self.new_frame.grid_columnconfigure(1, weight=1)
        tk.Label(
            self.new_frame, text="New Password:", bg="spring green",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, pady=(2, 0), sticky="e")
        self.new_password_entry.grid(row=0, column=1, pady=(2, 0), sticky="w")
        # Real time validation
        self.new_password_entry.bind(
            "<KeyRelease>", self.validate_password_strength
        )
        self.new_password_entry.bind(
            "<Return>", lambda e: self.confirm_password_entry.focus_set()
        )
        self.password_error_label.grid(row=1, column=0, columnspan=2, pady=(0, 2))
        tk.Label(
            self.new_frame, text="Confirm Password:", bg="spring green",
            font=("Arial", 12, "bold")
        ).grid(row=2, column=0, pady=(5, 0), sticky="e")
        self.confirm_password_entry.grid(row=2, column=1, pady=(5, 0), sticky="w")
        self.confirm_password_entry.bind(
            "<Return>", lambda e: self.change_password()
        )
        self.change_btn.grid(row=3, column=0, columnspan=2, pady=5)
        self.strength_bar.grid(row=4, column=0, columnspan=2, pady=(5, 0), sticky="ew")
        self.strength_label.grid(row=4, column=0, columnspan=2, pady=(2, 0), sticky="w")
        self.new_frame.grid_remove()

    def validate_password_strength(self, event=None):
        pwd = self.new_password_var.get()
        score = 0
        requirements = []

        if len(pwd) >= 6:
            score += 25
        else:
            requirements.append("6+ chars")
        if any(c.islower() for c in pwd):
            score += 15
        else:
            requirements.append("lowercase")
        if any(c.isupper() for c in pwd):
            score += 20
        else:
            requirements.append("uppercase")
        if any(c.isdigit() for c in pwd):
            score += 20
        else:
            requirements.append("digit")
        if any(c in string.punctuation for c in pwd):
            score += 20
        else:
            requirements.append("symbol")

        self.strength_var.set(score)
        # Strength label and color
        if score < 40:
            text, color = "Weak", "red"
        elif score < 70:
            text, color = "Fair", "orange"
        elif score < 90:
            text, color = "Good", "blue"
        else:
            text, color = "Strong", "green"
        self.strength_label.configure(text=f"Strength: {text}", fg=color)
        # Error Message
        if requirements:
            self.password_error_label.config(
                text="Missing: "+", ".join(requirements), fg="red"
            )
        else:
            self.password_error_label.config(text="", fg="green")
        # Enable button only if strong enough
        if score >= 70:
            self.change_btn.configure(state="normal")
        else:
            self.change_btn.configure(state="disabled")

    def verify_password_and_status(self, event=None):
        username = self.username_var.get().strip()
        entered_pass = self.password_var.get()
        if not username or not entered_pass:
            messagebox.showerror(
                "Error", "Username and Current Password Required.",
                parent=self.main_frame
            )
            return
        result = get_login_status_and_name(self.conn, username)
        if not result:
            messagebox.showerror(
                "Error", "User Not Authorised.", parent=self.main_frame
            )
            return
        user = result[0]
        status = result[1]
        success, password = fetch_password(self.conn, username)
        if not success:
            messagebox.showerror("Error", password, parent=self.window)
            return
        stored_password = password["password"]
        if not stored_password:
            messagebox.showwarning(
                "Invalid",
                "Invalid Username or Password.", parent=self.window
            )
            self.password_entry.focus_set()
            return
        if not PasswordSecurity.verify_password(entered_pass, stored_password):
            messagebox.showwarning(
                "Invalid",
                "Invalid Username or Password.", parent=self.window
            )
            self.password_entry.focus_set()
            return
        if status.lower() != "active":
            messagebox.showerror(
                "Disabled", f"{user}'s Account is Disabled.",
                parent=self.main_frame
            )
            return
        # If all checks passed
        self.show_password_change_fields()

    def show_password_change_fields(self):
        self.new_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        self.new_password_entry.focus_set()

    def change_password(self):
        new_pass = self.new_password_var.get()
        confirm_pass = self.confirm_password_var.get()
        if not new_pass or not confirm_pass:
            messagebox.showwarning(
                "Required", "Please Enter and Confirm New Password.",
                parent=self.main_frame
            )
            return
        if new_pass != confirm_pass:
            messagebox.showwarning(
                "Missmatch", "New Password and Confirmation Don't Match.",
                parent=self.main_frame
            )
            return
        user = self.username_var.get().strip()
        success, msg = update_login_password(self.conn, user, new_pass)
        if success:
            messagebox.showinfo("Success", msg, parent=self.main_frame)
            self.window.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self.main_frame)


class UserPrivilegesPopup(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("User Privileges")
        self.center_window(self.window, 650, 600, parent)
        self.window.configure(bg="lightgreen")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        # Fetch user list; usernames and user codes
        self.users_data = fetch_all_users(self.conn)
        if isinstance(self.users_data, str):
            messagebox.showerror(
                "Error", self.users_data, parent=self.window
            )
            self.window.destroy()
            return
        self.usernames = [user['username'] for user in self.users_data]
        self.usercodes = [user['user_code'] for user in self.users_data]
        self.username_var = tk.StringVar()
        self.usercode_var = tk.StringVar()
        self.privileges_data = []
        self.columns = ["No", "ID", "Privilege", "Clearance"]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.list_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=4, relief="ridge"
        )
        self.btn_frame = tk.Frame(self.list_frame, bg="lightgreen")
        self.username_cb = ttk.Combobox(
            self.top_frame, textvariable=self.username_var, width=10,
            values=self.usernames, font=("Arial", 12)
        )
        self.usercode_cb = ttk.Combobox(
            self.top_frame, textvariable=self.usercode_var, width=10,
            values=self.usercodes, font=("Arial", 12)
        )
        self.info_label = tk.Label(
            self.btn_frame, text="", bg="lightgreen", fg="red",
            font=("Arial", 14, "italic", "underline")
        )
        self.tree = ttk.Treeview(
            self.list_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tk.Label(
            self.main_frame, text="Privileges Assigned To User", fg="blue",
            bg="lightgreen", font=("Arial", 16, "bold", "underline")
        ).pack(side="top", pady=(5, 0), padx=10)
        self.top_frame.pack(padx=20)
        tk.Label(
            self.top_frame, text="Select Username:", bg="lightgreen",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(5, 0), padx=(0, 10))
        self.username_cb.grid(row=1, column=0, pady=(0, 5))
        self.username_cb.bind(
            "<<ComboboxSelected>>", self.on_username_selected
        )
        tk.Label(
            self.top_frame, text="Select User Code:", bg="lightgreen",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=1, sticky="w", pady=(5, 0), padx=10)
        self.usercode_cb.grid(row=1, column=1, pady=(0, 5))
        self.usercode_cb.bind(
            "<<ComboboxSelected>>", self.on_usercode_selected
        )
        self.btn_frame.pack(fill="x")
        self.info_label.pack(side="left", padx=10)
        tk.Button(
            self.btn_frame, text="Remove Privilege", bd=2, relief="groove",
            command=self.remove_privilege, bg="dodgerblue", fg="white",
            font=("Arial", 10, "bold")
        ).pack(side="right")
        scrollbar = tk.Scrollbar(self.list_frame, orient="vertical",
                                 command=self.tree.yview)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="w", width=30)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def on_username_selected(self, event=None):
        username = self.username_var.get()
        result = fetch_user_identity(self.conn, username)
        if isinstance(result, dict):
            self.usercode_var.set(result['user_code'])
            self.list_frame.pack(fill="both", expand=True)
            self.display_privileges()

    def on_usercode_selected(self, event=None):
        user_code = self.usercode_var.get()
        result = fetch_user_identity(self.conn, user_code)
        if isinstance(result, dict):
            self.username_var.set(result['username'])
            self.list_frame.pack(fill="both", expand=True)
            self.display_privileges()

    def display_privileges(self):
        identifier = self.username_var.get() or self.usercode_var.get()
        user_info, privileges = fetch_user_details_and_privileges(
            self.conn, identifier
        )
        if not user_info:
            messagebox.showerror(
                "Error", "No User Found.", parent=self.window
            )
        elif "error" in user_info:
            messagebox.showerror(
                "Error", user_info["error"], parent=self.window
            )
        rank = user_info['designation']
        user = user_info['username']
        self.info_label.config(text=f"Privileges Of {rank}; {user}.")
        self.privileges_data = privileges

        for row in self.tree.get_children():
            self.tree.delete(row)

        if privileges:
            formatter = DescriptionFormatter(30, 10)
            for i, p in enumerate(privileges, start=1):
                clearance = formatter.format(p["clearance"])
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=(
                    i,
                    p["no"],
                    p["privilege"],
                    clearance
                ), tags=(tag,))
        else:
            text = "No Privileges Assigned."
            self.tree.insert("", "end", values=("", "", text, ""))
        self.sorter.autosize_columns()

    def remove_privilege(self):
        """Remove the selected privilege from the list and database."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "No Selection", "Please Select Privilege to Remove.",
                parent=self.main_frame
            )
            return

        values = self.tree.item(selected[0], "values")
        aid = values[1]
        pname = values[2]
        name = self.username_var.get()
        user_code = self.usercode_var.get()
        confirm = messagebox.askyesno(
            "Confirm",
            f"Remove '{pname}' Privilege From {name}?", default="no",
            parent=self.window
        )
        if not confirm:
            return
        # Verify Privilege
        priv = "Remove Privilege"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Permission To {priv}.", parent=self.window
            )
            return
        success, msg = remove_user_privilege(
            self.conn, user_code, aid, pname, name, self.user
        )
        if success:
            messagebox.showinfo("Success", msg, parent=self.main_frame)
            self.display_privileges()
        else:
            messagebox.showerror("Error", msg, parent=self.main_frame)


class DepartmentsPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Departments")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 720, 450, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        # Bold table headings
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.left_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.add_btn = tk.Button(
            self.left_frame, text="New Department", bg="blue", fg="white",
            bd=4, relief="groove", font=("Arial", 10, "bold"),
            command=self.show_add_department
        )
        self.new_dept_label = tk.Label(
            self.left_frame, text="Department Name:", bg="lightgreen",
            font=("Arial", 11, "bold")
        )
        self.new_dept_entry = tk.Entry(
            self.left_frame, width=15, bd=4, relief="raised",
            font=("Arial", 11)
        )
        self.create_btn = tk.Button(
            self.left_frame, text="Post Department", bg="blue", fg="white", bd=4,
            relief="groove", font=("Arial", 10, "bold"),
            command=self.create_department
        )
        self.close_frame_btn = tk.Button(
            self.left_frame, text="X", command=self.hide_frame, bg="blue",
            fg="red", bd=4, relief="groove", font=("Arial", 10, "bold")
        )
        self.right_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.columns = ("No.", "Dept Name", "Dept Code", "Employees")
        self.tree = ttk.Treeview(
            self.right_frame, columns=self.columns, show="headings"
        )

        self.sorter = TreeviewSorter(self.tree, self.columns, "No.")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Left frame for add department section
        self.left_frame.pack(side="left", fill="y", padx=(0,5))
        tk.Label(self.left_frame, text="", bg="lightgreen").pack(pady=5)
        self.add_btn.pack(pady=(0, 10))
        # Right Frame for Table section
        self.right_frame.pack(side="right", fill="both", expand=True)
        table_title = tk.Label(
            self.right_frame, text="Current Available Departments", fg="blue",
            bg="lightgreen", font=("Arial", 16, "bold", "underline")
        )
        table_title.pack(padx=10, anchor="center")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        # Vertical Scrollbar
        vsb = ttk.Scrollbar(
            self.right_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

        self.populate_table()

    def show_add_department(self):
        self.add_btn.pack_forget()
        self.close_frame_btn.pack(anchor="ne", padx=5)
        self.new_dept_label.pack(pady=(5, 0))
        self.new_dept_entry.pack(pady=(0, 5))
        self.new_dept_entry.bind("<KeyRelease>", capitalize_customer_name)
        self.new_dept_entry.focus_set()
        self.new_dept_entry.bind(
            "<Return>", lambda e: self.create_btn.focus_set()
        )
        self.create_btn.pack(pady=(5, 0))
        self.create_btn.bind("<Return>", lambda e: self.create_department())

    def create_department(self):
        name = self.new_dept_entry.get().strip()
        if not name:
            messagebox.showwarning(
                "Input Error",
                "Department Name Can't be Empty.", parent=self.window
            )
            return
        # Verify user privilege
        priv = "Admin Add Department"
        verify_dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv
        )
        if verify_dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Permission to {priv}.", parent=self.window
            )
            return
        success, msg = insert_into_departments(self.conn, name, self.user)
        if success:
            messagebox.showinfo("Success", msg, parent=self.window)
            self.new_dept_entry.delete(0, tk.END)
            self.refresh_table()
            self.hide_frame()
        else:
            messagebox.showerror("Error", msg, parent=self.window)

    def populate_table(self):
        self.tree.delete(*self.tree.get_children())
        departments = fetch_departments(self.conn)
        if isinstance(departments, str):
            messagebox.showerror("Error", departments)
            return
        for idx, dept in enumerate(departments, start=1):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                idx,
                dept["name"],
                dept["code"],
                dept["employees"]
            ), tags=(tag,))
        self.sorter.autosize_columns()

    def hide_frame(self):
        self.new_dept_label.pack_forget()
        self.new_dept_entry.pack_forget()
        self.create_btn.pack_forget()
        self.close_frame_btn.pack_forget()
        self.add_btn.pack(pady=(0, 10))

    def refresh_table(self):
        self.populate_table()


class EditEmployeeWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Employee")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 350, 500, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.current_record = None # Will hold the fetched row
        # Variables
        self.search_type_var = tk.StringVar(value="username")
        self.identifier_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.salary_var = tk.StringVar()
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.search_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.search_type_cb = ttk.Combobox(
            self.search_frame, textvariable=self.search_type_var, width=10,
            values=["Username", "User Code"], state="readonly",
            font=("Arial", 11)
        )
        self.identifier_entry = tk.Entry(
            self.search_frame, width=15, textvariable=self.identifier_var,
            bd=4, relief="raised", font=("Arial", 11)
        )
        self.search_btn = tk.Button(
            self.search_frame, text="Search", bg="blue", fg="white", bd=4,
            relief="groove", font=("Arial", 10, "bold"),
            command=self.perform_search
        )
        self.prompt_label = tk.Label(
            self.search_frame, bg="lightgreen", font=("Arial", 11, "bold"),
            text=f"Search {self.search_type_var.get()}:"
        )
        self.edit_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=1, relief="solid"
        )
        # Header
        self.header_var = tk.StringVar(value="Editing User; ")
        self.header_label = tk.Label(
            self.edit_frame, bg="lightgreen", textvariable=self.header_var,
            font=("Arial", 12, "bold", "underline"), fg="dodgerblue"
        )
        # Status handled separately
        self.status_cb = ttk.Combobox(
            self.edit_frame, textvariable=self.status_var, width=10,
            values=["active", "disabled"], state="disabled",
            font=("Arial", 11)
        )
        self.post_btn = tk.Button(
            self.edit_frame, text="Post Update", bg="dodgerblue", fg="white",
            bd=4, relief="groove", state="disabled", font=("Arial", 10, "bold"),
            command=self.post_update
        )

        # Entry widgets container
        self.entries = {}

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(
            self.main_frame, text="Edit Employee Information", fg="blue",
            bg="lightgreen", font=("Arial", 18, "bold", "underline")
        ).pack(side="top", anchor="center")
        # Search section
        self.search_frame.pack(fill="x", pady=(5, 0))
        tk.Label(
            self.search_frame, text="Search by:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, sticky="e")
        self.search_type_cb.grid(row=0, column=1, padx=(0, 5), sticky="w")
        self.search_type_cb.bind("<<ComboboxSelected>>", self.update_prompt)
        self.prompt_label.grid(row=1, column=0, pady=5, sticky="e")
        self.identifier_entry.grid(row=1, column=1, pady=5, sticky="w")
        self.identifier_entry.focus_set()
        self.identifier_entry.bind(
            "<Return>", lambda e: self.search_btn.focus_set()
        )
        self.search_btn.grid(row=2, column=0, columnspan=2, pady=(5, 0))
        self.search_btn.bind("<Return>", lambda e: self.perform_search())
        self.edit_frame.pack(fill="both", expand=True, pady=(5, 0))
        self.header_label.grid(
            row=0, column=0, columnspan=2, pady=(0, 5), sticky="we"
        )
        # Create entry widgets
        labels_and_keys = [
            ("Name:", "name"),
            ("Username:", "username"),
            ("Designation:", "designation"),
            ("National ID:", "national_id"),
            ("Phone:", "phone"),
            ("Email:", "email"),
            ("Salary:", "salary"),
            ("Status:", "status")
        ]
        for _, key in labels_and_keys:
            if key != "status":
                self.entries[key] = tk.Entry(
                    self.edit_frame, width=25, bd=4, relief="raised",
                    font=("Arial", 11)
                )
        self.entries["salary"].configure(textvariable=self.salary_var)
        CurrencyFormatter.add_currency_trace(
            self.salary_var, self.entries["salary"]
        )
        # Layout fields (labels left, inputs right)
        row = 1
        for label_text, key in labels_and_keys:
            tk.Label(
                self.edit_frame, text=label_text, bg="lightgreen",
                font=("Arial", 11, "bold")
            ).grid(row=row, column=0, pady=3, sticky="e")
            if key == "status":
                self.status_cb.grid(row=row, column=1, pady=3, sticky="w")
                self.status_cb.configure(state="disabled")
            else:
                self.entries[key].grid(row=row, column=1, pady=3, sticky="w")
                self.entries[key].configure(state="disabled")
            row += 1
        # Post Button
        self.post_btn.grid(row=row, column=0, columnspan=2, pady=10)

    def update_prompt(self, event=None):
        kind = self.search_type_var.get()
        self.prompt_label.config(text=f"Search {kind}:")

    def select_all_text(self, event=None):
        event.widget.selection_range(0, tk.END)
        return 'break'

    def perform_search(self):
        identifier = self.identifier_var.get().strip()
        kind = self.search_type_var.get()
        if not identifier:
            messagebox.showwarning(
                "Required", f"Please enter {kind} to search.",
                parent=self.window
            )
            return
        success, result = fetch_employee_login_info(self.conn, identifier)
        if not success:
            messagebox.showerror("Not Found", result, parent=self.window)
            return
        self.current_record = result
        # Populate and enable fields
        ordered_keys = [
            "name", "username", "designation", "national_id", "phone",
            "email", "salary"
        ]
        for i, key in enumerate(ordered_keys):
            entry = self.entries.get(key)
            if entry:
                entry.configure(state="normal")
                entry.delete(0, tk.END)
                if key == "salary" and result.get(key):
                    self.salary_var.set(f"{int(float(result[key])):,}")
                else:
                    entry.insert(0, result.get(key, ""))
                # Bind Enter Navigation
                if i < len(ordered_keys) - 1:
                    next_entry = self.entries[ordered_keys[i + 1]]
                    entry.bind(
                        "<Return>", lambda e, next_e=next_entry: next_e.focus_set()
                    )
                # Bind focus-in to select all text
                entry.bind("<FocusIn>", self.select_all_text)
        # Capitalize Name on focus out
        self.entries["name"].bind("<KeyRelease>", capitalize_customer_name)
        digit_vcmd = (self.window.register(only_digits), "%S")
        self.entries["phone"].configure(
            validate="key", validatecommand=digit_vcmd
        )
        self.entries["national_id"].configure(
            validate="key", validatecommand=digit_vcmd
        )

        self.status_cb.configure(state="readonly")
        self.status_var.set(result.get("status", "active"))
        # Header text
        uname = result.get("username", "")
        self.header_var.set(f"Editing User Info For  {uname.capitalize()}.")
        # Enable post button
        self.post_btn.configure(state="normal")
        self.entries["name"].focus_set()

    def post_update(self):
        if not self.current_record:
            messagebox.showwarning(
                "No Record", "You Need to Search and Load Info First.",
                parent=self.window
            )
            return
        email = self.entries["email"].get().strip()
        if not is_valid_email(email):
            messagebox.showerror(
                "Error", "Invalid email format.", parent=self.window
            )
            self.entries["email"].focus_set()
            return
        # Verify user privilege
        priv = "Edit User"
        verify_dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv
        )
        if verify_dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Permission to {priv}.", parent=self.window
            )
            return
        info = {
            "user_code": self.current_record.get("user_code"),
            "name": self.entries["name"].get().strip(),
            "username": self.entries["username"].get().strip(),
            "designation": self.entries["designation"].get().strip(),
            "national_id": self.entries["national_id"].get().strip(),
            "phone": self.entries["phone"].get().strip(),
            "email": self.entries["email"].get().strip(),
            "salary": self.entries["salary"].get().replace(",", "").strip(),
            "status": self.status_var.get()
        }
        success, msg = update_employee_info(self.conn, info, self.user)
        if success:
            messagebox.showinfo("Updated", msg, parent=self.window)
            for entry in self.entries.values():
                entry.delete(0, tk.END)
                entry.configure(state="disabled")
            self.identifier_entry.delete(0, tk.END)
            self.status_cb.set("")
            self.status_cb.configure(state="disabled")
            self.post_btn.configure(state="disabled")
        else:
            messagebox.showerror("Error", msg, parent=self.window)

