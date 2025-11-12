import tkinter as tk
import string
import tkinter.font as tkFont
from tkinter import ttk, messagebox
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from windows_utils import (
    only_digits, capitalize_customer_name, is_valid_email, CurrencyFormatter
)
from working_on_employee import (
    get_departments, username_exists, insert_privilege, get_user_info,
    insert_user_privilege, get_all_privileges, EmployeeManager,
    fetch_departments, get_login_status_and_name, update_login_status,
    get_user_privileges, fetch_password, fetch_all_users,
    remove_user_privilege, reset_user_password, check_username_exists,
    update_login_password, fetch_user_identity, update_employee_info,
    fetch_user_details_and_privileges, insert_into_departments,
    fetch_employee_login_info
)

class EmployeePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Add New Employee")
        self.center_window(self.window, 300, 320, master)
        self.window.configure(bg="lightgreen")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.manager = EmployeeManager(self.conn, user)
        self.departments = get_departments(self.conn)
        self.username_var = tk.StringVar()
        self.username_entry = None
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.username_feedback = tk.Label(
            self.main_frame, text="", bg="lightgreen", fg="red"
        )
        self.entries = {}
        self.entry_order = []
        self.submit_btn = tk.Button(
            self.main_frame, text="Create Employee", bg="dodgerblue", bd=4,
            relief="groove", command=self.submit
        )

        self.build_form()

    def build_form(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        validate_cmd = self.window.register(only_digits)
        fields = [
            ("Name", "name", False),
            ("Username", "username", False),
            ("Department", "department", False),
            ("Designation", "designation", False),
            ("National ID", "national_id", True),
            ("Phone", "phone", True),
            ("Email", "email", False),
            ("Salary", "salary", True)
        ]
        departments = self.departments
        for idx, (label_text, field, digits_only) in enumerate(fields):
            label = tk.Label(
                self.main_frame, text=f"{label_text}:", bg="lightgreen",
                font=("Arial", 11, "bold")
            )
            label.grid(row=idx * 2, column=0, pady=3, sticky="e")
            if field == "department":
                cb = ttk.Combobox(
                    self.main_frame, values=departments, state="readonly"
                )
                cb.grid(row=idx * 2, column=1, pady=3, sticky="ew")
                self.entries[field] = cb
                self.entry_order.append(cb)
            elif field == "username":
                entry = tk.Entry(
                    self.main_frame, textvariable=self.username_var, bd=2,
                    relief="raised", font=("Arial", 11)
                )
                entry.grid(row=idx * 2, column=1, pady=3, sticky="ew")
                entry.bind("<KeyRelease>", self.validate_username)
                entry.bind("<Return>", self.focus_next_entry)
                self.entries[field] = entry
                self.username_entry = entry
                self.entry_order.append(entry)

            else:
                entry = tk.Entry(self.main_frame, bd=2, relief="raised",
                                 font=("Arial", 11))
                entry.grid(row=idx * 2, column=1, pady=3, sticky="ew")
                if field == "name":
                    entry.bind("<KeyRelease>", capitalize_customer_name)
                if digits_only:
                    entry.config(
                        validate="key", validatecommand=(validate_cmd, "%S")
                    )
                entry.bind("<Return>", self.focus_next_entry)
                self.entries[field] = entry
                self.entry_order.append(entry)
        self.entries["name"].focus_set()
        self.entries["salary"].bind("<Return>", lambda e: self.submit())
        self.submit_btn.grid(
            row=len(fields) * 2, column=0, columnspan=2, pady=10, sticky="ew"
        )

    def validate_username(self, event=None):
        keyword = self.username_var.get()
        if not keyword:
            self.username_feedback.grid_remove()
            self.username_entry.config(bg="white")
            return
        if not self.username_feedback.winfo_ismapped():
            self.username_feedback.grid(
                row=3, column=0, columnspan=2, sticky="e", padx=5
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
        # Verify user privilege
        priv = "Add User"
        verify_dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, priv
        )
        if verify_dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You don't Have Permission To {priv}.", parent=self.window
            )
            return
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
        try:
            emp_data = {
                "name": data["name"],
                "username": data["username"],
                "department": data["department"],
                "designation": data["designation"],
                "national_id": int(data["national_id"]),
                "phone": data["phone"],
                "email": data["email"],
                "salary": float(data["salary"])
            }
            success, message = self.manager.insert_employee(emp_data)
            if success:
                messagebox.showinfo("Success", message, parent=self.window)
                self.window.destroy()
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
        self.center_window(self.window, 300, 300, master)
        self.window.configure(bg="lightgreen")
        self.window.transient(master)
        self.window.grab_set()
        self.conn = conn
        self.user = user

        self.current_status = None
        self.identifier_type = tk.StringVar(value="username")
        self.identifier_input = tk.StringVar()
        self.status_var = tk.StringVar()
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.search_by_combo = ttk.Combobox(
            self.main_frame, textvariable=self.identifier_type, width=10,
            values=["Username", "User code"], state="readonly"
        )
        self.input_label = tk.Label(
            self.main_frame, text="Enter Username:", bg="lightgreen",
            font=("Arial", 11, "bold")
        )
        self.identifier_entry = tk.Entry(
            self.main_frame, textvariable=self.identifier_input, width=10,
            bd=2, relief="raised", font=("Arial", 11)
        )
        self.search_btn = tk.Button(
            self.main_frame, text="Search", bg="dodgerblue", fg="white",
            bd=2, relief="groove", width=10, command=self.search_user
        )
        self.status_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=2, relief="flat"
        )
        self.info_label = tk.Label(
            self.status_frame, text="", bg="lightgreen", fg="blue",
            font=("Arial", 12, "italic", "underline")
        )
        self.status_label = tk.Label(
            self.status_frame, text="", font=("Arial", 11, "bold"),
            bg="lightgreen"
        )
        self.status_combo = ttk.Combobox(
            self.status_frame, textvariable=self.status_var, state="readonly",
            values=["active", "disabled"], width=10
        )
        self.post_btn = tk.Button(
            self.main_frame, text="Post Status", bg="green", fg="white",
            command=self.post_update
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Search by label and combobox
        tk.Label(
            self.main_frame, text="Search User By:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, pady=5, padx=(5, 0), sticky="e")
        self.search_by_combo.grid(row=0, column=1, pady=5, sticky="w")
        # bind change in identifier type to update label
        self.search_by_combo.bind(
            "<<ComboboxSelected>>", self.update_input_label
        )
        # Entry field label and entry box
        self.input_label.grid(
            row=1, column=0, columnspan=2, pady=(5, 0), sticky="w"
        )
        self.identifier_entry.grid(
            row=2, column=0, columnspan=2, pady=(0, 5), padx=10, sticky="ew"
        )
        self.identifier_entry.focus_set()
        self.identifier_entry.bind(
            "<Return>", lambda e: self.search_btn.focus_set()
        )
        # Search Button
        self.search_btn.grid(row=3, column=0, columnspan=2, pady=5)
        self.search_btn.bind("<Return>", lambda e: self.search_user())
        # Label and status change combo (initially hidden)
        self.info_label.pack(pady=5, padx=10, anchor="center")
        self.status_label.pack(side="left", padx=(5, 0))
        self.status_combo.pack(side="left", padx=(0, 5))

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
        self.status_label.config(text=f"Set {identifier} to:")
        self.status_var.set(self.current_status) # Pre-fill current status
        self.status_frame.grid(row=4, column=0, columnspan=2, sticky="we")
        self.post_btn.grid(row=5, column=0, columnspan=2, pady=10)

    def post_update(self):
        identifier = self.identifier_input.get().strip()
        new_status = self.status_var.get().lower()
        # Verify User privilege
        if new_status == "active":
            priv = "Activate User"
        else:
            priv = "Deactivate User"
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
            self.window.destroy()
        else:
            messagebox.showerror("Error", result, parent=self.window)

class PrivilegePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Add Privileges")
        self.center_window(self.window, 300, 150, master)
        self.window.configure(bg="lightblue")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.privilege_var = tk.StringVar()
        self.main_frame = tk.Frame(
            self.window, bg="lightblue", bd=4, relief="solid"
        )
        self.entry = tk.Entry(
            self.main_frame, textvariable=self.privilege_var, width=30, bd=2,
            relief="raised", font=("Arial", 11)
        )

        self.build_form()

    def build_form(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Title Label
        tk.Label(
            self.main_frame, text="Enter Privilege:", bg="lightblue",
            font=("Arial", 12, "bold")
        ).pack(pady=(10, 0))
        # Entry field
        self.entry.pack(pady=(0, 10), padx=10)
        self.entry.bind("<KeyRelease>", capitalize_customer_name)
        self.entry.bind("<Return>", self.submit) # Press Enter to submit
        self.entry.focus_set()
        # Submit Button
        tk.Button(
            self.main_frame, text="Add Privilege", bd=2, relief="groove",
            bg="green", fg="white", command=self.submit
        ).pack(pady=5)

    def submit(self, event=None):
        privilege = self.privilege_var.get().strip()
        if not privilege:
            messagebox.showerror(
                "Input Error",
                "Privilege Cannot be empty.", parent=self.window
            )
            return
        # Verify user privilege
        priv = "Create Privilege"
        verify = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You Don't Have Permission To {priv}.", parent=self.window
            )
            return
        # Proceed to insert if access is granted
        success, result = insert_privilege(self.conn, privilege, self.user)
        if success:
            messagebox.showinfo("Success", result, parent=self.window)
            self.privilege_var.set("") # Clear input
            self.entry.focus_set()
        else:
            messagebox.showerror("Error", result, parent=self.window)


class AssignPrivilegePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Assign Privileges")
        self.center_window(self.window, 700, 450, master)
        self.window.configure(bg="lightgreen")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.identifier_type = tk.StringVar(value="Username")
        self.identifier_input = tk.StringVar()
        self.selected_privileges = {} # {id: name}
        self.user_code = None
        self.employee_name = None
        # {id: name}
        self.all_privileges = dict(get_all_privileges(self.conn))
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.identifier_entry = tk.Entry(
            self.top_frame, textvariable=self.identifier_input, width=15,
            bd=2, relief="raised", font=("Arial", 11)
        )
        self.input_label = tk.Label(
            self.top_frame, text="Search Username:", bg="lightgreen",
            font=("Arial", 11, "bold")
        )
        self.middle_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.left_frame = tk.Frame(self.middle_frame, bg="lightgreen")
        self.listbox_frame = tk.Frame(self.left_frame)
        self.privilege_listbox = tk.Listbox(
            self.listbox_frame, height=15, width=30, bd=2, relief="solid"
        )
        self.selected_frame = tk.Frame(
            self.middle_frame, bd=1, relief="sunken", bg="white"
        )
        self.assign_label = tk.Label(
            self.main_frame, text="", bg="lightgreen", fg="blue",
            font=("Arial", 12, "italic", "underline")
        )
        self.post_btn = tk.Button(
            self.main_frame, text="Add Privileges", bg="green", fg="white",
            width=15, command=self.post_privileges, bd=2, relief="groove"
        )

        self.build_layout()

    def build_layout(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Search Section
        self.top_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(
            self.top_frame, text="Search User By:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(5, 0))
        search_by = ttk.Combobox(
            self.top_frame, values=["Username", "User Code"], width=12,
            textvariable=self.identifier_type, state="readonly"
        )
        search_by.pack(side="left", padx=(0, 10))
        search_by.bind("<<ComboboxSelected>>", self.update_input_label)
        self.input_label.pack(side="left", padx=(5, 0))
        self.identifier_entry.pack(side="left")
        self.identifier_entry.focus_set()
        self.identifier_entry.bind("<Return>", self.search_user)
        search_btn = tk.Button(
            self.main_frame, text="Search", bg="dodgerblue", fg="white",
            width=10, command=self.search_user, bd=2, relief="groove"
        )
        search_btn.pack(pady=5, padx=5, anchor="center")
        # Assign Header
        self.assign_label.pack(pady=5)
        # Privileges and Selection Area
        tk.Label(
            self.left_frame, text="Select Privileges to Assign:",
            bg="lightgreen", font=("Arial", 11, "bold", "underline")
        ).pack(anchor="w")
        self.listbox_frame.pack()
        scrollbar = tk.Scrollbar(
            self.listbox_frame, command=self.privilege_listbox.yview
        )
        self.privilege_listbox.config(yscrollcommand=scrollbar.set)
        self.privilege_listbox.pack(side="left")
        scrollbar.pack(side="right", fill="y")
        for name in self.all_privileges.values():
            self.privilege_listbox.insert("end", name)
        self.privilege_listbox.bind(
            "<<ListboxSelect>>", self.handle_listbox_select
        )
        self.left_frame.pack(side="left", fill="y", padx=(3, 0))
        # Right Side: Selected privileges Display
        self.selected_frame.pack(side="left", fill="both", expand=True, pady=10)

    def update_input_label(self, event=None):
        if self.identifier_type.get() == "Username":
            self.input_label.config(text="Enter Username to Search:")
        else:
            self.input_label.config(text="Enter User Code to Search:")

    def search_user(self, event=None):
        identifier = self.identifier_input.get().strip()
        if not identifier:
            messagebox.showerror(
                "Input Error","Please Enter Valid Identifier.",
                parent=self.window
            )
            return
        user_info = get_user_info(self.conn, identifier)
        if not user_info:
            messagebox.showerror(
                "Not Found", f"No User Found for '{identifier}'.",
                parent=self.window
            )
            return
        self.user_code, self.employee_name = user_info
        name = self.employee_name
        self.assign_label.config(text= f"Assign Privileges to: {name}.")
        self.selected_privileges.clear()
        self.update_selected_display()
        self.middle_frame.pack(fill="both", expand=True, pady=5, padx=5)
        self.post_btn.pack(pady=5)

    def handle_listbox_select(self, event=None):
        selection = event.widget.curselection()
        if not selection:
            return
        selected_name = event.widget.get(selection[0])
        self.add_selected_privilege_from_list(selected_name)

    def add_selected_privilege_from_list(self, name):
        for pid, pname in self.all_privileges.items():
            if pname == name and pid not in self.selected_privileges:
                self.selected_privileges[pid] = pname
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
        priv = "Assign Privilege"
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
        for pid, pname in self.selected_privileges.items():
            success, msg = insert_user_privilege(
                self.conn, code, pid, pname, user_name, self.user
            )
            if success:
                success_count += 1
            else:
                fail_count += 1
        if success_count > 0:
            messagebox.showinfo(
                "Success",
                f"{success_count} Privilege(s) Assigned to {user_name}.",
                parent=self.window
            )
        else:
            messagebox.showerror(
                "Error", f"Failed to Add Privilege(s) From {user_name}.",
                parent=self.window
            )
        self.window.destroy()


class RemovePrivilegePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Remove User Privilege")
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
            bd=2, relief="raised", font=("Arial", 11)
        )
        self.middle_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=2, relief="solid"
        )
        self.left_frame = tk.Frame(
            self.middle_frame, bg="lightgreen", bd=2, relief="raised"
        )
        self.listbox_frame = tk.Frame(self.left_frame, bg="lightgreen")
        self.priv_listbox = tk.Listbox(
            self.listbox_frame, height=20, width=40, bd=2, relief="solid"
        )
        self.selected_frame = tk.Frame(
            self.middle_frame, bg="white", bd=2, relief="sunken"
        )
        self.header_label = tk.Label(
            self.middle_frame, text="", bg="lightgreen", fg="blue",
            font=("Arial", 13, "italic", "underline")
        )
        self.remove_btn = tk.Button(
            self.main_frame, text="Remove Privileges", bg="red", fg="white",
            width=15, command=self.remove_selected, bd=2, relief="groove"
        )


        self.build_gui()

    def build_gui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Top search Frame
        self.top_frame.pack(pady=(5, 0), fill="x", padx=5)
        tk.Label(
            self.top_frame, text="Search User By:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(5, 0))
        search_by_cb = ttk.Combobox(
            self.top_frame, values=["Username", "User Code"], width=12,
            textvariable=self.identifier_type, state="readonly"
        )
        search_by_cb.pack(side="left", padx=(0, 10))
        search_by_cb.bind("<<ComboboxSelected>>", self.update_input_label)
        self.dynamic_label.pack(side="left", padx=(5, 0))
        self.identifier_entry.pack(side="left")
        self.identifier_entry.bind("<Return>", self.search_user)
        # Search Button
        tk.Button(
            self.main_frame, text="Search", bg="dodgerblue", fg="white",
            width=10, command=self.search_user, bd=2, relief="groove"
        ).pack(pady=5)
        # Header
        self.header_label.pack(pady=(10, 5))
        # Privilege area
        tk.Label(
            self.left_frame, text="Select Privileges to Remove:",
            bg="lightgreen", font=("Arial", 12, "bold", "underline")
        ).pack(anchor="w")
        self.listbox_frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(
            self.listbox_frame, command=self.priv_listbox.yview
        )
        self.priv_listbox.config(yscrollcommand=scrollbar.set)
        self.priv_listbox.pack(side="left", fill="y")
        scrollbar.pack(side="right", fill="y")
        self.priv_listbox.bind(
            "<<ListboxSelect>>", self.handle_listbox_select
        )
        self.left_frame.pack(side="left", fill="y")
        self.selected_frame.pack(side="left", fill="both", expand=True)
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
        self.middle_frame.pack(fill="both", expand=True, pady=5)
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
        priv = "Remove Privilege"
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
        self.window.title("Reset User Password")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 350, 250, master)
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
            self.main_frame, textvariable=self.identifier_var, width=25,
            bd=2, relief="raised", font=("Arial", 11)
        )
        self.search_btn = tk.Button(
            self.main_frame, text="Search User", bg="dodgerblue", fg="white",
            command=self.search_user, bd=2, relief="groove"
        )
        self.reset_btn = tk.Button(
            self.main_frame, text="Reset Password", bg="green", fg="white",
            command=self.reset_password, bd=2, relief="groove"
        )
        self.reset_btn.bind("<Return>", lambda e: self.reset_password())
        self.identifier_entry.bind("<Return>", self.search_user)
        # Bind to clear previous on type
        self.identifier_entry.bind("<Key>", self.clear_on_type)
        # Flag to clear entry next time user types
        self.replace_on_type = False
        self.pass_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.new_password_entry =tk.Entry(
            self.pass_frame, textvariable=self.new_password_var, width=10,
            bd=2, relief="raised", font=("Arial", 11)
        )
        self.new_password_entry.bind("<KeyRelease>", self.repeat_digit)
        self.new_password_entry.bind(
            "<Return>", lambda e: self.reset_btn.focus_set()
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(
            self.main_frame, text="Username or User Code Search:",
            bg="lightgreen", font=("Arial", 11, "bold")
        ).pack(pady=(10, 5))
        self.identifier_entry.pack(pady=(0, 5))
        self.identifier_entry.focus_set()
        self.search_btn.pack(pady=10)
        tk.Label(
            self.pass_frame, text="One Digit to Set Password(optional):",
            bg="lightgreen", fg="blue", font=("Arial", 11, "bold")
        ).pack(padx=5, pady=(5, 0))
        self.new_password_entry.pack(padx=5)
        self.new_password_entry.bind("<Return>", self.reset_password)
        self.pass_frame.pack(anchor="center", pady=5, padx=2)
        self.pass_frame.pack_forget()
        self.reset_btn.pack(pady=10)
        self.reset_btn.pack_forget() # Hidden Initially

    def repeat_digit(self, event=None):
        digit = self.new_password_var.get().strip()
        if digit.isdigit() and len(digit) == 1:
            self.new_password_var.set(digit * 6)
        elif len(digit) > 1:
            self.new_password_var.set(digit[0] * 6 if digit[0].isdigit() else "")
        elif not digit:
            self.new_password_var.set("")

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
        self.user_code, self.employee_name = get_user_info(self.conn, identifier)
        if not self.user_code:
            messagebox.showerror(
                "Not Found", "No User Found.", parent=self.window
            )
            self.focus_identifier_entry()
            return

        confirm = messagebox.askyesno(
            "Confirm Reset",
            f"Reset Password For: {self.employee_name}?", parent=self.window
        )
        if confirm:
            self.pass_frame.pack(anchor="center", pady=5, padx=2)
            self.new_password_entry.focus_set()
            self.reset_btn.pack(pady=10)
        else:
            self.pass_frame.pack_forget()
            self.reset_btn.pack_forget()
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
            self.window.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self.window)


class ChangePasswordPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Change Password")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 320, 350, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.username_var = tk.StringVar()
        self.username_var.set(user)
        self.password_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.stored_username = None # Username once validated
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.username_entry = tk.Entry(
            self.main_frame, textvariable=self.username_var, bd=4, width=15,
            relief="raised", font=("Arial", 12)
        )
        self.password_entry = tk.Entry(
            self.main_frame, textvariable=self.password_var, show="*", bd=4,
            relief="raised", font=("Arial", 12)
        )
        # New Password (Initially Hidden)
        self.new_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.new_password_entry = tk.Entry(
            self.new_frame, textvariable=self.new_password_var, show="*",
            bd=4, relief="raised", font=("Arial", 12)
        )
        self.password_error_label = tk.Label(
            self.new_frame, text="", fg="red", bg="lightgreen",
            font=("Arial", 9, "italic"))

        self.confirm_password_entry = tk.Entry(
            self.new_frame, textvariable=self.confirm_password_var, show="*",
            bd=4, relief="raised"
        )
        self.change_btn = tk.Button(
            self.new_frame, text="Change Password", bg="dodgerblue", bd=2,
            relief="groove", fg="white", command=self.change_password
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Username Entry
        tk.Label(self.main_frame, text="Username:", bg="lightgreen", font=(
            "Arial", 12, "bold"
        )).pack(pady=(5, 0))
        self.username_entry.pack(pady=(0, 5))
        self.username_entry.focus_set()
        self.username_entry.icursor(tk.END)
        self.username_entry.bind("<Return>", self.check_username)
        # Current Password Entry
        tk.Label(
            self.main_frame, text="Current Password:", bg="lightgreen",
            font=("Arial", 12, "bold")
        ).pack(pady=(5, 0))
        self.password_entry.pack(pady=(0, 5))
        self.password_entry.bind("<Return>", self.verify_password_and_status)
        self.new_frame.pack()
        tk.Label(
            self.new_frame, text="New Password:", bg="lightgreen",
            font=("Arial", 12, "bold")
        ).pack(pady=(10, 0))
        self.new_password_entry.pack()
        # Real time validation
        self.new_password_entry.bind(
            "<KeyRelease>", self.validate_password_strength
        )
        self.new_password_entry.bind(
            "<Return>", lambda e: self.confirm_password_entry.focus_set()
        )
        self.password_error_label.pack(pady=(2, 0))
        # self.password_error_label.pack_forget()
        tk.Label(
            self.new_frame, text="Confirm New Password:", bg="lightgreen",
            font=("Arial", 12, "bold")
        ).pack(pady=(5, 0))
        self.confirm_password_entry.pack()
        self.confirm_password_entry.bind(
            "<Return>", lambda e: self.change_password()
        )
        self.change_btn.pack(pady=5, anchor="center")
        self.new_frame.pack_forget()

    def check_username(self, event=None):
        username = self.username_var.get().strip()
        exists = check_username_exists(self.conn, username)
        if isinstance(exists, tuple): # Error case
            messagebox.showerror(
                "Error", f"DB Error: {exists[1]}", parent=self.main_frame
            )
            return
        if not exists:
            messagebox.showerror(
                "Invalid", "Username Not Allowed. Consult System Admin.",
                parent=self.main_frame
            )
            return
        self.stored_username = username
        self.password_entry.focus_set()

    def validate_password_strength(self, event=None):
        pwd = self.new_password_var.get()
        errors = []
        if len(pwd) < 6:
            errors.append("length 6")
        if not any(c.isupper() for c in pwd):
            errors.append("uppercase")
        if not any(c.isdigit() for c in pwd):
            errors.append("digit")
        if not any(c in string.punctuation for c in pwd):
            errors.append("punctuation")
        if errors:
            self.password_error_label.config(
                text="Should be: "+", ".join(errors)
            )
        else:
            self.password_error_label.config(text="", fg="lightgreen")

    def verify_password_and_status(self, event=None):
        username = self.stored_username
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
        stored_password = fetch_password(self.conn, username)
        if not stored_password or entered_pass != stored_password[0]:
            messagebox.showerror(
                "Error", "Password is Incorrect.", parent=self.main_frame
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
        self.new_frame.pack()
        self.new_password_entry.focus_set()

    def change_password(self):
        new_pass = self.new_password_var.get()
        confirm_pass = self.confirm_password_var.get()
        if not new_pass or not confirm_pass:
            messagebox.showerror(
                "Error", "Please Enter and Confirm New Password.",
                parent=self.main_frame
            )
            return
        if new_pass != confirm_pass:
            messagebox.showerror(
                "Missmatch", "New Password and Confirmation Don't Match.",
                parent=self.main_frame
            )
            return
        success, msg = update_login_password(
            self.conn, self.stored_username, new_pass
        )
        if success:
            messagebox.showinfo("Success", msg, parent=self.main_frame)
            self.window.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self.main_frame)


class UserPrivilegesPopup(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("View User Privileges")
        self.center_window(self.window, 500, 400, parent)
        self.window.configure(bg="lightgreen")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        # Fetch user list; usernames and user codes
        self.users_data = fetch_all_users(self.conn)
        if isinstance(self.users_data, str):
            messagebox.showerror("Error", self.users_data)
            self.window.destroy()
            return
        self.usernames = [user['username'] for user in self.users_data]
        self.usercodes = [user['user_code'] for user in self.users_data]
        self.username_var = tk.StringVar()
        self.usercode_var = tk.StringVar()
        self.privileges_data = []
        self.columns = ["No", "Access ID", "Privilege"]
        style = ttk.Style()
        style.configure(
            "Treeview.Heading", font=("Arial", 11, "bold", "underline")
        )
        style.configure("Treeview", font=("Arial", 10))
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.list_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=2, relief="solid"
        )
        self.username_cb = ttk.Combobox(
            self.top_frame, textvariable=self.username_var, width=10,
            values=self.usernames, font=("Arial", 12)
        )
        self.usercode_cb = ttk.Combobox(
            self.top_frame, textvariable=self.usercode_var, width=10,
            values=self.usercodes, font=("Arial", 12)
        )
        self.info_label = tk.Label(
            self.main_frame, text="", bg="lightgreen", fg="red",
            font=("Arial", 14, "italic", "underline")
        )
        self.tree = ttk.Treeview(
            self.list_frame, columns=self.columns, show="headings", height=10
        )

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tk.Label(
            self.main_frame, text="Select User to Display Privileges",
            bg="lightgreen", font=("Arial", 14, "bold", "underline")
        ).pack(side="top", pady=(5, 0), padx=10)
        self.top_frame.pack(padx=20, fill="x", anchor="center")
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
        self.info_label.pack(pady=(5, 0))
        btn_frame = tk.Frame(self.list_frame, bg="lightgreen")
        btn_frame.pack(fill="x", padx=5)
        tk.Button(
            btn_frame, text="Remove Privilege", bd=2, relief="groove",
            command=self.remove_privilege, bg="dodgerblue", fg="white"
        ).pack(side="right")
        scrollbar = tk.Scrollbar(self.list_frame, orient="vertical",
                                 command=self.tree.yview)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

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
            for i, p in enumerate(privileges, start=1):
                self.tree.insert("", "end", values=(
                    i,
                    p["no"],
                    p["privilege"]
                ))
        else:
            text = "No Privileges Assigned."
            self.tree.insert("", "end", values=("", "", text))
        self.autosize_columns()

    def remove_privilege(self):
        """Remove the selected privilege from the list and database."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "No Selection", "Please Select Privilege to Remove.",
                parent=self.main_frame
            )
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

        values = self.tree.item(selected[0], "values")
        aid = values[1]
        pname = values[2]
        name = self.username_var.get()
        user_code = self.usercode_var.get()

        confirm = messagebox.askyesno(
            "Confirm",
            f"Remove Privilege to '{pname}' From {name}", default="no",
            parent=self.window
        )
        if not confirm:
            return
        success, msg = remove_user_privilege(
            self.conn, user_code, aid, pname, name, self.user
        )
        if success:
            messagebox.showinfo("Success", msg, parent=self.main_frame)
            self.display_privileges()
        else:
            messagebox.showerror("Error", msg, parent=self.main_frame)

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            self.tree.column(col, width=max_width)


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
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.left_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.add_btn = tk.Button(
            self.left_frame, text="New Department", bd=2, relief="groove",
            command=self.show_add_department
        )
        self.new_dept_label = tk.Label(
            self.left_frame, text="Department Name:", bg="lightgreen",
            font=("Arial", 11, "bold")
        )
        self.new_dept_entry = tk.Entry(
            self.left_frame, width=20, bd=2, relief="raised",
            font=("Arial", 11)
        )
        self.create_btn = tk.Button(
            self.left_frame, text="Create Department", bd=2, relief="groove",
            command=self.create_department
        )
        self.close_frame_btn = tk.Button(
            self.left_frame, text="X", command=self.hide_frame, bg="red",
            fg="white", relief="solid", font=("Arial", 10, "bold")
        )
        self.right_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.columns = ("No", "Name", "Code", "Employees")
        self.tree = ttk.Treeview(
            self.right_frame, columns=self.columns, show="headings"
        )
        # Bold table headings
        style = ttk.Style()
        style.theme_use("alt")
        style.configure("Treeview", font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))

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
            self.right_frame, text="Current Available Departments",
            bg="lightgreen", font=("Arial", 15, "bold", "underline")
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
        # Mousewheel binding
        self.tree.bind(
            "<Enter>", lambda e: self.tree.bind_all("<MouseWheel>", self.on_mousewheel)
        )
        self.tree.bind("<Leave>", lambda e: self.tree.unbind_all("<MouseWheel>"))

        self.populate_table()

    def on_mousewheel(self, event):
        self.tree.yview_scroll(int(-1 * (event.delta/120)), "units")

    def show_add_department(self):
        self.add_btn.pack_forget()
        self.close_frame_btn.pack(anchor="ne", pady=(5, 0), padx=(0, 5))
        self.new_dept_label.pack(pady=(5, 2))
        self.new_dept_entry.pack(pady=2)
        self.new_dept_entry.bind("<KeyRelease>", capitalize_customer_name)
        self.new_dept_entry.focus_set()
        self.new_dept_entry.bind(
            "<Return>", lambda e: self.create_btn.focus_set()
        )
        self.create_btn.pack(pady=5)
        self.create_btn.bind("<Return>", lambda e: self.create_department())

    def create_department(self):
        name = self.new_dept_entry.get().strip()
        if not name:
            messagebox.showwarning(
                "Input Error",
                "Department name cannot be empty.", parent=self.window
            )
            return
        # Verify user privilege
        priv = "Add Department"
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
            self.tree.insert("", "end", values=(
                idx,
                dept["name"],
                dept["code"],
                dept["employees"]
            ))
        self.autosize_columns()

    def hide_frame(self):
        self.new_dept_label.pack_forget()
        self.new_dept_entry.pack_forget()
        self.create_btn.pack_forget()
        self.close_frame_btn.pack_forget()
        self.add_btn.pack(pady=(0, 10))

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            self.tree.column(col, width=max_width)

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
            self.search_frame, text="Search", width=10, bd=4, relief="groove",
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
            command=self.post_update, bd=4, relief="groove", state="disabled"
        )

        # Entry widgets container
        self.entries = {}

        self.build_ui()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
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
        CurrencyFormatter.add_currency_trace(self.salary_var,
                                             self.entries["salary"])
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


# if __name__ == "__main__":
#     from connect_to_db import connect_db
#     conn=connect_db()
#     root=tk.Tk()
#     EditEmployeeWindow(root, conn, "Sniffy")
#     root.mainloop()