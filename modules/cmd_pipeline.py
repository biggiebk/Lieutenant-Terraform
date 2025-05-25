import re
import sys
from subprocess import Popen, PIPE, CalledProcessError
from typing import List, Callable
from beartype import beartype
from modules.config import LieutenantTerraformConfig
import tkinter as tk
from tkinter import messagebox


class CommandPipeline:
    """
    A utility class for executing shell commands and handling their output.
    """

    @beartype
    def __init__(self, cmd: List[str], output_callback: Callable[[str], None], config: LieutenantTerraformConfig) -> None:
        """
        Initialize the CommandPipeline.

        Args:
            cmd (List[str]): The command to execute as a list of strings.
            output_callback (Callable[[str], None]): A callback function to handle command output.
            config (LieutenantTerraformConfig): Configuration object for the pipeline.
        """
        self.cmd = cmd
        self.output_callback = output_callback
        self.cfg = config

        # Are we running a command alias?
        possible_aliases = list(filter(lambda word: word.startswith(self.cmd[0]), self.cfg.prefs['aliases'].keys()))
        if len(possible_aliases) == 1: # Can only match one alias
            self.__run_alias(possible_aliases[0])
        elif len(possible_aliases) > 1: # If more than one is possible
            complete_alias = list(filter(lambda word: word == self.cmd[0], possible_aliases))
            if len(complete_alias) == 1:  # If there is whole match
                self.__run_alias(complete_alias[0])
            else:	# Print a message and exit
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
        try:
            with Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True) as process:
                for line in process.stdout:
                    self.output_callback(line)
                for error_line in process.stderr:
                    self.output_callback(f"ERROR: {error_line}")
            if process.returncode != 0:
                raise CalledProcessError(process.returncode, process.args)
            return True
        except (CalledProcessError, FileNotFoundError, PermissionError, OSError) as e:
            if isinstance(e, CalledProcessError):
                error_msg = f"Error: Command '{e.cmd}' failed with return code {e.returncode}\n"
            elif isinstance(e, FileNotFoundError):
                error_msg = f"FileNotFoundError: Command not found - {str(e)}\n"
            elif isinstance(e, PermissionError):
                error_msg = f"PermissionError: Permission denied - {str(e)}\n"
            else:
                error_msg = f"OSError: OS-related error - {str(e)}\n"
            self.output_callback(error_msg)
            if on_error == "halt":
                return False
            elif on_error == "continue":
                return True
            elif on_error == "prompt":
                return self._prompt_error(error_msg)
            return False

    @beartype
    def _prompt_error(self, error_msg: str) -> bool:
        """
        Display a Tkinter window to prompt the user to halt or continue.
        Returns True if continue, False if halt.
        """
        # Use the main window as the parent if available
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
            success = self.run(re.split(r'\s+', list(cmd)[0]), list(cmd.values())[0])  # Split the command string into a list of arguments
            if not success:
                print(f"Alias '{alias}' failed to execute: {cmd}")
                return
