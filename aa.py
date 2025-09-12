
import tkinter as tk

root = tk.Tk()
root.title("Relief Styles by Border Width")

# Define border widths and relief styles
border_widths = [2, 4, 6]
reliefs = ["flat", "raised", "sunken", "groove", "ridge", "solid"]

# Create buttons grouped by border width
for bw in border_widths:
    label = tk.Label(root, text=f"Border Width: {bw}", font=("Arial", 12, "bold"))
    label.pack(pady=(10, 0))

    frame = tk.Frame(root)
    frame.pack(pady=5)

    for relief in reliefs:
        btn = tk.Button(
            frame,
            text=f"{relief.capitalize()}",
            borderwidth=bw,
            relief=relief,
            width=12
        )
        btn.pack(side="left", padx=5)

root.mainloop()


class YearlyProductSales(BaseWindow):
    def __init__(self, parent, conn, user):
        self.master = tk.Toplevel(parent)
        self.master.title("Yearly Product Sales Performance")
        self.center_window(self.master, 1200, 600, parent)
        self.master.configure(bg="lightblue")
        self.master.transient(parent)
        self.master.grab_set()

        self.conn = conn
        self.user = user
        # Load filter values from DB
        users, years, err = fetch_filter_values(self.conn)
        if err:
            messagebox.showerror("Error",
                                 f"Failed to fetch filter values:\n{err}")
            self.master.destroy()
            return
        # Data holders for filter options
        self.users = users
        self.years = years if years else [date.today().year]
        self.months = [
            ("January", 1), ("February", 2), ("March", 3), ("April", 4),
            ("May", 5), ("June", 6), ("July", 7), ("August", 8),
            ("September", 9), ("October", 10), ("November", 11),
            ("December", 12)
        ]
        self.columns = [
            "No", "Product Code", "Product Name", "Quantity",
            "Unit Cost", "Total Cost", "EST. Unit Price", "Total Amount",
            "Total Profit"
        ]
        # Variables for checkboxes
        self.month_var = tk.BooleanVar()
        self.user_var = tk.BooleanVar()
        self.show_all_var = tk.BooleanVar()
        # Frames
        self.top_frame = tk.Frame(self.master, bg="lightblue")
        self.filter_frame = tk.Frame(self.master, bg="lightblue")
        self.table_frame = tk.Frame(self.master, bg="lightblue")
        self.year_cb = ttk.Combobox(
            self.top_frame, width=8, values=self.years, state="readonly"
        )
        # Filters combobox
        self.month_cb = ttk.Combobox(
            self.filter_frame, width=12, state="disabled",
            values=[name for name, _num in self.months]
        )
        self.user_cb = ttk.Combobox(
            self.filter_frame, width=15, state="disabled", values=self.users
        )
        # Title Label
        self.title = "Products Sales Performance"
        self.title_label = tk.Label(
            self.master, bg="blue", fg="white", font=("Arial", 14, "bold"),
            text=self.title
        )
        # Table
        self.product_table = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self.top_frame.pack(side="top", fill="x", padx=5)
        tk.Label(self.top_frame, text="Select Sales Year:", bg="lightblue",
                 font=("Arial", 11, "bold")).pack(side="left", padx=(10, 0))
        self.year_cb.set(self.years[0])
        self.year_cb.pack(side="left", padx=(0, 15))
        self.year_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(self.top_frame, text="Sort Sales By:", bg="lightblue",
                 font=("Arial", 11, "bold")).pack(side="left", padx=(15, 0))
        tk.Checkbutton(
            self.top_frame, text="Month", variable=self.month_var,
            bg="lightblue", command=self.toggle_filters
        ).pack(side="left")
        tk.Checkbutton(
            self.top_frame, text="User", variable=self.user_var,
            bg="lightblue", command=self.toggle_filters
        ).pack(side="left")
        tk.Checkbutton(
            self.top_frame, text="Show All", variable=self.show_all_var,
            bg="lightblue", command=self.toggle_show_all
        ).pack(side="left")
        btn_frame = tk.Frame(self.top_frame, bg="lightblue")
        btn_frame.pack(side="right", padx=5)
        btns = {
            "Print": self.on_print,
            "Export PDF": self.on_export_pdf,
            "Export Excel": self.on_export_excel
        }
        for text, command in btns.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2,
                relief="solid", bg="dodgerblue", fg="white"
            ).pack(side="left")
        # Filter frame
        self.filter_frame.pack(fill="x", padx=5)
        tk.Label(
            self.filter_frame, text="Select Month:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(5, 0))
        self.month_cb.pack(side="left", padx=(0, 15))
        self.month_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        tk.Label(self.filter_frame, text="Select User:", bg="lightblue",
                 font=("Arial", 11, "bold")).pack(side="left", padx=(15, 0))
        self.user_cb.pack(side="left", padx=(0, 15))
        self.user_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        self.title_label.pack(pady=(5, 0), anchor="center")
        self.table_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        # Table + Scrollbars
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical",
                            command=self.product_table.yview)
        self.product_table.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        # Bold headings
        style = ttk.Style()
        style.configure(
            "Treeview.Heading", font=("Arial", 12, "bold", "underline")
        )
        style.configure("Treeview", font=("Arial", 10), rowheight=30)
        # Configure headings
        for col in self.columns:
            self.product_table.heading(col, text=col)
            self.product_table.column(col, anchor="center", width=20)
        self.product_table.pack(fill="both", expand=True)
        self.product_table.bind(
            "<MouseWheel>", lambda e: self.product_table.yview_scroll(
                -1 * int(e.delta / 120), "units"
        ))
        self.product_table.bind(
            "Button-4", lambda e: self.product_table.yview_scroll(-1, "units")
        )  # macOS
        self.product_table.bind(
            "Button-5", lambda e: self.product_table.yview_scroll(1, "units")
        )
        self.product_table.tag_configure(
            "total", font=("Arial", 12, "bold", "underline")
        )

    def toggle_show_all(self):
        """Handle logic for show all checkbox."""
        if self.show_all_var.get():
            # If Show all is checked, uncheck month and user filters
            self.month_var.set(False)
            self.user_var.set(False)
            self.toggle_filters() # disable combo boxes
        self.load_data() # Refresh table

    def toggle_filters(self):
        """Enable/Disable combo boxes based on checkboxes."""
        # If Show All is checked, force disable filters
        if self.show_all_var.get():
            self.month_cb.configure(state="disabled")
            self.user_cb.configure(state="disabled")
            return
        self.month_cb.configure(
            state="readonly" if self.month_var.get() else "disabled"
        )
        self.user_cb.configure(
            state="readonly" if self.user_var.get() else "disabled"
        )
        self.load_data()

    def load_data(self):
        """Load sales data based on current year only (initial)."""
        self.product_table.delete(*self.product_table.get_children())
        year = int(self.year_cb.get())
        # Filters
        month = None
        user = None
        title = "Products Sales Performance"
        # Only apply filters if show all is unchecked
        if not self.show_all_var.get():
            if self.user_var.get() and self.user_cb.get():
                user = self.user_cb.get()
                title += f" For {user.capitalize()}"
            if self.month_var.get() and self.month_cb.get():
                month = dict(self.months).get(self.month_cb.get())
                title += f" in {self.month_cb.get()}"
        title += f" {year}."
        rows, err = fetch_sales_summary_by_year(self.conn, year, month, user)
        if err:
            messagebox.showerror(
                "Error", f"Failed to fetch sales:\n{err}"
            )
            return
        # Totals accumulators
        total_qty = 0
        total_cost_sum = 0
        total_amount_sum = 0
        total_profit_sum = 0
        for idx, row in enumerate(rows, start=1):
            total_cost = float(row["unit_cost"] * row["total_quantity"])
            est_unit_price = float(
                row["total_amount"] / row["total_quantity"]
            ) if row["total_quantity"] else 0
            total_profit = float(row["total_amount"]) - total_cost
            self.product_table.insert("", "end", values=(
                idx,
                row["product_code"],
                row["product_name"],
                row["total_quantity"],
                f"{row["unit_cost"]:,.2f}",
                f"{total_cost:,.2f}",
                f"{est_unit_price:,.2f}",
                f"{row["total_amount"]:,.2f}",
                f"{total_profit:,.2f}"
            ))
            # Update totals
            total_qty += float(row["total_quantity"])
            total_cost_sum += total_cost
            total_amount_sum += float(row["total_amount"])
            total_profit_sum += total_profit
        if rows:
            self.product_table.insert(
                "", "end", values=("", "", "", "", "", "", "", "", "")
            )
            # Compute weighted averages for costs and prices
            avg_unit_cost = total_cost_sum / total_qty if total_qty else 0
            avg_unit_price = total_amount_sum / total_qty if total_qty else 0
            self.product_table.insert("", "end", values=(
                "",
                "",
                "TOTALS",
                total_qty,
                f"{avg_unit_cost:,.2f}",
                f"{total_cost_sum:,.2f}",
                f"{avg_unit_price:,.2f}",
                f"{total_amount_sum:,.2f}",
                f"{total_cost_sum:,.2f}"
            ), tags=("total",))
        self.title = title
        self.title_label.configure(text=self.title)
        self._resize_columns()

    def _collect_rows(self):
        rows = []
        for item in self.product_table.get_children():
            vals = self.product_table.item(item, "values")
            rows.append({
                "No": vals[0],
                "Product Code": vals[1],
                "Product Name": vals[2],
                "Quantity": vals[3],
                "Unit Cost": vals[4],
                "Total Cost": vals[5],
                "EST. Unit Price": vals[6],
                "Total Amount": vals[7],
                "Total Profit": vals[8]
            })
        return rows
    def _make_exporter(self):
        title = self.title
        columns = [
            "No", "Product Code", "Product Name", "Quantity", "Unit Cost",
            "Total Cost", "EST. Unit Price", "Total Amount", "Total Profit"
        ]
        rows = self._collect_rows()
        return ReportExporter(self.master, title, columns, rows)
    def on_export_excel(self):
        exporter = self._make_exporter()
        exporter.export_excel()
    def on_export_pdf(self):
        exporter = self._make_exporter()
        exporter.export_pdf()
    def on_print(self):
        exporter = self._make_exporter()
        exporter.print()

    def _resize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.product_table.get_children():
                val = str(self.product_table.set(item, col))
                max_width = max(max_width, font.measure(val))
            self.product_table.column(col, width=max_width + 10)
