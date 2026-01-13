import tkinter.font as tkFont


class TreeviewSorter:
    def __init__(self, tree, cols, no_col, even_tag, odd_tag):
        """
        tree - (ttk.Treeview instance). cols - (list of column names).
        no_col - (column used for numbering (not sortable)). zebra -
        (apply zebra striping).
        """
        self.tree = tree
        self.columns = cols
        self.number_column = no_col
        self.even_tag = even_tag
        self.odd_tag = odd_tag
        self.sort_direction = {}

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
        data = []
        for item in self.tree.get_children():
            value = self.tree.set(item, col)
            data.append((value, item))

        # Numeric sort -- fallback to string
        try:
            data.sort(
                key=lambda x: float(str(x[0]).replace(",", "")),
                reverse=reverse
            )
        except ValueError:
            data.sort(
                key=lambda x: str(x[0]).lower(), reverse=reverse
            )

        # Reorder rows
        for index, (_, item) in enumerate(data):
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
        for index, item in enumerate(self.tree.get_children(), start=1):
            if self.number_column in self.columns:
                self.tree.set(item, self.number_column, index)

                tag = self.even_tag if index % 2 == 0 else self.odd_tag
                self.tree.item(item, tags=(tag,))

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