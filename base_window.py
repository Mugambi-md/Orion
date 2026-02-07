import tkinter as tk
import os


class BaseWindow:
    ICON_PATH = "myicon.ico"

    @staticmethod
    def set_icon(window):
        """Sets the window icon for Tk or Toplevel."""
        if not os.path.exists(BaseWindow.ICON_PATH):
            return

        try:
            if BaseWindow.ICON_PATH.endswith(".ico"):
                window.iconbitmap(BaseWindow.ICON_PATH)
            else:
                icon = tk.PhotoImage(file=BaseWindow.ICON_PATH)
                window.iconphoto(True, icon)
        except (tk.TclError, FileNotFoundError):
            # Icon format not supported or platform limitation
            pass

    @staticmethod
    def center_window(window, width=800, height=600, parent=None):
        """Centers a Tk or Toplevel window.
        - If 'parent' is given, centers relative to the parent window.
        - Otherwise, centers on the screen."""
        # Ensure window has calculated dimensions
        window.update_idletasks()
        # Apply icon automatically
        BaseWindow.set_icon(window)
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
        # Fade-in only for child windows
        if parent:
            BaseWindow.fade_in(window)
            # Fade-out
            BaseWindow.bind_fade_close(window)

    @staticmethod
    def enable_dpi_scaling(window, scale=1.25):
        """
        Enable DPI scaling for high-resolution displays.
        Call once on root window.
        """
        try:
            window.tk.call("tk", "scaling", scale)
        except tk.TclError:
            pass

    @staticmethod
    def fade_in(window, duration=150, steps=10):
        """
        Smooth fade-in animation.
        Duration: total time in ms.
        steps: animation smoothness
        """
        window.attributes("-alpha", 0.0)
        window.update_idletasks()

        delay = max(1, duration // steps)
        def _fade(step=0):
            alpha = step / steps
            window.attributes("-alpha", alpha)
            if step < steps:
                window.after(delay, _fade, step + 1)

        _fade()

    @staticmethod
    def bind_fade_close(window):
        """Intercept Window close (X button) and apply fade-out."""
        window.protocol(
            "WM_DELETE_WINDOW", lambda: BaseWindow.fade_out(window)
        )

    @staticmethod
    def fade_out(window, duration=120, steps=6):
        """Fade out then destroy or callback."""
        delay = max(1, duration // steps)

        def _fade(step=steps):
            alpha = step / steps
            window.attributes("-alpha", alpha)
            if step > 0:
                window.after(delay, _fade, step - 1)
            else:
                window.destroy()

        _fade()