import tkinter as tk
from tkinter import ttk
import mplcursors
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, FuncFormatter
from dateutil import parser


class LineAnalysisWindow:
    def __init__(self, title, rows, metrics, date_field):
        """
        parent: Tk parent window. title: Window title (String). Rows: List of
        Dicts(query results). date_field: Key in row that holds data.
        Metrics: Dict{label: function(row) -> value}
        """
        self.master = tk.Toplevel()
        self.master.title(title)
        self.master.state("zoomed")
        self.master.configure(bg="lightblue")
        self.master.transient()
        self.master.grab_set()

        self.rows = rows
        self.metrics = metrics
        self.date_field = date_field
        self.title = title

        style = ttk.Style(self.master)
        style.theme_use("clam")
        # Frames
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.title_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.control_frame = tk.Frame(self.title_frame, bg="lightblue")
        self.option_cb = ttk.Combobox(
            self.control_frame, width=15, state="readonly", font=("Arial", 12),
            values=["Show All"] + list(metrics.keys())
        )
        self.option_cb.current(0)
        self.chart_container = tk.Frame(self.main_frame, bg="lightblue")
        self.chart_widget = None

        self._build_ui()
        self.chart_container.bind("<Configure>", self.update_chart)
        self.update_chart()

    def _build_ui(self):
        """Pack and arrange widgets."""
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.title_frame.pack(side="top", fill="x", pady=(5, 0))
        self.control_frame.pack(side="right", padx=10)
        tk.Label(
            self.title_frame, text=self.title, bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline"), width=60
        ).pack(side="right", anchor="sw")
        tk.Label(
            self.control_frame, text="View By:", bg="lightblue", fg="green",
            font=("Arial", 12, "bold")
        ).pack(side="left", anchor="s")
        self.option_cb.pack(side="left", anchor="s")
        self.option_cb.bind("<<ComboboxSelected>>", self.update_chart)
        self.chart_container.pack(fill="both", expand=True)

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
            self.chart_container, text=fig_title, bg="lightblue",
            font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="s")
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


class MonthLineAnalysis:
    def __init__(self, title, rows, metrics, date_field):
        """
        parent: Tk parent window. title: Window title (String). Rows: List of
        Dicts(query results). date_field: Key in row that holds data.
        Metrics: Dict{label: function(row) -> value}
        """
        self.master = tk.Toplevel()
        self.master.title(title)
        self.master.state("zoomed")
        self.master.configure(bg="lightblue")
        self.master.transient()
        self.master.grab_set()

        self.rows = rows
        self.metrics = metrics
        self.date_field = date_field
        self.title = title

        style = ttk.Style(self.master)
        style.theme_use("clam")
        # Frames
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.title_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.control_frame = tk.Frame(self.title_frame, bg="lightblue")
        self.option_cb = ttk.Combobox(
            self.control_frame, width=15, state="readonly", font=("Arial", 12),
            values=["Show All"] + list(metrics.keys())
        )
        self.option_cb.current(0)
        self.chart_container = tk.Frame(self.main_frame, bg="lightblue")
        self.chart_widget = None

        self._build_ui()
        self.chart_container.bind("<Configure>", self.update_chart)
        self.update_chart()

    def _build_ui(self):
        """Pack and arrange widgets."""
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.title_frame.pack(side="top", fill="x", pady=(5, 0))
        self.control_frame.pack(side="right", padx=10)
        tk.Label(
            self.title_frame, text=self.title, bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline"), width=60
        ).pack(side="right", anchor="sw")
        tk.Label(
            self.control_frame, text="View By:", bg="lightblue", fg="green",
            font=("Arial", 12, "bold")
        ).pack(side="left", anchor="s")
        self.option_cb.pack(side="left", anchor="s")
        self.option_cb.bind("<<ComboboxSelected>>", self.update_chart)
        self.chart_container.pack(fill="both", expand=True)

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
                first_date = data[0][0]
                month_start = first_date.replace(day=1)
                if month_start < first_date:
                    data.insert(0, (month_start, 0))
                data_by_metric[label] = list(zip(*data)) # (dates, values)
        # Build figure
        fig_title = (
            f"Graph Of {self.title} (All Metrics)."
            if metric_choice == "Show All"
            else f"Graph Of {self.title} By {metric_choice}."
        )
        tk.Label(
            self.chart_container, text=fig_title, bg="lightblue",
            font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="s")
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

        # Format x-axis MONTHLY-ONLY
        all_dates = []
        for dates, _ in data_by_metric.values():
            all_dates.extend(dates)

        if all_dates:
            month_start = min(all_dates).replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)

            ax.set_xlim(month_start, month_end)

        # Date formatting (clear daily labels)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        ax.set_xlabel(f"Day of Month")
        all_values = []
        for _, (_, values) in data_by_metric.items():
            all_values.extend(values)
        formatter_func, suffix = self.auto_scale_formatter(all_values)
        ax.yaxis.set_major_formatter(FuncFormatter(formatter_func))
        ax.set_ylabel(f"{metric_choice}{suffix}")
        ax.set_ylim(bottom=0)
        ax.axhline(0, color="black", linewidth=1)
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
            date_str = x[idx].strftime("%d %b")
            sel.annotation.set_text(
                f"{line.get_label()}\nDate: {date_str}\nValue: {y[idx]:,.2f}"
            )
            sel.annotation.get_bbox_patch().set(fc="lightyellow", alpha=0.9)
        # @cursor.connect("remove")
        def on_motion(event): # type: ignore
            if not event.inaxes:
                for sel in cursor.selections:
                    sel.annotation.set_visible(False)
                canvas.draw_idle()
                return
            over_line = any(l.contains(event)[0] for l in lines)
            if not over_line:
                for sel in cursor.selections:
                    sel.annotation.set_visible(False)
                canvas.draw_idle()
        fig.canvas.mpl_connect("motion_notify_event", on_motion)

    @staticmethod
    def auto_scale_formatter(values):
        """Returns (formatter_function, label_suffix)."""
        max_val = max(values) if values else 0
        if max_val >= 1_000_000:
            return (
                lambda x, _: f"{x / 1_000_000:.2f}", " (* 1,000,000)"
            )
        elif max_val >= 1_000:
            return (
                lambda x, _: f"{x / 1_000:.1f}", " (* 1,000)"
            )
        else:
            return (
                lambda x, _: f"{x:.0f}", ""
            )