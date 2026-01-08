from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from datetime import datetime
import pandas as pd
from xml.sax.saxutils import escape
import os
import platform
import tempfile
import subprocess
from tkinter import messagebox, filedialog
from reportlab.pdfbase import pdfmetrics

class ReportExporter:
    def __init__(self, parent, title, columns, rows):
        """
        parent: tk parent for dialogs. title: String title of report
        Columns: Ordered List of column headers. Rows: List of dicts
        representing rows.
        """
        self.parent = parent
        self.title = title
        self.columns = columns
        self.rows = self._normalize_rows(rows)

    def _normalize_rows(self, rows):
        """Ensures rows is a list of dicts; fill missing keys with empty
        string."""
        normalized = []
        for r in rows:
            if isinstance(r, dict):
                # Only keep expected columns, fill missing
                normalized.append({col: r.get(col, "") for col in self.columns})
            else:
                # If something slips through that's not a dict, try to coerce(zip)
                try:
                    normalized.append({col: val for col, val in zip(self.columns, list(r))})
                except (TypeError, ValueError):
                    continue
        return normalized

    def _default_filename(self, ext):
        safe_title = "".join(
            c if c.isalnum() or c in (" ", "_", "-") else "_" for c in self.title
        ).strip().replace(" ","_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{safe_title}_report_as_at{timestamp}.{ext.lstrip('.')}"

    def export_excel(self):
        try:
            df = pd.DataFrame(self.rows, columns=self.columns)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to build Excel data: {str(e)}",
                parent=self.parent
            )
            return
        default_name = self._default_filename("xlsx")
        try:
            filename = filedialog.asksaveasfilename(
                parent=self.parent,
                defaultextension=".xlsx",
                initialfile=default_name,
                filetypes=[("Excel", "*.xlsx")],
                title=f"Save {self.title} as Excel"
            )
            if not filename:
                return
            df.to_excel(filename, index=False)
            messagebox.showinfo(
                "Exported",
                f"Excel report saved to:\n{filename}", parent=self.parent
            )
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to save Excel: {str(e)}", parent=self.parent
            )

    def _calculate_column_widths(self, page_width):
        """
        Calculate column widths based on content. Usable width of the page.
        """
        font_name = "Helvetica"
        font_size = 10
        padding = 12 # Left + Right padding
        min_width = 30
        col_widths = []

        for col in self.columns:
            max_width = pdfmetrics.stringWidth(
                str(col), font_name, font_size
            )
            # Check each row's value for this column
            for row in self.rows:
                value = str(row.get(col, ""))
                text_width = pdfmetrics.stringWidth(
                    value, font_name, font_size
                )
                max_width = max(max_width, text_width)
            col_widths.append(max(max_width + padding, min_width))
        # Scale widths to fit page
        total_width = sum(col_widths)
        if total_width > page_width:
            scale = page_width / total_width
            col_widths = [w * scale for w in col_widths]
            col_widths = [max(w, min_width) for w in col_widths]
            total_width = sum(col_widths)
            if total_width > page_width:
                overflow = total_width - page_width
                flexible_cols = [
                    i for i, w in enumerate(col_widths) if w > min_width
                ]
                if flexible_cols:
                    reduce_per_col = overflow / len(flexible_cols)
                    for i in flexible_cols:
                        col_widths[i] = max(
                            min_width, col_widths[i] - reduce_per_col
                        )
        return col_widths

    def _build_pdf_story(self):
        # Page setup
        page_width, _ = landscape(A4)
        usable_width = page_width - 40 # Margins left 40 and right 40
        col_widths = self._calculate_column_widths(usable_width)
        # Title style
        title_style = ParagraphStyle(
            name="Title",
            fontName="Helvetica-Bold",
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        header_style = ParagraphStyle(
            name="Header",
            fontName="Helvetica-Bold",
            fontSize=12,
            alignment=TA_CENTER
        )
        cell_style = ParagraphStyle(
            name="Cell",
            fontName="Helvetica",
            fontSize=10,
            alignment=TA_CENTER
        )

        # Build table data: header + each row
        table_data = []
        header_row = [
            Paragraph(escape(str(col)), header_style) for col in self.columns
        ]
        table_data.append(header_row)

        for r in self.rows:
            row = []
            for col in self.columns:
                val_str = str(r.get(col, ""))
                row.append(Paragraph(val_str, cell_style))
            table_data.append(row)
        # Table Styling
        tbl_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.grey),
        ])

        # Create table; allow header to repeat
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(tbl_style)
        story = [Paragraph(self.title, title_style), Spacer(1, 6), table]

        return story

    def export_pdf(self):
        default_name = self._default_filename("pdf")
        filename = filedialog.asksaveasfilename(
            parent=self.parent,
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF", "*.pdf")],
            title=f"Save {self.title} as PDF"
        )
        if not filename:
            return
        try:
            story = self._build_pdf_story()
            # Always landscape
            doc = SimpleDocTemplate(
                filename, pagesize=landscape(A4), rightMargin=40,
                leftMargin=40, topMargin=60, bottomMargin=40
            )
            doc.build(story)
            messagebox.showinfo(
                "Exported",
                f"PDF report saved to:\n{filename}", parent=self.parent)
        except Exception as e:
            print(f"Failed to write pdf: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to write PDF: {str(e)}", parent=self.parent
            )

    def print(self):
        """Export report as PDF, send directly to printer and delete temp
        file after."""
        pdf_path = None
        try:
            # Always landscape orientation
            default_name = self._default_filename("pdf")
            pdf_path = os.path.join(tempfile.gettempdir(), default_name)
            story = self._build_pdf_story()
            doc = SimpleDocTemplate(
                pdf_path, pagesize=landscape(A4), rightMargin=40,
                leftMargin=40, topMargin=60, bottomMargin=40
            )
            doc.build(story)

            system_name = platform.system()
            if system_name == "Windows":
                os.startfile(pdf_path, "print")
            elif system_name == "Darwin": # macOS
                subprocess.run(["lpr", pdf_path], check=True,)
            elif system_name == "Linux":
                subprocess.run(["lp", pdf_path], check=True)
            else:
                messagebox.showwarning(
                    "Print Failed", f"Unsupported OS: {system_name}",
                    parent=self.parent
                )
                return
            messagebox.showinfo(
                "Printing", "Report sent to printer successfully.",
                parent=self.parent
            )
        except Exception as e:
            messagebox.showerror(
                "Print Failed", f"Print Failed: {str(e)}", parent=self.parent
            )
        finally:
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass