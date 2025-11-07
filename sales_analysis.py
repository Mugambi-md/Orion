import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
from datetime import date
from analysis_gui_pie import AnalysisWindow
from base_window import BaseWindow
from accounting_export import ReportExporter
from working_sales import (fetch_sales_summary_by_year, fetch_filter_values)



if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root=tk.Tk()
    YearlyProductSales(root, conn, "sniffy")
    root.mainloop()