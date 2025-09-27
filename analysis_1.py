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
        self.title_frame = tk.Frame(self.master, bg="lightblue")
        self.control_frame = tk.Frame(self.title_frame, bg="lightblue")
        self.option_cb = ttk.Combobox(
            self.control_frame, width=20, state="readonly",
            values=list(metrics.keys())
        )
        self.option_cb.current(0)
        # Chart type selector
        self.chart_type_cb = ttk.Combobox(
            self.control_frame, width=10, state="readonly",
            values=["Pie Chart", "Bar Graph"]
        )
        self.chart_type_cb.current(0)
        # Chart Frames (Scrollable Frame)
        self.chart_container = tk.Frame(self.master, bg="lightblue")
        self.chart_widget = None

        self._build_ui()
        self.chart_container.bind("<Configure>", self.update_charts)
        self.update_charts()

    def _build_ui(self):
        """Pack and arrange widgets."""
        # Title
        self.title_frame.pack(side="top", fill="x", pady=(5, 0))
        tk.Label(
            self.title_frame, text=self.title, bg="lightblue",
            font=("Arial", 16, "bold", "underline")
        ).pack(side="left", padx=(20, 0))
        # Controls
        self.control_frame.pack(side="right", anchor="e", padx=10)
        tk.Label(
            self.control_frame, text="View By:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(10, 0))
        self.option_cb.pack(side="left", padx=(0, 10))
        tk.Label(
            self.control_frame, text="Select Chart Type:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(10, 0))
        self.chart_type_cb.pack(side="left", padx=(0, 10))
        # Bind controls to redraw charts
        self.option_cb.bind("<<ComboboxSelected>>",  self.update_charts)
        self.chart_type_cb.bind("<<ComboboxSelected>>", self.update_charts)
        # Chart container
        self.chart_container.pack(fill="both", expand=True, padx=10,
                                  pady=(0, 10))

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
        chart_type = self.chart_type_cb.get()

        fig_title = f"{chart_type} Chart For {self.title} By {metric_name}."
        tk.Label(
            self.chart_container, bg="lightblue", fg="black", text=fig_title,
            font=("Arial", 14, "bold", "underline")
        ).pack(padx=10)
        width = max(600, self.chart_container.winfo_width())
        height = max(400, self.chart_container.winfo_height())
        dpi = 100
        fig_w = max(6, len(labels) * 0.4)
        fig_h = height / dpi

        fig = Figure(figsize=(fig_w, fig_h), dpi=dpi)
        ax = fig.add_subplot(111)

        # Pie Chart
        if not any(values):
            ax.text(
                0.5, 0.5, "No Data Available", ha="center", va="center",
                fontsize=12, color="red"
            )
        if chart_type == "Pie Chart":
            if sum(values) > 0:
                fig_width = fig.get_size_inches()[0]
                label_count = len(labels)
                fontsize = max(6, min(16, (fig_width * 2) - (label_count * 0.3)))
                ax.pie(
                    values, labels=labels, autopct="%1.1f%%",
                    textprops={'fontsize': fontsize}
                )
                fig.tight_layout()
            else:
                ax.text(
                    0.5, 0.5, f"No data to display for '{metric_name}'",
                    ha="center", va="center", fontsize=12, color="red"
                )
        else: # Bar Chart
            ax.bar(labels, values, color="dodgerblue")
            ax.set_ylabel(metric_name)
            ax.set_title(f"{self.title} - {metric_name}", fontsize=12, pad=15)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
            fig.subplots_adjust(bottom=0.25, right=0.95) # Make sure labels don't get cut off
            fig.tight_layout()
        # Embed chart into scroll frame
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.chart_widget = canvas.get_tk_widget()
        self.chart_widget.pack(fill="both", expand=True)
        canvas.draw()

