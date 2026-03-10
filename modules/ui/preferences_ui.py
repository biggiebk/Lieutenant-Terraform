"""
Description: Preferences UI for managing configuration settings
"""
import tkinter as tk
from beartype import beartype
from modules.config import LieutenantTerraformConfig
from modules.ui.child_window import ChildWindow


class PreferencesUI(ChildWindow):
	"""
	Description: Class for displaying and managing configuration settings
	"""

	@beartype
	def __init__(self, config: LieutenantTerraformConfig, preferences: str) -> None:
		"""
		Initialize the Preferences UI.

		Args:
			config (LieutenantTerraformConfig): Configuration object for the application.
			preferences (str): The preferences category to display (e.g., "settings", "cmds").
		"""
		super().__init__(config, title=preferences.capitalize(), geometry="400x300")

		# Create a dictionary to store input fields for settings
		self.preferences = preferences
		self.entries = {}

		# Customize scrollbar styles
		self.configure_scrollbar_style()

		# Build the UI
		self.__build_ui()

	def __build_ui(self):
		"""
		Description: Build the preferences UI
		"""
		# Configure the window grid to allocate space for the container and button frame
		self.grid_rowconfigure(0, weight=1)  # Row for the container
		self.grid_rowconfigure(1, weight=0)  # Row for the button frame
		self.grid_columnconfigure(0, weight=1)

		# Create a frame for the settings with scrollbars
		container, _canvas, scrollable_frame, _scrollbar_v, _scrollbar_h = self.create_scrollable_frame(
			self,
			padding=0,
			canvas_kwargs={"highlightthickness": 0},
		)
		container.grid(column=0, row=0, sticky="nsew")  # Place in row 0

		# Add labels and widgets for each configuration setting
		row = 0
		for key, value in self.cfg.prefs[self.preferences].items():
			self.entries[key] = self.create_preference_field(scrollable_frame, row, key, value)
			row += 1

		# Add Save and Cancel buttons using the add_button function
		button_frame = self.create_frame(self, padding="10")
		button_frame.grid(column=0, row=1, sticky="ew")  # Place in row 1

		# Configure the button_frame to center its contents
		button_frame.grid_columnconfigure(0, weight=1)  # Center the first column
		button_frame.grid_columnconfigure(1, weight=1)  # Center the second column

		# Use add_button to add Save and Cancel buttons to the button_frame
		save_button = self.create_button(button_frame, text="Save", command=self.__save_settings)
		save_button.grid(column=0, row=0, padx=5, pady=5, sticky="e")  # Align to the right

		cancel_button = self.create_button(button_frame, text="Cancel", command=self.destroy)
		cancel_button.grid(column=1, row=0, padx=5, pady=5, sticky="w")  # Align to the left

	def __save_settings(self):
		"""
		Description: Save the updated settings
		"""
		for key, entry in self.entries.items():
			if isinstance(entry, tk.BooleanVar):
				# Handle boolean values from checkboxes
				self.cfg.prefs[self.preferences][key] = entry.get()
			else:
				# Handle string values from entry widgets
				self.cfg.prefs[self.preferences][key] = entry.get()
		self.cfg.save()  # Assuming the config class has a save method
		self.destroy()
