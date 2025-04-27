"""
Description: Class for managing Tkinter child windows with a debug function.
"""
import tkinter as tk
from tkinter import ttk
from beartype import beartype
from modules.config import LieutenantTerraformConfig


class ChildWindow:
	"""
	Class for managing Tkinter child windows.
	Includes a debug function to display a text area with an OK button.
	"""

	@beartype
	def __init__(self, cfg: LieutenantTerraformConfig, title: str, geometry: str = "600x400") -> None:
		"""
		Initialize the child window.

		Args:
			config (LieutenantTerraformConfig): Configuration object for the application.
			title (str): Title of the Tkinter window.
			geometry (str): Geometry of the Tkinter window (e.g., "600x400"). Defaults to "600x400".
		"""
		self.cfg = cfg
		self.window = tk.Toplevel()
		self.window.title(title)
		self.window.geometry(geometry)
		self.window.resizable(True, True)

		# Call the private build UI function
		self.__build_ui()

	@beartype
	def add_button(self, text: str, command, master=None) -> ttk.Button:
		"""
		Add a button to the specified master widget and return the button.

		Args:
			text (str): The text to display on the button.
			command (function): The function to execute when the button is clicked.
			master: The parent widget where the button will be placed. Defaults to self.window.

		Returns:
			ttk.Button: The created button.
		"""
		if master is None:
			master = self.window  # Default to self.window if no master is provided

		button = ttk.Button(master, text=text, command=command)
		return button

	@beartype
	def debug(self, debug_text: str) -> None:
		"""
		Open a debug window with a text area and an OK button.

		Args:
			debug_text (str): The text to display in the debug window.
		"""
		debug_window = tk.Toplevel(self.window)
		debug_window.title("Debug")
		debug_window.geometry("500x400")
		debug_window.transient(self.window)
		debug_window.grab_set()

		# Text area for displaying debug information
		text_area = tk.Text(debug_window, wrap=tk.WORD)
		text_area.insert(tk.END, debug_text)
		text_area.config(state=tk.DISABLED)  # Make the text area read-only
		text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

		# OK button to close the debug window
		ok_button = ttk.Button(debug_window, text="OK", command=debug_window.destroy)
		ok_button.pack(pady=10)

	@beartype
	def __build_ui(self) -> None:
		"""
		Description: Build the child window UI.
		"""
