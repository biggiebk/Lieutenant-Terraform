"""
Description: Class for managing Tkinter child windows with shared widget helpers.
"""
from collections.abc import Callable
import tkinter as tk

from beartype import beartype

from modules.config import LieutenantTerraformConfig
from modules.ui.widget_mixin import ReusableWidgetMixin


class ChildWindow(ReusableWidgetMixin, tk.Toplevel):
	"""
	Class for managing Tkinter child windows.
	Includes shared helpers for buttons, dialogs, and tree widgets.
	"""

	@beartype
	def __init__(
		self,
		cfg: LieutenantTerraformConfig,
		title: str,
		geometry: str = "600x400",
		parent: tk.Misc | None = None,
	) -> None:
		"""
		Initialize the child window.

		Args:
			cfg (LieutenantTerraformConfig): Configuration object for the application.
			title (str): Title of the Tkinter window.
			geometry (str): Geometry of the Tkinter window (e.g., "600x400"). Defaults to "600x400".
			parent (tk.Misc | None): Optional parent widget for the child window.
		"""
		super().__init__(master=parent)
		self.cfg = cfg
		self.window = self
		self.content_frame = self
		self.configure_theme(self)
		self.title(title)
		self.geometry(geometry)
		self.position_window_below_cursor(self)
		self.resizable(True, True)
		self.apply_native_window_theme(self)
		if self.use_custom_windows_chrome():
			self.overrideredirect(True)
			self.grid_rowconfigure(1, weight=1)
			self.grid_columnconfigure(0, weight=1)
			self.title_bar = self.create_custom_title_bar(self, title, self.destroy)
			self.title_bar.grid(column=0, row=0, sticky="ew")
			self.content_frame = self.create_frame(self)
			self.content_frame.grid(column=0, row=1, sticky="nsew")
			self.content_frame.grid_rowconfigure(0, weight=1)
			self.content_frame.grid_columnconfigure(0, weight=1)
			self.create_resize_borders(self)
			resize_handle = self.create_resize_handle(self, self)
			resize_handle.grid(column=0, row=2, sticky="se", padx=4, pady=2)

	@beartype
	def add_button(
		self,
		text: str,
		command: Callable[..., object],
		master: tk.Misc | None = None,
	):
		"""
		Add a button to the specified master widget and return the button.

		Args:
			text (str): The text to display on the button.
			command (Callable[..., object]): The function to execute when the button is clicked.
			master (tk.Misc | None): The parent widget where the button will be placed. Defaults to self.

		Returns:
			ttk.Button: The created button.
		"""
		button_master = master or self._resolve_master(None)
		return self.create_button(button_master, text=text, command=command)

	def create_modal(self, title: str, geometry: str) -> tk.Toplevel:
		"""
		Create a modal dialog tied to this child window.

		Args:
			title (str): Title of the dialog window.
			geometry (str): Geometry of the dialog window.

		Returns:
			tk.Toplevel: The created modal dialog.
		"""
		dialog = tk.Toplevel(self)
		self.configure_theme(dialog)
		dialog.title(title)
		dialog.geometry(geometry)
		self.position_window_below_cursor(dialog)
		dialog.transient(self)
		dialog.grab_set()
		self.apply_native_window_theme(dialog)
		return dialog

	@beartype
	def debug(self, debug_text: str) -> None:
		"""
		Open a debug window with a text area and an OK button.

		Args:
			debug_text (str): The text to display in the debug window.
		"""
		debug_window = self.create_modal("Debug", "500x400")

		text_area = self.create_text_widget(debug_window, wrap=tk.WORD)
		text_area.insert(tk.END, debug_text)
		text_area.config(state=tk.DISABLED)
		text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

		self.add_button(text="OK", command=debug_window.destroy, master=debug_window).pack(pady=10)
