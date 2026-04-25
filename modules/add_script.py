import os
from tkinter import filedialog

from modules.script_manager import add_script_from_path as _add_script_from_path


def add_script(manager):
    path = filedialog.askopenfilename(
        title="选择 Python 脚本",
        filetypes=[("Python 文件", "*.py"), ("所有文件", "*.*")]
    )
    if path:
        _add_script_from_path(manager, path)
