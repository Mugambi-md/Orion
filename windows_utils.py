
import tkinter as tk
import re
from datetime import date
import bcrypt

def to_uppercase(entry_widget):
    """Convert the value of an entry widget to uppercase."""
    value = entry_widget.get()
    entry_widget.delete(0, "end")
    entry_widget.insert(0, value.upper())

def only_digits(char):
    """Allow only characters."""
    return char.isdigit() or char == '.'

def capitalize_customer_name(event):
        widget = event.widget
        name = widget.get()
        cursor_position = widget.index(tk.INSERT)
        capitalized = ' '.join(word.capitalize() for word in name.split(' '))
        if name != capitalized:
            widget.delete(0, tk.END)
            widget.insert(0, capitalized)
            widget.icursor(cursor_position)

def is_valid_email(email):
    """Simple email format validation."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,4}$'
    return re.match(pattern, email) is not None

def auto_format_date(event):
    """Automatically formats the date as YYYY-MM-DD while typing."""
    entry = event.widget
    text = entry.get()
    digits = ''.join(filter(str.isdigit, text))
    if len(digits) >= 7:
        new_text = f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"
    elif len(digits) >= 5:
        new_text = f"{digits[:4]}-{digits[4:]}"
    elif len(digits) >= 1:
        new_text = digits
    else:
        new_text = ""
    
    entry.delete(0, "end")
    entry.insert(0, new_text[:10])

class DateFormatter:
    @classmethod
    def _get_ordinal_suffix(cls, day: int) -> str:
        """Private method to get ordinal suffix for a day."""
        if 10 <= day % 100 <= 20:
            return 'th'
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    @classmethod
    def get_today_formatted(cls) -> str:
        """Returns today's date in format: 'Weekday DayOrdinal Month Year'"""
        today = date.today()
        day = today.day
        suffix = cls._get_ordinal_suffix(day)
        return today.strftime(f"%A {day}{suffix} %B %Y")

class CurrencyFormatter:
    """Helper class to auto-format Tkinter Entry Field as currency."""

    @staticmethod
    def add_currency_trace(var, entry):
        """Attach a trace to format the Entry value as currency."""
        def callback(var_name, index, mode):
            CurrencyFormatter.format_currency(var, entry)
        var.trace_add("write", callback)

    @staticmethod
    def format_currency(var, entry):
        """Automatically format entry text as money."""
        # Temporarily remove trace to prevent recursion
        traces = var.trace_info()
        if traces:
            for trace in traces:
                mode, cbname = trace[:2]
                var.trace_remove(mode, cbname)
        value = var.get().replace(",", "").strip()
        cleaned = ''.join(ch for ch in value if ch.isdigit())

        if not cleaned:
            CurrencyFormatter.add_currency_trace(var, entry)
            return
        formatted = f"{int(cleaned):,}"
        var.set(formatted)
        # Set cursor at end of text
        entry.after_idle(lambda: entry.icursor(tk.END))
        # Reattach trace
        CurrencyFormatter.add_currency_trace(var, entry)


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg, width=None):
        super().__init__(parent, bg=bg)

        self.canvas = tk.Canvas(
            self, bg=bg, highlightthickness=0, width=width)
        self.scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.window_id = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.window_id, width=e.width)
        )
        # Scroll config
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        # Layout
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mousewheel binding only when mouse is over canvas or inner frame
        for widget in (self.canvas, self.scrollable_frame):
            widget.bind("<Enter>", self._bind_mousewheel)
            widget.bind("<Enter>", self._unbind_mousewheel)

    def _bind_mousewheel(self, event):
        # Windows/ macOS
        self.canvas.bind("<Mousewheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_linux_scroll_up)
        self.canvas.bind("<Button-5>", self._on_linux_scroll_down)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind("<MouseWheel>")
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _on_linux_scroll_up(self, event):
        self.canvas.yview_scroll(-1, "units")

    def _on_linux_scroll_down(self, event):
        self.canvas.yview_scroll(1, "units")


class SentenceCapitalizer:
    """
    Auto-capitalizes the first letter of every sentence in a Text widget
    while the user is typing.
    """

    @staticmethod
    def bind(widget: tk.Text):
        def auto_capitalize(event=None):
            try:
                text = widget.get("1.0", tk.END)  # get all text
                cursor = widget.index(tk.INSERT)

                result = ""
                new_sentence = True

                for char in text:
                    if new_sentence and char.isalpha():
                        result += char.upper()
                        new_sentence = False
                    else:
                        result += char

                    if char in ".!?":
                        new_sentence = True

                if text != result:
                    widget.delete("1.0", tk.END)
                    widget.insert("1.0", result)
                    widget.mark_set(tk.INSERT, cursor)  # restore cursor
            except Exception:
                pass

        widget.bind("<KeyRelease>", auto_capitalize)

class PasswordSecurity:
    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Hash a plain password using bcrypt."""
        return bcrypt.hashpw(
            plain_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against stored hash."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )