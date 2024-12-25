from cx_Freeze import setup, Executable

setup(
    name = "WebContentFilter",
    version = "1.0",
    description = "Web Content Filter",
    executables = [Executable("web_filter.py", base="Win32GUI")],
    options = {
        "build_exe": {
            "packages": ["tkinter", "requests", "bs4", "webbrowser"],
            "include_files": []
        }
    }
)