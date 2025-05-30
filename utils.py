import tkinter as tk

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