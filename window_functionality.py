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


class TextCapitalizer:
    """
    Utility class that provides reusable auto-capitalization behaviors
    for Tkinter Entry and Text widgets.
    """

    @staticmethod
    def sentence_capitalize_text(widget):
        """
        Capitalizes the first letter of a sentence in a Text widget.
        """
        def auto_capitalize(event=None):
            try:
                text = widget.get("1.0", "end-1c")

                if len(text) >= 2:
                    # If the last character is a letter and second last is punctuation
                    if len(text) >= 3 and text[-2] in ".!?":
                        last = text[-1]
                        if last.isalpha() and last.islower():
                            widget.delete("end-2c")
                            widget.insert("end-1c", last.upper())
            except Exception:
                pass

        widget.bind("<KeyRelease>", auto_capitalize)

    @staticmethod
    def word_capitalize_entry(widget):
        """
        Auto-capitalize every word inside an Entry widget.
        Example: 'bank cash account' → 'Bank Cash Account'
        """

        def auto_capitalize(event=None):
            text = widget.get()
            if not text:
                return

            cursor_pos = widget.index(tk.INSERT)
            words = text.split()
            capitalized = " ".join(w.capitalize() for w in words)

            if text != capitalized:
                widget.delete(0, tk.END)
                widget.insert(0, capitalized)
                widget.icursor(cursor_pos)

        widget.bind("<KeyRelease>", auto_capitalize)

    @staticmethod
    def sentence_capitalize_entry(widget):
        """
        Capitalizes the beginning of each sentence in an Entry widget.
        Good for short descriptions inside ENTRY (not Text).
        """

        def auto_cap(event=None):
            text = widget.get()
            if len(text) == 0:
                return

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
                widget.delete(0, tk.END)
                widget.insert(0, result)
                widget.icursor(cursor)

        widget.bind("<KeyRelease>", auto_cap)