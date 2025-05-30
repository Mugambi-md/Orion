import tkinter as tk

class BaseWindow:
    def center_window(self, window, width=800, height=600):
        """Centers a Tk or Toplevel window on the screen."""
        window.update_idletasks() # Ensure window has calculated dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        window.geometry(f"{width}x{height}+{x}+{y}")