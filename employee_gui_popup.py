import tkinter as tk
import string
import tkinter.font as tkFont
from tkinter import ttk, messagebox
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from windows_utils import only_digits, capitalize_customer_name, is_valid_email
from working_on_employee import (
    get_departments, username_exists, insert_privilege, insert_user_privilege, get_all_privileges, EmployeeManager,
    get_user_info, get_login_status_and_name, update_login_status, get_user_privileges, fetch_password, fetch_all_users,
    remove_user_privilege, reset_user_password, check_username_exists, update_login_password, fetch_user_identity,
    fetch_user_details_and_privileges, fetch_departments, insert_into_departments, fetch_employee_login_info,
    update_employee_info)

class EmployeePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Add New Employee")
        self.center_window(self.window, 250, 300, master)
        self.window.configure(bg="lightgreen")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.manager = EmployeeManager(self.conn)
        self.departments = get_departments(self.conn)
        self.username_var = tk.StringVar()
        self.username_entry = None
        self.username_feedback = None
        self.entries = {}
        self.entry_order = []
        self.submit_btn = None
        self.build_form()

    def build_form(self):
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
        self.entries = {}
        for idx, (label_text, field, digits_only) in enumerate(fields):
            label = tk.Label(self.window, text=f"{label_text}:", bg="lightgreen")
            label.grid(row=idx * 2, column=0, pady=3, sticky="e")
            if field == "department":
                cb = ttk.Combobox(self.window, values=self.departments, state="readonly")
                cb.grid(row=idx * 2, column=1, pady=3, sticky="ew")
                self.entries[field] = cb
                self.entry_order.append(cb)
            elif field == "username":
                entry = tk.Entry(self.window, textvariable=self.username_var)
                entry.grid(row=idx * 2, column=1, pady=3, sticky="ew")
                entry.bind("<KeyRelease>", self.validate_username)
                entry.bind("<Return>", self.focus_next_entry)
                self.entries[field] = entry
                self.username_entry = entry
                self.entry_order.append(entry)
                self.username_feedback = tk.Label(self.window, text="", bg="lightgreen", fg="red")
            else:
                entry = tk.Entry(self.window)
                entry.grid(row=idx * 2, column=1, pady=3, sticky="ew")
                if field == "name":
                    entry.bind("<KeyRelease>", capitalize_customer_name)
                if digits_only:
                    entry.config(validate="key", validatecommand=(validate_cmd, "%S"))
                entry.bind("<Return>", self.focus_next_entry)
                self.entries[field] = entry
                self.entry_order.append(entry)
        self.submit_btn = tk.Button(self.window, text="Create Employee", bg="dodgerblue", width=10, command=self.submit)
        self.submit_btn.grid(row=len(fields) * 2, column=0, columnspan=2, pady=10, padx=5, sticky="ew")

    def validate_username(self, event=None):
        keyword = self.username_var.get()
        if not keyword:
            self.username_feedback.grid_remove()
            self.username_entry.config(bg="white")
            return
        if not self.username_feedback.winfo_ismapped():
            self.username_feedback.grid(row=3, column=0, columnspan=2, sticky="e", padx=5)
        if username_exists(self.conn, keyword):
            self.username_feedback.config(text="❌ Username not available", fg="red")
            self.username_entry.config(bg="misty rose")
        else:
            self.username_feedback.config(text="\u2713 Username Available", fg="green")
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
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, "Add User")
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", "You do not have permission to Add User.")
            return
        if missing_fields:
            messagebox.showerror("Error", f"Missing fields: {', '.join(missing_fields)}.")
            return
        if self.username_entry["bg"] == "misty rose":
            messagebox.showerror("Error", "Username is already taken.")
            return
        if not is_valid_email(data["email"]):
            messagebox.showerror("Error", "Invalid email format.")
            return
        try:
            result = self.manager.insert_employee(
                name=data["name"],
                username=data["username"],
                department=data["department"],
                designation=data["designation"],
                national_id=int(data["national_id"]),
                phone=data["phone"],
                email=data["email"],
                salary=float(data["salary"])
            )
            messagebox.showinfo("Success", result)
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Insert field: {e}")

class LoginStatusPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Update Employee Login Status")
        self.center_window(self.window, 275, 210, master)
        self.window.configure(bg="lightgreen")
        self.window.transient(master)
        self.window.grab_set()
        self.conn = conn
        self.user = user

        self.current_status = None
        self.fetched_name = None
        self.identifier_type = tk.StringVar(value="username")
        self.identifier_input = tk.StringVar()
        self.search_by_combo = ttk.Combobox(self.window, textvariable=self.identifier_type, width=15,
                                            values=["Username", "User code"], state="readonly")
        self.input_label = tk.Label(self.window, text="Enter Username:", bg="lightgreen")
        self.identifier_entry = tk.Entry(self.window, textvariable=self.identifier_input, width=20)
        self.search_btn = tk.Button(self.window, text="Search", bg="dodgerblue", fg="white", command=self.search_user)
        self.status_frame = tk.Frame(self.window, bg="lightgreen")
        self.info_label = tk.Label(self.status_frame, text="", font=("Arial", 11, "italic"), bg="lightgreen")
        self.status_label = tk.Label(self.status_frame, text="", bg="lightgreen")
        self.status_var = tk.StringVar()

        self.status_combo = ttk.Combobox(self.status_frame, textvariable=self.status_var,
                                         values=["active", "disabled"], state="readonly")
        self.post_btn = tk.Button(self.window, text="Post Status", bg="green", fg="white", command=self.post_update)
        self.build_ui()

    def build_ui(self):
        # Search by label and combobox
        tk.Label(self.window, text="Search User By:", bg="lightgreen").grid(row=0, column=0, pady=5, padx=(5, 0),
                                                                            sticky="w")
        self.search_by_combo.grid(row=0, column=1, pady=5, sticky="w")
        # bind change in identifier type to update label
        self.search_by_combo.bind("<<ComboboxSelected>>", self.update_input_label)
        # Entry field label and entry box
        self.input_label.grid(row=1, column=0, pady=5, padx=(5, 0), sticky="w")
        self.identifier_entry.grid(row=1, column=1, pady=5, sticky="w")
        self.identifier_entry.focus_set()
        self.identifier_entry.bind("<Return>", lambda e: self.search_btn.focus_set())
        # Search Button
        self.search_btn.grid(row=2, column=0, columnspan=2, pady=10)
        self.search_btn.bind("<Return>", lambda e: self.search_user())
        # Label and status change combo (initially hidden)
        self.info_label.pack(pady=3, padx=(5, 0), anchor="w")
        self.status_label.pack(side="left", padx=(5, 0))

        self.status_combo.pack(side="left", padx=(0, 5))


    def update_input_label(self, event=None):
        label_text = f"Enter {self.identifier_type.get()}:"
        self.input_label.config(text=label_text)
    def search_user(self):
        identifier = self.identifier_input.get().strip()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter a valid Identifier.")
            return
        result = get_login_status_and_name(self.conn, identifier)
        if not result:
            messagebox.showerror("Not Found", f"No user with: {self.identifier_type.get()} '{identifier}'")
            return
        self.fetched_name, self.current_status = result
        self.info_label.config(text=f"{self.fetched_name} is Currently: {self.current_status}.")
        self.status_label.config(text=f"Set {self.fetched_name} to:") # Show label
        self.status_var.set(self.current_status) # Pre-fill current status
        self.status_frame.grid(row=3, column=0, columnspan=2, pady=5)
        self.post_btn.grid(row=4, column=0, columnspan=2, pady=10)
    def post_update(self):
        identifier = self.identifier_input.get().strip()
        new_status = self.status_var.get().lower()
        # Verify User privilege
        if new_status == "active":
            priv = "Activate User"
        else:
            priv = "Deactivate User"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to: {priv}.")
            return
        if new_status == self.current_status:
            messagebox.showerror("Info", f"Status is already '{self.current_status}'.")
            return
        result = update_login_status(self.conn, identifier, new_status)
        if result:
            messagebox.showinfo("Update Result", result)
            self.window.destroy()
        else:
            messagebox.showerror("Error", result)

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
        self.entry = tk.Entry(self.window, textvariable=self.privilege_var, width=40)

        self.build_form()

    def build_form(self):
        # Title Label
        tk.Label(self.window, text="Enter New Privilege:", bg="lightblue", font=("Arial", 12)).pack(pady=10)
        # Entry field
        self.entry.pack(pady=(0, 5), padx=5)
        self.entry.bind("<KeyRelease>", capitalize_customer_name)
        self.entry.bind("<Return>", self.submit) # Press Enter to submit
        self.entry.focus_set()
        # Submit Button
        tk.Button(self.window, text="Add Privilege", bg="green", fg="white", command=self.submit).pack(pady=5)
    def submit(self, event=None):
        privilege = self.privilege_var.get().strip()
        if not privilege:
            messagebox.showerror("Input Error", "Privilege Cannot be empty.")
            return
        # Verify user privilege
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, required_privilege="Create Privilege")
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", "You do not have permission to Create Privileges.")
            return
        # Proceed to insert if access is granted
        result = insert_privilege(self.conn, privilege)
        if "successfully" in result.lower():
            messagebox.showinfo("Success", result)
            self.privilege_var.set("") # Clear input
            self.entry.focus_set()
        else:
            messagebox.showerror("Error", result)

class AssignPrivilegePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Assign Privileges")
        self.center_window(self.window, 650, 450, master)
        self.window.configure(bg="lightgreen")
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.identifier_type = tk.StringVar(value="Username")
        self.identifier_input = tk.StringVar()
        self.selected_privileges = {} # {id: name}
        self.all_privileges = dict(get_all_privileges(self.conn))  # {id: name}
        self.top_frame = tk.Frame(self.window, bg="lightgreen")
        self.user_code = None
        self.identifier_entry = tk.Entry(self.top_frame, textvariable=self.identifier_input, width=20)
        self.employee_name = None
        self.input_label = tk.Label(self.top_frame, text="Enter Username to Search:", font=("Arial", 12),
                                    bg="lightgreen")
        self.middle_frame = tk.Frame(self.window, bg="lightgreen")
        self.left_frame = tk.Frame(self.middle_frame, bg="lightgreen")
        self.listbox_frame = tk.Frame(self.left_frame)
        self.privilege_listbox = tk.Listbox(self.listbox_frame, height=15, width=30)
        self.selected_frame = tk.Frame(self.middle_frame, bd=1, relief="sunken", bg="white")
        self.assign_label = tk.Label(self.window, text="", bg="lightgreen", font=("Arial", 10, "bold"))
        self.post_btn = tk.Button(self.window, text="Add Privileges", command=self.post_privileges, bg="green",
                                  fg="white", width=15)


        self.build_layout()

    def build_layout(self):
        # Search Section
        self.top_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(self.top_frame, text="Search User By:", font=("Arial", 12),
                 bg="lightgreen").pack(side="left", padx=(5, 0))
        search_by = ttk.Combobox(self.top_frame, values=["Username", "User Code"], width=12,
                                 textvariable=self.identifier_type, state="readonly")
        search_by.pack(side="left", padx=(0, 10))
        search_by.bind("<<ComboboxSelected>>", self.update_input_label)
        self.input_label.pack(side="left", padx=(5, 0))
        self.identifier_entry.pack(side="left")
        self.identifier_entry.bind("<Return>", self.search_user)
        search_btn = tk.Button(self.window, text="Search", bg="dodgerblue", fg="white", width=10, command=self.search_user)
        search_btn.pack(pady=5, padx=5, anchor="center")
        # Assign Header
        self.assign_label.pack(pady=5)
        # Privileges and Selection Area
        tk.Label(self.left_frame, text="Select Privileges to Assign:", bg="lightgreen").pack(anchor="w")
        self.listbox_frame.pack(pady=5)
        scrollbar = tk.Scrollbar(self.listbox_frame, command=self.privilege_listbox.yview)
        self.privilege_listbox.config(yscrollcommand=scrollbar.set)
        self.privilege_listbox.pack(side="left")
        scrollbar.pack(side="right", fill="y")
        for name in self.all_privileges.values():
            self.privilege_listbox.insert("end", name)
        self.privilege_listbox.bind("<<ListboxSelect>>", self.handle_listbox_select)
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
            messagebox.showerror("Input Error","Please Enter Valid Identifier.")
            return
        user_info = get_user_info(self.conn, identifier)
        if not user_info:
            messagebox.showerror("Not Found", f"No User Found for '{identifier}'.")
            return
        self.user_code, self.employee_name = user_info
        self.assign_label.config(text= f"Assign Privileges to: {self.employee_name}")
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
        row = 0
        col = 0
        for pid, pname in self.selected_privileges.items():
            item_frame = tk.Frame(self.selected_frame, bg="lightblue", bd=1, relief="flat", padx=3, pady=2)
            label = tk.Label(item_frame, text=pname, bg="lightblue")
            label.pack(side="left")
            remove_btn = tk.Label(item_frame, text="X", fg="red", bg="white", cursor="hand2")
            remove_btn.pack(side="right")
            remove_btn.bind("<Button-1>", lambda e, p=pid: self.remove_privilege(p))
            item_frame.grid(row=row, column=col, padx=3, pady=3, sticky="w")
            col += 1
            if col >= 3: # 3 items per row
                col = 0
                row += 1
    def remove_privilege(self, privilege_id):
        if privilege_id in self.selected_privileges:
            del self.selected_privileges[privilege_id]
            self.update_selected_display()

    def post_privileges(self):
        if not self.user_code or not self.selected_privileges:
            messagebox.showerror("Error", "Please search user and select at least one privilege.")
            return
        # Verify user privilege
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, "Assign Privilege")
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", "You do not have permission to Assign Privileges.")
            return
        success_count = 0
        for access_id in self.selected_privileges:
            if insert_user_privilege(self.conn, self.user_code, access_id):
                success_count += 1
        messagebox.showinfo("Success", f"{success_count} Privileges assigned to {self.employee_name}.")
        self.window.destroy()


class RemovePrivilegePopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Remove User Privilege")
        self.window.configure(bg="Lightgreen")
        self.center_window(self.window, 600, 550, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.identifier_type = tk.StringVar(value="Username")
        self.identifier_input = tk.StringVar()
        self.selected_privileges = [] # [(access_id, privilege)]
        self.privileges_assigned = [] # [(user_code, access_id, privilege)]
        self.top_frame = tk.Frame(self.window, bg="lightgreen")
        self.dynamic_label = tk.Label(self.top_frame, text="Enter Username to Search:", font=("Arial", 11, "bold"),
                                      bg="lightgreen")
        self.identifier_entry = tk.Entry(self.top_frame, textvariable=self.identifier_input, width=20)
        self.middle_frame = tk.Frame(self.window, bg="lightgreen")
        self.header_label = tk.Label(self.middle_frame, text="", bg="lightgreen", font=("Arial", 10, "bold"))
        self.content_frame = tk.Frame(self.middle_frame, bg="lightgreen")
        self.left_frame = tk.Frame(self.content_frame, bg="lightgreen")
        self.priv_listbox = tk.Listbox(self.left_frame, width=30, height=20)
        self.right_frame = tk.Frame(self.content_frame, bg="lightgreen")
        self.selected_frame = tk.Frame(self.right_frame, bg="white", bd=1, relief="flat")
        self.user_code = None

        self.build_gui()

    def build_gui(self):
        # Top search Frame
        self.top_frame.pack(pady=5, fill="x")
        tk.Label(self.top_frame, text="Search By:", font=("Arial", 11, "bold"), bg="lightgreen"
                 ).pack(side="left", padx=(10, 0))
        search_by_cb = ttk.Combobox(self.top_frame, values=["Username", "User Code"], textvariable=self.identifier_type,
                                    state="readonly", width=10)
        search_by_cb.pack(side="left", padx=(0, 10))

        self.dynamic_label.pack(side="left", padx=(10, 0))
        self.identifier_entry.pack(side="left", padx=(0, 10))
        self.identifier_entry.focus_set()
        self.identifier_entry.bind("<Return>", lambda e: search_btn.focus_set())
        search_by_cb.bind("<<ComboboxSelected>>", self.update_input_label)
        # Search Button
        search_btn = tk.Button(self.window, text="Search", command=self.search_user,
                               bg="dodgerblue", fg="white")
        search_btn.pack(pady=5)
        search_btn.bind("<Return>", lambda e: self.search_user())
        # Frame shown after search
        self.middle_frame.pack_forget()
        self.header_label.pack(pady=(10, 5))
        self.content_frame.pack(fill="both", expand=True)
        # Left listbox
        self.left_frame.pack(side="left", fill="y", padx=(5, 0))
        tk.Label(self.left_frame, text="Select Privileges to Remove:", bg="lightgreen").pack(anchor="w")
        scrollbar = tk.Scrollbar(self.left_frame, command=self.priv_listbox.yview)
        self.priv_listbox.config(yscrollcommand=scrollbar.set)
        self.priv_listbox.pack(pady=5, side="left")
        self.priv_listbox.bind("<<ListboxSelect>>", self.add_selected_privileges)
        scrollbar.pack(side="right", fill="y", pady=5)
        # Right selected privileges frame
        self.right_frame.pack(side="right", fill="both", expand=True, padx=5)
        tk.Label(self.right_frame, text="Privileges to Remove From User:", bg="lightgreen").pack(anchor="w")
        self.selected_frame.pack(pady=5, fill="both", expand=True)
        # Bottom remove button
        tk.Button(self.middle_frame, text="Remove Privileges", command=self.remove_selected, bg="dodgerblue",
                  fg="white").pack(pady=10)

    def update_input_label(self, event=None):
        selected = self.identifier_type.get()
        if selected == "Username":
            self.dynamic_label.config(text="Enter Username to Search:")
        else:
            self.dynamic_label.config(text="Enter User Code to Search:")
    def search_user(self):
        identifier = self.identifier_input.get().strip()
        if not identifier:
            messagebox.showerror("Error", "Please enter valid identifier.")
            return
        result = get_user_privileges(self.conn, identifier)
        if not result or isinstance(result, str):
            messagebox.showerror("Not Found", f"No privileged found for '{identifier}'.")
            return
        self.user_code = result[0][0]
        self.privileges_assigned = result
        self.header_label.config(text=f"Remove privilege from user code: {self.user_code}")
        self.priv_listbox.delete(0, tk.END)
        for _, aid, pname in result:
            self.priv_listbox.insert(tk.END, f"{aid}: {pname}")
        self.selected_privileges.clear()
        self.update_selected_display()
        self.middle_frame.pack(pady=5,fill="both", expand=True)
    def add_selected_privileges(self, event=None):
        self.selected_privileges.clear()
        selections = self.priv_listbox.curselection()
        for index in selections:
            access_id, pname = self.privileges_assigned[index][1], self.privileges_assigned[index][2]
            self.selected_privileges.append((access_id, pname))
        self.update_selected_display()
    def update_selected_display(self):
        for widget in self.selected_frame.winfo_children():
            widget.destroy()
        row = 0
        col = 0
        for access_id, privilege in self.selected_privileges:
            item_frame = tk.Frame(self.selected_frame, bg="lightblue", bd=1, relief="flat", padx=3, pady=2)
            label = tk.Label(item_frame, text=privilege, bg="lightblue")
            label.pack(side="left")
            remove_btn = tk.Label(item_frame, text="X", fg="red", bg="white", cursor="hand2")
            remove_btn.pack(side="right")
            remove_btn.bind("<Button-1>", lambda e, aid=access_id: self.remove_privilege_from_list(aid))
            item_frame.grid(row=row, column=col, padx=3, pady=3, sticky="w")
            col += 1
            if col >= 3:  # 3 items per row
                col = 0
                row += 1
    def remove_privilege_from_list(self, access_id):
        self.selected_privileges = [item for item in self.selected_privileges if item[0] != access_id]
        self.update_selected_display()
    def remove_selected(self):
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, "Remove Privilege")
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", "You do not have permission to Remove Privileges.")
            return
        if not self.selected_privileges:
            messagebox.showwarning("No Selection", "No privileges selected to remove.")
            return
        message = []
        for aid, _ in self.selected_privileges:
            result = remove_user_privilege(self.conn, self.user_code, aid)
            message.append(result)
        messagebox.showinfo("Result", "\n".join(message))
        self.window.destroy()

class ResetPasswordPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Reset User Password")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 350, 200, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.user_code = None
        self.employee_name = None
        self.identifier_var = tk.StringVar()
        self.identifier_entry = tk.Entry(self.window, textvariable=self.identifier_var, width=25)
        self.search_btn = tk.Button(self.window, text="Search User", command=self.search_user, bg="dodgerblue", fg="white")
        self.reset_btn = tk.Button(self.window, text="Reset Password", command=self.reset_password, bg="green", fg="white")
        self.reset_btn.bind("<Return>", lambda e: self.reset_password())
        self.identifier_entry.bind("<Return>", self.search_user)
        self.identifier_entry.bind("<Key>", self.clear_on_type) # Bind to clear previous on type
        self.replace_on_type = False # Flag to clear entry next time user types
        self.pass_frame = tk.Frame(self.window, bg="lightgreen")
        self.new_password_var = tk.StringVar()
        self.new_password_entry =tk.Entry(self.pass_frame, textvariable=self.new_password_var, width=8)
        self.new_password_entry.bind("<KeyRelease>", self.repeat_digit)
        self.new_password_entry.bind("<Return>", lambda e: self.reset_btn.focus_set())

        self.build_ui()

    def build_ui(self):
        tk.Label(self.window, text="Enter Username or User Code to Reset:", font=("Arial", 10, "bold"),
                 bg="lightgreen").pack(pady=(10, 5))
        self.identifier_entry.pack(pady=(0, 5))
        self.identifier_entry.focus_set()
        self.search_btn.pack(pady=10)
        tk.Label(self.pass_frame, text="Enter 1-digit to set as password(optional):", bg="lightgreen"
                 ).pack(padx=5, pady=(5, 0))
        self.new_password_entry.pack(padx=5)
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
            messagebox.showerror("Input Error", "Please Enter valid Identifier.")
            self.focus_identifier_entry()
            return
        identifier = self.identifier_var.get().strip()
        self.user_code, self.employee_name = get_user_info(self.conn, identifier)
        if not self.user_code:
            messagebox.showerror("Not Found", f"No user found for '{identifier}'.")
            self.focus_identifier_entry()
            return

        confirm = messagebox.askyesno("Confirm Reset",
                                      f"Do you want to Reset password for: {self.employee_name}?")
        if confirm:
            self.pass_frame.pack(anchor="center", pady=5, padx=2)
            self.new_password_entry.focus_set()
            self.reset_btn.pack(pady=10)
        else:
            self.pass_frame.pack_forget()
            self.reset_btn.pack_forget()
            self.focus_identifier_entry()

    def reset_password(self):
        # Verify user privilege
        priv = "Reset Password"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        user_code = str(self.user_code)
        new_password = self.new_password_var.get().strip() or "000000"
        result = reset_user_password(self.conn, user_code, new_password)
        if "successfully" in result.lower():
            messagebox.showinfo("Success", result)
            messagebox.showinfo("Advice Info", f"Advice User to use '{new_password}' as Login Password.")
            self.window.destroy()
        else:
            messagebox.showerror("Error", result)

