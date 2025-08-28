import os
import platform
import tempfile
import tkinter as tk
from datetime import datetime
from base_window import BaseWindow
from report_exporter import PDFExporter
from tkinter import scrolledtext, messagebox, filedialog


class DeliveryNotePreviewer(BaseWindow):
    def __init__(self, master, order_data):
        self.master = master
        self.order_data = order_data
        self.window = tk.Toplevel(master)
        self.window.title("Delivery Note Preview")
        self.window.focus_force()
        self.window.grab_set()
        self.window.update_idletasks()
        self.center_window(self.window, 1200, 700)

        # Buttons
        button_frame = tk.Frame(self.window, bg="lightblue")
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="Export to PDF", command=self.export_to_pdf).pack(side="left", padx=10)
        tk.Button(button_frame, text="Print", command=self.print_note).pack(side="left", padx=10)
        tk.Button(button_frame, text="Close", bg="red", command=self.window.destroy).pack(side="right", padx=10)
        self.text_area = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, font=("Courier New", 12))
        self.text_area.pack(expand=True, fill="both", padx=5, pady=5)

        self.generate_note()
        self.text_area.config(state="disabled")

    def center_line(self, text, width=120):
        return text.center(width)
    
    def generate_note(self):
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)
        o = self.order_data
        self.text_area.insert(tk.END, self.center_line("DELIVERY NOTE") + "\n")
        status_line = f"Delivery note for Order #{o['order_id']} ordered on {o['date_placed']}. "
        if o["balance"] > 0:
            status_line += f"Partially paid. Remaining Balance: {o["balance"]:.2f}."
        else:
            status_line += "Fully Paid."
        self.text_area.insert(tk.END, self.center_line(status_line) + "\n\n")
        self.text_area.insert(tk.END, self.center_line("Ordered Items") + "\n")
        #Table Headers
        headers = ["No", "Product Code", "Product Name", "Quantity", "Unit Price", "Total Price"]
        col_widths = [6, 16, 30, 10, 14, 14]
        header_row = "".join(h.ljust(w) for h, w in zip(headers, col_widths))
        self.text_area.insert(tk.END, header_row + "\n")
        self.text_area.insert(tk.END, "-" * sum(col_widths) + "\n")
        # Table Rows
        for idx, item in enumerate(o["items"], start=1):
            row = [
                str(idx),
                item["product_code"],
                item["product_name"],
                str(item["quantity"]),
                f"{item['unit_price']:.2f}",
                f"{item['total_price']:.2f}"
            ]
            self.text_area.insert(tk.END, "".join(val.ljust(w) for val, w in zip(row, col_widths)) + "\n")
        self.text_area.insert(tk.END, "\n\n")
        # Summary
        self.text_area.insert(tk.END, f"{'Total Cost: '}{o['total_cost']:.2f}{'  Amount Paid: '}{o['amount_paid']:.2f}{'  Balance: '}{o['balance']:.2f}\n")
        # Signatures
        self.text_area.insert(tk.END, "\n\n")
        self.text_area.insert(tk.END, f"{'Approved By:':<40}{'Delivered By:':<40}{'Received By:'}\n\n\n")
        self.text_area.insert(tk.END, f"{'-'*30:<40}{'-'*30:<40}{'-'*30}\n")
        self.text_area.insert(tk.END, f"{'Name:':<40}{'Name:':<40}{'Name:'}\n\n\n")
        self.text_area.insert(tk.END, f"{'-'*30:<40}{'-'*30:<40}{'-'*30}\n")
        self.text_area.config(state="disabled")

    def export_to_pdf(self):
        content = self.text_area.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Export", "Nothing to export.")
            return
        now = datetime.now().strftime("%Y %B %d %H_%M")
        default_name = f"Delivery Note of date {now}."
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
            title="Save PDF"
            )
        if filepath:
            pdf = PDFExporter(filepath)
            success, message = pdf.export(content)
            if success:
                messagebox.showinfo("Export to PDF", message)
            else:
                messagebox.showerror("Export Failed", message)
    def print_note(self):
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

if __name__ == "__main__":
    root = tk.Tk()
    #root.withdraw()

    mock_data = {
        "order_id": 123,
        "date_placed": "2025-05-29",
        "total_cost": 15000.0,
        "amount_paid": 10000.0,
        "balance": 5000.0,
        "items": [
            {"product_code": "P001", "product_name": "Product One", "quantity": 2, "unit_price": 2500.0, "total_price": 5000.0},
            {"product_code": "P002", "product_name": "Product Two", "quantity": 1, "unit_price": 10000.0, "total_price": 10000.0}
        ]
    }

    DeliveryNotePreviewer(root, mock_data)
    root.mainloop()