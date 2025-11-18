import tkinter as tk
from tkinter import ttk, messagebox
from base_window import BaseWindow
import tkinter.font as tkFont
from accounting_export import ReportExporter
from authentication import VerifyPrivilegePopup
from working_on_employee import fetch_all_employee_details
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
        self.center_window(self.window, 1300, 700, parent)
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
            "No", "Name", "User Code", "Username", "Department",
            "Designation", "ID No", "Phone", "Email", "Salary", "Status"
        ]
        style = ttk.Style()
        style.theme_use("alt")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 11))
        self.main_frame = tk.Frame(
            self.window, bg="lightgreen", bd=4, relief="solid"
        )
        self.right_frame = tk.Frame(self.main_frame, bg="lightgreen")
        self.top_frame = tk.Frame(self.right_frame, bg="lightgreen")
        self.btn_frame = tk.Frame(self.top_frame, bg="lightgreen")
        self.search_fields = [
            "Name", "User Code", "Username", "Department", "Designation"
        ]
        self.search_option = tk.StringVar(value=self.search_fields[0])
        self.search_label = tk.Label(
            self.btn_frame, text=f"Search {self.search_fields[0]}:",
            font=("Arial", 11, "bold"), bg="lightgreen"
        )
        self.search_entry = tk.Entry(
            self.btn_frame, bd=4, relief="raised", font=("Arial", 11),
            width=20
        )
        self.table_frame = tk.Frame(self.right_frame, bg="lightgreen")
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self.setup_widgets()
        self.load_data()

    def setup_widgets(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Left Frame With action buttons
        top_frame = tk.Frame(self.main_frame, bg="lightgreen")
        top_frame.pack(side="top", fill="x", padx=5, pady=5)
        actions = [
            ("Departments", self.departments),
            ("Create Privilege", self.create_priv),
            ("Add New Employee", self.add_employee),
            ("Assigned Privilege", self.view_user_priv),
            ("Assign Privilege", self.give_priv),
            ("Remove Privilege", self.remove_privilege),
            ("Deactivate Employee", self.deactivate_employee),
            ("Activate Employee", self.activate_employee),
            ("Edit Employee Info", self.edit_employee),
            ("Reset User Password", self.reset_pass)
        ]
        for text, command in actions:
            tk.Button(
                top_frame, text=text, command=command, bd=4, relief="groove",
                bg="blue", fg="white", font=("Arial", 9, "bold")
            ).pack(side="left")
        # Right Frame
        self.right_frame.pack(side="left", expand=True, fill="both")
        self.top_frame.pack(fill="x") # Top Title Frame
        tk.Label(
            self.top_frame, text="Current Employees Information", bd=2,
            relief="ridge", font=("Arial", 16, "bold", "underline"),
            bg="lightgreen", fg="blue"
        ).pack(side="left", padx=20, ipadx=10)
        # Top Button Frame
        self.btn_frame.pack(side="right", padx=5)
        tk.Label(
            self.btn_frame, text="Search by:", font=("Arial", 11, "bold"),
            bg="lightgreen"
        ).pack(side="left", padx=(5, 0))
        search_combo = ttk.Combobox(
            self.btn_frame, textvariable=self.search_option, width=10,
            state="readonly", values=self.search_fields, font=("Arial", 11)
        )
        search_combo.pack(side="left", padx=(0, 5))
        search_combo.bind(
            "<<ComboboxSelected>>", lambda e: self.update_search_label()
        )
        self.search_label.pack(side="left", padx=(5, 0))
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.filter_table)
        btn_action =[
            ("Export Excel", self.export_excel),
            ("Export PDF", self.export_pdf),
            ("Print Data", self.print_data)
        ]
        for text, command in btn_action:
            tk.Button(
                self.btn_frame, text=text, command=command, bg="lightblue",
                bd=2, relief="groove", font=("Arial", 10)
            ).pack(side="left")
        self.table_frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        # Enable mousewheel scroll
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(
            -1 * int(e.delta / 120), "units"
        ))
        self.tree.bind(
            "<Button-4>", lambda e: self.tree.yview_scroll(-1, "units")
        )
        self.tree.bind(
            "<Button-5>", lambda e: self.tree.yview_scroll(1, "units")
        )
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
                f"{row['salary']:,.2f}",
                row["status"]
            ), tags=(tag,))
        self.autosize_columns()

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
        elif selected_field == "Department":
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

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                max_width = max(max_width, font.measure(text))
            self.tree.column(col, width=max_width + 5)

    def update_search_label(self):
        selected = self.search_option.get()
        self.search_label.config(text=f"Search {selected}:")
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
        if not self.has_privilege("Create Privilege"):
            return
        PrivilegePopup(self.window, self.conn, self.user)

    def add_employee(self):
        # Verify user privilege
        if not self.has_privilege("Add User"):
            return
        EmployeePopup(self.window, self.conn, self.user)

    def give_priv(self):
        # Verify user privilege
        if not self.has_privilege("Assign Privilege"):
            return
        AssignPrivilegePopup(self.window, self.conn, self.user)

    def view_user_priv(self):
        # Verify user privilege
        if not self.has_privilege("View User Privilege"):
            return

        UserPrivilegesPopup(self.window, self.conn, self.user)

    def deactivate_employee(self):
        # Verify user privilege
        if not self.has_privilege("Deactivate User"):
            return
        LoginStatusPopup(self.window, self.conn, self.user)

    def activate_employee(self):
        # Verify user privilege
        if not self.has_privilege("Activate User"):
            return
        LoginStatusPopup(self.window, self.conn, self.user)

    def departments(self):
        # Verify user privilege
        if not self.has_privilege("Add Department"):
            return
        DepartmentsPopup(self.window, self.conn, self.user)

    def remove_privilege(self):
        if not self.has_privilege("Remove Privilege"):
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
                "Department": vals[4],
                "Designation": vals[5],
                "ID No": vals[6],
                "Phone": vals[7],
                "Email": vals[8],
                "Salary": vals[9],
                "Status": vals[10]
            })
        return rows

    def _make_exporter(self):
        title = "Employee Data"
        columns = [
            "No", "Name", "User Code", "Username", "Department",
            "Designation", "ID No", "Phone", "Email", "Salary", "Status"
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
    conn = connect_db()
    root = tk.Tk()
    EmployeeManagementWindow(root, conn, "sniffy")
    root.mainloop()