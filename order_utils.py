import re
import tkinter as tk
from tkinter import messagebox, ttk
import tkinter.font as tkFont
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from report_exporter import DeliveryExporter
from order_popups import AddItemWindow, EditQuantityWindow
from working_on_orders import (
    fetch_orders_payments_by_order_id, receive_order_payment,
    fetch_order_balance_by_id, fetch_order_items_by_order_id,
    mark_order_as_delivered, delete_order_item
)


class OrderPayment(BaseWindow):
    def __init__(self, parent, conn, user, order_id):
        self.master = tk.Toplevel(parent)
        self.master.title("Order Payment")
        self.master.configure(bg="lightblue")
        self.center_window(self.master, 350, 250, parent)
        self.master.transient(parent)
        self.master.grab_set()

        self.conn = conn
        self.user = user
        self.order_id = order_id
        self.balance = None
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.center_frame = tk.Frame(
            self.main_frame, bg="lightblue", bd=4, relief="sunken"
        )
        self.cash_var = tk.StringVar()
        self.mpesa_var = tk.StringVar()

        self.build_ui()

    def build_ui(self):
        payments = fetch_orders_payments_by_order_id(self.conn, self.order_id)
        amount, paid = None, None
        if isinstance(payments, str):
            messagebox.showerror("Error", payments, parent=self.master)
        elif not payments:
            messagebox.showinfo(
                "No Payment",
                "No Payment Found for This Order", parent=self.master
            )
        else:
            amount = payments["total_amount"]
            paid = payments["paid_amount"]
            self.balance = payments["balance"]
        self.main_frame.pack(fill="both", expand=True, pady=(0, 5), padx=5)
        top_frame = tk.Frame(self.main_frame, bg="lightblue")
        top_frame.pack(side="top", fill="x")
        tk.Label(
            top_frame, text=f"Payment For Order No. {self.order_id}.",
            bg="lightblue", font=("Arial", 15, "bold", "underline")
        ).grid(row=0, column=0, columnspan=3, pady=(10, 0))
        tk.Label(
            top_frame, text="Full Amount:", bg="lightblue", fg="dodgerblue",
            font=("Arial", 11, "bold")
        ).grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")
        tk.Label(
            top_frame, text="Paid:", bg="lightblue", fg="dodgerblue",
            font=("Arial", 11, "bold")
        ).grid(row=1, column=1, padx=10, pady=(5, 0), sticky="w")
        tk.Label(
            top_frame, text="Balance:", bg="lightblue", fg="dodgerblue",
            font=("Arial", 11, "bold")
        ).grid(row=1, column=2, padx=10, pady=(5, 0), sticky="w")
        tk.Label(
            top_frame, text=f"{amount:,.2f}", bg="lightblue", bd=2, fg="blue",
            relief="raised",  font=("Arial", 11, "bold")
        ).grid(row=2, column=0, padx=10, pady=(0, 10))
        tk.Label(
            top_frame, text=f"{paid:,.2f}", bg="lightblue", bd=2, fg="blue",
            relief="raised", font=("Arial", 11, "bold")
        ).grid(row=2, column=1, padx=10, pady=(0, 10))
        tk.Label(
            top_frame, text=f"{self.balance:,.2f}", bg="lightblue", bd=2,
            fg="blue", relief="raised", font=("Arial", 11, "bold")
        ).grid(row=2, column=2, padx=10, pady=(0, 10))
        self.center_frame.pack(fill="both", expand=True)
        tk.Label(
            self.center_frame, text="Cash Amount:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, pady=(5, 0), padx=10, sticky="w")
        tk.Label(
            self.center_frame, text="Mpesa Amount:", bg="lightblue",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=1, pady=(5, 0), padx=10, sticky="w")
        cash = tk.Entry(
            self.center_frame, textvariable=self.cash_var, width=10, bd=2,
            relief="raised", font=("Arial", 11)
        )
        mpesa = tk.Entry(
            self.center_frame, textvariable=self.mpesa_var, width=10, bd=2,
            relief="raised", font=("Arial", 11)
        )
        cash.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="e")
        cash.focus_set()
        cash.bind("<Return>", lambda e: mpesa.focus_set())
        mpesa.grid(row=1, column=1, padx=10, pady=(0, 5), sticky="e")
        mpesa.bind("<Return>", lambda e: self.post_payment())
        # Auto-format both field as money while typing
        self.add_currency_trace(self.cash_var, cash)
        self.add_currency_trace(self.mpesa_var, mpesa)

        tk.Button(
            self.center_frame, text="Post Payment", bg="dodgerblue", bd=4,
            fg="white", relief="raised", command=self.post_payment
        ).grid(row=2, column=0, columnspan=2, pady=10)

    def add_currency_trace(self, var, entry):
        def callback(var_name, index, mode):
            self.format_currency(var, entry)
        var.trace_add("write", callback)

    def format_currency(self, var, entry):
        """Automatically format entry into money format."""
        # Temporarily remove trace to avoid recursion
        traces = var.trace_info()
        if traces:
            for mode, cbname in traces:
                var.trace_remove(mode, cbname)
        value = var.get().replace(",", "").strip()
        cleaned = ''.join(ch for ch in value if ch.isdigit())
        if not cleaned:
            # Reattach trace and return
            self.add_currency_trace(var, entry)
            return
        formatted = f"{int(cleaned):,}"
        var.set(formatted)
        entry.after_idle(lambda : entry.icursor(tk.END))
        # Reattach trace
        self.add_currency_trace(var, entry)

    def post_payment(self):
        """Handle posting of payment."""
        # Verify user privilege
        priv = "Receive Order Payment"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        try:
            # Read and clean values
            cash_val = self.cash_var.get().replace(",", "").strip()
            mpesa_val = self.mpesa_var.get().replace(",", "").strip()
            cash = float(cash_val) if cash_val else 0.0
            mpesa = float(mpesa_val) if mpesa_val else 0.0

            total_paid = cash + mpesa
            balance = float(self.balance)
            # Validation
            if total_paid <= 0:
                messagebox.showwarning(
                    "Invalid Payment",
                    "Please Enter Valid Amount.", parent=self.master
                )
                return
            if balance == 0:
                messagebox.showwarning(
                    "Invalid Payment",
                    "Order is Fully Paid.", parent=self.master
                )
                return
            change = 0
            if total_paid > balance:
                # Calculate change only if overpayment occurs
                change = total_paid - balance
                # Adjust cash first, since Mpesa cannot be refunded
                if cash >= change:
                    cash -= change
                else:
                    change = total_paid - balance
                    cash = 0
                # Continue posting payment normally

            # Prepare data for posting
            payment_data = {"cash": cash, "mpesa": mpesa}
            # Post to database
            success, message = receive_order_payment(
                self.conn, self.order_id, payment_data, self.user
            )
            # Handle Response
            if success:
                messagebox.showinfo(
                    "Payment Successful", message, parent=self.master
                )
                if change > 0:
                    messagebox.showinfo(
                        "Change Notice",
                    f"Customer Change: {change:,.2f}\n"
                    f"Amount to Record: {balance:,.2f}",
                        parent=self.master
                    )
                self.master.destroy()
            else:
                messagebox.showerror(
                    "Payment Error", message, parent=self.master
                )
        except ValueError:
            messagebox.showerror(
                "Input Error",
                "Invalid Entry. Please Check Your Entries", parent=self.master
            )
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error",
                f"Unexpected Error Occurred: {str(e)}.", parent=self.master
            )


