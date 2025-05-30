import os
import tempfile
import platform
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, messagebox, filedialog
from report_exporter import ExportReports, ExportReportToExcel
from base_window import BaseWindow

class ReportPreviewer(BaseWindow):
    def __init__(self, user):
        self.user = user
        self.sections = {}

    def show(self, **sections):
        """Display the preview window with data sections.
            Args:
                Sections: key-value pairs where key is section title, value is a list of dicts."""
        self.sections = sections
        self.preview_window = tk.Toplevel()
        self.preview_window.title("Report Preview")
        self.center_window(self.preview_window, 1300, 600)
        self.preview_window.state('zoomed') # Maximize (windows)
        self.preview_window.lift()
        self.preview_window.focus_force()
        self.preview_window.grab_set()
        #self.preview_window.update_idletasks()
        self.preview_window.bind("<Escape>", lambda e: self.preview_window.destroy())
        # Buttons Frame
        button_frame = tk.Frame(self.preview_window, bg="lightgreen")
        button_frame.pack(padx=2, pady=1, anchor="center")
        tk.Button(button_frame, text="Export to PDF", command=self.export_to_pdf).pack(side="left", padx=3)
        tk.Button(button_frame, text="Export to Excel", command=self.export_to_excel).pack(side="left", padx=3)
        tk.Button(button_frame, text="Print", command=self.print_report).pack(side="left", padx=3)
        tk.Button(button_frame, text="Close", bg="red", command=self.preview_window.destroy).pack(side="right", padx=10)
        # Report Area
        self.text_area = scrolledtext.ScrolledText(self.preview_window, wrap=tk.WORD, font=("Courier New", 12))
        self.text_area.pack(expand=True, fill='both', pady=(5, 10))

        self.generate_preview_text()
    def generate_preview_text(self):
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert(tk.END, self.center_text_line(f"REPORT PREVIEW", 120) + "\n")
        self.text_area.insert(tk.END, self.center_text_line(f"Exported by: {self.user}", 120) + "\n\n")
        for section_name, data in self.sections.items():
            title = section_name.upper()
            underline = "=" * len(title)
            self.text_area.insert(tk.END, self.center_text_line(title, 120) + "\n")
            self.text_area.insert(tk.END, self.center_text_line(underline, 120) + "\n")
            if isinstance(data, list) and data:
                headers = list(data[0].keys())
                 # Determine widths based on longest item in each column
                col_widths = {header: max(len(header), max(len(str(row.get(header, ''))) for row in data)) + 4 for header in headers}
                header_row = ''.join(header.ljust(col_widths[header]) for header in headers)
                self.text_area.insert(tk.END, self.center_text_line(header_row, 120) + "\n")
                for row in data:
                    line = ''.join(str(row.get(col, '')).ljust(col_widths[col]) for col in headers)
                    self.text_area.insert(tk.END, self.center_text_line(line, 120) + "\n")
                self.text_area.insert(tk.END, "\n\n")
    
    def center_text_line(self, text, total_width=120):
        """Pad the text with spaces to center it within total width characters."""
        return text.center(total_width)
    def export_to_pdf(self):
        now = datetime.now().strftime("%Y %B %d %H_%M")
        exporter = ExportReports()
        if len(self.sections) == 1:
            section_name = next(iter(self.sections)).title()
        else:
            section_name = "_".join(name.title() for name in self.sections.keys())
        default_name = f"{section_name} Reports as at {now}.pdf"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
            title="Save Report As"
        )
        if not filepath:
            return
        exporter.export_reports_to_pdf(filepath, **self.sections)
        messagebox.showinfo("Export Completed", f"Reports Exported Successfully to: {filepath}...")
    def export_to_excel(self):
        now = datetime.now().strftime("%Y %B %d %H_%M")
        exporter = ExportReportToExcel()
        if len(self.sections) == 1:
            section_name = next(iter(self.sections)).title()
        else:
            section_name = "_".join(name.title() for name in self.sections.keys())
        default_name = f"{section_name} Reports as at {now}.xlsx"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=default_name,
            title="Save Report As"
        )
        if not filepath:
            return
        exporter.export_to_excel(filepath, **self.sections)
        messagebox.showinfo("Export Completed", f"Reports Exported Successfully to: {filepath}.")
    def print_report(self):
        # Get the text from the preview area
        content = self.text_area.get('1.0', tk.END)
        if not content.strip():
            messagebox.showwarning("Print", "Nothing to Print.")
            return
        try: # Create a temporary text file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            # Detect OS and use appropriate command
            system_name = platform.system()
            if system_name == "Windows":
                os.startfile(temp_file_path, "print")
            elif system_name == "Darwin": # macOS
                os.system(f"lpr {temp_file_path}")
            elif system_name == "Linux":
                os.system(f"lp {temp_file_path}")
            else:
                messagebox.showerror("Print Error", f"Unsupported Os: {system_name}")
                return
            messagebox.showinfo("Print", "Report sent to printer successfully.")
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print.\n\n{e}")