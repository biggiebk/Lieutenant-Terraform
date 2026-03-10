"""
UI for editing tags in preferences.
"""
import tkinter as tk

from beartype import beartype

from modules.config import LieutenantTerraformConfig
from modules.ui.child_window import ChildWindow


class TagsUI(ChildWindow):
	"""
	UI for editing tags in preferences.
	"""

	@beartype
	def __init__(
		self,
		cfg: LieutenantTerraformConfig,
		parent: tk.Misc | None = None,
		title: str = "Edit Tags",
		geometry: str = "600x400",
	) -> None:
		super().__init__(cfg, title, geometry, parent=parent)
		self.tags = cfg.prefs["tags"]
		self.parent = parent

		columns = (
			("Tag", "Tag", 100, tk.W),
			("Color", "Color", 100, tk.W),
			("Patterns", "Patterns", 300, tk.W),
		)
		frame, self.tree = self.create_treeview(columns)
		frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
		self._populate_tree()

		button_frame = self.create_button_bar(
			left_buttons=(
				("Add", self._add_tag),
				("Edit", self._edit_tag),
				("Delete", self._delete_tag),
			),
			right_buttons=(("Save", self._save_tags),),
		)
		button_frame.pack(fill=tk.X, padx=10, pady=5)

	def _populate_tree(self) -> None:
		self.tree.delete(*self.tree.get_children())
		for tag, info in self.tags.items():
			patterns = ", ".join(info.get("patterns", []))
			color = info.get("color", "")
			self.tree.insert("", tk.END, values=(tag, color, patterns))

	def _add_tag(self) -> None:
		self._edit_tag_dialog()

	def _edit_tag(self) -> None:
		selected = self.tree.selection()
		if not selected:
			return
		values = self.tree.item(selected, "values")
		self._edit_tag_dialog(values)

	def _delete_tag(self) -> None:
		selected = self.tree.selection()
		if not selected:
			return
		tag = self.tree.item(selected, "values")[0]
		if tag in self.tags:
			del self.tags[tag]
		self._populate_tree()

	def _save_tags(self) -> None:
		self.cfg.prefs["tags"] = self.tags
		self.cfg.save()
		self.destroy()

	def _edit_tag_dialog(self, values=None) -> None:
		dialog = self.create_modal("Edit Tag", "400x260")
		tag_entry = self.create_labeled_entry(
			dialog,
			label_text="Tag:",
			width=30,
			value=values[0] if values else "",
		)
		color_entry = self.create_labeled_entry(
			dialog,
			label_text="Color:",
			width=30,
			value=values[1] if values else "",
		)
		patterns_entry = self.create_labeled_entry(
			dialog,
			label_text="Patterns (comma separated):",
			width=40,
			value=values[2] if values else "",
		)

		def save() -> None:
			tag = tag_entry.get().strip()
			color = color_entry.get().strip()
			patterns = [pattern.strip() for pattern in patterns_entry.get().split(",") if pattern.strip()]
			if tag:
				self.tags[tag] = {"color": color, "patterns": patterns}
				self._populate_tree()
			dialog.destroy()

		self.add_button(text="Save", command=save, master=dialog).pack(pady=10)