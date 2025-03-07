import sys
import os

# The Python files to compile
script_to_compile = "main.py"

# Common options for both builds
common_options = [
    '--standalone',          # Create a standalone executable
    '--onefile',             # Bundle everything into a single file
    '--windows-uac-admin',   # Run as administrator
    '--include-data-files=logs/*=logs/',
    '--include-data-files=patch/*=patch/',
    '--include-data-files=proxy/*=proxy/',
    '--include-data-files=web/*=web/'
]

# Release build options (hidden console)
release_options = common_options + [
    '--windows-disable-console',
    '--output-filename=main-release.exe'
]

# Debug build options (visible console)
debug_options = common_options + [
    '--output-filename=main-debug.exe'
]

# Build release version
os.system(f"python -m nuitka {script_to_compile} " + " ".join(release_options))

# Build debug version
os.system(f"python -m nuitka {script_to_compile} " + " ".join(debug_options))