"""
Description: Reusable Tkinter widget factory helpers.
"""
from collections.abc import Callable, Sequence
import tkinter as tk
from tkinter import ttk


class ReusableWidgetMixin:
	"""
	Mixin providing reusable Tkinter and ttk widget helpers.
	"""

	def _resolve_master(self, master: tk.Misc | None) -> tk.Misc:
		"""
		Resolve a widget master, defaulting to the current window when available.
		"""
		if master is not None:
			return master
		window = getattr(self, "window", None)
		if window is not None:
			return window
		if isinstance(self, tk.Misc):
			return self
		msg = "A master widget is required for this helper."
		raise ValueError(msg)

	def configure_scrollbar_style(self) -> None:
		"""
		Configure the shared scrollbar styles.
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

	def create_menu(self, master: tk.Misc, tearoff: int = 0, **kwargs) -> tk.Menu:
		"""
		Create a menu widget.
		"""
		return tk.Menu(master, tearoff=tearoff, **kwargs)

	def create_paned_window(self, master: tk.Misc, orient: str = tk.HORIZONTAL, **kwargs) -> tk.PanedWindow:
		"""
		Create a paned window widget.
		"""
		style = ttk.Style()
		background = style.lookup("TFrame", "background") or "SystemButtonFace"
		paned_window_kwargs = {
			"orient": orient,
			"bd": 0,
			"bg": background,
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
		popup.title(title)
		popup.geometry(geometry)
		popup.transient(parent)
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
		return tk.Canvas(master, **kwargs)

	def create_text_widget(self, master: tk.Misc, **kwargs) -> tk.Text:
		"""
		Create a text widget.
		"""
		return tk.Text(master, **kwargs)

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
