"""
Description: Class for managing a Tkinter window to edit aliases in preferences.
"""
import tkinter as tk
from tkinter import ttk
from beartype import beartype
from modules.ui.child_window import ChildWindow
from modules.config import LieutenantTerraformConfig


class AliasesUI(ChildWindow):
	"""
	Class for managing a Tkinter window to edit the aliases in preferences.
	"""

	@beartype
	def __init__(
		self,
		cfg: LieutenantTerraformConfig,
		title: str = "Edit Aliases",
		geometry: str = "800x600"
	) -> None:
		"""
		Initialize the edit aliases window.

		Args:
			cfg (LieutenantTerraformConfig): Configuration object for the application.
			title (str): Title of the Tkinter window. Defaults to "Edit Aliases".
			geometry (str): Geometry of the Tkinter window (e.g., "800x600"). Defaults to "800x600".
		"""
		super().__init__(cfg, title, geometry)
		self.aliases = cfg.prefs['aliases']
		self.__build_aliases_ui()

	@beartype
	def __build_aliases_ui(self) -> None:
		"""
		Build the UI for editing aliases.
		"""
		# Create a frame for the aliases
		frame = ttk.Frame(self.window)
		frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

		# Add a treeview to display aliases
		self.tree = ttk.Treeview(frame, columns=("Alias", "Commands"), show="headings")
		self.tree.heading("Alias", text="Alias")
		self.tree.heading("Commands", text="Commands")
		self.tree.column("Alias", width=100, anchor=tk.W)
		self.tree.column("Commands", width=600, anchor=tk.W)
		self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

		# Populate the treeview with aliases
		for alias, commands in self.aliases.items():
			command_list = ", ".join([
				f"{list(cmd.keys())[0]} ({list(cmd.values())[0]})"
				for cmd in commands
			])
			self.tree.insert("", tk.END, values=(alias, command_list))

		# Add a scrollbar
		scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
		self.tree.configure(yscrollcommand=scrollbar.set)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

		# Bind double-click event to open alias editor
		self.tree.bind("<Double-1>", self.__on_tree_double_click)

		# Add buttons for editing
		button_frame = ttk.Frame(self.window)
		button_frame.pack(fill=tk.X, padx=10, pady=10)

		add_button = ttk.Button(button_frame, text="Add", command=self.__add_alias)
		add_button.pack(side=tk.LEFT, padx=5)

		edit_button = ttk.Button(button_frame, text="Edit", command=self.__edit_alias)
		edit_button.pack(side=tk.LEFT, padx=5)

		delete_button = ttk.Button(button_frame, text="Delete", command=self.__delete_alias)
		delete_button.pack(side=tk.LEFT, padx=5)

		save_button = ttk.Button(button_frame, text="Save", command=self.__save_aliases)
		save_button.pack(side=tk.RIGHT, padx=5)

	@beartype
	def __on_tree_double_click(self, event) -> None:
		"""
		Handle double-click event on the Treeview to open the alias editor.

		Args:
			event: The event object.
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
		Delete the selected alias.
		"""
		selected_item = self.tree.selection()
		if selected_item:
			self.tree.delete(selected_item)

	@beartype
	def __open_alias_editor(self, values=None) -> None:
		"""
		Open a dialog to edit or add an alias.

		Args:
			values (tuple): The current values of the alias (alias, commands). Defaults to None.
		"""
		editor = tk.Toplevel(self.window)
		editor.title("Edit Alias")
		editor.geometry("500x400")
		editor.transient(self.window)
		editor.grab_set()

		# Alias entry
		ttk.Label(editor, text="Alias:").pack(pady=5)
		alias_entry = ttk.Entry(editor, width=50)
		alias_entry.pack(pady=5)
		if values:
			alias_entry.insert(0, values[0])

		# Commands frame
		commands_frame = ttk.Frame(editor)
		commands_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

		# Add headers for the commands and enable columns
		headers_frame = ttk.Frame(commands_frame)
		headers_frame.pack(fill=tk.X, pady=5)
		ttk.Label(headers_frame, text="Command", width=40, anchor=tk.W).pack(side=tk.LEFT, padx=5)
		ttk.Label(headers_frame, text="On Error", width=20, anchor=tk.W).pack(side=tk.LEFT, padx=5)

		command_widgets = []

		# Populate commands if editing an existing alias
		if values:
			commands = values[1].split(", ")
			for command in commands:
				command_name, enable_state = self.__parse_command(command)
				command_var = tk.StringVar(value=command_name)
				enabled_var = tk.StringVar(value=enable_state)
				self.__create_command_row(commands_frame, command_var, enabled_var)
				command_widgets.append((command_var, enabled_var))

		# Add button to add new command rows
		def add_command_row():
			command_var = tk.StringVar()
			enabled_var = tk.StringVar(value="continue")  # Default to "continue"
			self.__create_command_row(commands_frame, command_var, enabled_var)
			command_widgets.append((command_var, enabled_var))

		add_command_button = ttk.Button(editor, text="Add Command", command=add_command_row)
		add_command_button.pack(pady=5)

		# Save button
		def save():
			alias = alias_entry.get()
			commands = []
			for command_var, enabled_var in command_widgets:
				command = command_var.get()
				enable_state = enabled_var.get()
				if command:
					commands.append({command: enable_state})

			# Update the Treeview with the new or edited alias
			if values:
				# Update existing alias
				selected_item = self.tree.selection()
				self.tree.item(
					selected_item,
					values=(
						alias,
						", ".join([
							f"{list(cmd.keys())[0]} ({list(cmd.values())[0]})"
							for cmd in commands
						])
					)
				)
			else:
				# Add new alias
				self.tree.insert(
					"",
					tk.END,
					values=(
						alias,
						", ".join([
							f"{list(cmd.keys())[0]} ({list(cmd.values())[0]})"
							for cmd in commands
						])
					)
				)

			# Update the internal aliases dictionary
			self.aliases[alias] = commands

			# Close the editor window
			editor.destroy()

		save_button = ttk.Button(editor, text="Save", command=save)
		save_button.pack(pady=10)

	@beartype
	def __create_command_row(self, parent, command_var, enabled_var) -> None:
		"""
		Create a single row for a command with an Entry widget and a dropdown.

		Args:
			parent: The parent widget where the row will be added.
			command_var (tk.StringVar): The variable for the command Entry widget.
			enabled_var (tk.StringVar): The variable for the dropdown menu.

		Returns:
			None
		"""
		row_frame = ttk.Frame(parent)
		row_frame.pack(fill=tk.X, pady=2)

		command_entry = ttk.Entry(row_frame, textvariable=command_var, width=40)
		command_entry.pack(side=tk.LEFT, padx=5)

		enabled_dropdown = ttk.Combobox(
			row_frame,
			textvariable=enabled_var,
			values=["continue", "halt", "prompt"],
			state="readonly",
			width=15
		)
		enabled_dropdown.pack(side=tk.LEFT, padx=5)

	@beartype
	def __parse_command(self, command: str) -> tuple:
		"""
		Parse a command string into its name and enable state.

		Args:
			command (str): The command string in the format "command (state)".

		Returns:
			tuple: A tuple containing the command name and enable state.
		"""
		if "(" in command and ")" in command:
			command_name, enable_state = command.rsplit("(", 1)
			return command_name.strip(), enable_state.strip(")")
		return command, "continue"  # Default to "continue" if no state is provided

	@beartype
	def __save_aliases(self) -> None:
		"""
		Save the aliases back to the configuration.
		"""
		new_aliases = {}
		for item in self.tree.get_children():
			alias, commands = self.tree.item(item, "values")
			command_list = []
			for cmd in commands.split(", "):
				if "(" in cmd and ")" in cmd:
					command_name, enable_state = cmd.rsplit("(", 1)
					command_list.append(
						{command_name.strip(): enable_state.strip(")")}
					)
				else:
					command_list.append(
						{cmd.strip(): "continue"}
					)  # Default to "continue" if no state is provided
			new_aliases[alias] = command_list
		self.cfg.update({"aliases": new_aliases}, save_config=True)
