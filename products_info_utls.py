import csv
from stock_access_tables import products_report_table
from tkinter import filedialog, messagebox
from datetime import datetime
import os

def export_products_to_csv(parent_window):
    try: # Create default filename
        columns, rows, _ = products_report_table()
        now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        default_filename = f"Products Information as At {now}.csv"
        # Ask user where to save file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,
            filetypes=[("CSV files", "*.csv")],
            title="Save Products CSV File",
            parent=parent_window
        )
        if not file_path:
            return
        # Write to CSV
        with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns) # Write headers
            for row in rows:
                writer.writerow(row)
        messagebox.showinfo("Success", f"Product Data Exported Successfully to:\n{file_path}", parent=parent_window)
    except Exception as e:
        messagebox.showerror("Export Failed", f"An Error Occured:\n{str(e)}", parent=parent_window)