import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from matplotlib.backends.backend_pdf import PdfPages
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
        self.current_figure = None
        style = ttk.Style(self.master)
        style.theme_use("clam")
        # Title
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.title_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=2, relief="flat"
        )
        self.control_frame = tk.Frame(self.title_frame, bg="lightblue")
        self.option_cb = ttk.Combobox(
            self.control_frame, font=("Arial", 12), state="readonly",
            width=20, values=list(metrics.keys())
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
        self.control_frame.pack(side="right", padx=5)
        # Controls
        tk.Label(
            self.control_frame, text="View By:", bg="lightblue", fg="green",
            font=("Arial", 12, "bold")
        ).pack(side="left", anchor="s")
        self.option_cb.pack(side="left", anchor="s")
        tk.Button(
            self.control_frame, text="Export PDF", bg="blue", fg="white", bd=4,
            relief="groove", font=("Arial", 10, "bold"), command=self.export_pdf
        ).pack(side="left", anchor="s", padx=5)
        text = f"Pie Chart For {self.title}"
        tk.Label(
            self.title_frame, text=text, bg="lightblue", fg="blue",
            font=("Arial", 20, "bold", "underline")
        ).pack(side="right", anchor="sw")

        # Bind controls to redraw charts
        self.option_cb.bind("<<ComboboxSelected>>",  self.update_charts)
        # Chart container
        self.chart_container.pack(fill="both", expand=True)

    def update_charts(self, _event=None):
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

        fig_title = f"Chart For {self.title} By {metric_name}."
        tk.Label(
            self.chart_container, text=fig_title, bg="lightblue",
            fg="dodgerblue", font=("Arial", 16, "bold", "underline")
        ).pack(side="top", anchor="s")

        dpi = 100
        fig_w = 10
        fig_h = 6
        fig = Figure(figsize=(fig_w, fig_h), dpi=dpi)
        self.current_figure = fig
        # Big pie area (=78% width)
        ax_pie = fig.add_axes((0.01, 0.05, 0.66, 0.9))
        # SMALL legend area (=22% width)
        ax_leg = fig.add_axes((0.70, 0.1, 0.28, 0.8))
        ax_leg.axis("off")

        # Pie Chart
        if sum(values) > 0:
            wedges, _, autotexts = ax_pie.pie(
                values,
                labels=None,
                autopct="%1.1f%%",
                startangle=90,
                counterclock=False,
                pctdistance=0.75,
                textprops={'fontsize': 10}
            )
            ax_pie.set_aspect("equal") # Keep pie circular
            total_value = sum(values)
            legend_labels = [
                f"{label} → {value:,}   ({(value / total_value) * 100:.1f}%)"
                for label, value in zip(labels, values)
            ]
            ax_leg.legend(
                wedges,
                legend_labels,
                title="Items",
                loc="upper left",
                fontsize=11,
                title_fontsize=13,
                frameon=True
            )
            def on_motion(event):
                if event.inaxes != ax_pie:
                    ax_pie.set_title("")
                    fig.canvas.draw_idle()
                    return
                for i, w in enumerate(wedges):
                    contains, _ = w.contains(event)
                    if contains:
                        label = labels[i]
                        value = values[i]
                        percent = (value / sum(values)) * 100
                        ax_pie.set_title(
                            f"{label}: {value:,} ({percent:.1f}%)",
                            fontsize=12,
                            pad=12
                        )
                        fig.canvas.draw_idle()
                        return
            fig.canvas.mpl_connect("motion_notify_event", on_motion)
        else:
            ax_pie.text(
                0.5, 0.5,
                f"No data to display for '{metric_name}'",
                ha="center", va="center", fontsize=12,
                color="red", transform=ax_pie.transAxes
            )
        # Embed chart into scroll frame
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.chart_widget = canvas.get_tk_widget()
        self.chart_widget.pack(fill="both", expand=True)
        canvas.draw()

    def export_pdf(self):
        """Export the current display chart to PDF."""
        if not hasattr(self, "current_figure"):
            messagebox.showwarning(
                "No Chart", "Nothing to Export.", parent=self.master
            )
            return
        metric = self.option_cb.get()
        default_name = f"{self.title}_{metric}.pdf".replace(" ", "_")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not file_path:
            return

        try:
            with PdfPages(file_path) as pdf:
                pdf.savefig(self.current_figure, bbox_inches="tight")
            messagebox.showinfo(
                "Success", f"PDF Saved To:\n{file_path}.", parent=self.master
            )
        except Exception as e:
            messagebox.showerror("Failed", str(e), parent=self.master)