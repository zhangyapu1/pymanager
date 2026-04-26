"""删除脚本 - 删除选中的脚本文件。"""
import os

from modules.script_manager import resolve_path
from modules.app_context import AppContext


def delete_selected(ctx: AppContext):
    item = ctx.get_selected_item()
    if not item:
        return

    display_name = item['display']
    storage_path = item["storage_path"]
    abs_path = resolve_path(ctx.data_dir, storage_path)

    confirmed = ctx.ui.ask_yes_no("确认删除", f"从管理器中移除\n{display_name}\n（内部存储的副本也会被删除）")

    if not confirmed:
        return

    ctx.append_output(f"正在删除：{display_name}")
    file_deleted = False
    try:
        os.remove(abs_path)
        file_deleted = True
    except FileNotFoundError:
        file_deleted = True
    except OSError as e:
        msg = f"无法删除内部文件：{e}\n该项目将从列表中保留。"
        ctx.append_output(f"[警告] {msg}")
        ctx.ui.show_warning("删除警告", msg)
        return

    ctx.scripts.remove(item)

    ctx.update_listbox()
    msg = f"已移除：{display_name}"
    ctx.append_output(msg)
    ctx.set_status(msg)
