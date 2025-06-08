import tkinter as tk
from tkinter import ttk
from beartype import beartype
from modules.ui.child_window import ChildWindow

class TagsUI(ChildWindow):
    """
    UI for editing tags in preferences.
    """

    @beartype
    def __init__(self, cfg, parent=None, title="Edit Tags", geometry="600x400") -> None:
        super().__init__(cfg, title, geometry)
        self.tags = cfg.prefs["tags"]
        self.cfg = cfg
        self.parent = parent
        self.tree = ttk.Treeview(self.window, columns=("Tag", "Color", "Patterns"), show="headings")
        self.tree.heading("Tag", text="Tag")
        self.tree.heading("Color", text="Color")
        self.tree.heading("Patterns", text="Patterns")
        self.tree.column("Tag", width=100, anchor=tk.W)
        self.tree.column("Color", width=100, anchor=tk.W)
        self.tree.column("Patterns", width=300, anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._populate_tree()
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="Add", command=self._add_tag).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit", command=self._edit_tag).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self._delete_tag).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save", command=self._save_tags).pack(side=tk.RIGHT, padx=5)

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        for tag, info in self.tags.items():
            patterns = ", ".join(info.get("patterns", []))
            color = info.get("color", "")
            self.tree.insert("", tk.END, values=(tag, color, patterns))

    def _add_tag(self):
        self._edit_tag_dialog()

    def _edit_tag(self):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        self._edit_tag_dialog(values)

    def _delete_tag(self):
        selected = self.tree.selection()
        if not selected:
            return
        tag = self.tree.item(selected, "values")[0]
        if tag in self.tags:
            del self.tags[tag]
        self._populate_tree()

    def _save_tags(self):
        self.cfg.prefs["tags"] = self.tags
        self.cfg.save()
        self.window.destroy()

    def _edit_tag_dialog(self, values=None):
        dialog = tk.Toplevel(self.window)
        dialog.title("Edit Tag")
        dialog.geometry("400x260")
        dialog.transient(self.window)
        dialog.grab_set()
        ttk.Label(dialog, text="Tag:").pack(pady=5)
        tag_entry = ttk.Entry(dialog, width=30)
        tag_entry.pack(pady=5)
        ttk.Label(dialog, text="Color:").pack(pady=5)
        color_entry = ttk.Entry(dialog, width=30)
        color_entry.pack(pady=5)
        ttk.Label(dialog, text="Patterns (comma separated):").pack(pady=5)
        patterns_entry = ttk.Entry(dialog, width=40)
        patterns_entry.pack(pady=5)
        if values:
            tag_entry.insert(0, values[0])
            color_entry.insert(0, values[1])
            patterns_entry.insert(0, values[2])
        def save():
            tag = tag_entry.get().strip()
            color = color_entry.get().strip()
            patterns = [p.strip() for p in patterns_entry.get().split(",") if p.strip()]
            if tag:
                self.tags[tag] = {"color": color, "patterns": patterns}
                self._populate_tree()
            dialog.destroy()
        ttk.Button(dialog, text="Save", command=save).pack(pady=10)