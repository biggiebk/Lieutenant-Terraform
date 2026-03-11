"""
Description: Main module for LT (Lieutenant Terraform)
"""
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk
import os
from beartype import beartype
from modules.config import LieutenantTerraformConfig
from modules.ui.highlights_ui import HighlightsUI
from modules.ui.aliases_ui import AliasesUI
from modules.ui.preferences_ui import PreferencesUI
from modules.ui.tags_ui import TagsUI
from modules.ui.widget_mixin import ReusableWidgetMixin
from modules.cmd_pipeline import CommandPipeline


class LieutenantTerraform(ReusableWidgetMixin):
	"""
	Main class for managing the Lieutenant Terraform application.
	Handles configuration, UI initialization, and command execution.
	"""

	@beartype
	def __init__(self, arguments: list) -> None:
		"""
		Initialize the application with configuration and UI setup.

		Args:
			arguments (list): Command-line arguments to execute.
		"""
		self.cfg = LieutenantTerraformConfig()
		self.tkr = tk.Tk()
		self.configure_theme(self.tkr)
		self.tkr.title("Lieutenant Terraform")
		self.raw_output = ""
		self.tkr.geometry(self.cfg.prefs["settings"].get("Window geometry", "800x600"))
		self.tkr.protocol("WM_DELETE_WINDOW", self.__exit)
		self.apply_native_window_theme(self.tkr)
		self.output = tk.StringVar()

		self.thread = None

		# Search-related variables
		self.search_results = []
		self.current_match_index = -1
		self.match_item_lines = {}
		self.match_pattern_items = {}
		self.match_pattern_counts = {}

		# Load the main UI
		self.__load_main(arguments)

	@beartype
	def __load_main(self, cmd: list) -> None:
		"""
		Set up the main UI, including the menu, text area, scrollbars, and search bar.

		Args:
			cmd (list): Command to execute in the text area.
		"""
		content_parent = self.tkr
		main_row = 0
		self.tkr.grid_columnconfigure(0, weight=1)

		if self.use_custom_windows_chrome():
			self.tkr.overrideredirect(True)
			self.enable_taskbar_icon_for_custom_window(self.tkr)
			self.tkr.grid_rowconfigure(2, weight=1)
			title_bar = self.create_custom_title_bar(self.tkr, "Lieutenant Terraform", self.__exit)
			title_bar.grid(column=0, row=0, sticky="ew")

			menu_bar = self.create_custom_menu_bar(self.tkr)
			menu_bar.grid(column=0, row=1, sticky="ew")
			content_parent = self.create_frame(self.tkr)
			content_parent.grid(column=0, row=2, sticky="nsew")
			resize_handle = self.create_resize_handle(self.tkr, self.tkr)
			resize_handle.grid(column=0, row=3, sticky="se", padx=4, pady=2)
			main_row = 0
		else:
			self.tkr.grid_rowconfigure(0, weight=1)
			menu_bar = self.create_menu(self.tkr)

		content_parent.grid_rowconfigure(0, weight=1)
		content_parent.grid_columnconfigure(0, weight=1)

		preferences = self.create_menu(menu_bar)
		preferences.add_command(label="Settings", command=lambda: PreferencesUI(self.cfg, "settings"))
		preferences.add_command(label="Commands", command=lambda: PreferencesUI(self.cfg, "cmds"))
		preferences.add_command(label="Aliases", command=lambda: AliasesUI(self.cfg))
		preferences.add_command(label="Highlights", command=lambda: HighlightsUI(self.cfg, parent=self.tkr))
		preferences.add_command(label="Tags", command=lambda: TagsUI(self.cfg, parent=self.tkr))

		self.word_wrap_var = tk.BooleanVar(value=False)
		view_menu = self.create_menu(menu_bar)
		view_menu.add_checkbutton(
			label="Word Wrap",
			variable=self.word_wrap_var,
			command=self.__toggle_word_wrap
		)

		run_menu = self.create_menu(menu_bar)
		self.run_alias_var = tk.StringVar()
		alias_names = list(self.cfg.prefs.get("aliases", {}).keys())
		for alias in alias_names:
			run_menu.add_radiobutton(
				label=alias,
				variable=self.run_alias_var,
				value=alias,
				command=lambda: self.__run_selected_alias()
			)

		if self.use_custom_windows_chrome():
			self.create_menu_button(menu_bar, text="Preferences", menu=preferences).pack(side=tk.LEFT)
			self.create_menu_button(menu_bar, text="View", menu=view_menu).pack(side=tk.LEFT)
			self.create_menu_button(menu_bar, text="Run", menu=run_menu).pack(side=tk.LEFT)
		else:
			menu_bar.add_cascade(label="Preferences", menu=preferences)
			menu_bar.add_cascade(label="View", menu=view_menu)
			menu_bar.add_cascade(label="Run", menu=run_menu)
			self.tkr.configure(menu=menu_bar)

		main_pane = self.create_paned_window(
			content_parent,
			orient=tk.HORIZONTAL,
		)
		main_pane.grid(column=0, row=main_row, sticky="nsew")

		output_frame = self.create_frame(main_pane)
		output_frame.grid_rowconfigure(0, weight=1)
		output_frame.grid_columnconfigure(0, weight=1)
		main_pane.add(output_frame, stretch="always", minsize=400)

		match_sidebar = self.create_frame(main_pane)
		main_pane.add(match_sidebar, minsize=180)

		# Configure the text area for displaying output
		self.main_text_area = self.create_text_widget(
			output_frame,
			wrap=tk.NONE,
			highlightthickness=0,  # Remove white border when selected
			bd=0,  # Remove border
			relief="flat"  # Flat appearance
		)
		self.main_text_area.grid(column=0, row=0, sticky="nsew")

		# Treeview for displaying matching tag patterns, to the right of main_text_area
		match_columns = (
			("Tag", "Tag", 100, tk.W),
			("Pattern", "Pattern", 180, tk.W),
			("Count", "Count", 60, tk.CENTER),
		)
		self.__configure_match_sidebar_style()
		match_frame, self.match_patterns_tree = self.create_treeview(match_columns, master=match_sidebar)
		self.match_patterns_tree.configure(style="TagSidebar.Treeview")
		match_frame.pack(fill=tk.BOTH, expand=True, padx=(5, 0), pady=2)
		self.match_patterns_tree.bind("<<TreeviewSelect>>", self.__on_pattern_selected)

		# Enable copy and paste in the text area
		def copy(event=None):
			self.main_text_area.event_generate("<<Copy>>")
			return "break"

		def paste(event=None):
			self.main_text_area.event_generate("<<Paste>>")
			return "break"

		def cut(event=None):
			self.main_text_area.event_generate("<<Cut>>")
			return "break"

		if sys.platform == "darwin":  # macOS
			self.main_text_area.bind("<Command-c>", copy)
			self.main_text_area.bind("<Command-x>", cut)
			self.main_text_area.bind("<Command-v>", paste)
		else:  # Others
			self.main_text_area.bind("<Control-c>", copy)
			self.main_text_area.bind("<Control-x>", cut)
			self.main_text_area.bind("<Control-v>", paste)

		# Configure highlight tags
		self.__configure_output_tags()

		# Configure scrollbars for the text area
		self.configure_scrollbar_style()

		scroll_v = self.create_scrollbar(
			output_frame, orient="vertical", command=self.main_text_area.yview, style="Vertical.TScrollbar"
		)
		scroll_v.grid(column=1, row=0, sticky="ns")

		scroll_h = self.create_scrollbar(
			output_frame, orient="horizontal", command=self.main_text_area.xview, style="Horizontal.TScrollbar"
		)
		scroll_h.grid(column=0, row=1, sticky="we")
		self.main_text_area.config(yscrollcommand=scroll_v.set, xscrollcommand=scroll_h.set)

		# Configure the search bar
		search_frame = self.create_frame(content_parent)
		search_frame.grid(column=0, row=1, sticky="ew", pady=5)

		find_button = self.create_button(search_frame, text="Find", command=self.__find)
		find_button.grid(column=0, row=0, padx=5)

		self.search_entry = self.create_entry(search_frame)
		self.search_entry.grid(column=1, row=0, padx=5, sticky="ew")
		self.search_entry.bind("<Return>", lambda e: self.__find())
		search_frame.grid_columnconfigure(1, weight=1)

		# Add ignore case checkbox
		self.ignore_case_var = tk.BooleanVar(value=True)
		ignore_case_checkbox = self.create_checkbutton(
			search_frame,
			text="Ignore Case",
			variable=self.ignore_case_var
		)
		ignore_case_checkbox.grid(column=2, row=0, padx=5)

		# Configure navigation controls for search results
		navigation_frame = self.create_frame(content_parent)
		navigation_frame.grid(column=0, row=2, sticky="ew", pady=5)

		prev_button = self.create_button(navigation_frame, text="<", command=self.__previous_match)
		prev_button.grid(column=0, row=0, padx=1)

		next_button = self.create_button(navigation_frame, text=">", command=self.__next_match)
		next_button.grid(column=1, row=0, padx=1)

		self.search_status = self.create_label(navigation_frame, foreground="darkgray", text="0/0 matches")
		self.search_status.grid(column=2, row=0, padx=5, sticky="w")

		# Add folder and branch labels to the navigation frame
		self.running_label = self.create_label(
			navigation_frame,
			text="",
			anchor=tk.W,
			foreground="darkgray",
			font=("Arial", 10),
		)
		self.running_label.grid(column=3, row=0, padx=5, sticky="e")

		self.folder_label = self.create_label(
			navigation_frame,
			text="",
			anchor=tk.W,
			foreground="darkgray",
			font=("Arial", 10),
		)
		self.folder_label.grid(column=4, row=0, padx=5, sticky="e")

		self.branch_label = self.create_label(
			navigation_frame,
			text="",
			anchor=tk.W,
			foreground="darkgray",
			font=("Arial", 10),
		)
		self.branch_label.grid(column=5, row=0, padx=5, sticky="e")

		# Configure column weights to align labels to the far right
		navigation_frame.grid_columnconfigure(0, weight=0)
		navigation_frame.grid_columnconfigure(1, weight=0)
		navigation_frame.grid_columnconfigure(2, weight=1)
		navigation_frame.grid_columnconfigure(3, weight=0)
		navigation_frame.grid_columnconfigure(4, weight=0)

		self.__update_status_bar()

		# Start the main loop and execute the command
		self.tkr.after(0, self.__run(cmd, self.main_text_area))
		self.tkr.mainloop()

	def __configure_match_sidebar_style(self) -> None:
		"""
		Configure a dedicated style for the match sidebar treeview.
		"""
		style = ttk.Style(self.tkr)
		style.configure(
			"TagSidebar.Treeview",
			background=self.THEME_BACKGROUND,
			fieldbackground=self.THEME_BACKGROUND,
			foreground=self.THEME_FOREGROUND,
			bordercolor=self.THEME_BORDER,
		)
		style.map(
			"TagSidebar.Treeview",
			background=[("selected", self.THEME_SELECTION)],
			foreground=[("selected", self.THEME_FOREGROUND)],
		)
		style.configure(
			"TagSidebar.Treeview.Heading",
			background=self.THEME_BACKGROUND,
			foreground=self.THEME_FOREGROUND,
			bordercolor=self.THEME_BORDER,
		)
		style.map(
			"TagSidebar.Treeview.Heading",
			background=[("active", self.THEME_BACKGROUND)],
			foreground=[("active", self.THEME_FOREGROUND)],
		)

	def __configure_output_tags(self) -> None:
		"""
		Configure output text tags from the highlight preferences.
		"""
		self.main_text_area.tag_configure("cmd", foreground="lightgray", font=("Arial", 10, "bold"))
		for highlight_name, highlight_info in self.cfg.prefs.get("highlights", {}).items():
			self.main_text_area.tag_configure(highlight_name, foreground=highlight_info.get("color", self.THEME_FOREGROUND))

	def __match_rule_group(self, preference_key: str, line: str) -> tuple[str | None, str | None]:
		"""
		Return the first configured rule name and pattern matching a line.
		"""
		for rule_name, rule_info in self.cfg.prefs.get(preference_key, {}).items():
			for pattern in rule_info.get("patterns", []):
				try:
					if re.search(pattern, line, re.IGNORECASE):
						return rule_name, pattern
				except re.error:
					continue
		return None, None

	def __record_sidebar_match(self, name: str, pattern: str, line_number: int) -> None:
		"""
		Record a matched tag in the sidebar with a running count.
		"""
		match_key = (name, pattern)
		count = self.match_pattern_counts.get(match_key, 0) + 1
		self.match_pattern_counts[match_key] = count
		item_id = self.match_pattern_items.get(match_key)
		if item_id is None:
			item_id = self.match_patterns_tree.insert(
				"",
				tk.END,
				values=(name, pattern, count),
			)
			self.match_pattern_items[match_key] = item_id
			self.match_item_lines[item_id] = line_number
		else:
			self.match_patterns_tree.item(item_id, values=(name, pattern, count))

	@beartype
	def __update_status_bar(self) -> None:
		"""
		Update the status bar with the parent folder name and Git branch (if applicable).
		"""
		# Get the parent folder name
		parent_folder = os.path.basename(os.getcwd())

		# Check if the current directory is a Git repository
		git_branch = ""
		try:
			git_branch = subprocess.check_output(
				["git", "rev-parse", "--abbrev-ref", "HEAD"],
				stderr=subprocess.DEVNULL,
				universal_newlines=True,
			).strip()
		except (subprocess.CalledProcessError, FileNotFoundError):
			git_branch = "Not a Git repo"

		# Update the labels
		self.running_label.config(text="")
		self.folder_label.config(text=parent_folder)
		self.branch_label.config(text=git_branch)

	@beartype
	def __find(self) -> None:
		"""
		Search for a pattern in the text area and highlight matches.
		"""
		pattern = self.search_entry.get()
		self.main_text_area.tag_remove("highlight", "1.0", tk.END)
		self.main_text_area.tag_remove("current_highlight", "1.0", tk.END)

		text = self.main_text_area.get("1.0", tk.END)
		flags = re.IGNORECASE if self.ignore_case_var.get() else 0
		self.search_results = []
		self.current_match_index = -1

		if not pattern:
			self.__update_search_status()
			return

		try:
			for match in re.finditer(pattern, text, flags):
				start_idx = f"1.0 + {match.start()}c"
				end_idx = f"1.0 + {match.end()}c"
				self.search_results.append((start_idx, end_idx))
				self.main_text_area.tag_add("highlight", start_idx, end_idx)
			self.main_text_area.tag_config("highlight", background="yellow", foreground="black")
			self.__next_match()
			self.__update_search_status()
		except re.error:
			self.search_status.config(text="Invalid regex")

	@beartype
	def __next_match(self) -> None:
		"""
		Navigate to the next match in the search results.
		"""
		if not self.search_results:
			return
		self.current_match_index = (self.current_match_index + 1) % len(self.search_results)
		self.__highlight_current_match()

	@beartype
	def __previous_match(self) -> None:
		"""
		Navigate to the previous match in the search results.
		"""
		if not self.search_results:
			return
		self.current_match_index = (self.current_match_index - 1) % len(self.search_results)
		self.__highlight_current_match()

	@beartype
	def __highlight_current_match(self) -> None:
		"""
		Highlight the currently selected match and scroll to it.
		"""
		if not self.search_results:
			return
		start, end = self.search_results[self.current_match_index]
		self.main_text_area.tag_remove("current_highlight", "1.0", tk.END)
		self.main_text_area.tag_add("current_highlight", start, end)
		self.main_text_area.tag_config("current_highlight", background="orange", foreground="black", selectbackground="orange", selectforeground="black")
		self.main_text_area.see(start)
		self.__update_search_status()

	@beartype
	def __on_pattern_selected(self, _event) -> None:
		"""
		Use the selected sidebar pattern as the current search.
		"""
		selected_item = self.match_patterns_tree.selection()
		if not selected_item:
			return

		item_id = selected_item[0]
		_tag_name, pattern, _count = self.match_patterns_tree.item(item_id, "values")
		self.search_entry.delete(0, tk.END)
		self.search_entry.insert(0, pattern)
		self.__find()
		self.__focus_match_for_line(self.match_item_lines.get(item_id))

	@beartype
	def __focus_match_for_line(self, line_number) -> None:
		"""
		Focus the search result that corresponds to a selected tag row line.
		"""
		if not self.search_results:
			return

		try:
			target_line = int(line_number)
		except (TypeError, ValueError):
			return

		for index, (start, _end) in enumerate(self.search_results):
			result_line = int(self.main_text_area.index(start).split(".")[0])
			if result_line == target_line:
				self.current_match_index = index
				self.__highlight_current_match()
				break

	@beartype
	def __update_search_status(self) -> None:
		"""
		Update the search status label with the current match index and total matches.
		"""
		total_matches = len(self.search_results)
		current_match = self.current_match_index + 1 if self.current_match_index >= 0 else 0
		self.search_status.config(text=f"{current_match}/{total_matches} matches")

	@beartype
	def __exit(self) -> None:
		"""
		Handle application exit, including saving configuration if enabled.
		"""
		try:
			if self.cfg.prefs["settings"]["Save window geometry on exit"]:
				self.cfg.prefs["settings"]["Window geometry"] = self.tkr.geometry()
				self.cfg.save()
		except KeyError as e:
			print(f"KeyError: Missing configuration key - {str(e)}")
		except IOError as e:
			print(f"IOError: Failed to save configuration - {str(e)}")
		finally:
			self.tkr.destroy()

	@beartype
	def __run(self, cmd: list, text_area: tk.Text) -> None:
		"""
		Execute a command and display its output in the text area.

		Args:
			cmd (list): Command to execute.
			text_area (tk.Text): Text area to display the command output.
		"""
		def output_callback(line: str, tag: str = None) -> None:
			"""
			Handle the output of the command by inserting it into the text area.

			Args:
				line (str): A line of output from the command.
			"""
			applied_tag = tag
			line_number = int(float(text_area.index(tk.END))) - 1

			highlight_name = None
			highlight_pattern = None
			if not tag:
				highlight_name, highlight_pattern = self.__match_rule_group("highlights", line)
				if highlight_name and highlight_pattern:
					applied_tag = highlight_name

			tag_name, tag_pattern = self.__match_rule_group("line_tags", line)
			if tag_name and tag_pattern:
				self.__record_sidebar_match(tag_name, tag_pattern, line_number)

			text_area.insert(tk.END, line, applied_tag)
			text_area.see(tk.END)
			self.raw_output += line
			if self.cfg.prefs["settings"]["Echo"]:
				print(line, end="")

		def running_callback(command: str) -> None:
			"""
			Handle the output of the command by inserting it into the text area.

			Args:
				line (str): A line of output from the command.
			"""
			self.running_label.config(text=command)

		def run_pipeline():
			# Clear the match sidebar before each run
			self.match_item_lines = {}
			self.match_pattern_items = {}
			self.match_pattern_counts = {}
			for item in self.match_patterns_tree.get_children():
				self.match_patterns_tree.delete(item)
			pipeline = CommandPipeline(cmd, self.__exit, output_callback, running_callback, config=self.cfg)
			running_callback("")
			self.tkr.after(
				0,
				lambda: self.__show_run_completion(
					pipeline.completed_command,
					pipeline.completed_successfully,
					pipeline.exit_on_done,
				),
			)

		self.thread = threading.Thread(target=run_pipeline, daemon=True)
		self.thread.start()

	def __show_run_completion(self, command: str, was_successful: bool, exit_on_done: bool = False) -> None:
		"""
		Bring the main window to the foreground when a run finishes.
		"""
		self.tkr.deiconify()
		self.tkr.lift()
		self.tkr.focus_force()
		self.tkr.attributes("-topmost", True)
		self.tkr.after(200, lambda: self.tkr.attributes("-topmost", False))
		if exit_on_done and was_successful:
			self.tkr.after(250, self.__exit)

	@beartype
	def __toggle_word_wrap(self) -> None:
		"""
		Toggle word wrap in the main text area.
		"""
		if self.word_wrap_var.get():
			self.main_text_area.config(wrap=tk.WORD)
		else:
			self.main_text_area.config(wrap=tk.NONE)

	def __run_selected_alias(self):
		"""
		Clear the main text area and run the selected alias from the Run menu.
		"""
		alias = self.run_alias_var.get()
		if alias:
			self.main_text_area.delete("1.0", tk.END)
			self.__run([alias], self.main_text_area)