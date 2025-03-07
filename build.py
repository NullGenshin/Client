import sys
import os
import multiprocessing

# The Python files to compile
script_to_compile = "main.py"

# Common options for both builds
common_options = [
    '--standalone',          # Create a standalone executable
    '--onefile',             # Bundle everything into a single file
    '--windows-uac-admin',   # Run as administrator
    '--windows-icon-from-ico=icon.png',  # Use custom icon
    '--include-data-files=logs/*=logs/',
    '--include-data-files=patch/*=patch/',
    '--include-data-files=proxy/*=proxy/',
    '--include-data-files=web/*=web/'
]

# Release build options (hidden console)
release_options = common_options + [
    '--windows-console-mode=disable',
    '--output-filename=main-release.exe'
]

# Debug build options (visible console)
debug_options = common_options + [
    '--output-filename=main-debug.exe'
]

def build_release():
    print("Starting release build...")
    os.system(f"python -m nuitka {script_to_compile} " + " ".join(release_options))
    print("Release build completed")

def build_debug():
    print("Starting debug build...")
    os.system(f"python -m nuitka {script_to_compile} " + " ".join(debug_options))
    print("Debug build completed")

if __name__ == '__main__':
    build_release()
    build_debug()