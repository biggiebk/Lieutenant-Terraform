"""
UI for editing highlights in preferences.
"""
import tkinter as tk

from beartype import beartype

from modules.config import LieutenantTerraformConfig
from modules.ui.tags_ui import PatternRulesUI


class HighlightsUI(PatternRulesUI):
	"""
	UI for editing highlights in preferences.
	"""

	@beartype
	def __init__(
		self,
		cfg: LieutenantTerraformConfig,
		parent: tk.Misc | None = None,
		title: str = "Edit Highlights",
		geometry: str = "600x400",
	) -> None:
		super().__init__(
			cfg,
			preference_key="highlights",
			item_label="Highlight",
			parent=parent,
			title=title,
			geometry=geometry,
		)
