import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from base_window import BaseWindow

class AnalysisWindow(BaseWindow):
    def __init__(self, parent, title, rows, metrics, label_field):
        """
        parent: Tk parent window. title: window title (string).
        rows: List of Dicts (query results). metrics: Dict {label: function(row) -> value}
        label_field: Key in row to use as category label
        """
        self.master = tk.Toplevel(parent)
        self.master.title(title)
        self.center_window(self.master, 1200, 700, parent)
        self.master.configure(bg="lightblue")
        self.master.transient(parent)
        self.master.grab_set()

        self.rows = rows
        self.metrics = metrics
        self.label_field = label_field
        self.title = title
        # Title
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.title_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="flat"
        )
        self.control_frame = tk.Frame(self.title_frame, bg="lightblue")
        self.option_cb = ttk.Combobox(
            self.control_frame, width=20, state="readonly",
            values=list(metrics.keys())
        )
        self.option_cb.current(0)
        # Chart Frames (Scrollable Frame)
        self.chart_container = tk.Frame(self.main_frame, bg="lightblue")
        self.chart_widget = None

        self._build_ui()
        self.chart_container.bind("<Configure>", self.update_charts)
        self.update_charts()

    def _build_ui(self):
        """Pack and arrange widgets."""
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Title
        self.title_frame.pack(side="top", fill="x", pady=(5, 0))
        self.control_frame.pack(side="right", padx=10)
        text = f"Pie Chart For {self.title}"
        tk.Label(
            self.title_frame, text=text, bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline")
        ).pack(side="right", anchor="sw")
        # Controls
        tk.Label(
            self.control_frame, text="View:", bg="lightblue", fg="green",
            font=("Arial", 12, "bold")
        ).pack(side="left", anchor="s")
        self.option_cb.pack(side="left", anchor="s")
        # Bind controls to redraw charts
        self.option_cb.bind("<<ComboboxSelected>>",  self.update_charts)
        # Chart container
        self.chart_container.pack(fill="both", expand=True)

    def update_charts(self, event=None):
        """Refresh pie and bar charts based on selected metric.
        Filling container."""
        for widget in self.chart_container.winfo_children():
            widget.destroy()
            if self.chart_widget:
                self.chart_widget.destroy()
                self.chart_widget = None

        if not self.rows:
            return
        labels = [r[self.label_field] for r in self.rows]
        metric_name = self.option_cb.get()
        metric_fn = self.metrics[metric_name]
        values = [metric_fn(r) for r in self.rows]

        fig_title = f"Pie Chart For {self.title} By {metric_name}."
        tk.Label(
            self.chart_container, bg="lightblue", text=fig_title,
            font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="s")

        dpi = 100
        fig_w = 8
        fig_h = 6
        fig = Figure(figsize=(fig_w, fig_h), dpi=dpi)
        ax = fig.add_subplot(111)

        # Pie Chart
        if sum(values) > 0:
            fig_width = fig.get_size_inches()[0].item()
            label_count = len(labels)
            fontsize = max(6, min(16, (fig_width * 2) - (label_count * 0.3)))
            ax.pie(values, labels=labels, autopct="%1.1f%%",
                   textprops={'fontsize': fontsize})
            fig.tight_layout()
        else:ax.text(
            0.5, 0.5, f"No data to display for '{metric_name}'", ha="center",
            va="center", fontsize=12, color="red"
        )
        # Embed chart into scroll frame
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.chart_widget = canvas.get_tk_widget()
        self.chart_widget.pack(fill="both", expand=True)
        canvas.draw()