class ChangePasswordPopup(BaseWindow):
    def __init__(self, master, conn, user):
        self.window = tk.Toplevel(master)
        self.window.title("Change Password")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 300, 260, master)
        self.window.transient(master)
        self.window.grab_set()

        self.conn = conn
        self.username_var = tk.StringVar()
        self.username_var.set(user)
        self.password_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.stored_username = None # Username once validated
        self.employee_name = None # Fetched name
        self.username_entry = tk.Entry(self.window, textvariable=self.username_var)
        self.password_entry = tk.Entry(self.window, textvariable=self.password_var, show="*")
        # New Password (Initially Hidden)
        self.new_frame = tk.Frame(self.window, bg="lightgreen")
        self.new_password_label = tk.Label(self.new_frame, text="New Password:", bg="lightgreen",
                                           font=("Arial", 12, "bold"))
        self.new_password_entry = tk.Entry(self.new_frame, textvariable=self.new_password_var, show="*")
        self.password_error_label = tk.Label(self.new_frame, text="", fg="red", bg="lightgreen",
                                             font=("Arial", 8, "italic"))
        self.confirm_password_label = tk.Label(self.new_frame, text="Confirm New Password:", bg="lightgreen",
                                               font=("Arial", 12, "bold"))
        self.confirm_password_entry = tk.Entry(self.new_frame, textvariable=self.confirm_password_var, show="*")
        self.change_btn = tk.Button(self.new_frame, text="Change Password", bg="dodgerblue", fg="white",
                                    command=self.change_password)

        self.build_ui()

    def build_ui(self):
        # Username Entry
        tk.Label(self.window, text="Username:", bg="lightgreen", font=("Arial", 12, "bold")).pack(pady=(5, 0))
        self.username_entry.pack()
        self.username_entry.bind("<Return>", self.check_username)
        # Current Password Entry
        tk.Label(self.window, text="Current Password:", bg="lightgreen", font=("Arial", 12, "bold")).pack(pady=(5, 0))
        self.password_entry.pack()
        self.password_entry.bind("<Return>", self.verify_password_and_status)
        self.new_frame.pack()
        self.new_password_label.pack(pady=(10, 0))
        self.new_password_entry.pack()
        self.new_password_entry.bind("<KeyRelease>", self.validate_password_strength) # Real time validation
        self.new_password_entry.bind("<Return>", lambda e: self.confirm_password_entry.focus_set())
        self.password_error_label.pack(pady=(2, 0))
        # self.password_error_label.pack_forget()
        self.confirm_password_label.pack(pady=(5, 0))
        self.confirm_password_entry.pack()
        self.confirm_password_entry.bind("<Return>", lambda e: self.change_password())
        self.change_btn.pack(pady=5, anchor="center")
        self.new_frame.pack_forget()
    def check_username(self, event=None):
        username = self.username_var.get().strip()
        exists = check_username_exists(self.conn, username)
        if isinstance(exists, tuple): # Error case
            messagebox.showerror("Error", f"DB Error: {exists[1]}")
            return
        if not exists:
            messagebox.showerror("Invalid","Username not allowed. Consult System Admin.")
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
            self.password_error_label.config(text="Should be: "+", ".join(errors))
        else:
            self.password_error_label.config(text="", fg="lightgreen")
    def verify_password_and_status(self, event=None):
        username = self.stored_username
        entered_pass = self.password_var.get()
        if not username or not entered_pass:
            messagebox.showerror("Error", "Username and Current Password Required.")
            return
        result = get_login_status_and_name(self.conn, username)
        if not result:
            messagebox.showerror("Error", "User Not Authorised.")
            return
        name, status = result
        self.employee_name = name
        stored_password = fetch_password(self.conn, username)
        if not stored_password or entered_pass != stored_password[0]:
            messagebox.showerror("Error", "Password is Incorrect.")
            self.password_entry.focus_set()
            return
        if status.lower() != "active":
            messagebox.showerror("Account Disabled", f"{name}'s Account is Disabled.")
            return
        # If all checks passed
        self.show_password_change_fields()
        self.new_password_entry.focus_set()
    def show_password_change_fields(self):
        self.new_frame.pack()
    def change_password(self):
        new_pass = self.new_password_var.get()
        confirm_pass = self.confirm_password_var.get()
        if not new_pass or not confirm_pass:
            messagebox.showerror("Error", "Please Enter and Confirm New Password.")
            return
        if new_pass != confirm_pass:
            messagebox.showerror("Missmatch", "New Password and Confirmation Don't Match.")
            return
        result = update_login_password(self.conn, self.stored_username, new_pass)
        if "successfully" in result.lower():
            messagebox.showinfo("Success", result)
            self.window.destroy()
        else:
            messagebox.showerror("Error", result)


