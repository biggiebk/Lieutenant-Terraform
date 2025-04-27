"""
Description: Main module for LT (Lieutenant Terraform)
"""
import re
import tkinter as tk
from tkinter import ttk
from subprocess import Popen, PIPE, CalledProcessError
from beartype import beartype
from modules.config import LieutenantTerraformConfig
from modules.ui.preferences_ui import PreferencesUI


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
		preferences.add_command(label="Aliases", command=lambda: PreferencesUI(self.cfg, "aliases"))
		self.tkr.configure(menu=menubar)

		# Configure the text area for displaying output
		self.main_text_area = tk.Text(self.tkr, wrap=tk.NONE)
		self.main_text_area.grid(column=0, row=0, columnspan=3, sticky="nesw")
		self.tkr.grid_rowconfigure(0, weight=1)
		self.tkr.grid_columnconfigure(0, weight=1)

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

		# Configure navigation controls for search results
		navigation_frame = ttk.Frame(self.tkr)
		navigation_frame.grid(column=0, row=3, columnspan=3, sticky="ew", pady=5)

		prev_button = ttk.Button(navigation_frame, text="<", command=self.__previous_match)
		prev_button.grid(column=0, row=0, padx=1)

		next_button = ttk.Button(navigation_frame, text=">", command=self.__next_match)
		next_button.grid(column=1, row=0, padx=1)

		self.search_status = ttk.Label(navigation_frame, text="0/0 matches")
		self.search_status.grid(column=2, row=0, padx=5)

		navigation_frame.grid_columnconfigure(0, weight=0)
		navigation_frame.grid_columnconfigure(1, weight=0)
		navigation_frame.grid_columnconfigure(2, weight=0)
		navigation_frame.grid_columnconfigure(3, weight=0)

		# Add an exit button
		exit_button = ttk.Button(self.tkr, text="Exit", command=self.__exit)
		exit_button.grid(column=0, row=4, columnspan=3, pady=10)

		# Start the main loop and execute the command
		self.tkr.after(0, self.__run(cmd, self.main_text_area))
		self.tkr.mainloop()

	@beartype
	def __find(self) -> None:
		"""
		Search for a pattern in the text area and highlight matches.
		"""
		pattern = self.search_entry.get()
		self.main_text_area.tag_remove("highlight", "1.0", tk.END)
		self.main_text_area.tag_remove("current_highlight", "1.0", tk.END)
		self.search_results = []
		self.current_match_index = -1

		if not pattern:
			self.search_status.config(text="0/0 matches")
			return

		try:
			start = "1.0"
			while True:
				start = self.main_text_area.search(pattern, start, stopindex=tk.END, regexp=True)
				if not start:
					break
				end = f"{start}+{len(pattern)}c"
				self.search_results.append((start, end))
				self.main_text_area.tag_add("highlight", start, end)
				start = end
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
		self.main_text_area.tag_config("current_highlight", background="orange", foreground="black")
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
		except Exception as e:
			print(f"Error saving configuration: {str(e)}")
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
		try:
			with Popen(cmd, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
				for line in p.stdout:
					text_area.insert(tk.END, line)
					self.raw_output += line
					print(line, end="")
			if p.returncode != 0:
				raise CalledProcessError(p.returncode, p.args)
		except CalledProcessError as e:
			error_message = f"Error: Command '{e.cmd}' failed with return code {e.returncode}\n"
			text_area.insert(tk.END, error_message)
			print(error_message)
		except Exception as e:
			error_message = f"Unexpected error: {str(e)}\n"
			text_area.insert(tk.END, error_message)
			print(error_message)
