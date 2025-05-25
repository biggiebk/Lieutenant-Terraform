"""
Description: Script to launch Lieutenant Terraform (LT)
"""
import sys
from modules.lieutenant_terraform import LieutenantTerraform

if __name__ == "__main__":
	# Pass all command-line arguments (excluding the script name) to LieutenantTerraform
	lt = LieutenantTerraform(sys.argv[1:])
