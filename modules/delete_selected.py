"""
删除脚本 - 删除选中的脚本文件及其内部存储副本。

功能：
    delete_selected(ctx)：
        1. 获取当前选中脚本项
        2. 解析脚本的绝对存储路径
        3. 弹出确认对话框，提示将同时删除内部副本
        4. 用户确认后执行删除：
           - os.remove 删除文件
           - FileNotFoundError 视为已删除，继续执行
           - OSError 删除失败时弹出警告，保留列表项
        5. 从脚本集合中移除该项
        6. 更新列表显示和状态栏

安全机制：
    - 删除前必须用户确认
    - 文件删除失败时不从列表移除，避免数据丢失
    - 输出操作日志到控制台

依赖：modules.script_manager, modules.app_context
"""
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
