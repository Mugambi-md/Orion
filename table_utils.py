import tkinter
import tkinter.font as tkFont


class TreeviewSorter:
    def __init__(self, tree, cols, no_col, style_name="App.Treeview"):
        """
        tree - (ttk.Treeview instance). cols - (list of column names).
        no_col - (column used for numbering (not sortable)). zebra -
        (apply zebra striping).
        """
        self.tree = tree
        self.columns = cols
        self.number_column = no_col
        # self.even_tag = even_tag
        # self.odd_tag = odd_tag
        self.sort_direction = {}
        self.style_name = style_name
        self.heading_style = f"{style_name}.Heading"

    def apply_style(self, style):
        """Apply default treeview styling. Fonts and theme are fixed."""
        # Apply theme only if not already active
        try:
            if style.theme_use() != "clam":
                style.theme_use("clam")
        except tkinter.TclError:
            style.theme_use("clam")
        style.configure(self.style_name, font=("Arial", 11))
        style.configure(self.heading_style, font=("Arial", 13, "bold"))
        self.tree.configure(style=self.style_name)

    def set_row_height(self, style, height=None):
        """Update row height dynamically (Optional)."""
        style.configure(self.style_name)
        style.configure(
            self.style_name, rowheight=height if height else style.lookup(
                "Treeview", "rowheight"
            )
        )

    def attach_sorting(self):
        """Attach sorting behavior to treeview headings."""
        for col in self.columns:
            self.tree.heading(
                col, text=col, command=lambda c=col: self.sort_by_column(c)
            )

    def sort_by_column(self, col):
        # Skip numbering column
        if col == self.number_column:
            return
        reverse = self.sort_direction.get(col, False)
        sortable = []
        fixed = []
        for item in self.tree.get_children():
            tags = set(self.tree.item(item, "tags"))
            # Keep TOTAL (or any fixed-tagged rows) out of sorting
            if tags & {"total", "totalrow", "grandtotalrow"}:
                fixed.append(item)
                continue
            value = self.tree.set(item, col)
            sortable.append((value, item))

        # Numeric sort -- fallback to string
        try:
            sortable.sort(
                key=lambda x: float(str(x[0]).replace(",", "")),
                reverse=reverse
            )
        except ValueError:
            sortable.sort(
                key=lambda x: str(x[0]).lower(), reverse=reverse
            )

        # Reorder rows
        for index, (_, item) in enumerate(sortable):
            self.tree.move(item, "", index)

        # Toggle direction
        self.sort_direction[col] = not reverse

        # Update column headers with arrow
        for heading in self.columns:
            text = heading
            if heading == col:
                text += " ▲" if not reverse else " ▼"
            self.tree.heading(
                heading, text=text,
                command=lambda c=heading: self.sort_by_column(c)
            )
        self.renumber_rows()

    def renumber_rows(self):
        """Renumber rows and apply zebra striping."""
        index = 1
        for item in self.tree.get_children():
            tags = set(self.tree.item(item, "tags"))
            if tags & {"total", "totalrow", "grandtotalrow"}:
                continue
            if self.number_column in self.columns:
                self.tree.set(item, self.number_column, index)
                # Remove old zebra tags
                tags.discard("evenrow")
                tags.discard("oddrow")
                # Apply new zebra tag
                tags.add("evenrow" if index % 2 == 0 else "oddrow")
                self.tree.item(item, tags=tuple(tags))
                # tag = self.even_tag if index % 2 == 0 else self.odd_tag
                # self.tree.item(item, tags=(tag,))
                index += 1

    def autosize_columns(self, padding=None):
        """Auto resize columns based on header and cell content."""
        font = tkFont.Font()
        spacing = padding if padding else 2
        for col in self.columns:
            # Fixed numbering column to support upto 3 digits
            if col == self.number_column:
                width = font.measure("000") + spacing
                self.tree.column(col, width=width, anchor="center")
                continue
            # Start with header width
            max_width = font.measure(col)
            for item in self.tree.get_children():
                cell_value = self.tree.set(item, col)
                width = font.measure(str(cell_value))
                if width > max_width:
                    max_width = width

            self.tree.column(col, width=max_width + spacing)

    def bind_mousewheel(self):
        def _on_mousewheel(event):
            if event.delta:
                self.tree.yview_scroll(
                    int(-1 * (event.delta / 120)), "units"
                )

        def _on_linux_scroll_up(event):
            self.tree.yview_scroll(-1, "units")

        def _on_linux_scroll_down(event):
            self.tree.yview_scroll(1, "units")

        self.tree.bind("<Enter>", lambda e: self.tree.bind(
            "<MouseWheel>", _on_mousewheel
        ))
        self.tree.bind(
            "<Leave>", lambda e: self.tree.unbind("<MouseWheel>")
        )
        self.tree.bind("<Button-4>", _on_linux_scroll_up)
        self.tree.bind("<Button-5>", _on_linux_scroll_down)