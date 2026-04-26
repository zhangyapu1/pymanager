"""
工具函数 - 窗口标题设置、docstring 提取、程序目录打开等通用工具。

函数：
    update_title_mode(root)：
        设置主窗口标题为"Python 脚本管理器"
        - 安全处理 None 和 TclError

    open_program_dir()：
        使用 Windows 资源管理器打开程序所在目录
        - 调用 explorer 命令

    extract_docstring(file_path)：
        提取 Python 文件的模块级 docstring
        支持三种格式：
        1. 三引号 docstring（三双引号或三单引号）
           - 单行：三双引号内容三双引号
           - 多行：三双引号第一行\n第二行\n三双引号
        2. 井号注释（# 开头的连续注释行）
           - 在代码之前的注释行合并为文档
        3. 无文档时返回 None

        解析逻辑：
        1. 读取文件所有行
        2. 找到第一个非空非注释行
        3. 如果是三引号开头，提取完整 docstring
        4. 否则收集代码前的 # 注释行
        5. 编码错误时返回 None

依赖：os, sys, subprocess
"""
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
