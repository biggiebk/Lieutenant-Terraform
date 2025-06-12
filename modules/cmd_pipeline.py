"""
Description: CommandPipeline class for executing shell commands with output handling.
"""
import re
import sys
import asyncio
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
        exit_callback: Callable[[str], None],
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
        self.exit_callback = exit_callback
        self.output_callback = output_callback
        self.running_callback = running_callback
        self.cfg = config
        self.process = None

        try:
            # Are we running a command alias?
            possible_aliases = list(
                filter(
                    lambda word: word.startswith(self.cmd[0]),
                    self.cfg.prefs['aliases'].keys()
                )
            )
            if len(possible_aliases) == 1:
                asyncio.run(self.__run_alias(possible_aliases[0]))
            elif len(possible_aliases) > 1:
                complete_alias = list(
                    filter(lambda word: word == self.cmd[0], possible_aliases)
                )
                if len(complete_alias) == 1:
                    asyncio.run(self.__run_alias(complete_alias[0]))
                else:
                    print("Multiple aliases found, please specify which one to run.")
                    print(f"  Matches: {', '.join(possible_aliases)}")
                    sys.exit(1)
            else:
                asyncio.run(self.run(self.cmd))
        except KeyError as e:
            self.output_callback(f"KeyError: {e}\n", tag="critical")
        except Exception as e:
            self.output_callback(f"Exception in CommandPipeline.__init__: {type(e).__name__}: {e}\n", tag="critical")

    @beartype
    async def run(self, cmd: list, on_error: str = "halt") -> bool:
        """
        Execute the command and stream its output to the callback function.

        Returns:
            bool: True if the command succeeded, False if it failed.
        """
        try:
            self.running_callback(' '.join(cmd))
        except Exception as e:
            self.output_callback(f"Error in running_callback: {type(e).__name__}: {e}\n", tag="critical")
        try:
            if cmd[0] in self.cfg.prefs['cmds']:
                cmd[0] = self.cfg.prefs['cmds'][cmd[0]]
        except Exception as e:
            self.output_callback(f"Error accessing cmds: {type(e).__name__}: {e}\n", tag="critical")
        try:
            self.output_callback(f"=====Start {' '.join(cmd)}=====\n", tag="cmd")
        except Exception as e:
            print(f"Output callback failed: {e}")
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.process = process
            stdout_task = asyncio.create_task(self._read_stream(process.stdout, self.output_callback))
            stderr_task = asyncio.create_task(self._read_stream(process.stderr, lambda l: self.output_callback("ERROR: " + l, tag="critical")))
            await asyncio.wait([stdout_task, stderr_task])
            returncode = await process.wait()
            if returncode != 0:
                raise Exception(f"Command failed with return code {returncode}")
            self.output_callback(f"=====End {' '.join(cmd)}=====\n", tag="cmd")
            return True
        except FileNotFoundError as e:
            self.output_callback(f"FileNotFoundError: {e}\n", tag="critical")
            self.output_callback(f"=====End {' '.join(cmd)}=====\n", tag="critical")
            return False
        except asyncio.CancelledError:
            self.output_callback("Command cancelled by user.\n", tag="critical")
            self.output_callback(f"=====End {' '.join(cmd)}=====\n", tag="critical")
            return False
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n"
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

    async def _read_stream(self, stream, callback):
        while True:
            try:
                line = await stream.readline()
                if not line:
                    break
                try:
                    callback(line.decode())
                except Exception as e:
                    print(f"Exception in output callback: {e}")
            except Exception as e:
                print(f"Exception while reading stream: {e}")
                break

    @beartype
    def _prompt_error(self, error_msg: str) -> bool:
        """
        Display a Tkinter window to prompt the user to halt or continue.
        Returns True if continue, False if halt.
        """
        parent = getattr(self.cfg, "tkr", None)
        try:
            result = messagebox.askquestion(
                "Command Error",
                f"{error_msg}\n\nDo you want to continue?",
                icon='warning',
                parent=parent
            )
            return result == 'yes'
        except Exception as e:
            self.output_callback(f"Error in prompt dialog: {type(e).__name__}: {e}\n", tag="critical")
            return False

    @beartype
    async def __run_alias(self, alias: str) -> None:
        """
        Run the command pipeline.
        """
        try:
            pipeline = self.cfg.prefs['aliases'][alias]["pipeline"]
        except KeyError as e:
            self.output_callback(f"Alias pipeline KeyError: {e}\n", tag="critical")
            return
        except Exception as e:
            self.output_callback(f"Exception accessing alias pipeline: {type(e).__name__}: {e}\n", tag="critical")
            return
        for cmd in pipeline:
            try:
                success = await self.run(
                    re.split(r'\s+', list(cmd)[0]),
                    list(cmd.values())[0]
                )
            except Exception as e:
                self.output_callback(f"Exception running command in alias: {type(e).__name__}: {e}\n", tag="critical")
                return
            if not success:
                self.output_callback(f"Alias '{alias}' failed to execute: {cmd}\n", tag="critical")
                return
        try:
            if self.cfg.prefs['aliases'][alias].get("exit_on_done", False):
                self.exit_callback()
        except Exception as e:
            self.output_callback(f"Exception in exit_callback: {type(e).__name__}: {e}\n", tag="critical")

    def terminate(self):
        """
        Terminate the running process if it exists.
        """
        try:
            if self.process and self.process.returncode is None:
                self.process.terminate()
        except Exception as e:
            print(f"Exception in terminate: {e}")
