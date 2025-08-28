import tkinter as tk
import re
from datetime import date

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

