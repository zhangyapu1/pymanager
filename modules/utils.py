"""工具函数 - 窗口标题模式、docstring 提取等通用工具。"""
import os
import sys
import subprocess
import tkinter as tk


def update_title_mode(root):
    if root is None:
        return

    if not hasattr(root, 'title'):
        return

    try:
        root.title("Python 脚本管理器")
    except (tk.TclError, AttributeError):
        pass


def open_program_dir():
    program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    subprocess.Popen(f'explorer "{program_dir}"')


def extract_docstring(file_path):
    if not os.path.isfile(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return None

    stripped = [l.strip() for l in lines]
    non_empty = [i for i, l in enumerate(stripped) if l and not l.startswith('#')]
    if not non_empty:
        comments = [l for l in stripped if l.startswith('#')]
        return '\n'.join(l.lstrip('#').strip() for l in comments if l) or None

    first = non_empty[0]
    line = stripped[first]
    if line.startswith('"""') or line.startswith("'''"):
        quote = line[:3]
        rest = line[3:]
        if rest.endswith(quote) and len(rest) > 0:
            return rest[:-3].strip() or None
        parts = [rest]
        for l in lines[first + 1:]:
            s = l.strip()
            if s.endswith(quote):
                parts.append(s[:-3])
                break
            parts.append(s)
        return '\n'.join(parts).strip() or None

    comments = []
    for l in stripped[:first]:
        if l.startswith('#'):
            comments.append(l.lstrip('#').strip())
    return '\n'.join(comments) if comments else None
