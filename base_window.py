import tkinter as tk


class BaseWindow:
    @staticmethod
    def center_window(window, width=800, height=600, parent=None):
        """Centers a Tk or Toplevel window.
        - If 'parent' is given, centers relative to the parent window.
        - Otherwise, centers on the screen."""
        window.update_idletasks() # Ensure window has calculated dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        if parent:
            parent.update_idletasks()
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            x = parent_x + (parent_width - width) //2
            y = parent_y + (parent_height - height) //2
        else:
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        # Ensure the window stays on screen
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        window.geometry(f"{width}x{height}+{x}+{y}")

# class BaseWindow:
#     @staticmethod
#     def center_window(self, window, width=800, height=600):
#         """Centers a Tk or Toplevel window on the screen."""
#         window.update_idletasks() # Ensure window has calculated dimensions
#         screen_width = window.winfo_screenwidth()
#         screen_height = window.winfo_screenheight()
#         x = int((screen_width - width) / 2)
#         y = int((screen_height - height) / 2)
#         window.geometry(f"{width}x{height}+{x}+{y}")


# if __name__ == "__main__":
#     root = tk.Tk()
#     BasePopWindow.center_window(root, 600, 500)
#     root.mainloop()