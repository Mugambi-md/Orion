import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
from connect_to_db import connect_db
from base_window import BaseWindow
from report_preview import ReportPreviewer
from working_on_orders import fetch_all_orders, fetch_all_order_items, fetch_all_orders_logs, order_items_history
conn = connect_db()
class ReportsWindow(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Order Reports")
        self.center_window(self.master, 900, 600)
        self.master.transient(parent)
        self.master.configure(bg="lightblue")
        self.master.grab_set()

        self.user = user
        self.conn = conn
        self.create_widgets()

    def create_widgets(self):
        top_frame = tk.Frame(self.master, bg="lightgreen")
        top_frame.pack(fill="x", padx=5)
        btn_orders = tk.Button(top_frame, text="Orders History", command=self.show_orders_history)
        btn_items = tk.Button(top_frame, text="Ordered Items", command=self.show_ordered_items)
        btn_logs = tk.Button(top_frame, text="View Order Logs", command=self.show_order_logs)
        btn_ordered = tk.Button(top_frame, text="Most Ordered Items", command=self.show_ordered_history)
        btn_export_all = tk.Button(top_frame, text="Export All Reports", command=self.preview_all_reports, bg="blue")
        btn_orders.pack(side="left", padx=5)
        btn_items.pack(side="left", padx=5)
        btn_logs.pack(side="left", padx=5)
        btn_ordered.pack(side="left", padx=5)
        btn_export_all.pack(side="right", padx=10)
        self.table_frame = tk.Frame(self.master, bg="lightblue")
        self.table_frame.pack(fill="both", expand=True, pady=(0, 7))
        self.show_orders_history()
    def clear_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

    def build_table(self, title_text, columns, data=None):
        self.clear_table()
        self.last_export = {
            "title": title_text,
            "columns": columns,
            "rows": data or []
        }

        title = tk.Label(self.table_frame, text=title_text, font=("Arial", 13, "bold"), bg="lightblue")
        title.grid(row=0, column=1, padx=5)
        export_btn = tk.Button(self.table_frame, text="Export Report", command=self.export_current_report)
        export_btn.grid(row=0, column=2, sticky="e", padx=5)
        # Allow the table frame to expand
        self.table_frame.rowconfigure(1, weight=1)
        self.table_frame.columnconfigure(0, weight=1)
        self.table_frame.columnconfigure(1, weight=1)
        self.table_frame.columnconfigure(2, weight=1)
        tree_frame = tk.Frame(self.table_frame)
        tree_frame.grid(row=1, column=0, columnspan=3, padx=3, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", stretch=True)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=vsb.set)
        def _on_mousewheel(event): # Mouse wheel scrolling (window and Linux)
            tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        tree.bind("<MouseWheel>", _on_mousewheel) # Windows/Linux
        if data:
            for row in data:
                tree.insert("", "end", values=row)
        self.auto_adjust_column_widths(tree)
        def on_resize(event):
            self.auto_adjust_column_widths(tree)
        tree_frame.bind("<Configure>", on_resize)

        return tree
    def show_orders_history(self):
        cols = ("No.", "Order ID", "Customer Name", "Date Placed", "Deadline", "Amount", "Status")
        orders = fetch_all_orders(self.conn)
        rows = [
            (
                i + 1,
                row["order_id"],
                row["customer_name"],
                row["date_placed"],
                row["deadline"],
                row["amount"],
                row["status"]
            )
            for i, row in enumerate(orders)
        ]
        self.build_table("Orders History", cols, rows)

    def show_ordered_items(self):
        cols = ("No.", "Order ID", "Product Code", "Product Name", "Quantity", "Unit Price", "Total Price")
        items = fetch_all_order_items(self.conn)
        rows = [
            (
                i + 1,
                row["order_id"],
                row["product_code"],
                row["product_name"],
                row["quantity"],
                row["unit_price"],
                row["total_price"]
            )
            for i, row in enumerate(items)
        ]
        self.build_table("Ordered Items History", cols, rows)

    def show_order_logs(self):
        cols = ("No.", "Date", "Order ID", "User", "Action", "Amount")
        logs = fetch_all_orders_logs(self.conn)
        rows = [
            (
                i + 1,
                row["log_date"],
                row["order_id"],
                row["user"],
                row["action"],
                row["total_amount"]
            )
            for i, row in enumerate(logs)
        ]
        self.build_table("Order Logs History", cols, rows)
    def show_ordered_history(self):
        cols = ("No.", "Order ID", "Product Code", "Product Name", "Quantity", "Unit Price", "Total Price")
        items = order_items_history(self.conn)
        rows = [
            (
                i + 1,
                row["order_id"],
                row["product_code"],
                row["product_name"],
                row["quantity"],
                row["unit_price"],
                row["total_price"]
            )
            for i, row in enumerate(items)
        ]
        self.build_table("Most Ordered Items", cols, rows)
    def auto_adjust_column_widths(self, tree):
        font = tkFont.Font()
        for col in tree["columns"]:
            max_width = max([font.measure(str(tree.set(child, col))) for child in tree.get_children()] + [font.measure(col)])
            tree.column(col, width=max_width + 40)

    
    def export_current_report(self):
        report = self.last_export
        if not report or not report["rows"]:
            messagebox.showinfo("Export", "No Data to Export.")
            return
        columns = report["columns"]
        rows = report["rows"]
        formatted_rows = [dict(zip(columns, row)) for row in rows] # Convert tupples to dicts
        previewer = ReportPreviewer(user=self.user)
        previewer.show(**{report["title"]: formatted_rows})
        
    def preview_all_reports(self):
        orders = fetch_all_orders(self.conn)
        items_in_pending_orders = fetch_all_order_items(self.conn)
        previewer = ReportPreviewer(user=self.user)
        previewer.show(orders=orders, items_in_pending_orders=items_in_pending_orders)

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = ReportsWindow(root, conn, "Sniffy")
#     #root.withdraw()
#     root.mainloop()