class OrderItemsGui(BaseWindow):
    def __init__(self, parent, conn, user, order_id):
        self.master = tk.Toplevel(parent)
        self.master.title("Order Delivery Options")
        self.master.configure(bg="lightblue")
        self.center_window(self.master, 850, 600, parent)
        self.master.transient(parent)
        self.master.grab_set()

        self.conn = conn
        self.user = user
        self.order_id = order_id
        result = fetch_order_balance_by_id(self.conn, order_id)
        # Error string returned
        if isinstance(result, dict) and "error" in result:
            messagebox.showerror(
                "Error", result["error"], parent=self.master
            )
            return
        elif not result:
            messagebox.showinfo(
                "Not Found",
                "No Payment Found for this Order.", parent=self.master
            )
            return
        self.balance = float(result["balance"])
        self.status = None
        self.total_amount = None

        (self.selected_code, self.selected_amount,
         self.name) = None, None, None
        style = ttk.Style(self.master)
        style.configure("Treeview", rowheight=20, font=("Arial", 10))
        style.configure(
            "Treeview.Heading", font=("Arial", 11, "bold", "underline")
        )
        self.columns = ["No", "Product Code", "Product Name", "Quantity",
                   "Unit Price", "Total Price"]
        self.main_frame = tk.Frame(
            self.master, bg="lightblue", bd=4, relief="solid"
        )
        self.top_frame = tk.Frame(self.main_frame, bg="lightblue", bd=2,
                                  relief="solid")
        self.table_frame = tk.Frame(self.main_frame, bg="lightblue")
        self.btn_frame = tk.Frame(self.table_frame, bg="lightblue")
        self.label = tk.Label(
            self.btn_frame, text="", bg="lightblue", fg="dodgerblue",
            font=("Arial", 14, "italic", "underline")
        )
        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns, show="headings"
        )


        self.build_ui()
        self.load_data()

    def build_ui(self):
        self.main_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.top_frame.pack(side="top", fill="x")
        tk.Label(
            self.top_frame, text="Ordered Items.", bg="lightblue",
            font=("Arial", 16, "bold", "underline")
        ).pack(side="left", padx=10)
        btn_frame = tk.Frame(self.top_frame, bg="lightblue")
        btn_frame.pack(side="right")
        btns = {
            "Clear Balance": self.clear_balance,
            "Mark Delivered": self.mark_delivered,
            "Print & Mark Delivered": self.mark_print_delivery,
            "Print Delivery": self.print_delivery_note
        }
        for text, command in btns.items():
            tk.Button(
                btn_frame, text=text, command=command, bd=2, relief="raised",
                bg="blue", fg="white"
            ).pack(side="left")
        self.table_frame.pack(side="left", fill="both", expand=True)
        self.btn_frame.pack(side="top", fill="x", padx=10)
        action_btn = {
            "Add Order Items": self.add_item,
            "Edit Item Quantity": self.edit_qty,
            "Delete Item": self.delete_item
        }
        for text, command in action_btn.items():
            tk.Button(
                self.btn_frame, text=text, command=command, bd=2, relief="raised",
                bg="green", fg="white"
            ).pack(side="left")
        self.label.pack(side="left", padx=20)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=20)
        self.tree.bind("<<TreeviewSelect>>", self.item_selected)
        scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind(
            "<MouseWheel>", lambda e: self.tree.yview_scroll(-1 * (
                    e.delta // 120
            ), "units")
        )
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.tag_configure("total", font=(
            "Arial", 11, "bold", "underline"
        ), background="lightgray")

    def load_data(self):
        if self.balance > 0:
            msg_text = f"Remaining Order Balance: Ksh.{self.balance:,.2f}."
            self.label.configure(text=msg_text, fg="red")
        else:
            msg_text = "Order Fully Paid."
            self.label.configure(text=msg_text, fg="dodgerblue")
        self.status = msg_text
        items = fetch_order_items_by_order_id(self.conn, self.order_id)
        for i, item in enumerate(items, start=1):
            name = re.sub(r"\s+", " ", str(item["product_name"])).strip()
            self.tree.insert("", "end", values=(
                i,
                item["product_code"],
                name,
                item["quantity"],
                f"{item["unit_price"]:,.2f}",
                f"{item["total_price"]:,.2f}"
            ))
        total_sum = sum(item["total_price"] for item in items)
        self.total_amount = total_sum
        if items:
            self.tree.insert("", "end", values=(
                "", "","", "", "TOTAL", f"{total_sum:,.2f}"
            ), tags=("total",))
        self.autosize_columns()

    def collect_treeview_data(self):
        data = []
        for row_id in self.tree.get_children():
            data.append(self.tree.item(row_id)["values"])
        return data

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.load_data()

    def item_selected(self, event):
        selected = self.tree.focus()
        if selected:
            values = self.tree.item(selected)["values"]
            self.selected_code = values[1]
            self.name = values[2]
            self.selected_amount = float(values[5].replace(",", ""))


    def edit_qty(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning(
                "No Selection", "Select Order Item First.", parent=self.master
            )
            return
        # Verify user privilege
        priv = "Edit Order"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        values = self.tree.item(selected)["values"]
        item_data = {
            "order": self.order_id,
            "code": values[1],
            "product": values[2],
            "quantity": values[3],
            "price": values[4].replace(",", ""),
            "total": values[5].replace(",", "")
        }
        EditQuantityWindow(
            self.master, self.conn, item_data, self.refresh, self.user
        )

    def mark_print_delivery(self):
        order = self.order_id
        confirm = messagebox.askyesno(
            "Confirm",
            f"You want to Mark Order; {order} Delivered?", parent=self.master
        )
        # Verify user privilege
        priv = "Mark Order Delivered"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        if not confirm:
            self.print_delivery_note()
        else:
            try:
                success, message = mark_order_as_delivered(
                    self.conn, self.order_id, self.total_amount, self.user
                )
                if success:
                    self.print_delivery_note()
                    messagebox.showinfo(
                        "Success", message, parent=self.master
                    )
                    self.order_id = None
                    self.master.destroy()
                else:
                    messagebox.showerror("Error", message, parent=self.master)
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to update order: {e}", parent=self.master
                )

    def mark_delivered(self):
        if self.balance > 0:
            messagebox.showerror(
                "Unpaid",
                "Order is not Full Paid, Clear Balance!.", parent=self.master
            )
            return
        # Verify user privilege
        priv = "Mark Order Delivered"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        success, message = mark_order_as_delivered(
            self.conn, self.order_id, self.total_amount, self.user
        )
        if success:
            messagebox.showinfo(
                "Success",
                f"Order No.{self.order_id} Marked Delivered.", parent=self.master
            )
        else:
            messagebox.showerror("Error", message, parent=self.master)

    def print_delivery_note(self):
        data = self.collect_treeview_data()
        exporter = DeliveryExporter(self.order_id, data, self.status)
        path = exporter.export_to_pdf()
        messagebox.showinfo("PDF Exported", f"Saved to: {path}")
        self.master.destroy()

    def clear_balance(self):
        if self.balance <= 0:
            messagebox.showinfo(
                "Fully Paid",
                "Order is Fully Paid.", parent=self.master
            )
            return
        # Verify user privilege
        priv = "Receive Order Payment"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        OrderPayment(self.master, self.conn, self.user, self.order_id)

    def add_item(self):
        # Verify user privilege
        priv = "Edit Order"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        AddItemWindow(
            self.master, self.conn, self.order_id, self.refresh, self.user
        )

    def delete_item(self):
        if not self.selected_code and not self.selected_amount:
            messagebox.showwarning(
                "No Selection", "Select Order Item First.", parent=self.master
            )
            return
        # Verify user privilege
        priv = "Mark Order Delivered"
        verify = VerifyPrivilegePopup(self.master, self.conn, self.user, priv)
        if verify.result != "granted":
            messagebox.showwarning(
                "Access Denied",
                f"Access Denied to {priv}.", parent=self.master
            )
            return
        order_id = self.order_id
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"DELETE {self.name} for Order #{order_id}?", parent=self.master
        )
        if confirm:
            try:
                success, message = delete_order_item(
                    self.conn, self.order_id, self.selected_code,
                    self.selected_amount, self.user
                )
                if success:
                    messagebox.showinfo("Success", message, parent=self.master)
                    self.refresh()
                else:
                    messagebox.showerror("Error", message, parent=self.master)
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error Deleting {self.name}: {str(e)}.",
                    parent=self.master
                )
        else:
            messagebox.showinfo(
                "Cancelled", "Order Item Deletion Cancelled.",
                parent=self.master
            )

    def autosize_columns(self):
        font = tkFont.Font()
        for col in self.columns:
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_value = str(self.tree.set(item, col))
                cell_width = font.measure(cell_value)
                if cell_width > max_width:
                    max_width = cell_width
            self.tree.column(col, width=max_width + 5)

# if __name__ == "__main__":
#     from connect_to_db import connect_db
#     conn=connect_db()
#     root = tk.Tk()
#     OrderItemsGui(root, conn,"Sniffy", 15)
#     root.mainloop()