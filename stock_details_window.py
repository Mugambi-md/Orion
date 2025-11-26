import re
import tkinter as tk
import tkinter.font as tkFont 
from tkinter import ttk, messagebox
from base_window import BaseWindow
from analysis_gui_pie import AnalysisWindow
from working_on_stock import view_all_products
from accounting_export import ReportExporter
from authentication import VerifyPrivilegePopup, DescriptionFormatter


class ProductsDetailsWindow(BaseWindow):
    def __init__(self, parent, user, conn):
        self.window = tk.Toplevel(parent)
        self.window.title("Products Information")
        self.center_window(self.window, 1350, 700, parent)
        self.window.configure(bg="green")
        self.window.grab_set()
        self.window.transient(parent)

        self.user = user
        self.conn = conn
        self.title = "AVAILABLE  PRODUCTS  INFORMATION"
        self.columns = [
            "No", "Code", "Name", "Description", "Quantity", "Cost",
            "Wholesale Price", "Retail Price", "Min Stock"
        ]
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"))
        style.configure("Treeview", font=("Arial", 11))
        self.main_frame = tk.Frame(
            self.window, bg="green", bd=4, relief="solid"
        )
        self.tree_frame = tk.Frame(self.main_frame, bg="green")

        self.tree = ttk.Treeview(
            self.tree_frame, columns=self.columns, show="headings"
        )

        self.create_widgets()
        self.populate_table()

    def create_widgets(self):
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Top frame with buttons
        top_frame = tk.Frame(self.main_frame, bg="green")
        top_frame.pack(side="top", fill="x", padx=5)
        # Buttons on top and Table Title
        tk.Label(
            top_frame, text=self.title, bg="green", fg="white", bd=2,
            relief="groove", font=("Arial", 17, "bold", "underline")
        ).pack(side="left", padx=10)
        buttons = {
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel,
            "Products Chart": self.products_statistics,
        }
        for text, command in buttons.items():
            tk.Button(
                top_frame, text=text, font=("Arial", 12), bg="blue", bd=4,
                relief="groove", command=command
            ).pack(side="right")
        self.tree_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(
            self.tree_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.tag_configure("evenrow", background="#fffde7")
        self.tree.tag_configure("oddrow", background="#e0f7e9")
        # Set Headings
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=50)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.tag_configure(
            "totalrow", font=("Arial", 11, "bold", "underline")
        )
        self.tree.tag_configure(
            "grandtotalrow", background="#c5cae9",
            font=("Arial", 12, "bold", "underline")
        )
        self.tree.bind("<MouseWheel>", lambda e:self.tree.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))

    def populate_table(self):
        products = view_all_products(self.conn)
        total_qty = 0
        total_cost = 0.0
        total_wholesale = 0.0
        total_retail = 0.0
        formatter = DescriptionFormatter()
        for i, product in enumerate(products, start=1):
            name = re.sub(r"\s+", " ", str(product["product_name"])).strip()
            description = formatter.format(product["description"])
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                i,
                product["product_code"],
                name,
                description,
                product["quantity"],
                f"{product['cost']:,.2f}",
                f"{product['wholesale_price']:,.2f}",
                f"{product['retail_price']:,.2f}",
                product["min_stock_level"]
            ), tags=(tag,))


            # Accumulate totals
            total_qty += product["quantity"]
            total_cost += product["cost"]
            total_wholesale += product["wholesale_price"]
            total_retail += product["retail_price"]
        # Insert totals row
        if products:
            total_values = [
                "",
                "",
                "",
                "TOTAL",
                f"{total_qty:,}",
                f"{total_cost:,.2f}",
                f"{total_wholesale:,.2f}",
                f"{total_retail:,.2f}",
                ""
            ]
            self.tree.insert("", "end", values=total_values, tags=("totalrow",))
            grand_total_cost = total_cost * total_qty
            grand_total_wholesale = total_wholesale * total_qty
            grand_total_retail = total_retail * total_qty
            self.tree.insert("", "end", values=(
                "",
                "",
                "",
                "GRAND TOTAL",
                "",
                f"{grand_total_cost:,.2f}",
                f"{grand_total_wholesale:,.2f}",
                f"{grand_total_retail:,.2f}",
                ""
            ), tags=("grandtotalrow",))

        self.resize_columns()

    def resize_columns(self):
        """Auto-resize columns based on the content."""
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                text = str(self.tree.set(item, col))
                width = font.measure(text)
                if width > max_width:
                    max_width = width
            self.tree.column(col, width=max_width)


    def has_privilege(self, privilege: str) -> bool:
        """Check if the current user has the required privilege."""
        dialog = VerifyPrivilegePopup(
            self.window, self.conn, self.user, privilege
        )
        if dialog.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"You do not have permission to {privilege}.",
                parent=self.window
            )
            return False
        return True

    def _collect_rows(self):
        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append({
                "No": vals[0] or "",
                "Code": vals[1] or "",
                "Name": vals[2] or "",
                "Description": vals[3] or "",
                "Quantity": vals[4] or "",
                "Cost": vals[5] or "",
                "Wholesale Price": vals[6] or "",
                "Retail Price": vals[7] or "",
                "Min Stock Level": vals[8] or ""
            })
        return rows

    def _make_exporter(self):
        title = "Available Product Information"
        columns = [
            "No", "Code", "Name", "Description", "Quantity", "Cost",
            "Wholesale Price", "Retail Price", "Min Stock Level"
        ]
        rows = self._collect_rows()
        return ReportExporter(self.window, title, columns, rows)

    def on_export_excel(self):
        if not self.has_privilege("Export Products Records"):
            return
        exporter = self._make_exporter()
        exporter.export_excel()

    def on_export_pdf(self):
        if not self.has_privilege("Export Products Records"):
            return
        exporter = self._make_exporter()
        exporter.export_pdf()

    def on_print(self):
        if not self.has_privilege("Export Products Records"):
            return
        exporter = self._make_exporter()
        exporter.print()

    def products_statistics(self):
        # Fetch current product data
        products = view_all_products(self.conn)
        if not products:
            messagebox.showinfo(
                "No Data",
                "No Products Available For Analysis.", parent=self.window
            )
            return
        # Verify user privilege
        if not self.has_privilege("View Products"):
            return
        # Define metrics for charting
        metrics = {
            "Quantity": lambda r: r["quantity"],
            "Cost": lambda r: r["cost"],
            "Wholesale Price": lambda r: r["wholesale_price"],
            "Retail Price": lambda r: r["retail_price"],
            "Min Stock Level": lambda r: r["min_stock_level"],
        }
        # Create and open Analysis Window
        title = "Products"
        field = "product_name"
        AnalysisWindow(self.window, title, products, metrics, field)




if __name__ == "__main__":
    from connect_to_db import connect_db
    conn=connect_db()
    root = tk.Tk()
    # root.withdraw()
    app=ProductsDetailsWindow(root, "sniffy", conn)
    root.mainloop()