class UserPrivilegesPopup(BaseWindow):
    def __init__(self, parent, conn):
        self.window = tk.Toplevel(parent)
        self.window.title("View User Privileges")
        self.center_window(self.window, 500, 400, parent)
        self.window.configure(bg="lightgreen")
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        # Fetch user list; usernames and user codes
        self.users_data = fetch_all_users(self.conn)
        if isinstance(self.users_data, str):
            messagebox.showerror("Error", self.users_data)
            self.window.destroy()
            return
        self.usernames = [user['username'] for user in self.users_data]
        self.usercodes = [user['user_code'] for user in self.users_data]
        self.top_frame = tk.Frame(self.window, bg="lightgreen")
        self.username_var = tk.StringVar()
        self.usercode_var = tk.StringVar()
        self.username_cb = ttk.Combobox(self.top_frame, textvariable=self.username_var, values=self.usernames,
                                        width=20)
        self.usercode_cb = ttk.Combobox(self.top_frame, textvariable=self.usercode_var, values=self.usercodes,
                                         width=10)
        self.search_btn = tk.Button(self.top_frame, text="Search", width=10, command=self.display_privileges)
        self.info_label = tk.Label(self.window, text="", font=("Arial", 12, "italic"), bg="lightgreen", fg="red")
        self.priv_listbox = tk.Listbox(self.window, width=60)

        self.build_ui()

    def build_ui(self):
        self.top_frame.pack(pady=(5, 0), padx=5, fill="x")
        tk.Label(self.top_frame, text="Select Username:", bg="lightgreen", font=("Arial", 11, "bold")
                 ).grid(row=0, column=0, sticky="w", padx=(5, 0))
        self.username_cb.grid(row=0, column=1, padx=(0, 3))
        self.username_cb.bind("<<ComboboxSelected>>", self.on_username_selected)
        tk.Label(self.top_frame, text="User Code:", bg="lightgreen", font=("Arial", 11, "bold")
                 ).grid(row=0, column=2, sticky="w", padx=(3, 0))
        self.usercode_cb.grid(row=0, column=3, padx=(0, 5))
        self.usercode_cb.bind("<<ComboboxSelected>>", self.on_usercode_selected)
        self.search_btn.grid(row=1, column=0, columnspan=4, padx=10, pady=5)
        self.info_label.pack(pady=10)
        self.priv_listbox.pack(pady=(0, 5), padx=5, fill="both", expand=True)

    def on_username_selected(self, event=None):
        username = self.username_var.get()
        result = fetch_user_identity(self.conn, username)
        if isinstance(result, dict):
            self.usercode_var.set(result['user_code'])

    def on_usercode_selected(self, event=None):
        user_code = self.usercode_var.get()
        result = fetch_user_identity(self.conn, user_code)
        if isinstance(result, dict):
            self.username_var.set(result['username'])

    def display_privileges(self):
        identifier = self.username_var.get() or self.usercode_var.get()
        user_info, privileges = fetch_user_details_and_privileges(self.conn, identifier)

        if not user_info:
            messagebox.showerror("Error", "No user found.")
        elif "error" in user_info:
            messagebox.showerror("Error", user_info["error"])
        else:
            self.info_label.config(
                text=f"Showing Privileges Assigned to {user_info['designation']}, {user_info['username']}."
            )
            self.priv_listbox.delete(0, tk.END)
            if privileges:
                for i, p in enumerate(privileges, start=1):
                    self.priv_listbox.insert(tk.END, f"{i} - {p['privilege']}")
            else:
                self.priv_listbox.insert(tk.END, "No Privileges Assigned.")

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
        self.left_frame = tk.Frame(self.window, bg="lightgreen")
        self.add_btn = tk.Button(
            self.left_frame, text="Add New Department", command=self.show_add_department
        )
        self.new_dept_label = tk.Label(self.left_frame,
                                       text="Enter New Department Name:", bg="lightgreen")
        self.new_dept_entry = tk.Entry(self.left_frame, width=25)
        self.create_btn = tk.Button(
            self.left_frame, text="Create New Department", command=self.create_department
        )
        self.close_frame_btn = tk.Button(
            self.left_frame, text="X", command=self.hide_frame, bg="red", fg="white",
            relief="flat", font=("Arial", 10, "bold")
        )
        self.right_frame = tk.Frame(self.window, bg="lightgreen")
        self.columns = ("No", "Name", "Code", "Employees")
        self.tree = ttk.Treeview(self.right_frame, columns=self.columns, show="headings")
        # Bold table headings
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        self.build_ui()

    def build_ui(self):
        # Left frame for add department section
        self.left_frame.pack(side="left", fill="y", padx=(10, 0), pady=10)
        tk.Label(self.left_frame, text="", bg="lightgreen").pack(pady=5)
        self.add_btn.pack(pady=(0, 10))
        # Right Frame for Table section
        self.right_frame.pack(side="right", fill="both", expand=True,
                              pady=(0, 10), padx=10)
        table_title = tk.Label(self.right_frame,
                               text="Current Available Departments", font=("Arial", 12, "bold"),
                               bg="lightgreen")
        table_title.pack(pady=(5, 0), anchor="center")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        # Vertical Scrollbar
        vsb = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.tree.yview)
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
        self.new_dept_entry.bind("<Return>", lambda e: self.create_btn.focus_set())
        self.create_btn.pack(pady=5)
        self.create_btn.bind("<Return>", lambda e: self.create_department())

    def create_department(self):
        name = self.new_dept_entry.get().strip()
        if not name:
            messagebox.showwarning("Input Error", "Department name cannot be empty.")
            return
        # Verify user privilege
        priv = "Add Department"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        result = insert_into_departments(self.conn, name)
        if "successfully" in result.lower():
            messagebox.showinfo("Department Created", result)
            self.new_dept_entry.delete(0, tk.END)
            self.refresh_table()
            self.hide_frame()
        else:
            messagebox.showerror("Error", result)

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
            self.tree.column(col, width=max_width + 5)

    def refresh_table(self):
        self.populate_table()

class EditEmployeeWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Employee")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 300, 400, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.current_record = None # Will hold the fetched row
        # Variables
        self.search_type_var = tk.StringVar(value="username")
        self.identifier_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.search_frame = tk.Frame(self.window, bg="lightgreen")
        self.search_type_cb = ttk.Combobox(
            self.search_frame,
            textvariable=self.search_type_var,
            values=["username", "user code"],
            state="readonly",
            width=15
        )
        self.identifier_entry = tk.Entry(self.search_frame, width=20,
                                         textvariable=self.identifier_var)
        self.search_btn = tk.Button(self.search_frame, text="Search", width=10,
                                    command=self.perform_search)
        self.prompt_label = tk.Label(
            self.search_frame, bg="lightgreen",
            text=f"Search {self.search_type_var.get()}:"
        )
        self.edit_frame = tk.Frame(self.window, bg="lightgreen", bd=1,
                                   relief="groove")
        # Header
        self.header_var = tk.StringVar(value="Editing User: _ With Code: _")
        self.header_label = tk.Label(
            self.edit_frame, bg="lightgreen", textvariable=self.header_var,
            font=("Arial", 10, "bold")
        )
        # Status handled separately
        self.status_cb = ttk.Combobox(
            self.edit_frame,
            textvariable=self.status_var,
            values=["active", "disabled"],
            state="disabled",
            width=20
        )
        self.post_btn = tk.Button(
            self.edit_frame, text="Post Update", bg="dodgerblue", fg="white",
            command=self.post_update, width=10, state="disabled"
        )

        # Entry widgets container
        self.entries = {}

        self.build_ui()

    def build_ui(self):
        # Search section
        self.search_frame.pack(fill="x", pady=10, padx=10)
        tk.Label(self.search_frame, text="Search by:",
                 bg="lightgreen").grid(row=0, column=0)
        self.search_type_cb.grid(row=0, column=1, padx=(0, 5))
        self.search_type_cb.bind("<<ComboboxSelected>>", self.update_prompt)
        self.prompt_label.grid(row=1, column=0, pady=5)
        self.identifier_entry.grid(row=1, column=1, pady=5)
        self.identifier_entry.focus_set()
        self.identifier_entry.bind("<Return>", lambda e: self.search_btn.focus_set())
        self.search_btn.grid(row=2, column=0, columnspan=2, pady=(5, 0))
        self.search_btn.bind("<Return>", lambda e: self.perform_search())
        self.edit_frame.pack(fill="both", expand=False, pady=(0, 5), padx=5)
        self.header_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
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
                self.entries[key] = tk.Entry(self.edit_frame, width=30)
        # Layout fields (labels left, inputs right)
        row = 1
        for label_text, key in labels_and_keys:
            tk.Label(self.edit_frame, text=label_text, bg="lightgreen"
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
            messagebox.showwarning("Input Required",
                                   f"Please enter {kind} to search.")
            return
        success, result = fetch_employee_login_info(self.conn, identifier)
        if not success:
            messagebox.showerror("Not Found", result)
            return
        self.current_record = result
        # Populate and enable fields
        ordered_keys = ["name", "username", "designation", "national_id", "phone", "email", "salary"]
        for i, key in enumerate(ordered_keys):
            entry = self.entries.get(key)
            if entry:
                entry.configure(state="normal")
                entry.delete(0, tk.END)
                entry.insert(0, result.get(key, ""))
                # Bind Enter Navigation
                if i < len(ordered_keys) - 1:
                    next_entry = self.entries[ordered_keys[i + 1]]
                    entry.bind("<Return>", lambda e, next_e=next_entry: next_e.focus_set())
                # Bind focus-in to select all text
                entry.bind("<FocusIn>", self.select_all_text)
        # Capitalize Name on focus out
        self.entries["name"].bind("<KeyRelease>", capitalize_customer_name)
        digit_vcmd = (self.window.register(only_digits), "%S")
        self.entries["phone"].configure(validate="key", validatecommand=digit_vcmd)
        self.entries["national_id"].configure(validate="key", validatecommand=digit_vcmd)

        self.status_cb.configure(state="readonly")
        self.status_var.set(result.get("status", "active"))
        # Header text
        uname = result.get("username", "")
        ucode = result.get("user_code", "")
        self.header_var.set(f"Editing User: {uname} With Code: {ucode}")
        # Enable post button
        self.post_btn.configure(state="normal")

    def post_update(self):
        if not self.current_record:
            messagebox.showwarning("No Record",
                                   "You need to search and load info first.")
            return
        email = self.entries["email"].get().strip()
        if not is_valid_email(email):
            messagebox.showerror("Error", "Invalid email format.")
            self.entries["email"].focus_set()
            return
        info = {
            "user_code": self.current_record.get("user_code"),
            "name": self.entries["name"].get().strip(),
            "username": self.entries["username"].get().strip(),
            "designation": self.entries["designation"].get().strip(),
            "national_id": self.entries["national_id"].get().strip(),
            "phone": self.entries["phone"].get().strip(),
            "email": self.entries["email"].get().strip(),
            "salary": self.entries["salary"].get().strip(),
            "status": self.status_var.get()
        }
        success, msg = update_employee_info(self.conn, info)
        if success:
            messagebox.showinfo("Updated", msg)
            for entry in self.entries.values():
                entry.delete(0, tk.END)
                entry.configure(state="disabled")
            self.identifier_entry.delete(0, tk.END)
            self.status_cb.set("")
            self.status_cb.configure(state="disabled")
            self.post_btn.configure(state="disabled")
        else:
            messagebox.showerror("Error", msg)
