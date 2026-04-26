"""右键菜单 - 脚本列表的右键上下文菜单。"""
import tkinter as tk

from modules.config import DEFAULT_GROUP
from modules.script_manager import move_script_to_group, scan_data_directory
from modules.run_selected import run_selected
from modules.rename_selected import rename_selected
from modules.delete_selected import delete_selected
from modules.app_context import AppContext
from modules.favorites import is_favorite, toggle_favorite
from modules.script_icons import ICON_OPTIONS, get_script_icon, set_script_icon
from modules.batch_ops import batch_delete, batch_move, batch_export


def _edit_content(ctx):
    from modules.edit_content import _edit_content as _do_edit
    _do_edit(ctx)


def show_context_menu(ctx: AppContext, event):
    item = ctx.get_selected_item()
    if not item:
        return

    selected_items = ctx.get_selected_items()
    is_batch = len(selected_items) > 1

    current_group = item.get("group", DEFAULT_GROUP)
    menu = tk.Menu(ctx.get_root_window(), tearoff=0)

    if is_batch:
        menu.add_command(label=f"批量删除（{len(selected_items)} 个）", command=lambda: batch_delete(ctx, selected_items))

        move_menu = tk.Menu(menu, tearoff=0)
        other_groups = [g for g in ctx.group_manager.groups if g != current_group]
        for group in other_groups:
            move_menu.add_command(label=group, command=lambda g=group: batch_move(ctx, selected_items, g))
        if not other_groups:
            move_menu.add_command(label="无其他分组", state="disabled")
        menu.add_cascade(label=f"批量移动到分组（{len(selected_items)} 个）", menu=move_menu)

        menu.add_command(label=f"批量导出（{len(selected_items)} 个）", command=lambda: batch_export(ctx, selected_items))
        menu.add_separator()

    is_fav = is_favorite(ctx.settings, item["storage_path"])
    fav_label = "取消收藏" if is_fav else "收藏（置顶）"
    menu.add_command(label=fav_label, command=lambda: toggle_favorite(ctx, item["storage_path"]))

    icon_menu = tk.Menu(menu, tearoff=0)
    current_icon = get_script_icon(ctx.settings, item["storage_path"])
    for label, icon_char in ICON_OPTIONS:
        check = "\u2713 " if icon_char == current_icon else ""
        icon_menu.add_command(label=f"{check}{label}", command=lambda ic=icon_char: _set_icon(ctx, item, ic))
    menu.add_cascade(label="设置图标", menu=icon_menu)

    menu.add_separator()

    move_menu = tk.Menu(menu, tearoff=0)
    other_groups = [g for g in ctx.group_manager.groups if g != current_group]

    for group in other_groups:
        move_menu.add_command(label=group, command=lambda g=group: move_script_to_group(ctx, item, g))

    if not other_groups:
        move_menu.add_command(label="无其他分组", state="disabled")

    move_menu.add_separator()
    move_menu.add_command(label="新建分组...", command=lambda: create_group_and_move(ctx, item))

    menu.add_cascade(label="移动到分组", menu=move_menu)
    menu.add_separator()
    menu.add_command(label="运行", command=lambda: run_selected(ctx))
    menu.add_command(label="编辑内容", command=lambda: _edit_content(ctx))
    menu.add_command(label="重命名", command=lambda: rename_selected(ctx))
    menu.add_command(label="删除", command=lambda: delete_selected(ctx))
    menu.add_separator()
    menu.add_command(label="刷新列表", command=lambda: scan_data_directory(ctx))

    menu.post(event.x_root, event.y_root)


def _set_icon(ctx, item, icon):
    set_script_icon(ctx, item["storage_path"], icon)
    if icon:
        ctx.append_output(f"已设置图标：{icon} {item['display']}")
    else:
        ctx.append_output(f"已移除图标：{item['display']}")


def create_group_and_move(ctx: AppContext, item):
    new_group = ctx.group_manager.new_group(ctx.get_root_window())
    if new_group:
        move_script_to_group(ctx, item, new_group)
