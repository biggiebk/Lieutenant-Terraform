"""
Description: Preferences UI for managing configuration settings
"""
import tkinter as tk
from tkinter import ttk
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
		self.__configure_scrollbar_style()

		# Build the UI
		self.__build_ui()

	def __configure_scrollbar_style(self):
		"""
		Configure the style of the scrollbars to make them more visible.
		"""
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

	def __build_ui(self):
		"""
		Description: Build the preferences UI
		"""
		# Configure the window grid to allocate space for the container and button frame
		self.window.grid_rowconfigure(0, weight=1)  # Row for the container
		self.window.grid_rowconfigure(1, weight=0)  # Row for the button frame
		self.window.grid_columnconfigure(0, weight=1)

		# Create a frame for the settings with scrollbars
		container = ttk.Frame(self.window)
		container.grid(column=0, row=0, sticky="nsew")  # Place in row 0
		container.grid_rowconfigure(0, weight=1)  # Allow the canvas to expand
		container.grid_columnconfigure(0, weight=1)

		canvas = tk.Canvas(container, highlightthickness=0)  # Remove the border
		scrollbar_v = ttk.Scrollbar(
			container, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar"
		)
		scrollbar_h = ttk.Scrollbar(
			container, orient="horizontal", command=canvas.xview, style="Horizontal.TScrollbar"
		)

		scrollable_frame = ttk.Frame(canvas, padding=0)  # Ensure no padding is applied

		# Configure the canvas and scrollbars
		scrollable_frame.bind(
			"<Configure>",
			lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
		)
		canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

		# Place the canvas and scrollbars in the container
		canvas.grid(column=0, row=0, sticky="nsew")
		scrollbar_v.grid(column=1, row=0, sticky="ns")
		scrollbar_h.grid(column=0, row=1, sticky="ew")

		# Configure the canvas to expand with the window
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)

		# Add labels and widgets for each configuration setting
		row = 0
		for key, value in self.cfg.prefs[self.preferences].items():
			label = ttk.Label(scrollable_frame, text=key)
			label.grid(column=0, row=row, sticky="w", padx=5, pady=5)

			if isinstance(value, bool):
				# Display a checkbox for boolean values
				var = tk.BooleanVar(value=value)
				checkbox = ttk.Checkbutton(scrollable_frame, variable=var)
				checkbox.grid(column=1, row=row, sticky="w", padx=5, pady=5)
				self.entries[key] = var
			else:
				# Display an entry widget for other types
				entry = ttk.Entry(scrollable_frame)
				entry.insert(0, str(value))
				entry.grid(column=1, row=row, sticky="ew", padx=5, pady=5)
				self.entries[key] = entry

			row += 1

		# Add Save and Cancel buttons using the add_button function
		button_frame = ttk.Frame(self.window, padding="10")
		button_frame.grid(column=0, row=1, sticky="ew")  # Place in row 1

		# Configure the button_frame to center its contents
		button_frame.grid_columnconfigure(0, weight=1)  # Center the first column
		button_frame.grid_columnconfigure(1, weight=1)  # Center the second column

		# Use add_button to add Save and Cancel buttons to the button_frame
		save_button = self.add_button(master=button_frame, text="Save", command=self.__save_settings)
		save_button.grid(column=0, row=0, padx=5, pady=5, sticky="e")  # Align to the right

		cancel_button = self.add_button(master=button_frame, text="Cancel", command=self.window.destroy)
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
		self.window.destroy()
