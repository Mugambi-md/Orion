import tkinter as tk

root = tk.Tk()
root.title("Button Styles Demo")

# Define styles
styles = [
    {"borderwidth": 2, "relief": "raised"},
    {"borderwidth": 4, "relief": "sunken"},
    {"borderwidth": 6, "relief": "groove"},
    {"borderwidth": 2, "relief": "ridge"},
    {"borderwidth": 4, "relief": "flat"},
    {"borderwidth": 6, "relief": "solid"},
]

# Create buttons in pairs
for i, style in enumerate(styles):
    frame = tk.Frame(root)
    frame.pack(pady=5)

    btn1 = tk.Button(frame, text=f"Button A{i+1}", **style, width=12)
    btn2 = tk.Button(frame, text=f"Button B{i+1}", **style, width=12)

    btn1.pack(side="left", padx=10)
    btn2.pack(side="left", padx=10)

root.mainloop()