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
    os.system(f"python -m nuitka {script_to_compile} " + " ".join(release_options))

def build_debug():
    os.system(f"python -m nuitka {script_to_compile} " + " ".join(debug_options))

if __name__ == '__main__':
    # Create two processes for parallel builds
    release_process = multiprocessing.Process(target=build_release)
    debug_process = multiprocessing.Process(target=build_debug)

    # Start both builds
    release_process.start()
    debug_process.start()

    # Wait for both builds to complete
    release_process.join()
    debug_process.join()