import tkinter as tk


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

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")