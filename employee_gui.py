import tkinter as tk
from tkinter import ttk, messagebox
from base_window import BaseWindow
import tkinter.font as tkFont
from accounting_export import ReportExporter
from authentication import VerifyPrivilegePopup
from working_on_employee import fetch_all_employee_details
from employee_gui_popup import (EmployeePopup, LoginStatusPopup, PrivilegePopup, AssignPrivilegePopup,
                                UserPrivilegesPopup, DepartmentsPopup, RemovePrivilegePopup, ResetPasswordPopup,
                                EditEmployeeWindow)


class EmployeeManagementWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.window = tk.Toplevel(parent)
        self.window.title("Employee Management")
        self.window.configure(bg="lightgreen")
        self.center_window(self.window, 1300, 600, parent)
        self.window.transient(parent)
        self.window.grab_set()

        self.conn = conn
        self.user = user
        self.columns = ["No", "Name", "User Code", "Username", "Department", "Designation", "National ID", "Phone",
            "Email", "Salary", "Status"]
        self.right_frame = tk.Frame(self.window, bg="lightgreen")
        self.top_frame = tk.Frame(self.right_frame, bg="lightgreen")
        self.btn_frame = tk.Frame(self.top_frame, bg="lightgreen")
        self.search_fields = ["Name", "User Code", "Username", "Department", "Designation"]
        self.search_option = tk.StringVar(value=self.search_fields[0])
        self.search_label = tk.Label(self.btn_frame, text=f"Enter {self.search_fields[0]} to Search:",
                                     font=("Arial", 10, "bold"), bg="lightgreen")
        self.search_entry = tk.Entry(self.btn_frame, width=20)
        self.table_frame = tk.Frame(self.right_frame, bg="lightgreen")
        self.scrollbar = tk.Scrollbar(self.table_frame, orient="vertical")
        self.h_scroll = tk.Scrollbar(self.table_frame, orient="horizontal")
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        self.tree = ttk.Treeview(self.table_frame, columns=self.columns, show="headings",
                                 yscrollcommand=self.scrollbar.set, xscrollcommand=self.h_scroll.set)
        self.all_data = []

        self.setup_widgets()
        self.load_data()

    def setup_widgets(self):
        # Left Frame With action buttons
        left_frame = tk.Frame(self.window, bg="lightgreen", width=100)
        left_frame.pack(side="left", fill="y", pady=5, padx=(5, 0))
        tk.Label(left_frame, text="", bg="lightgreen").pack(padx=5, pady=5)
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
                left_frame, text=text, width=17, command=command, bd=4,
                relief="solid", height=2
            ).pack(padx=(5, 0))
        # Right Frame
        self.right_frame.pack(side="right", expand=True, fill="both", padx=(0, 5), pady=5)
        self.top_frame.pack(fill="x") # Top Title Frame
        tk.Label(
            self.top_frame, text="Current Employees Information", bg="lightgreen",
            font=("Arial", 15, "bold")
        ).pack(side="left", padx=5)
        # Top Button Frame
        self.btn_frame.pack(side="right", padx=5)
        tk.Label(
            self.btn_frame, text="Search by:", font=("Arial", 10, "bold"),
            bg="lightgreen"
        ).pack(side="left", padx=(5, 0))
        search_combo = ttk.Combobox(self.btn_frame, textvariable=self.search_option, state="readonly", width=15,
                                    values=self.search_fields)
        search_combo.pack(side="left", padx=(0, 5))
        search_combo.bind("<<ComboboxSelected>>", lambda e: self.update_search_label())
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
                self.btn_frame, text=text, command=command, bd=2,
                relief="ridge"
            ).pack(side="left")
        self.table_frame.pack(fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.pack(fill="both", expand=True)
        self.h_scroll.pack(side="bottom", fill="x")
        self.scrollbar.config(command=self.tree.yview)
        self.h_scroll.config(command=self.tree.xview)
        # Enable mousewheel scroll
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(-1 * int(e.delta / 120), "units"))
        self.tree.bind("<Button-4>", lambda e: self.tree.yview_scroll(-1, "units"))
        self.tree.bind("<Button-5>", lambda e: self.tree.yview_scroll(1, "units"))

    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        data, error = fetch_all_employee_details(self.conn)
        if error:
            messagebox.showerror("Error", error)
            return
        for i, row in enumerate(data, start=1):
            values=(
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
            )
            self.tree.insert("", "end", values=values)
            self.all_data.append(values)
        self.autosize_columns()
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
        self.search_label.config(text=f"Enter {selected} to Search:")
        self.filter_table()
    def filter_table(self, event=None):
        keyword = self.search_entry.get().strip().lower()
        field_map = {
            "Name": 1,
            "User Code": 2,
            "Username": 3,
            "Department": 4,
            "Designation": 5
        }
        col_index = field_map.get(self.search_option.get(), 1)
        self.tree.delete(*self.tree.get_children())
        if not keyword:
            self.load_data()
            return
        filtered = [row for row in self.all_data if keyword in str(row[col_index]).lower()]
        for row in filtered:
            self.tree.insert("", "end", values=row)
    # Placeholder for functionality
    def create_priv(self):
        # Verify user privilege
        priv = "Create Privilege"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        PrivilegePopup(self.window, self.conn, self.user)

    def add_employee(self):
        # Verify user privilege
        priv = "Add User"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        EmployeePopup(self.window, self.conn, self.user)

    def give_priv(self):
        # Verify user privilege
        priv = "Assign Privilege"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        AssignPrivilegePopup(self.window, self.conn, self.user)

    def view_user_priv(self):
        # Verify user privilege
        priv = "View User Privilege"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        UserPrivilegesPopup(self.window, self.conn)

    def deactivate_employee(self):
        # Verify user privilege
        priv = "Deactivate User"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        LoginStatusPopup(self.window, self.conn, self.user)

    def activate_employee(self):
        # Verify user privilege
        priv = "Activate User"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        LoginStatusPopup(self.window, self.conn, self.user)

    def departments(self):
        # Verify user privilege
        priv = "Add Department"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        DepartmentsPopup(self.window, self.conn, self.user)

    def remove_privilege(self):
        priv = "Remove Privilege"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        RemovePrivilegePopup(self.window, self.conn, self.user)

    def reset_pass(self):
        priv = "Reset Password"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
            return
        ResetPasswordPopup(self.window, self.conn, self.user)
    def edit_employee(self):
        priv = "Edit Employee"
        verify_dialog = VerifyPrivilegePopup(self.window, self.conn, self.user, priv)
        if verify_dialog.result != "granted":
            messagebox.showwarning("Access Denied", f"You do not have permission to {priv}.")
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
                "National ID": vals[6],
                "Phone": vals[7],
                "Email": vals[8],
                "Salary": vals[9],
                "Status": vals[10]
            })
        return rows

    def _make_exporter(self):
        title = "Employee Data"
        columns = ["No", "Name", "User Code", "Username", "Department", "Designation", "National ID", "Phone",
            "Email", "Salary", "Status"]
        rows = self._collect_rows()
        return ReportExporter(self.window, title, columns, rows)

    def export_excel(self):
        exporter = self._make_exporter()
        exporter.export_excel()
    def export_pdf(self):
        exporter = self._make_exporter()
        exporter.export_pdf()
    def print_data(self):
        exporter = self._make_exporter()
        exporter.print()


if __name__ == "__main__":
    from connect_to_db import connect_db
    conn = connect_db()
    root = tk.Tk()
    EmployeeManagementWindow(root, conn, "sniffy")
    root.mainloop()