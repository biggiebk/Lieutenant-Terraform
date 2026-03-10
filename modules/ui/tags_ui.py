"""
UI for editing tag-like pattern rules in preferences.
"""
import tkinter as tk

from beartype import beartype

from modules.config import LieutenantTerraformConfig
from modules.ui.child_window import ChildWindow


class PatternRulesUI(ChildWindow):
	"""
	Reusable UI for editing named pattern rules in preferences.
	"""

	@beartype
	def __init__(
		self,
		cfg: LieutenantTerraformConfig,
		preference_key: str,
		item_label: str,
		parent: tk.Misc | None = None,
		title: str = "Edit Rules",
		geometry: str = "600x400",
	) -> None:
		super().__init__(cfg, title, geometry, parent=parent)
		self.preference_key = preference_key
		self.item_label = item_label
		self.item_label_plural = f"{item_label}s"
		self.rules = cfg.prefs[preference_key]
		self.parent = parent

		columns = (
			(self.item_label, self.item_label, 100, tk.W),
			("Color", "Color", 100, tk.W),
			("Patterns", "Patterns", 300, tk.W),
		)
		frame, self.tree = self.create_treeview(columns)
		frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
		self._populate_tree()

		button_frame = self.create_button_bar(
			left_buttons=(
				("Add", self._add_rule),
				("Edit", self._edit_rule),
				("Delete", self._delete_rule),
			),
			right_buttons=(("Save", self._save_rules),),
		)
		button_frame.pack(fill=tk.X, padx=10, pady=5)

	def _populate_tree(self) -> None:
		self.tree.delete(*self.tree.get_children())
		for rule_name, info in self.rules.items():
			patterns = ", ".join(info.get("patterns", []))
			color = info.get("color", "")
			self.tree.insert("", tk.END, values=(rule_name, color, patterns))

	def _add_rule(self) -> None:
		self._edit_tag_dialog()

	def _edit_rule(self) -> None:
		selected = self.tree.selection()
		if not selected:
			return
		values = self.tree.item(selected, "values")
		self._edit_tag_dialog(values)

	def _delete_rule(self) -> None:
		selected = self.tree.selection()
		if not selected:
			return
		rule_name = self.tree.item(selected, "values")[0]
		if rule_name in self.rules:
			del self.rules[rule_name]
		self._populate_tree()

	def _save_rules(self) -> None:
		self.cfg.prefs[self.preference_key] = self.rules
		self.cfg.save()
		self.destroy()

	def _edit_tag_dialog(self, values=None) -> None:
		dialog = self.create_modal(f"Edit {self.item_label}", "400x260")
		rule_entry = self.create_labeled_entry(
			dialog,
			label_text=f"{self.item_label}:",
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
			rule_name = rule_entry.get().strip()
			color = color_entry.get().strip()
			patterns = [pattern.strip() for pattern in patterns_entry.get().split(",") if pattern.strip()]
			if rule_name:
				self.rules[rule_name] = {"color": color, "patterns": patterns}
				self._populate_tree()
			dialog.destroy()

		self.add_button(text="Save", command=save, master=dialog).pack(pady=10)


class TagsUI(PatternRulesUI):
	"""
	UI for editing tag rules in preferences.
	"""

	@beartype
	def __init__(
		self,
		cfg: LieutenantTerraformConfig,
		parent: tk.Misc | None = None,
		title: str = "Edit Tags",
		geometry: str = "600x400",
	) -> None:
		super().__init__(
			cfg,
			preference_key="line_tags",
			item_label="Tag",
			parent=parent,
			title=title,
			geometry=geometry,
		)