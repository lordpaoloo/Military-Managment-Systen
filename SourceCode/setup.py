import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might miss some of them.
# If any modules are missing, list them in the "packages" or "includes" list.
build_exe_options = {
    "packages": [
        "os", "sqlite3", "fitz", "sys", "PyQt5", "hijri_converter",
        "reportlab", "arabic_reshaper", "bidi", "aspose.pdf","pymupdf"
    ],
    "includes": ["pymupdf"],  # Include 'mupdf' explicitly if it's missing
    "include_files": ["icon.ico"],  # Add any extra files like the icon here
    "excludes": [],
}

# Base options
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # If you want to remove the console, use "Win32GUI" for GUI applications

# Define the executables
executables = [
    Executable("main.py", base=base, icon="icon.png")  # Replace "main.py" with your main Python file and set the icon
]

# Setup configuration
setup(
    name="Military Management System",
    version="0.2",
    description="Military Management System is an app you can use to manage military operations. Made by me. Github: https://github.com/lordpaoloo",
    options={"build_exe": build_exe_options},
    executables=executables
)
