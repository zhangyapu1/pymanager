"""批量操作 - 批量删除、移动脚本等。"""
import os
import shutil

from modules.script_manager import resolve_path, move_script_to_group


def batch_delete(ctx, items):
    if not items:
        return
    names = "\n".join(item["display"] for item in items)
    if not ctx.ui.ask_yes_no("批量删除", f"确定删除以下 {len(items)} 个脚本？\n\n{names}"):
        return
    deleted = 0
    for item in items:
        abs_path = resolve_path(ctx.data_dir, item["storage_path"])
        try:
            os.remove(abs_path)
        except FileNotFoundError:
            pass
        except OSError:
            continue
        ctx.scripts.remove(item)
        deleted += 1
    ctx.update_listbox()
    msg = f"批量删除完成：{deleted} 个脚本"
    ctx.append_output(msg)
    ctx.set_status(msg)


def batch_move(ctx, items, target_group):
    if not items:
        return
    moved = 0
    for item in items:
        if item["group"] == target_group:
            continue
        move_script_to_group(ctx, item, target_group)
        moved += 1
    msg = f"批量移动完成：{moved} 个脚本移动到「{target_group}」"
    ctx.append_output(msg)
    ctx.set_status(msg)


def batch_export(ctx, items):
    if not items:
        return
    from tkinter import filedialog
    export_dir = filedialog.askdirectory(title="选择导出目录")
    if not export_dir:
        return
    exported = 0
    for item in items:
        abs_path = resolve_path(ctx.data_dir, item["storage_path"])
        if not os.path.exists(abs_path):
            continue
        dest = os.path.join(export_dir, os.path.basename(abs_path))
        try:
            shutil.copy2(abs_path, dest)
            exported += 1
        except OSError as e:
            ctx.append_output(f"[错误] 导出失败：{item['display']} - {e}")
    msg = f"批量导出完成：{exported} 个脚本导出到 {export_dir}"
    ctx.append_output(msg)
    ctx.set_status(msg)
