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
from modules.cmd_pipeline import CommandPipeline


class LieutenantTerraform:
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
		self.tkr.title("Lieutenant Terraform")
		self.raw_output = ""
		self.tkr.geometry(self.cfg.prefs["settings"].get("Window geometry", "800x600"))
		self.tkr.protocol("WM_DELETE_WINDOW", self.__exit)
		self.output = tk.StringVar()

		self.thread = None

		# Search-related variables
		self.search_results = []
		self.current_match_index = -1

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
		menubar = tk.Menu(self.tkr)
		preferences = tk.Menu(menubar, tearoff=0)
		menubar.add_cascade(label="Preferences", menu=preferences)
		preferences.add_command(label="Settings", command=lambda: PreferencesUI(self.cfg, "settings"))
		preferences.add_command(label="Commands", command=lambda: PreferencesUI(self.cfg, "cmds"))
		preferences.add_command(label="Aliases", command=lambda: AliasesUI(self.cfg))
		preferences.add_command(label="Tags", command=lambda: TagsUI(self.cfg, parent=self.tkr))

		# Add word wrap toggle to the menu bar
		self.word_wrap_var = tk.BooleanVar(value=False)
		view_menu = tk.Menu(menubar, tearoff=0)
		view_menu.add_checkbutton(
			label="Word Wrap",
			variable=self.word_wrap_var,
			command=self.__toggle_word_wrap
		)
		menubar.add_cascade(label="View", menu=view_menu)

		# Add Run drop down menu for aliases
		run_menu = tk.Menu(menubar, tearoff=0)
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

		# Configure the text area for displaying output
		self.main_text_area = tk.Text(
			self.tkr,
			wrap=tk.NONE,
			highlightthickness=0,  # Remove white border when selected
			bd=0,  # Remove border
			relief="flat"  # Flat appearance
		)
		self.main_text_area.grid(column=0, row=0, columnspan=3, sticky="nesw")
		self.tkr.grid_rowconfigure(0, weight=1)
		self.tkr.grid_columnconfigure(0, weight=1)

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
		style = ttk.Style()
		style.configure(
			"Vertical.TScrollbar",
			background="lightgray",
			troughcolor="darkgray",
			bordercolor="black",
			arrowcolor="black",
		)
		style.configure(
			"Horizontal.TScrollbar",
			background="lightgray",
			troughcolor="darkgray",
			bordercolor="black",
			arrowcolor="black",
		)

		scroll_v = ttk.Scrollbar(
			self.tkr, orient="vertical", command=self.main_text_area.yview, style="Vertical.TScrollbar"
		)
		scroll_v.grid(column=3, row=0, sticky="ns")

		scroll_h = ttk.Scrollbar(
			self.tkr, orient="horizontal", command=self.main_text_area.xview, style="Horizontal.TScrollbar"
		)
		scroll_h.grid(column=0, row=1, columnspan=3, sticky="we")
		self.main_text_area.config(yscrollcommand=scroll_v.set, xscrollcommand=scroll_h.set)

		# Configure the search bar
		search_frame = ttk.Frame(self.tkr)
		search_frame.grid(column=0, row=2, columnspan=3, sticky="ew", pady=5)

		find_button = ttk.Button(search_frame, text="Find", command=self.__find)
		find_button.grid(column=0, row=0, padx=5)

		self.search_entry = ttk.Entry(search_frame)
		self.search_entry.grid(column=1, row=0, padx=5, sticky="ew")
		self.search_entry.bind("<Return>", lambda e: self.__find())
		search_frame.grid_columnconfigure(1, weight=1)

		# Add ignore case checkbox
		self.ignore_case_var = tk.BooleanVar(value=True)
		ignore_case_checkbox = ttk.Checkbutton(
			search_frame,
			text="Ignore Case",
			variable=self.ignore_case_var
		)
		ignore_case_checkbox.grid(column=2, row=0, padx=5)

		# Configure navigation controls for search results
		navigation_frame = ttk.Frame(self.tkr)
		navigation_frame.grid(column=0, row=3, columnspan=3, sticky="ew", pady=5)

		prev_button = ttk.Button(navigation_frame, text="<", command=self.__previous_match)
		prev_button.grid(column=0, row=0, padx=1)

		next_button = ttk.Button(navigation_frame, text=">", command=self.__next_match)
		next_button.grid(column=1, row=0, padx=1)

		self.search_status = ttk.Label(navigation_frame, foreground="darkgray", text="0/0 matches")
		self.search_status.grid(column=2, row=0, padx=5, sticky="w")

		# Add folder and branch labels to the navigation frame
		self.running_label = ttk.Label(
			navigation_frame,
			text="",
			anchor=tk.W,
			foreground="darkgray",
			font=("Arial", 10),
		)
		self.running_label.grid(column=3, row=0, padx=5, sticky="e")

		self.folder_label = ttk.Label(
			navigation_frame,
			text="",
			anchor=tk.W,
			foreground="darkgray",
			font=("Arial", 10),
		)
		self.folder_label.grid(column=4, row=0, padx=5, sticky="e")

		self.branch_label = ttk.Label(
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
							if re.search(pattern, line, re.IGNORECASE):
								applied_tag = tag_name
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
			CommandPipeline(cmd, self.__exit, output_callback, running_callback, config=self.cfg)
			running_callback("")


		self.thread = threading.Thread(target=run_pipeline, daemon=True)
		self.thread.start()

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