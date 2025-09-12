import tkinter as tk
from tkinter import ttk
from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from dateutil import parser
import mplcursors
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
        # Bind controls to redraw charts
        self.option_cb.bind("<<ComboboxSelected>>",  self.update_charts)
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

        fig_title = f"Pie Chart For {self.title} By {metric_name}."
        tk.Label(
            self.chart_container, bg="lightblue", fg="black", text=fig_title,
            font=("Arial", 14, "bold", "underline")
        ).pack(padx=10)

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

class LineAnalysisWindow(BaseWindow):
    def __init__(self, parent, title, rows, metrics, date_field):
        """
        parent: Tk parent window. title: Window title (String). Rows: List of
        Dicts(query results). date_field: Key in row that holds data.
        Metrics: Dict{label: function(row) -> value}
        """
        self.master = tk.Toplevel(parent)
        self.master.title(title)
        self.center_window(self.master, 1300, 700, parent)
        self.master.state("zoomed")
        self.master.configure(bg="lightblue")
        self.master.transient(parent)
        self.master.grab_set()

        self.rows = rows
        self.metrics = metrics
        self.date_field = date_field
        self.title = title

        # Frames
        self.title_frame = tk.Frame(self.master, bg="lightblue")
        self.control_frame = tk.Frame(self.title_frame, bg="lightblue")
        self.option_cb = ttk.Combobox(
            self.control_frame, width=20, state="readonly",
            values=["Show All"] + list(metrics.keys())
        )
        self.option_cb.current(0)
        self.chart_container = tk.Frame(self.master, bg="lightblue")
        self.chart_widget = None

        self._build_ui()
        self.chart_container.bind("<Configure>", self.update_chart)
        self.update_chart()

    def _build_ui(self):
        """Pack and arrange widgets."""
        self.title_frame.pack(side="top", fill="x", pady=(5, 0))
        tk.Label(
            self.title_frame, text=self.title, bg="lightblue",
            font=("Arial", 16, "bold", "underline")
        ).pack(side="left", padx=(20, 0))
        self.control_frame.pack(side="right", anchor="e", padx=10)
        tk.Label(
            self.control_frame, text="View By:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(10, 0))
        self.option_cb.pack(side="left", padx=(0, 10))
        self.option_cb.bind("<<ComboboxSelected>>", self.update_chart)
        self.chart_container.pack(fill="both", expand=True, padx=10,
                                  pady=(0, 10))

    def update_chart(self, event=None):
        """Refresh line chart based on selected metrics."""
        for widget in self.chart_container.winfo_children():
            widget.destroy()
            if self.chart_widget:
                self.chart_widget.destroy()
                self.chart_widget = None
        if not self.rows:
            return
        metric_choice = self.option_cb.get()
        # Extract dates once
        data_by_metric = {}
        for label, metric_fn in self.metrics.items():
            data = []
            for row in self.rows:
                raw_date = row[self.date_field]
                try:
                    dt = parser.parse(str(raw_date))
                except (ValueError, TypeError):
                    continue
                data.append((dt, metric_fn(row)))
            if data:
                data.sort(key=lambda x: x[0])
                data_by_metric[label] = list(zip(*data)) # (dates, values)
        # Build figure
        fig_title = (
            f"Line Graph For {self.title} (All Metrics)."
            if metric_choice == "Show All"
            else f"Line Graph For {self.title} By {metric_choice}."
        )
        tk.Label(
            self.chart_container, text=fig_title, bg="lightblue", fg="black",
            font=("Arial", 14, "bold", "underline")
        ).pack(padx=5, anchor="center")
        dpi = 100
        fig = Figure(figsize=(8, 6), dpi=dpi)
        ax = fig.add_subplot(111)
        colors = ["blue", "green", "red", "orange", "purple", "brown"]
        lines, labels = [], [] # For legend
        if metric_choice == "Show All":
            for i, (label, (dates, values)) in enumerate(data_by_metric.items()):
                color = colors[i % len(colors)]
                line, = ax.plot(
                    dates, values, marker="o", linestyle="-", color=color,
                    label=label
                )
                lines.append(line)
                labels.append(label)
        else:  # Plot only the selected metric
            if metric_choice in data_by_metric:
                dates, values = data_by_metric[metric_choice]
                line, = ax.plot(
                    dates, values, marker="o", linestyle="-", color=colors[0],
                    label=metric_choice
                )
                lines.append(line)
                labels.append(metric_choice)
        if lines and labels:
            legend = ax.legend(
                lines, labels, loc="best", frameon=True, framealpha=0.7,
                facecolor="white"
            )
            legend.set_draggable(True)

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        year = ""
        if data_by_metric:
            for dates, _ in data_by_metric.values():
                if dates: # Only pick if we have at least one date
                    year = dates[0].year
                    break
        ax.set_xlabel(f"Date ({year})")
        ax.set_ylabel(metric_choice)
        ax.grid(True, linestyle="--", alpha=0.7)
        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.chart_widget = canvas.get_tk_widget()
        self.chart_widget.pack(fill="both", expand=True)
        canvas.draw()
        # Enable tooltip on hover
        cursor = mplcursors.cursor(lines, hover=True)
        @cursor.connect("add")
        def on_add(sel):
            line = sel.artist
            x, y = line.get_data()
            if sel.index is None:
                return
            idx = int(sel.index)
            if idx < 0 or idx >= len(x):
                return # Out of range safety
            date_str = x[idx].strftime("%d %b %Y")
            sel.annotation.set_text(
                f"{line.get_label()}\nDate: {date_str}\nValue: {y[idx]:,.2f}"
            )
            sel.annotation.get_bbox_patch().set(fc="lightyellow", alpha=0.9)
        # @cursor.connect("remove")
        def on_motion(event):
            if not event.inaxes:
                for sel in cursor.selections:
                    sel.annotation.set_visible(False)
                canvas.draw_idle()
                return
            over_line = any(line.contains(event)[0] for line in lines)
            if not over_line:
                for sel in cursor.selections:
                    sel.annotation.set_visible(False)
                canvas.draw_idle()
        fig.canvas.mpl_connect("motion_notify_event", on_motion)


if __name__ == "__main__":
    rows = [
        {"date": "2025-01-01", "sales": 120, "profit": 40},
        {"date": "2025-01-02", "sales": 150, "profit": 60},
        {"date": "2025-01-03", "sales": 90, "profit": 25},
        {"date": "2025-01-04", "sales": 200, "profit": 80},
        {"date": "2025-01-05", "sales": 170, "profit": 55},
        {"date": "2025-01-06", "sales": 220, "profit": 100},
        {"date": "2025-01-07", "sales": 180, "profit": 65},
        {"date": "2025-01-08", "sales": 130, "profit": 50},
        {"date": "2025-01-09", "sales": 250, "profit": 120},
        {"date": "2025-01-10", "sales": 210, "profit": 90},
    ]
    metrics = {
        "Sales Amount": lambda r: r["sales"],
        "Profit Amount": lambda r: r["profit"],
        "Profit Margin %": lambda r: (r["profit"] / r["sales"]) * 100 if r["sales"] else 0,
        "Double Sales": lambda r: r["sales"] * 2,  # just to test dynamic scaling
    }
    root = tk.Tk()
    LineAnalysisWindow(root, "Sales & Profit Trends", rows, metrics, date_field="date")

    root.mainloop()