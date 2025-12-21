import tkinter as tk
from tkinter import ttk, messagebox
from base_window import BaseWindow
from authentication import VerifyPrivilegePopup
from window_functionality import FocusChain
from windows_utils import CurrencyFormatter
from working_sales import (
    fetch_cashier_control_users, get_net_sales, CashierControl
)



