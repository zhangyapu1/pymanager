"""拖放支持 - 解析 Windows 拖放操作传入的文件路径。"""
import os
import re

_PATTERN = re.compile(r'\{([^{}]*)\}|([^\s]+)')


def parse_dropped_files(raw):
    if not isinstance(raw, str):
        return []
    files = []
    matches = _PATTERN.findall(raw)
    for match in matches:
        p = match[0] if match[0] else match[1]
        if p:
            files.append(p)
    return files


def setup_drag_drop(ctx):
    try:
        from tkinterdnd2 import DND_FILES
    except ImportError:
        ctx.append_output("[提示] tkinterdnd2 未安装，拖拽功能不可用。安装后将自动启用。")
        return
    listbox = ctx.ui_state.listbox
    if not listbox:
        return
    listbox.drop_target_register(DND_FILES)
    listbox.dnd_bind('<<Drop>>', lambda e: on_drop(ctx, e))


def on_drop(ctx, event):
    from modules.script_manager import add_script_from_path
    files = parse_dropped_files(event.data)
    added = 0
    skipped = 0
    for f in files:
        if not f or not os.path.exists(f):
            skipped += 1
            continue
        if f.lower().endswith('.py'):
            add_script_from_path(ctx, f)
            added += 1
        else:
            skipped += 1
    msg = f"拖拽完成：添加 {added} 个脚本，跳过 {skipped} 个非.py文件"
    ctx.set_status(msg)
    ctx.append_output(msg)