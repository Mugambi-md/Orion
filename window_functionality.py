import tkinter as tk
def auto_manage_focus(parent):
    """Automatically sets focus to the first Entry in a parent widget. Shift focus to the next Entry on Enter.
    Invokes the first Button on Enter at the last Entry."""
    entries = [child for child in parent.winfo_children() if isinstance(child, tk.Entry)] # Collect Entry in creation order
    buttons = [child for child in parent.winfo_children() if isinstance(child, tk.Button)]
    if not entries:
        return
    parent.after(100, entries[0].focus_set) # Set focus to the first entry when window opens
    for i in range(len(entries)): # Function to bind Enter to focus next or press button
        if i < len(entries) - 1:
            entries[i].bind("<Return>", lambda e, next_entry=entries[i + 1]: next_entry.focus_set())
        else:
            if buttons:
                entries[i].bind("<Return>", lambda e, btn=buttons[0]: btn.invoke())

def to_uppercase(entry_widget):
    """Convert the value of an entry widget to uppercase."""
    value = entry_widget.get()
    entry_widget.delete(0, "end")
    entry_widget.insert(0, value.upper())

def only_digits(char):
    """Allow only characters."""
    return char.isdigit() or char == '.'

