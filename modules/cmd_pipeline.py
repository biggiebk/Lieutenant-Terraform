"""
Description: CommandPipeline class for executing shell commands with output handling.
"""
import re
import sys
from subprocess import Popen, PIPE, CalledProcessError
from typing import List, Callable
from tkinter import messagebox
from beartype import beartype
from modules.config import LieutenantTerraformConfig


class CommandPipeline:
	"""
	A utility class for executing shell commands and handling their output.
	"""

	@beartype
	def __init__(
		self,
		cmd: List[str],
		output_callback: Callable[[str], None],
		running_callback: Callable[[str], None],
		config: LieutenantTerraformConfig
	) -> None:
		"""
		Initialize the CommandPipeline.

		Args:
			cmd (List[str]): The command to execute as a list of strings.
			output_callback (Callable[[str], None]): A callback function to handle command output.
			config (LieutenantTerraformConfig): Configuration object for the pipeline.
		"""
		self.cmd = cmd
		self.output_callback = output_callback
		self.running_callback = running_callback
		self.cfg = config
		self.process = None

		# Are we running a command alias?
		possible_aliases = list(
			filter(
				lambda word: word.startswith(self.cmd[0]),
				self.cfg.prefs['aliases'].keys()
			)
		)
		if len(possible_aliases) == 1:
			self.__run_alias(possible_aliases[0])
		elif len(possible_aliases) > 1:
			complete_alias = list(
				filter(lambda word: word == self.cmd[0], possible_aliases)
			)
			if len(complete_alias) == 1:
				self.__run_alias(complete_alias[0])
			else:
				print("Multiple aliases found, please specify which one to run.")
				print(f"  Matches: {', '.join(possible_aliases)}")
				sys.exit(1)
		else:
			self.run(self.cmd)

	@beartype
	def run(self, cmd: list, on_error: str = "halt") -> bool:
		"""
		Execute the command and stream its output to the callback function.

		Returns:
			bool: True if the command succeeded, False if it failed.
		"""
		self.running_callback(' '.join(cmd))
		if cmd[0] in self.cfg.prefs['cmds']:
			cmd[0] = self.cfg.prefs['cmds'][cmd[0]]
		self.output_callback(f"=====Start {' '.join(cmd)}=====\n", tag="cmd")
		try:
			with Popen(
				cmd,
				stdout=PIPE,
				stderr=PIPE,
				bufsize=1,
				universal_newlines=True
			) as process:
				self.process = process
				for line in process.stdout:
					self.output_callback(line)
				for error_line in process.stderr:
					self.output_callback("ERROR: ", tag="critical")
					self.output_callback(error_line)
			if self.process and self.process.returncode is None:
				self.process.terminate()
			if process.returncode != 0:
				raise CalledProcessError(process.returncode, process.args)
			self.output_callback(f"=====End {' '.join(cmd)}=====\n", tag="cmd")
			return True
		except (CalledProcessError, FileNotFoundError, PermissionError, OSError, Exception) as e:
			if isinstance(e, CalledProcessError):
				error_msg = (
					f"CommandError '{' '.join(e.cmd)}' failed with return code {e.returncode}\n"
				)
				self.output_callback(error_msg, tag="critical")
			elif isinstance(e, FileNotFoundError):
				error_msg = f"FileNotFoundError: Command not found - {str(e)}\n"
				self.output_callback(error_msg, tag="critical")
			elif isinstance(e, PermissionError):
				error_msg = f"PermissionError: Permission denied - {str(e)}\n"
				self.output_callback(error_msg, tag="critical")
			elif isinstance(e, OSError):
				error_msg = f"OSError: OS-related error - {str(e)}\n"
				self.output_callback(error_msg, tag="critical")
			else:
				error_msg = f"Unknown: error - {str(e)}\n"
				self.output_callback(error_msg, tag="critical")
			if on_error == "halt":
				self.output_callback(f"=====End {' '.join(cmd)}=====\n", tag="critical")
				return False
			elif on_error == "continue":
				self.output_callback(f"=====End {' '.join(cmd)}=====\n", tag="critical")
				return True
			elif on_error == "prompt":
				return self._prompt_error(error_msg)
			self.output_callback(f"=====End {' '.join(cmd)}=====\n", tag="critical")
			return False

	@beartype
	def _prompt_error(self, error_msg: str) -> bool:
		"""
		Display a Tkinter window to prompt the user to halt or continue.
		Returns True if continue, False if halt.
		"""
		parent = getattr(self.cfg, "tkr", None)
		result = messagebox.askquestion(
			"Command Error",
			f"{error_msg}\n\nDo you want to continue?",
			icon='warning',
			parent=parent
		)
		return result == 'yes'

	@beartype
	def __run_alias(self, alias: str) -> None:
		"""
		Run the command pipeline.
		"""
		for cmd in self.cfg.prefs['aliases'][alias]:
			success = self.run(
				re.split(r'\s+', list(cmd)[0]),
				list(cmd.values())[0]
			)
			if not success:
				print(f"Alias '{alias}' failed to execute: {cmd}")
				return

	def terminate(self):
		"""
		Terminate the running process if it exists.
		"""
		if self.process and self.process.poll() is None:
			self.process.terminate()
