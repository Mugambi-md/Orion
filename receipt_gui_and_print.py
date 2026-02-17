import os
import shutil
import tempfile
import platform
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from working_sales import fetch_receipt_data
from datetime import date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from tkinter import filedialog

class ReceiptViewer:
    def __init__(self, conn, receipt_no, user):
        self.window = tk.Toplevel()
        self.window.title("Receipt Viewer")
        self.window.configure(bg="lightgray")
        self.window.state("zoomed")
        self.window.transient()
        self.window.grab_set()

        self.conn = conn
        self.receipt_no = receipt_no
        self.user = user
        self.center_frame = tk.Frame(self.window, bg="white")
        self.receipt_text = ScrolledText(
            self.center_frame, width=58, wrap=tk.WORD, bg="white", height=40,
            font=("Courier New", 10)
        )

        self.create_widgets()
        self.display_receipt()

    def create_widgets(self):
        # Top Frame
        top_frame = tk.Frame(self.window, bg="white")
        top_frame.pack(side="top", anchor="center", pady=(5, 0))
        tk.Button(
            top_frame, text="Print", fg="blue", bd=4, relief="groove",
            font=("Arial", 9, "bold"), command=self.print_receipt
        ).pack(side="right", padx=5)
        tk.Button(
            top_frame, text="Export", fg="green", bd=4, relief="groove",
            font=("Arial", 9, "bold"), command=self.export_receipt
        ).pack(side="right", padx=5)
        self.center_frame.pack(expand=True, anchor="center", fill="both")
        # ScrolledText for receipt display
        self.receipt_text.pack(padx=20, pady=5)
        self.receipt_text.configure(state="disabled") # Initially disabled

    def display_receipt(self):
        self.receipt_text.configure(state="normal")  # Enable text box before writing
        try:
            sale, items = fetch_receipt_data(self.conn, self.receipt_no)
            if not sale:
                messagebox.showerror(
                    "Not Found",
                    f"No Sale Found For Receipt: {self.receipt_no}",
                    parent=self.window
                )
                return
            # Build receipt text
            printed_on = date.today().strftime("%Y-%m-%d")
            self.receipt_text.delete('1.0', tk.END)
            rt = self.receipt_text
            # rt.configure(state="normal")

            rt.insert(tk.END, f"{'ORION STAR':^54}\n")
            rt.insert(tk.END, f"{'SALES RECEIPT':^54}\n\n")
            rt.insert(tk.END, f"{'='*54}\n")
            rt.insert(tk.END, f"Receipt No: {sale['receipt_no']}\n")
            rt.insert(tk.END, f"Date: {sale['sale_date']}  Time: {sale['sale_time']}\n")
            rt.insert(tk.END, f"{'-'*54}\n")
            rt.insert(tk.END, f"{'No':<4}{'Code':<6}{'Name':<13}{'Unit.P':>10}{'Qty':>6}{'Total':>13}\n")
            rt.insert(tk.END, f"{'-'*54}\n")

            for no, item in enumerate(items, 1):
                code = item['product_code']
                name = item['product_name'][:13] # Truncate to 13 chars max
                unit_price = item['unit_price']
                qty = item['quantity']
                total = item['total_amount']
                rt.insert(tk.END, f"{no:<4}{code:<6}{name:<13}{unit_price:>10,.2f}{qty:>6}{total:>13,.2f}\n\n")
            rt.insert(tk.END, f"{'-'*54}\n")
            rt.insert(tk.END, f"{'TOTAL':>41}: {sale['total_amount']:>11,.2f}\n")
            rt.insert(tk.END, f"{'-'*54}\n")
            rt.insert(tk.END, f"Served By: {sale['user']}\n")
            rt.insert(tk.END, f"Printed On: {printed_on}\n\n")
            rt.insert(tk.END, f"Printed By: {self.user}\n")
            rt.insert(tk.END, f"{'='*54}\n")
            rt.insert(tk.END, f"{'Thank You For Your Purchase!':^54}\n")
            rt.insert(tk.END, f"{'='*54}\n")
            rt.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            self.receipt_text.configure(state="disabled") # Disable on failure too

    def print_receipt(self):
        try:
            self.receipt_text.configure(state="normal")
            receipt_content = self.receipt_text.get('1.0', tk.END)
            self.receipt_text.configure(state="disabled")
            # Create a temporary text file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp_file:
                temp_file.write(receipt_content)
                temp_file_path = temp_file.name
            system_platform = platform.system()
            # Send to printer
            if system_platform == "Windows":
                # windows: use default print handler
                os.startfile(temp_file_path, "print")
            elif system_platform == "Darwin" or system_platform == "Linux":
                # macOS or Linux
                if shutil.which("lp"):
                    print_command=["lp", temp_file_path]
                elif shutil.which("lpr"):
                    print_command = ["lpr", temp_file_path]
                else:
                    raise EnvironmentError("No Printing Command found (lp or lpr).")
                subprocess.run(print_command, check=True)
            else:
                raise OSError(f"Unsupported OS: {system_platform}")
            messagebox.showinfo("Print", "Receipt sent to printer.")
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print receipt.\n{str(e)}")

    def export_receipt(self):
        try:
            # Get receipt text
            self.receipt_text.configure(state="normal")
            receipt_content = self.receipt_text.get('1.0', tk.END)
            self.receipt_text.configure(state="disabled")
            # Ask user where to save PDF
            day = date.today().strftime("%y%m%d")
            default_filename = f"Sales Receipt {day}.pdf"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=default_filename,
                title="Save Receipt as PDF"
            )
            if not filepath:
                return  # User cancelled

            # Setup PDF document
            c = canvas.Canvas(filepath, pagesize=A4)
            width, height = A4
            c.setFont("Courier", 10)
            left_margin = 50
            top_margin = height - 50
            line_height = 12  # Adjust as needed
            # Write each line of the receipt
            y = top_margin
            for line in receipt_content.splitlines():
                c.drawString(left_margin, y, line)
                y -= line_height
                if y < 50:  # Create new page if needed
                    c.showPage()
                    y = top_margin

            c.save()
            messagebox.showinfo("Export", f"Receipt saved as PDF:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export receipt.\n{str(e)}")


