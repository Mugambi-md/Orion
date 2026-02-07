import re
import textwrap
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from working_on_employee import fetch_password, get_assigned_privileges
from windows_utils import PasswordSecurity

class VerifyPrivilegePopup(simpledialog.Dialog):
    def __init__(self, master, conn, username, required_privilege):
        self.conn = conn
        self.username = username
        self.req_privilege = required_privilege # Required Privilege
        self.master = master
        self.result = None  # Will be 'granted' or 'denied'
        self.username_entry = None
        self.password_entry = None

        super().__init__(master, title="User Verification")

    def body(self, master):
        master.configure(bg="lightgreen")
        tk.Label(
            master, text="Username:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, sticky="w", padx=(5, 0), pady=5)
        self.username_entry = tk.Entry(
            master, bd=4, relief="raised", font=("Arial", 11, "bold")
        )
        self.username_entry.insert(0, self.username)
        self.username_entry.config(state="readonly")
        self.username_entry.grid(row=0, column=1, padx=(0, 5), pady=5)
        tk.Label(
            master, text="Password:", bg="lightgreen",
            font=("Arial", 11, "bold")
        ).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.password_entry = tk.Entry(
            master, show="*", bd=4, relief="raised", font=("Arial", 11))
        self.password_entry.grid(row=1, column=1, padx=(0, 5), pady=5)
        self.password_entry.bind("<Return>", self.check_credentials)
        self.password_entry.focus_set()

        return self.password_entry  # initial focus

    def check_credentials(self, event=None):
        entered_password = self.password_entry.get()
        success, result = fetch_password(self.conn, self.username)
        if not success:
            messagebox.showerror("Error", result, parent=self.master)
            self.result = "denied"
            return
        password = result["password"]
        if not password:
            messagebox.showerror(
                "Access Denied",
                "User Authentication Failed", parent=self.master
            )
            self.result = "denied"
            self.cancel()
            return
        if not PasswordSecurity.verify_password(entered_password, password):
            messagebox.showerror(
                "Access Denied",
                "Invalid Username or Password.", parent=self.master
            )
            self.result = "denied"
            self.cancel()
            return

        status, privileges, role, error = get_assigned_privileges(
            self.conn, self.username
        )
        granted_roles = ["administrator", "manager", "supervisor", "admin"]
        if error:
            messagebox.showerror(
                "Error",
                f"Failed to retrieve privileges:\n{error}.", parent=self.master
            )
            self.result = "denied"
            self.cancel()
            return
        if not status or status.lower() != "active":
            messagebox.showerror(
                "Access Denied", "User Not Found.", parent=self.master
            )
            self.result = "denied"
        elif role and role.lower() in granted_roles:
            self.result = "granted"
        elif self.req_privilege.lower() in [p.lower() for p in privileges]:
            self.result = "granted"
        else:
            self.result = "denied"

        self.cancel()  # Close the popup

    def apply(self):
        # When Ok button is clicked
        self.check_credentials()

    def cancel(self, event = None):
        if self.result is None:
            self.result = "denied"
        super().cancel(event)


class DescriptionFormatter:
    DEFAULT_MAX_LEN = 35
    DEFAULT_MIN_SECOND = 5
    def __init__(self, max_len=None, min_second=None):
        """
        Args: max_len (int): Maximum length of the first line before wrapping.
            min_second (int): Minimum length required for second line."""
        self.max_len = max_len or self.DEFAULT_MAX_LEN
        self.min_sec = min_second or self.DEFAULT_MIN_SECOND

    def _normalize(self, text: str) -> str:
        """Normalize whitespace."""
        return re.sub(r"\s+", " ", text).strip()

    def format(self, text: str):
        """Truncate long lines into maximum length."""
        if not text:
            return ""
        text = self._normalize(text)
        if len(text) <= self.max_len:
            return text
        # Split at nearest space before/after max_len
        break_at = text.rfind(" ", 0, self.max_len)
        if break_at == -1:
            break_at = text.find(" ", self.max_len)
        if break_at == -1:
            break_at = self.max_len  # Fallback
        first_part = text[:break_at].rstrip()
        second_part = text[break_at:].lstrip()
        if len(second_part) > self.min_sec:
            return first_part + "..."
        else:
            return text

    def wrap(self, text: str) -> str:
        """Wrap text into two lines instead of truncating."""
        if not text:
            return ""

        text = self._normalize(text)

        wrapped_lines = textwrap.wrap(
            text,
            width=self.max_len,
            break_long_words=False,
            break_on_hyphens=False
        )
        # Enforce minimum second-line length rule
        if len(wrapped_lines) > 1 and len(wrapped_lines[1]) < self.min_sec:
            return text

        return "\n".join(wrapped_lines)