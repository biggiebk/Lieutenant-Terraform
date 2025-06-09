"""
Description: Open and manage configuration files for LT
"""
import os
import json
from beartype import beartype

class LieutenantTerraformConfig():
	"""
		Description: Main class for initiating the LieutenantTerraform
		Responsible for:
			1. Locate configuration file
			2. Loading configuration
			3. Perform CRUD operations on configuration
	"""
	@beartype
	def __init__(self) -> None:
		"""
			Construct for LieutenantTerraformConfig class
			Responsible for:
				1. Locates configuration file if present
				2. Loads default configurations
				3. If config is found loads it
		"""
		# Find the config file if there is one.
		self.config_file = ""  # If none, empty string

		# Check for config file in environment variable
		if 'LT_CFG' in os.environ:
			self.config_file = os.environ['LT_CFG']
		# Check for config file in local directory
		elif os.path.isfile('./.lt_cfg.json'):
			self.config_file = "./.lt_cfg.json"
		else:
			# Check for config file in home directory for macOS and Windows
			home = os.path.expanduser("~")
			home_cfg = os.path.join(home, ".lt_cfg.json")
			if os.path.isfile(home_cfg):
				self.config_file = home_cfg

		# Load config defaults
		self.prefs = {}
		self.prefs['aliases'] = {
			'fmt': [
				{'terraform fmt -recursive': "halt"}
			],
			'init': [
				{'terraform init --upgrade': "halt"}
			],
			'lint': [
				{'terraform init --upgrade': "halt"},
				{'terraform validate': "halt"},
				{'terraform plan': "continue"},
				{'terraform fmt -recursive': "halt"}
			],
			'plan': [
				{'terraform validate': "halt"},
				{'terraform plan': "halt"},
				{'terraform fmt -recursive': "halt"}
			],
			'validate': [
				{'terraform validate': "halt"}
			]
		}
		self.prefs['cmds'] = {
			'terraform': 'terraform',
			'git': 'git'
		}
		self.prefs['settings'] = {
			"Debug": False,
			"Echo": True,
			"Save window geometry on exit": True,
			"TF_CLI_ARGS": "-no-color",
			"Window geometry": "754x763"
		}
		self.prefs['tags'] = {
			"error": {
				"color": "red",
				"patterns": ["error", "failed", "failure", "invalid", "\s-\s"]
			},
			"good": {
				"color": "green",
				"patterns": ["success", "successful", "\s+\s"]
			},
			"info": {
				"color": "blue",
				"patterns": ["https://", "http://", "plan:"]
			},
			"warn": {
				"color": "orange",
				"patterns": ["warning", "warn", "\s~\s"]
			}
		}
		if self.config_file != "":
			self.load(self.config_file)

	@beartype
	def load(self, config_file: str) -> None:
		"""
			Description: Load the configurations
			Responsible for:
				1. Opens the config file
				2. Loads the settings
		"""
		with open(config_file, 'r', encoding='utf-8') as cfg:
			cfg_json = cfg.read()
		cfg = json.loads(cfg_json)
		if 'settings' in cfg:
			self.prefs['settings'].update(cfg['settings'])
		if 'cmds' in cfg:
			self.prefs['cmds'].update(cfg['cmds'])
		if 'aliases' in cfg:
			self.prefs['aliases'].update(cfg['aliases'])
		if 'tags' in cfg:
			self.prefs['tags'].update(cfg['tags'])
		self.prefs["config_file"] = self.config_file
		self.prefs.update()
		self.set_env()  # Set environment variables based on the loaded config

	@beartype
	def save(self) -> None:
		"""
		Description: Save the current configurations to the config file
		Responsible for:
			1. Writing the current preferences to the config file
			2. If no config file is specified, save it to the user's home directory as .lt_cfg.json
		"""
		# Use the default file in the user's home directory if no config file is specified
		if not self.config_file:
			self.config_file = os.path.join(os.path.expanduser("~"), ".lt_cfg.json")

		with open(self.config_file, 'w', encoding='utf-8') as cfg:
			# Exclude the "config_file" key from being saved
			data_to_save = {key: value for key, value in self.prefs.items() if key != "config_file"}
			json.dump(data_to_save, cfg, indent=4)

	@beartype
	def set_env(self) -> None:
		"""
		Description: Set environment variables based on the current preferences
		Responsible for:
			1. Setting environment variables for Terraform CLI arguments
		"""
		if 'TF_CLI_ARGS' in self.prefs['settings']:
			os.environ['TF_CLI_ARGS'] = self.prefs['settings']['TF_CLI_ARGS']

	@beartype
	def update(self, updates: dict, save_config: bool = False) -> None:
		"""
		Description: Update the preferences with the provided dictionary
		Responsible for:
			1. Merging the updates into the current preferences
			2. Optionally saving the updated preferences to the config file
		Args:
			updates (dict): A dictionary containing the updates to apply to preferences
			save_config (bool): If True, save the updated preferences to the config file
		"""
		for key, value in updates.items():
			if key in self.prefs and isinstance(self.prefs[key], dict) and isinstance(value, dict):
				# Merge dictionaries
				self.prefs[key].update(value)
			else:
				# Overwrite or add new key-value pairs
				self.prefs[key] = value

		# Save the updated preferences if requested
		if save_config:
			self.save()
