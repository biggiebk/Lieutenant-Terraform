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
		self.tag_item_lines = {}

		# Load the main UI
		self.__load_main(arguments)

	@beartype
	def __load_main(self, cmd: list) -> None:
		"""
		Set up the main UI, including the menu, text area, scrollbars, and search bar.

		Args:
			cmd (list): Command to execute in the text area.
		"""
		# Configure the menu bar with preferences
		menubar = self.create_menu(self.tkr)
		preferences = self.create_menu(menubar)
		menubar.add_cascade(label="Preferences", menu=preferences)
		preferences.add_command(label="Settings", command=lambda: PreferencesUI(self.cfg, "settings"))
		preferences.add_command(label="Commands", command=lambda: PreferencesUI(self.cfg, "cmds"))
		preferences.add_command(label="Aliases", command=lambda: AliasesUI(self.cfg))
		preferences.add_command(label="Tags", command=lambda: TagsUI(self.cfg, parent=self.tkr))

		# Add word wrap toggle to the menu bar
		self.word_wrap_var = tk.BooleanVar(value=False)
		view_menu = self.create_menu(menubar)
		view_menu.add_checkbutton(
			label="Word Wrap",
			variable=self.word_wrap_var,
			command=self.__toggle_word_wrap
		)
		menubar.add_cascade(label="View", menu=view_menu)

		# Add Run drop down menu for aliases
		run_menu = self.create_menu(menubar)
		self.run_alias_var = tk.StringVar()
		alias_names = list(self.cfg.prefs.get("aliases", {}).keys())
		for alias in alias_names:
			run_menu.add_radiobutton(
				label=alias,
				variable=self.run_alias_var,
				value=alias,
				command=lambda: self.__run_selected_alias()
			)
		menubar.add_cascade(label="Run", menu=run_menu)

		self.tkr.configure(menu=menubar)
		self.tkr.grid_rowconfigure(0, weight=1)
		self.tkr.grid_columnconfigure(0, weight=1)

		main_pane = self.create_paned_window(
			self.tkr,
			orient=tk.HORIZONTAL,
		)
		main_pane.grid(column=0, row=0, sticky="nsew")

		output_frame = self.create_frame(main_pane)
		output_frame.grid_rowconfigure(0, weight=1)
		output_frame.grid_columnconfigure(0, weight=1)
		main_pane.add(output_frame, stretch="always", minsize=400)

		tag_sidebar = self.create_frame(main_pane)
		main_pane.add(tag_sidebar, minsize=180)

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
		tag_columns = (
			("Tag", "Tag", 100, tk.W),
			("Pattern", "Pattern", 200, tk.W),
		)
		self.__configure_tag_sidebar_style()
		tag_frame, self.tag_patterns_tree = self.create_treeview(tag_columns, master=tag_sidebar)
		self.tag_patterns_tree.configure(style="TagSidebar.Treeview")
		tag_frame.pack(fill=tk.BOTH, expand=True, padx=(5, 0), pady=2)
		self.tag_patterns_tree.bind("<<TreeviewSelect>>", self.__on_tag_pattern_selected)

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

		# Configure tags
		self.main_text_area.tag_configure("cmd", foreground="lightgray", font=("Arial", 10, "bold"))
		self.main_text_area.tag_configure("critical", foreground="red")
		self.main_text_area.tag_configure("good", foreground="green")
		self.main_text_area.tag_configure("info", foreground="blue")
		self.main_text_area.tag_configure("warn", foreground="orange")

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
		search_frame = self.create_frame(self.tkr)
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
		navigation_frame = self.create_frame(self.tkr)
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

	def __configure_tag_sidebar_style(self) -> None:
		"""
		Configure a dedicated style for the tag sidebar treeview.
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
	def __on_tag_pattern_selected(self, _event) -> None:
		"""
		Use the selected tag sidebar pattern as the current search.
		"""
		selected_item = self.tag_patterns_tree.selection()
		if not selected_item:
			return

		item_id = selected_item[0]
		_tag_name, pattern = self.tag_patterns_tree.item(item_id, "values")
		self.search_entry.delete(0, tk.END)
		self.search_entry.insert(0, pattern)
		self.__find()
		self.__focus_match_for_line(self.tag_item_lines.get(item_id))

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
			# Only perform the search if a tag is not already applied
			if not tag and "tags" in self.cfg.prefs:
				for tag_name, tag_info in self.cfg.prefs["tags"].items():
					for pattern in tag_info.get("patterns", []):
						try:
							match = re.search(pattern, line, re.IGNORECASE)
							if match:
								applied_tag = tag_name
								# Insert into the tag_patterns_tree
								line_number = int(float(text_area.index(tk.END))) - 1
								item_id = self.tag_patterns_tree.insert(
									"", tk.END,
									values=(tag_name, pattern)
								)
								self.tag_item_lines[item_id] = line_number
								break
						except re.error:
							continue
					if applied_tag:
						break
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
			# Clear the tag_patterns_tree before each run
			self.tag_item_lines = {}
			for item in self.tag_patterns_tree.get_children():
				self.tag_patterns_tree.delete(item)
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
		Display an always-on-top popup when a run finishes.
		"""
		status_text = "completed successfully" if was_successful else "failed"
		title = "Run Complete" if was_successful else "Run Failed"
		message = f"Run for '{command}' {status_text}."
		self.create_popup(
			self.tkr,
			title=title,
			message=message,
			on_ok=self.__exit if exit_on_done and was_successful else None,
		)

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