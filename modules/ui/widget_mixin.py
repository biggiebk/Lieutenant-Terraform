"""
Description: Reusable Tkinter widget factory helpers.
"""
from collections.abc import Callable, Sequence
import sys
import tkinter as tk
from tkinter import ttk


class ReusableWidgetMixin:
	"""
	Mixin providing reusable Tkinter and ttk widget helpers.
	"""

	THEME_BACKGROUND = "#141414"
	THEME_FOREGROUND = "#c0effe"
	THEME_SURFACE = "#223038"
	THEME_ACTIVE = "#2b3d45"
	THEME_BORDER = "#35525d"
	THEME_SELECTION = "#406a79"
	WINDOWS_DARK_MODE_ATTRIBUTE_IDS = (20, 19)
	WINDOWS_BORDER_COLOR_ATTRIBUTE_ID = 34
	WINDOWS_CAPTION_COLOR_ATTRIBUTE_ID = 35
	WINDOWS_TEXT_COLOR_ATTRIBUTE_ID = 36
	WINDOWS_GWL_EXSTYLE = -20
	WINDOWS_WS_EX_APPWINDOW = 0x00040000
	WINDOWS_WS_EX_TOOLWINDOW = 0x00000080
	WINDOWS_SWP_NOSIZE = 0x0001
	WINDOWS_SWP_NOMOVE = 0x0002
	WINDOWS_SWP_NOZORDER = 0x0004
	WINDOWS_SWP_NOACTIVATE = 0x0010
	WINDOWS_SWP_FRAMECHANGED = 0x0020
	WINDOW_MIN_WIDTH = 320
	WINDOW_MIN_HEIGHT = 220
	CURSOR_WINDOW_OFFSET_Y = 16
	WINDOW_SCREEN_MARGIN = 12

	def _resolve_master(self, master: tk.Misc | None) -> tk.Misc:
		"""
		Resolve a widget master, defaulting to the current window when available.
		"""
		if master is not None:
			return master
		content_frame = getattr(self, "content_frame", None)
		if content_frame is not None:
			return content_frame
		window = getattr(self, "window", None)
		if window is not None:
			return window
		if isinstance(self, tk.Misc):
			return self
		msg = "A master widget is required for this helper."
		raise ValueError(msg)

	def configure_theme(self, widget: tk.Misc) -> None:
		"""
		Configure the shared widget theme for a root or toplevel window.
		"""
		style = ttk.Style(widget)
		try:
			style.theme_use("clam")
		except tk.TclError:
			pass

		widget.configure(bg=self.THEME_BACKGROUND)
		widget.option_add("*Background", self.THEME_BACKGROUND)
		widget.option_add("*Foreground", self.THEME_FOREGROUND)
		widget.option_add("*Menu.background", self.THEME_BACKGROUND)
		widget.option_add("*Menu.foreground", self.THEME_FOREGROUND)
		widget.option_add("*Menu.activeBackground", self.THEME_ACTIVE)
		widget.option_add("*Menu.activeForeground", self.THEME_FOREGROUND)
		widget.option_add("*Menu.selectColor", self.THEME_FOREGROUND)
		widget.option_add("*Menu.disabledForeground", self.THEME_BORDER)
		widget.option_add("*Menu.relief", "flat")

		style.configure(
			".",
			background=self.THEME_BACKGROUND,
			foreground=self.THEME_FOREGROUND,
			fieldbackground=self.THEME_SURFACE,
			bordercolor=self.THEME_BORDER,
			lightcolor=self.THEME_BORDER,
			darkcolor=self.THEME_BORDER,
			troughcolor=self.THEME_BACKGROUND,
			arrowcolor=self.THEME_FOREGROUND,
		)
		style.configure("TFrame", background=self.THEME_BACKGROUND)
		style.configure("TLabel", background=self.THEME_BACKGROUND, foreground=self.THEME_FOREGROUND)
		style.configure(
			"TButton",
			background=self.THEME_BACKGROUND,
			foreground=self.THEME_FOREGROUND,
			bordercolor=self.THEME_BORDER,
			focuscolor=self.THEME_BORDER,
			padding=6,
		)
		style.map(
			"TButton",
			background=[("active", self.THEME_ACTIVE), ("pressed", self.THEME_SELECTION)],
			foreground=[("disabled", self.THEME_BORDER)],
		)
		style.configure(
			"TEntry",
			fieldbackground=self.THEME_BACKGROUND,
			foreground=self.THEME_FOREGROUND,
			insertcolor=self.THEME_FOREGROUND,
			bordercolor=self.THEME_BORDER,
		)
		style.configure(
			"TCombobox",
			fieldbackground=self.THEME_BACKGROUND,
			foreground=self.THEME_FOREGROUND,
			background=self.THEME_BACKGROUND,
			arrowcolor=self.THEME_FOREGROUND,
			bordercolor=self.THEME_BORDER,
		)
		style.map(
			"TCombobox",
			fieldbackground=[("readonly", self.THEME_BACKGROUND)],
			selectbackground=[("readonly", self.THEME_SELECTION)],
			selectforeground=[("readonly", self.THEME_FOREGROUND)],
		)
		style.configure("TCheckbutton", background=self.THEME_BACKGROUND, foreground=self.THEME_FOREGROUND)
		style.map("TCheckbutton", background=[("active", self.THEME_BACKGROUND)])
		style.configure(
			"Treeview",
			background=self.THEME_SURFACE,
			fieldbackground=self.THEME_SURFACE,
			foreground=self.THEME_FOREGROUND,
			bordercolor=self.THEME_BORDER,
		)
		style.map(
			"Treeview",
			background=[("selected", self.THEME_SELECTION)],
			foreground=[("selected", self.THEME_FOREGROUND)],
		)
		style.configure(
			"Treeview.Heading",
			background=self.THEME_ACTIVE,
			foreground=self.THEME_FOREGROUND,
			bordercolor=self.THEME_BORDER,
		)
		style.map("Treeview.Heading", background=[("active", self.THEME_SELECTION)])
		style.configure(
			"TLabelframe",
			background=self.THEME_BACKGROUND,
			foreground=self.THEME_FOREGROUND,
			bordercolor=self.THEME_BORDER,
		)
		style.configure("TLabelframe.Label", background=self.THEME_BACKGROUND, foreground=self.THEME_FOREGROUND)

		self.configure_scrollbar_style(style)
		self.apply_native_window_theme(widget)

	def _to_windows_colorref(self, color: str) -> int:
		"""
		Convert a hex color to a Windows COLORREF integer.
		"""
		color = color.lstrip("#")
		red = int(color[0:2], 16)
		green = int(color[2:4], 16)
		blue = int(color[4:6], 16)
		return red | (green << 8) | (blue << 16)

	def apply_native_window_theme(self, widget: tk.Misc) -> None:
		"""
		Apply native Windows title bar theming when supported.
		"""
		if sys.platform != "win32":
			return
		if not isinstance(widget, (tk.Tk, tk.Toplevel)):
			return

		def apply_theme() -> None:
			try:
				import ctypes

				widget.update_idletasks()
				hwnd = widget.winfo_id()
				dwmapi = ctypes.windll.dwmapi

				for attribute_id in self.WINDOWS_DARK_MODE_ATTRIBUTE_IDS:
					dark_mode = ctypes.c_int(1)
					result = dwmapi.DwmSetWindowAttribute(
						hwnd,
						attribute_id,
						ctypes.byref(dark_mode),
						ctypes.sizeof(dark_mode),
					)
					if result == 0:
						break

				for attribute_id, color in (
					(self.WINDOWS_BORDER_COLOR_ATTRIBUTE_ID, self.THEME_BORDER),
					(self.WINDOWS_CAPTION_COLOR_ATTRIBUTE_ID, self.THEME_BACKGROUND),
					(self.WINDOWS_TEXT_COLOR_ATTRIBUTE_ID, self.THEME_FOREGROUND),
				):
					color_value = ctypes.c_uint(self._to_windows_colorref(color))
					dwmapi.DwmSetWindowAttribute(
						hwnd,
						attribute_id,
						ctypes.byref(color_value),
						ctypes.sizeof(color_value),
					)
			except (AttributeError, OSError, RuntimeError, tk.TclError, ValueError):
				return

		widget.after_idle(apply_theme)

	def enable_taskbar_icon_for_custom_window(self, window: tk.Tk | tk.Toplevel) -> None:
		"""
		Force a custom-chrome window to use normal Windows app-window taskbar behavior.
		"""
		if sys.platform != "win32":
			return

		window._force_taskbar_icon = True

		def apply_style() -> None:
			try:
				import ctypes

				window.update_idletasks()
				hwnd = window.winfo_id()
				user32 = ctypes.windll.user32
				get_window_long_ptr = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
				set_window_long_ptr = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)

				extended_style = get_window_long_ptr(hwnd, self.WINDOWS_GWL_EXSTYLE)
				extended_style &= ~self.WINDOWS_WS_EX_TOOLWINDOW
				extended_style |= self.WINDOWS_WS_EX_APPWINDOW
				set_window_long_ptr(hwnd, self.WINDOWS_GWL_EXSTYLE, extended_style)

				user32.SetWindowPos(
					hwnd,
					0,
					0,
					0,
					0,
					0,
					self.WINDOWS_SWP_NOMOVE
					| self.WINDOWS_SWP_NOSIZE
					| self.WINDOWS_SWP_NOZORDER
					| self.WINDOWS_SWP_NOACTIVATE
					| self.WINDOWS_SWP_FRAMECHANGED,
				)

				window.withdraw()
				window.after(10, window.deiconify)
			except (AttributeError, OSError, RuntimeError, tk.TclError):
				return

		window.after_idle(apply_style)

	def use_custom_windows_chrome(self) -> bool:
		"""
		Return whether Windows should use custom in-app chrome.
		"""
		return sys.platform == "win32"

	def position_window_below_cursor(self, window: tk.Tk | tk.Toplevel, offset_y: int | None = None) -> None:
		"""
		Center a window below the current mouse cursor while keeping it on screen.
		"""
		window.update_idletasks()
		width = window.winfo_width() or window.winfo_reqwidth()
		height = window.winfo_height() or window.winfo_reqheight()
		pointer_x = window.winfo_pointerx()
		pointer_y = window.winfo_pointery()
		offset = self.CURSOR_WINDOW_OFFSET_Y if offset_y is None else offset_y
		screen_width = window.winfo_screenwidth()
		screen_height = window.winfo_screenheight()

		x_pos = pointer_x - (width // 2)
		y_pos = pointer_y + offset

		max_x = max(self.WINDOW_SCREEN_MARGIN, screen_width - width - self.WINDOW_SCREEN_MARGIN)
		max_y = max(self.WINDOW_SCREEN_MARGIN, screen_height - height - self.WINDOW_SCREEN_MARGIN)
		x_pos = min(max(self.WINDOW_SCREEN_MARGIN, x_pos), max_x)
		y_pos = min(max(self.WINDOW_SCREEN_MARGIN, y_pos), max_y)

		window.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

	def create_plain_frame(self, master: tk.Misc, **kwargs) -> tk.Frame:
		"""
		Create a plain Tk frame for custom chrome areas.
		"""
		frame_kwargs = {
			"bg": self.THEME_BACKGROUND,
			"bd": 0,
			"highlightthickness": 0,
		}
		frame_kwargs.update(kwargs)
		return tk.Frame(master, **frame_kwargs)

	def create_plain_label(self, master: tk.Misc, text: str = "", **kwargs) -> tk.Label:
		"""
		Create a plain Tk label for custom chrome areas.
		"""
		label_kwargs = {
			"text": text,
			"bg": self.THEME_BACKGROUND,
			"fg": self.THEME_FOREGROUND,
			"anchor": tk.W,
			"bd": 0,
			"highlightthickness": 0,
		}
		label_kwargs.update(kwargs)
		return tk.Label(master, **label_kwargs)

	def create_window_button(
		self,
		master: tk.Misc,
		text: str,
		command: Callable[..., object],
		**kwargs,
	) -> tk.Button:
		"""
		Create a plain Tk button for custom chrome areas.
		"""
		button_kwargs = {
			"text": text,
			"command": command,
			"bg": self.THEME_BACKGROUND,
			"fg": self.THEME_FOREGROUND,
			"activebackground": self.THEME_ACTIVE,
			"activeforeground": self.THEME_FOREGROUND,
			"relief": tk.FLAT,
			"bd": 0,
			"highlightthickness": 0,
			"padx": 10,
			"pady": 6,
		}
		button_kwargs.update(kwargs)
		return tk.Button(master, **button_kwargs)

	def create_menu_button(self, master: tk.Misc, text: str, menu: tk.Menu, **kwargs) -> tk.Button:
		"""
		Create a themed button that posts a dropdown menu for a custom menu bar.
		"""
		def show_menu() -> None:
			menu.update_idletasks()
			x_position = button.winfo_rootx()
			y_position = button.winfo_rooty() + button.winfo_height()
			try:
				menu.tk_popup(x_position, y_position)
			finally:
				menu.grab_release()

		button_kwargs = {
			"text": text,
			"command": show_menu,
			"bg": self.THEME_BACKGROUND,
			"fg": self.THEME_FOREGROUND,
			"activebackground": self.THEME_ACTIVE,
			"activeforeground": self.THEME_FOREGROUND,
			"relief": tk.FLAT,
			"bd": 0,
			"highlightthickness": 0,
			"padx": 10,
			"pady": 6,
			"anchor": tk.W,
		}
		button_kwargs.update(kwargs)
		button = tk.Button(master, **button_kwargs)
		button.bind("<Down>", lambda _event: show_menu())
		return button

	def _start_window_drag(self, event, window: tk.Tk | tk.Toplevel) -> str:
		"""
		Capture the initial drag position for a custom window title bar.
		"""
		window._drag_origin = (window.winfo_x(), window.winfo_y(), event.x_root, event.y_root)
		return "break"

	def _drag_window(self, event, window: tk.Tk | tk.Toplevel) -> str:
		"""
		Move a custom-chrome window while dragging its title bar.
		"""
		start_x, start_y, root_x, root_y = getattr(
			window,
			"_drag_origin",
			(window.winfo_x(), window.winfo_y(), event.x_root, event.y_root),
		)
		delta_x = event.x_root - root_x
		delta_y = event.y_root - root_y
		window.geometry(f"+{start_x + delta_x}+{start_y + delta_y}")
		return "break"

	def _start_window_resize(self, event, window: tk.Tk | tk.Toplevel) -> str:
		"""
		Capture the initial resize position for a custom window resize grip.
		"""
		window._resize_origin = (window.winfo_width(), window.winfo_height(), event.x_root, event.y_root)
		return "break"

	def _resize_window(self, event, window: tk.Tk | tk.Toplevel) -> str:
		"""
		Resize a custom-chrome window from its resize grip.
		"""
		width, height, root_x, root_y = getattr(
			window,
			"_resize_origin",
			(window.winfo_width(), window.winfo_height(), event.x_root, event.y_root),
		)
		new_width = max(self.WINDOW_MIN_WIDTH, width + (event.x_root - root_x))
		new_height = max(self.WINDOW_MIN_HEIGHT, height + (event.y_root - root_y))
		window.geometry(f"{new_width}x{new_height}")
		return "break"

	def minimize_custom_window(self, window: tk.Tk | tk.Toplevel) -> None:
		"""
		Minimize a custom-chrome window and restore the override afterward.
		"""
		window.overrideredirect(False)
		window.iconify()

	def restore_custom_window(self, _event, window: tk.Tk | tk.Toplevel) -> None:
		"""
		Restore custom chrome after a minimized window is shown again.
		"""
		if window.state() == "normal":
			window.overrideredirect(True)
			window.lift()
			if getattr(window, "_force_taskbar_icon", False):
				self.enable_taskbar_icon_for_custom_window(window)

	def create_custom_title_bar(
		self,
		window: tk.Tk | tk.Toplevel,
		title: str,
		close_command: Callable[..., object],
	) -> tk.Frame:
		"""
		Create a custom title bar for Windows themed windows.
		"""
		title_bar = self.create_plain_frame(
			window,
			highlightthickness=1,
			highlightbackground=self.THEME_BORDER,
			highlightcolor=self.THEME_BORDER,
		)
		title_bar.grid_columnconfigure(0, weight=1)

		title_label = self.create_plain_label(
			title_bar,
			text=title,
			font=("Arial", 10, "bold"),
			padx=12,
			pady=8,
		)
		title_label.grid(column=0, row=0, sticky="ew")

		minimize_button = self.create_window_button(
			title_bar,
			text="—",
			command=lambda: self.minimize_custom_window(window),
			width=3,
		)
		minimize_button.grid(column=1, row=0, sticky="e")

		close_button = self.create_window_button(
			title_bar,
			text="✕",
			command=close_command,
			width=3,
		)
		close_button.grid(column=2, row=0, sticky="e")

		for drag_widget in (title_bar, title_label):
			drag_widget.bind("<ButtonPress-1>", lambda event, win=window: self._start_window_drag(event, win))
			drag_widget.bind("<B1-Motion>", lambda event, win=window: self._drag_window(event, win))

		window.bind("<Map>", lambda event, win=window: self.restore_custom_window(event, win), add="+")
		return title_bar

	def create_custom_menu_bar(self, master: tk.Misc) -> tk.Frame:
		"""
		Create a custom themed menu bar container.
		"""
		return self.create_plain_frame(
			master,
			highlightthickness=1,
			highlightbackground=self.THEME_BORDER,
			highlightcolor=self.THEME_BORDER,
		)

	def create_resize_handle(self, master: tk.Misc, window: tk.Tk | tk.Toplevel) -> tk.Label:
		"""
		Create a resize handle for a custom-chrome window.
		"""
		handle = self.create_plain_label(master, text="◢", cursor="size_nw_se")
		handle.bind("<ButtonPress-1>", lambda event, win=window: self._start_window_resize(event, win))
		handle.bind("<B1-Motion>", lambda event, win=window: self._resize_window(event, win))
		return handle

	def configure_scrollbar_style(self, style: ttk.Style | None = None) -> None:
		"""
		Configure the shared scrollbar styles.
		"""
		style = style or ttk.Style()
		style.configure(
			"Vertical.TScrollbar",
			background=self.THEME_BACKGROUND,
			troughcolor=self.THEME_BACKGROUND,
			bordercolor=self.THEME_BORDER,
			arrowcolor=self.THEME_FOREGROUND,
		)
		style.configure(
			"Horizontal.TScrollbar",
			background=self.THEME_BACKGROUND,
			troughcolor=self.THEME_BACKGROUND,
			bordercolor=self.THEME_BORDER,
			arrowcolor=self.THEME_FOREGROUND,
		)
		style.map(
			"Vertical.TScrollbar",
			background=[("active", self.THEME_ACTIVE)],
		)
		style.map(
			"Horizontal.TScrollbar",
			background=[("active", self.THEME_ACTIVE)],
		)

	def create_menu(self, master: tk.Misc, tearoff: int = 0, **kwargs) -> tk.Menu:
		"""
		Create a menu widget.
		"""
		menu_kwargs = {
			"tearoff": tearoff,
			"bg": self.THEME_BACKGROUND,
			"fg": self.THEME_FOREGROUND,
			"activebackground": self.THEME_ACTIVE,
			"activeforeground": self.THEME_FOREGROUND,
			"disabledforeground": self.THEME_BORDER,
			"selectcolor": self.THEME_FOREGROUND,
			"activeborderwidth": 0,
			"relief": tk.FLAT,
			"bd": 0,
		}
		menu_kwargs.update(kwargs)
		return tk.Menu(master, **menu_kwargs)

	def create_paned_window(self, master: tk.Misc, orient: str = tk.HORIZONTAL, **kwargs) -> tk.PanedWindow:
		"""
		Create a paned window widget.
		"""
		paned_window_kwargs = {
			"orient": orient,
			"bd": 0,
			"bg": self.THEME_BACKGROUND,
			"relief": tk.FLAT,
			"sashrelief": tk.FLAT,
			"sashwidth": 8,
			"sashpad": 2,
			"showhandle": False,
			"opaqueresize": True,
		}
		paned_window_kwargs.update(kwargs)
		return tk.PanedWindow(master, **paned_window_kwargs)

	def create_popup(
		self,
		parent: tk.Misc,
		title: str,
		message: str,
		ok_text: str = "OK",
		on_ok: Callable[..., object] | None = None,
		always_on_top: bool = True,
		geometry: str = "360x140",
	) -> tk.Toplevel:
		"""
		Create a dismissable popup window with a single OK button.
		"""
		popup = tk.Toplevel(parent)
		self.configure_theme(popup)
		popup.title(title)
		popup.geometry(geometry)
		popup.transient(parent)
		self.position_window_below_cursor(popup)
		if always_on_top:
			popup.attributes("-topmost", True)

		content_frame = self.create_frame(popup, padding="12")
		content_frame.pack(fill=tk.BOTH, expand=True)

		self.create_label(
			content_frame,
			text=message,
			anchor=tk.CENTER,
			justify=tk.CENTER,
			wraplength=320,
		).pack(expand=True, fill=tk.BOTH, pady=(0, 10))

		def handle_ok() -> None:
			popup.destroy()
			if on_ok:
				on_ok()

		self.create_button(content_frame, text=ok_text, command=handle_ok).pack()
		popup.grab_set()
		popup.focus_force()
		return popup

	def create_frame(self, master: tk.Misc, **kwargs) -> ttk.Frame:
		"""
		Create a frame widget.
		"""
		return ttk.Frame(master, **kwargs)

	def create_label(self, master: tk.Misc, text: str = "", **kwargs) -> ttk.Label:
		"""
		Create a label widget.
		"""
		return ttk.Label(master, text=text, **kwargs)

	def create_button(
		self,
		master: tk.Misc,
		text: str,
		command: Callable[..., object],
		**kwargs,
	) -> ttk.Button:
		"""
		Create a button widget.
		"""
		return ttk.Button(master, text=text, command=command, **kwargs)

	def create_entry(
		self,
		master: tk.Misc,
		textvariable: tk.StringVar | None = None,
		width: int | None = None,
		value: str = "",
		**kwargs,
	) -> ttk.Entry:
		"""
		Create an entry widget.
		"""
		entry_kwargs = dict(kwargs)
		if textvariable is not None:
			entry_kwargs["textvariable"] = textvariable
		if width is not None:
			entry_kwargs["width"] = width
		entry = ttk.Entry(master, **entry_kwargs)
		if value:
			entry.insert(0, value)
		return entry

	def create_checkbutton(
		self,
		master: tk.Misc,
		text: str = "",
		variable: tk.BooleanVar | None = None,
		**kwargs,
	) -> ttk.Checkbutton:
		"""
		Create a checkbutton widget.
		"""
		checkbutton_kwargs = dict(kwargs)
		if variable is not None:
			checkbutton_kwargs["variable"] = variable
		return ttk.Checkbutton(master, text=text, **checkbutton_kwargs)

	def create_combobox(
		self,
		master: tk.Misc,
		textvariable: tk.StringVar,
		values: Sequence[str],
		state: str = "readonly",
		width: int | None = None,
		**kwargs,
	) -> ttk.Combobox:
		"""
		Create a combobox widget.
		"""
		combobox_kwargs = dict(kwargs)
		if width is not None:
			combobox_kwargs["width"] = width
		return ttk.Combobox(
			master,
			textvariable=textvariable,
			values=list(values),
			state=state,
			**combobox_kwargs,
		)

	def create_scrollbar(
		self,
		master: tk.Misc,
		orient: str,
		command,
		style: str | None = None,
		**kwargs,
	) -> ttk.Scrollbar:
		"""
		Create a scrollbar widget.
		"""
		scrollbar_kwargs = dict(kwargs)
		if style is not None:
			scrollbar_kwargs["style"] = style
		return ttk.Scrollbar(master, orient=orient, command=command, **scrollbar_kwargs)

	def create_canvas(self, master: tk.Misc, **kwargs) -> tk.Canvas:
		"""
		Create a canvas widget.
		"""
		canvas_kwargs = {
			"bg": self.THEME_BACKGROUND,
			"highlightthickness": 0,
			"bd": 0,
		}
		canvas_kwargs.update(kwargs)
		return tk.Canvas(master, **canvas_kwargs)

	def create_text_widget(self, master: tk.Misc, **kwargs) -> tk.Text:
		"""
		Create a text widget.
		"""
		text_kwargs = {
			"bg": self.THEME_BACKGROUND,
			"fg": self.THEME_FOREGROUND,
			"insertbackground": self.THEME_FOREGROUND,
			"selectbackground": self.THEME_SELECTION,
			"selectforeground": self.THEME_FOREGROUND,
		}
		text_kwargs.update(kwargs)
		return tk.Text(master, **text_kwargs)

	def create_treeview_widget(
		self,
		master: tk.Misc,
		columns: Sequence[tuple[str, str, int, str]],
		show: str = "headings",
		height: int | None = None,
	) -> ttk.Treeview:
		"""
		Create a treeview widget.
		"""
		treeview_kwargs = {
			"columns": tuple(column_name for column_name, _, _, _ in columns),
			"show": show,
		}
		if height is not None:
			treeview_kwargs["height"] = height
		tree = ttk.Treeview(master, **treeview_kwargs)
		for column_name, heading, width, anchor in columns:
			tree.heading(column_name, text=heading)
			tree.column(column_name, width=width, anchor=anchor)
		return tree

	def create_treeview(
		self,
		columns: Sequence[tuple[str, str, int, str]],
		master: tk.Misc | None = None,
	) -> tuple[ttk.Frame, ttk.Treeview]:
		"""
		Create a treeview with a vertical scrollbar.
		"""
		container = self.create_frame(self._resolve_master(master))
		tree = self.create_treeview_widget(container, columns)
		tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
		scrollbar = self.create_scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
		tree.configure(yscrollcommand=scrollbar.set)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		return container, tree

	def create_scrollable_frame(
		self,
		master: tk.Misc,
		padding: int = 0,
		canvas_kwargs: dict | None = None,
	) -> tuple[ttk.Frame, tk.Canvas, ttk.Frame, ttk.Scrollbar, ttk.Scrollbar]:
		"""
		Create a frame containing a scrollable frame backed by a canvas.
		"""
		container = self.create_frame(master)
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)

		canvas = self.create_canvas(container, **(canvas_kwargs or {}))
		scrollbar_v = self.create_scrollbar(
			container,
			orient="vertical",
			command=canvas.yview,
			style="Vertical.TScrollbar",
		)
		scrollbar_h = self.create_scrollbar(
			container,
			orient="horizontal",
			command=canvas.xview,
			style="Horizontal.TScrollbar",
		)
		scrollable_frame = self.create_frame(canvas, padding=padding)
		scrollable_frame.bind(
			"<Configure>",
			lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
		)
		canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

		canvas.grid(column=0, row=0, sticky="nsew")
		scrollbar_v.grid(column=1, row=0, sticky="ns")
		scrollbar_h.grid(column=0, row=1, sticky="ew")
		return container, canvas, scrollable_frame, scrollbar_v, scrollbar_h

	def create_button_bar(
		self,
		master: tk.Misc | None = None,
		left_buttons: Sequence[tuple[str, Callable[..., object]]] | None = None,
		right_buttons: Sequence[tuple[str, Callable[..., object]]] | None = None,
	) -> ttk.Frame:
		"""
		Create a standard button bar with left- and right-aligned buttons.
		"""
		button_frame = self.create_frame(self._resolve_master(master))
		for text, command in left_buttons or ():
			self.create_button(button_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)
		for text, command in right_buttons or ():
			self.create_button(button_frame, text=text, command=command).pack(side=tk.RIGHT, padx=5)
		return button_frame

	def create_labeled_entry(
		self,
		master: tk.Misc,
		label_text: str,
		width: int = 40,
		value: str = "",
	) -> ttk.Entry:
		"""
		Create a vertically stacked label and entry widget.
		"""
		self.create_label(master, text=label_text).pack(pady=5)
		entry = self.create_entry(master, width=width, value=value)
		entry.pack(pady=5)
		return entry

	def create_entry_dropdown_row(
		self,
		master: tk.Misc,
		entry_var: tk.StringVar,
		dropdown_var: tk.StringVar,
		dropdown_values: Sequence[str],
		entry_width: int = 40,
		dropdown_width: int = 15,
	) -> ttk.Frame:
		"""
		Create a row containing an entry and read-only dropdown.
		"""
		row_frame = self.create_frame(master)
		row_frame.pack(fill=tk.X, pady=2)
		self.create_entry(row_frame, textvariable=entry_var, width=entry_width).pack(side=tk.LEFT, padx=5)
		self.create_combobox(
			row_frame,
			textvariable=dropdown_var,
			values=dropdown_values,
			width=dropdown_width,
		).pack(side=tk.LEFT, padx=5)
		return row_frame

	def create_preference_field(
		self,
		master: tk.Misc,
		row: int,
		key: str,
		value: object,
	) -> tk.BooleanVar | ttk.Entry:
		"""
		Create a standard grid-based preferences field.
		"""
		self.create_label(master, text=key).grid(column=0, row=row, sticky="w", padx=5, pady=5)
		if isinstance(value, bool):
			variable = tk.BooleanVar(value=value)
			self.create_checkbutton(master, variable=variable).grid(column=1, row=row, sticky="w", padx=5, pady=5)
			return variable
		entry = self.create_entry(master, value=str(value))
		entry.grid(column=1, row=row, sticky="ew", padx=5, pady=5)
		return entry