class ReceiptPrinter:
    @classmethod
    def print_receipt(cls, conn, receipt_no):
        try:
            sale, items = fetch_receipt_data(conn, receipt_no)
            if not sale:
                return False, f"No Sale found for receipt: {receipt_no}"
            printed_on = date.today().strftime("%Y/%m/%d")
            # Build receipt string
            lines = []
            lines.append(f"{'ORION STAR':^54}")
            lines.append(f"{'SALES RECEIPT':^54}")
            lines.append(" ")
            lines.append(f"{'=' * 54}")
            lines.append(f"Receipt No: {sale['receipt_no']}")
            lines.append(f"Date: {sale['sale_date']} Time: {sale['sale_time']}")
            lines.append(f"{'-' * 54}")
            lines.append(f"{'No':<4}{'Code':<6}{'Name':<13}{'Unit.P':>10}{'Qty':>6}{'Total':>13}")
            lines.append(f"{'-' * 54}")
            for no, item in enumerate(items, 1):
                code = item['product_code']
                name = item['product_name'][:13]
                unit_price = item['unit_price']
                qty = item['quantity']
                total = item['total_amount']
                lines.append(f"{no:<4}{code:<6}{name:<13}{unit_price:>10,.2f}{qty:>6}{total:>13,.2f}")
                lines.append("")
            lines.append(f"{'-' * 54}")
            lines.append(f"{'TOTAL':>41}: {sale['total_amount']:>11,.2f}")
            lines.append(f"{'-' * 54}")
            lines.append(f"Served By: {sale['user']}")
            lines.append(f"Printed On: {printed_on}")
            lines.append("")
            lines.append(f"{'=' * 54}")
            lines.append(f"{'Thank You For Your Purchase':^54}")
            lines.append(f"{'=' * 54}")

            receipt_text = "\n".join(lines)
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp_file:
                temp_file.write(receipt_text)
                temp_file_path = temp_file.name

            # Detect OS and print
            system_platform = platform.system()
            if system_platform == "Windows":
                os.startfile(temp_file_path, "print")
            elif system_platform == "Darwin" or system_platform == "Linux":
                if shutil.which("lp"):
                    subprocess.run(["lp", temp_file_path], check=True)
                elif shutil.which("lpr"):
                    subprocess.run(["lpr", temp_file_path], check=True)
                else:
                    return False, "No print command found (lp or lpr)."
            else:
                return False, f"Unsupported OS: {system_platform}"
            return True, "Receipt sent to printer."
        except Exception as e:
            return  False, f"Print Error: {e}"


