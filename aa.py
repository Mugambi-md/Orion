
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