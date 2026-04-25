import tkinter as tk

from modules.config import DEFAULT_GROUP
from modules.script_manager import move_script_to_group
from modules.run_selected import run_selected
from modules.edit_content import edit_content
from modules.rename_selected import rename_selected
from modules.delete_selected import delete_selected


def show_context_menu(manager, event):
    selected = manager.listbox.curselection()
    if not selected:
        return
    item = manager.get_selected_item()
    if not item:
        return

    current_group = item.get("group", DEFAULT_GROUP)
    menu = tk.Menu(manager.root, tearoff=0)

    move_menu = tk.Menu(menu, tearoff=0)
    other_groups = [g for g in manager.group_manager.groups if g != current_group]

    for group in other_groups:
        move_menu.add_command(label=group, command=lambda g=group: move_script_to_group(manager, item, g))

    if not other_groups:
        move_menu.add_command(label="无其他分组", state="disabled")

    move_menu.add_separator()
    move_menu.add_command(label="新建分组...", command=lambda: create_group_and_move(manager, item))

    menu.add_cascade(label="移动到分组", menu=move_menu)
    menu.add_separator()
    menu.add_command(label="运行", command=lambda: run_selected(manager))
    menu.add_command(label="编辑内容", command=lambda: edit_content(manager))
    menu.add_command(label="重命名", command=lambda: rename_selected(manager))
    menu.add_command(label="删除", command=lambda: delete_selected(manager))
    menu.add_separator()
    menu.add_command(label="刷新列表", command=manager.scan_data_directory)

    menu.post(event.x_root, event.y_root)


def create_group_and_move(manager, item):
    new_group = manager.group_manager.new_group(manager.root)
    if new_group:
        move_script_to_group(manager, item, new_group)
