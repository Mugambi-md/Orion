from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from openpyxl import Workbook
from openpyxl.styles import Font
import datetime
class ExportReports:
    def export_reports_to_pdf(self, filepath, **sections):
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        title_style = styles['Heading2']
        normal_style = styles['Normal']
        elements.append(Paragraph(f"Exported on: {datetime.datetime.now().strftime('%Y/%B/%d %H:%M')}", normal_style))
        elements.append(Spacer(1, 12))
        for section_name, data in sections.items():
            if not data:
                continue
            # Section title
            elements.append(Paragraph(section_name.replace("_", " ").title(), title_style))
            elements.append(Spacer(1, 6))
            # Generate headers from keys
            headers = ["No."] + list(data[0].keys())
            table_data = [headers]

            for i, row in enumerate(data):
                row_data = [i + 1] + [row.get(col, "") for col in data[0].keys()]
                table_data.append(row_data)
            bg_color = colors.lightblue if "order" in section_name.lower() else colors.lightgreen
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), bg_color),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            elements.append(table)
            elements.append(PageBreak())
        doc.build(elements)

class ExportReportToExcel:
    def export_to_excel(self, filepath, **sections):
        wb = Workbook()
        ws = wb.active
        ws.title = "Report"

        bold_font = Font(bold=True)
        ws.append([f"Exported on: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"])
        ws.append([])
        col_widths = {}
        for section_name, records in sections.items():
            # section title
            ws.append([section_name.replace("_", " ").title()])
            ws.cell(row=ws.max_row, column=1).font = bold_font # Make title bold
            ws.append([])
            if records:
                headers = list(records[0].keys())
                ws.append(headers)
                header_row_index = ws.max_row
                for col_num, header in enumerate(headers, 1):
                    cell = ws.cell(row=header_row_index, column=col_num)
                    cell.font = bold_font # Make header bold
                    col_widths[col_num] = max(col_widths.get(col_num, 0), len(str(header)) + 2)
                for row in records:
                    values = [str(row.get(h, "")) for h in headers]
                    ws.append(values)
                    for col_num, value in enumerate(values, 1):
                        col_widths[col_num] = max(col_widths.get(col_num, 0), len(value) + 2)
            else:
                ws.append(["No data available."])
            ws.append([])
            ws.append([])
        wb.save(filepath)