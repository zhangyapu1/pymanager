import tkinter as tk

from modules.config import DEFAULT_GROUP
from modules.script_manager import move_script_to_group
from modules.run_selected import run_selected
from modules.rename_selected import rename_selected
from modules.delete_selected import delete_selected
from modules.app_context import AppContext


def _edit_content(ctx):
    from modules.edit_content import _edit_content as _do_edit
    _do_edit(ctx)


def show_context_menu(ctx: AppContext, event):
    item = ctx.get_selected_item()
    if not item:
        return

    current_group = item.get("group", DEFAULT_GROUP)
    menu = tk.Menu(ctx.get_root_window(), tearoff=0)

    move_menu = tk.Menu(menu, tearoff=0)
    other_groups = [g for g in ctx.get_groups() if g != current_group]

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
    menu.add_command(label="刷新列表", command=ctx.scan_data_directory)

    menu.post(event.x_root, event.y_root)


def create_group_and_move(ctx: AppContext, item):
    new_group = ctx.group_manager.new_group(ctx.get_root_window())
    if new_group:
        move_script_to_group(ctx, item, new_group)
