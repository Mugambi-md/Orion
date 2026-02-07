import tkinter as tk
from tkinter import ttk, messagebox
from base_window import BaseWindow
from accounting_export import ReportExporter
from authentication import VerifyPrivilegePopup
from working_on_employee import fetch_all_employee_details
from table_utils import TreeviewSorter
from employee_gui_popup import (
    EmployeePopup, LoginStatusPopup, PrivilegePopup, AssignPrivilegePopup,
    UserPrivilegesPopup, DepartmentsPopup, RemovePrivilegePopup,
    ResetPasswordPopup, EditEmployeeWindow
)


class EmployeeManagementWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Employee Management")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 1350, 700, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        data, error = fetch_all_employee_details(self.conn)
        if error:
            messagebox.showerror("Error", error, parent=self.window)
            return
        else:
            self.all_data = data
        self.columns = [
            "No", "Name", "User Code", "Username", "Section", "Role",
            "ID No", "Phone", "Email", "Status"
        ]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.right_frame = tk.Frame(
            self.main_frame, bg="lightgreen", bd=4, relief="ridge"
        )
        self.top_frame = tk.Frame(self.right_frame, bg="lightgreen")
        self.btn_frame = tk.Frame(self.top_frame, bg="lightgreen")
        self.search_fields = [
            "Name", "User Code", "Username", "Section", "Role"
        ]
        self.search_option = tk.StringVar(value=self.search_fields[0])
        self.search_label = tk.Label(
            self.btn_frame, text=f"{self.search_fields[0]}:",
            bg="lightgreen", font=("Arial", 12, "bold")
        )
        self.search_entry = tk.Entry(
            self.btn_frame, bd=4, relief="raised", font=("Arial", 12),
            width=20
        )
        self.table_frame = tk.Frame(self.right_frame, bg="lightgreen")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )
        self.sorter = TreeviewSorter(self.tree, self.columns, "No")
        self.sorter.apply_style(style)
        self.sorter.attach_sorting()
        self.sorter.bind_mousewheel()

        self.setup_widgets()
        self.load_data()

    def setup_widgets(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Left Frame With action buttons
        top_frame = tk.Frame(self.main_frame, bg="lightgreen")
        top_frame.pack(side="top", fill="x")
        actions = [
            ("Departments", self.departments),
            ("New Access", self.create_priv),
            ("New User", self.add_employee),
            ("User Access", self.view_user_priv),
            ("Give Access", self.give_priv),
            ("Deny Access", self.remove_privilege),
            ("Disable User", self.deactivate_employee),
            ("Edit User", self.edit_employee),
            ("Reset\nPassword", self.reset_pass)
        ]
        for text, command in actions:
            tk.Button(
                top_frame, text=text, command=command, bd=4, relief="groove",
                height=2, bg="blue", fg="white", font=("Arial", 11, "bold"),
            ).pack(side="left")
        # Right Frame
        self.right_frame.pack(side="left", fill="both", expand=True)
        self.top_frame.pack(fill="x") # Top Title Frame
        tk.Label(
            self.top_frame, text="Current Employees Information", fg="blue",
            bg="lightgreen", font=("Arial", 20, "bold", "underline")
        ).pack(side="left")
        # Top Button Frame
        self.btn_frame.pack(side="right", padx=5, anchor="s")
        tk.Label(
            self.btn_frame, text="Search:", font=("Arial", 12, "bold"),
            bg="lightgreen"
        ).pack(side="left", padx=(3, 0), anchor="s")
        search_combo = ttk.Combobox(
            self.btn_frame, textvariable=self.search_option, width=10,
            state="readonly", values=self.search_fields, font=("Arial", 12)
        )
        search_combo.pack(side="left", padx=(0, 5), anchor="s")
        search_combo.bind(
            "<<ComboboxSelected>>", lambda e: self.update_search_label()
        )
        self.search_label.pack(side="left", padx=(5, 0), anchor="s")
        self.search_entry.pack(side="left", padx=(0, 5), anchor="s")
        self.search_entry.bind("<KeyRelease>", self.filter_table)
        tk.Button(
            self.btn_frame, text="Refresh", bg="dodgerblue", fg="white",
            bd=4, relief="ridge", font=("Arial", 10, "bold"),
            command=self.refresh
        ).pack(side="left", padx=5, anchor="s")
        btn_action =[
            ("Export Excel", self.export_excel),
            ("Export PDF", self.export_pdf),
            ("Print Data", self.print_data)
        ]
        for text, command in btn_action:
            tk.Button(
                self.btn_frame, text=text, command=command, bg="lightblue",
                bd=4, relief="groove", font=("Arial", 11, "bold")
            ).pack(side="left", anchor="s")
        self.table_frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=30)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")

    def load_data(self, data=None):
        for row in self.tree.get_children():
            self.tree.delete(row)

        if data is None:
            current_data = self.all_data
        else:
            current_data = data
        for i, row in enumerate(current_data, start=1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                row["name"],
                row["user_code"],
                row["username"],
                row["department"],
                row["designation"],
                row["national_id"],
                row["phone"],
                row["email"],
                row["status"]
            ), tags=(tag,))
        self.sorter.autosize_columns()

    def filter_table(self, event=None):
        keyword = self.search_entry.get().strip().lower()
        selected_field = self.search_option.get()
        if not keyword:
            self.load_data()
            return
        if selected_field == "Name":
            data = [
                row for row in self.all_data
                if str(row["name"]).lower().startswith(keyword)
            ]
        elif selected_field == "User Code":
            data = [
                row for row in self.all_data
                if str(row["user_code"]).lower().startswith(keyword)
            ]
        elif selected_field == "Username":
            data = [
                row for row in self.all_data
                if str(row["username"]).lower().startswith(keyword)
            ]
        elif selected_field == "Section":
            data = [
                row for row in self.all_data
                if str(row["department"]).lower().startswith(keyword)
            ]
        else:
            data = [
                row for row in self.all_data
                if str(row["designation"]).lower().startswith(keyword)
            ]
        self.load_data(data)

    def refresh(self):
        """Refreshes Table."""
        data, error = fetch_all_employee_details(self.conn)
        if error:
            messagebox.showerror("Error", error, parent=self.window)
            return
        self.load_data(data)

    def update_search_label(self):
        selected = self.search_option.get()
        self.search_label.config(text=f"{selected}:")
        self.search_entry.focus_set()
        self.filter_table()

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

    def create_priv(self):
        # Verify user privilege
        if not self.has_privilege("Admin Create Privilege"):
            return
        PrivilegePopup(self.window, self.conn, self.user)

    def add_employee(self):
        # Verify user privilege
        if not self.has_privilege("Admin Add User"):
            return
        EmployeePopup(self.window, self.conn, self.user)

    def give_priv(self):
        # Verify user privilege
        if not self.has_privilege("Admin Assign Privilege"):
            return
        AssignPrivilegePopup(self.window, self.conn, self.user)

    def view_user_priv(self):
        # Verify user privilege
        if not self.has_privilege("View User Privilege"):
            return
        UserPrivilegesPopup(self.window, self.conn, self.user)

    def deactivate_employee(self):
        # Verify user privilege
        privilege = "Admin Deactivate User" or "Admin Activate User"
        if not self.has_privilege(privilege):
            return
        LoginStatusPopup(self.window, self.conn, self.user)

    def departments(self):
        # Verify user privilege
        if not self.has_privilege("Admin Add Department"):
            return
        DepartmentsPopup(self.window, self.conn, self.user)

    def remove_privilege(self):
        if not self.has_privilege("Admin Remove Privilege"):
            return
        RemovePrivilegePopup(self.window, self.conn, self.user)

    def reset_pass(self):
        if not self.has_privilege("Reset Password"):
            return
        ResetPasswordPopup(self.window, self.conn, self.user)

    def edit_employee(self):
        if not self.has_privilege("Edit Employee"):
            return
        EditEmployeeWindow(self.window, self.conn, self.user)

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0],
                "Name": vals[1],
                "User Code": vals[2],
                "Username": vals[3],
                "Section": vals[4],
                "Role": vals[5],
                "ID No": vals[6],
                "Phone": vals[7],
                "Email": vals[8],
                "Status": vals[9]
            })
        return rows

    def _make_exporter(self):
        title = "Employee Data"
        columns = [
            "No", "Name", "User Code", "Username", "Section", "Role",
            "ID No", "Phone", "Email", "Status"
        ]
        rows = self._collect_rows()
        return ReportExporter(self.window, title, columns, rows)

    def export_excel(self):
        if not self.has_privilege("Employee Data"):
            return
        exporter = self._make_exporter()
        exporter.export_excel()

    def export_pdf(self):
        if not self.has_privilege("Employee Data"):
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def print_data(self):
        if not self.has_privilege("Employee Data"):
            return
        exporter = self._make_exporter()
        exporter.print()

if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root=tk.Tk()
    EmployeeManagementWindow(root, conn, "Sniffy")
    root.mainloop()