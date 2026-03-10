"""
Description: Class for managing a Tkinter window to edit aliases in preferences.
"""
import tkinter as tk

from beartype import beartype

from modules.config import LieutenantTerraformConfig
from modules.ui.child_window import ChildWindow


class AliasesUI(ChildWindow):
	"""
	Class for managing a Tkinter window to edit the aliases in preferences.
	"""

	@beartype
	def __init__(
		self,
		cfg: LieutenantTerraformConfig,
		title: str = "Edit Aliases",
		geometry: str = "800x600",
		parent: tk.Misc | None = None,
	) -> None:
		"""
		Initialize the edit aliases window.

		Args:
			cfg (LieutenantTerraformConfig): Configuration object for the application.
			title (str): Title of the Tkinter window. Defaults to "Edit Aliases".
			geometry (str): Geometry of the Tkinter window (e.g., "800x600"). Defaults to "800x600".
			parent (tk.Misc | None): Optional parent widget for the child window.
		"""
		super().__init__(cfg, title, geometry, parent=parent)
		self.aliases = cfg.prefs["aliases"]
		self.__build_aliases_ui()

	@beartype
	def __build_aliases_ui(self) -> None:
		"""
		Build the UI for editing aliases.
		"""
		columns = (
			("Alias", "Alias", 100, tk.W),
			("Exit On Done", "Exit On Done", 60, tk.CENTER),
			("Pipeline", "Pipeline", 600, tk.W),
		)
		frame, self.tree = self.create_treeview(columns)
		frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

		self.__populate_tree()
		self.tree.bind("<Double-1>", self.__on_tree_double_click)

		button_frame = self.create_button_bar(
			left_buttons=(
				("Add", self.__add_alias),
				("Edit", self.__edit_alias),
				("Delete", self.__delete_alias),
			),
			right_buttons=(("Save", self.__save_aliases),),
		)
		button_frame.pack(fill=tk.X, padx=10, pady=10)

	def __populate_tree(self) -> None:
		"""
		Populate the treeview with alias data.
		"""
		self.tree.delete(*self.tree.get_children())
		for alias, alias_data in self.aliases.items():
			exit_on_done = alias_data.get("exit_on_done", False)
			pipeline = alias_data.get("pipeline", [])
			self.tree.insert(
				"",
				tk.END,
				values=(alias, str(exit_on_done), self.__format_pipeline(pipeline)),
			)

	@staticmethod
	def __format_pipeline(pipeline: list[dict[str, str]]) -> str:
		"""
		Format a pipeline list for display in the treeview.
		"""
		return ", ".join(
			f"{list(command.keys())[0]} ({list(command.values())[0]})"
			for command in pipeline
		)

	@beartype
	def __on_tree_double_click(self, _event) -> None:
		"""
		Handle double-click event on the Treeview to open the alias editor.
		"""
		selected_item = self.tree.selection()
		if selected_item:
			values = self.tree.item(selected_item, "values")
			self.__open_alias_editor(values)

	@beartype
	def __add_alias(self) -> None:
		"""
		Add a new alias.
		"""
		self.__open_alias_editor()

	@beartype
	def __edit_alias(self) -> None:
		"""
		Edit the selected alias.
		"""
		selected_item = self.tree.selection()
		if selected_item:
			values = self.tree.item(selected_item, "values")
			self.__open_alias_editor(values)

	@beartype
	def __delete_alias(self) -> None:
		"""
		Delete the selected alias and save changes.
		"""
		selected_item = self.tree.selection()
		if selected_item:
			alias = self.tree.item(selected_item, "values")[0]
			self.tree.delete(selected_item)
			if alias in self.aliases:
				del self.aliases[alias]
			self.__save_aliases()

	@beartype
	def __open_alias_editor(self, values=None) -> None:
		"""
		Open a dialog to edit or add an alias.

		Args:
			values (tuple): The current values of the alias (alias, exit_on_done, pipeline). Defaults to None.
		"""
		editor = self.create_modal("Edit Alias", "500x400")

		exit_on_done_var = tk.BooleanVar(value=False)
		alias_entry = self.create_labeled_entry(
			editor,
			label_text="Alias:",
			width=50,
			value=values[0] if values else "",
		)
		if values:
			exit_on_done_var.set(values[1] == "True")

		self.create_checkbutton(editor, text="Exit On Done", variable=exit_on_done_var)

		commands_frame = self.create_frame(editor)
		commands_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

		headers_frame = self.create_frame(commands_frame)
		headers_frame.pack(fill=tk.X, pady=5)
		self.create_label(headers_frame, text="Command", width=40, anchor=tk.W).pack(side=tk.LEFT, padx=5)
		self.create_label(headers_frame, text="On Error", width=20, anchor=tk.W).pack(side=tk.LEFT, padx=5)

		command_widgets: list[tuple[tk.StringVar, tk.StringVar]] = []

		if values:
			pipeline = values[2].split(", ") if len(values) > 2 else []
			for command in pipeline:
				command_name, enable_state = self.__parse_command(command)
				command_var = tk.StringVar(value=command_name)
				enabled_var = tk.StringVar(value=enable_state)
				self.create_entry_dropdown_row(
					commands_frame,
					entry_var=command_var,
					dropdown_var=enabled_var,
					dropdown_values=["continue", "halt", "prompt"],
				)
				command_widgets.append((command_var, enabled_var))

		def add_command_row() -> None:
			command_var = tk.StringVar()
			enabled_var = tk.StringVar(value="continue")
			self.create_entry_dropdown_row(
				commands_frame,
				entry_var=command_var,
				dropdown_var=enabled_var,
				dropdown_values=["continue", "halt", "prompt"],
			)
			command_widgets.append((command_var, enabled_var))

		self.add_button(text="Add Command", command=add_command_row, master=editor).pack(pady=5)

		def save() -> None:
			alias = alias_entry.get()
			exit_on_done = exit_on_done_var.get()
			pipeline = []
			for command_var, enabled_var in command_widgets:
				command = command_var.get()
				enable_state = enabled_var.get()
				if command:
					pipeline.append({command: enable_state})

			if values:
				selected_item = self.tree.selection()
				self.tree.item(
					selected_item,
					values=(alias, str(exit_on_done), self.__format_pipeline(pipeline)),
				)
			else:
				self.tree.insert(
					"",
					tk.END,
					values=(alias, str(exit_on_done), self.__format_pipeline(pipeline)),
				)

			self.aliases[alias] = {
				"exit_on_done": exit_on_done,
				"pipeline": pipeline,
			}

			editor.destroy()

		self.add_button(text="Save", command=save, master=editor).pack(pady=10)

	@beartype
	def __parse_command(self, command: str) -> tuple[str, str]:
		"""
		Parse a command string into its name and enable state.
		"""
		if "(" in command and ")" in command:
			command_name, enable_state = command.rsplit("(", 1)
			return command_name.strip(), enable_state.strip(")")
		return command, "continue"

	@beartype
	def __save_aliases(self) -> None:
		"""
		Save the aliases back to the configuration.
		"""
		new_aliases = {}
		for item in self.tree.get_children():
			alias, exit_on_done, pipeline = self.tree.item(item, "values")
			pipeline_list = []
			for command_text in pipeline.split(", "):
				if "(" in command_text and ")" in command_text:
					command_name, enable_state = command_text.rsplit("(", 1)
					pipeline_list.append({command_name.strip(): enable_state.strip(")")})
				else:
					pipeline_list.append({command_text.strip(): "continue"})
			new_aliases[alias] = {
				"exit_on_done": exit_on_done == "True",
				"pipeline": pipeline_list,
			}
		self.cfg.update({"aliases": new_aliases}, save_config=True)
