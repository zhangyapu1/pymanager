import os
import shutil
import tkinter as tk

from modules.config import DATA_DIR, DEFAULT_GROUP
from modules.logger import log_error
from modules.dependencies import check_script_deps_and_install


def resolve_path(data_dir, rel_path):
    if os.path.isabs(rel_path):
        return rel_path
    return os.path.join(data_dir, rel_path)


def get_unique_path(directory, filename):
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        return path

    name_without_ext, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_filename = f"{name_without_ext}_{counter}{ext}"
        path = os.path.join(directory, new_filename)
        if not os.path.exists(path):
            return path
        counter += 1


def get_selected_item(manager):
    sel = manager.listbox.curselection()
    if not sel:
        return None

    display_name = manager.listbox.get(sel[0])
    for item in manager.scripts:
        if item["display"] == display_name and item.get("group") == manager.group_manager.current_group:
            return item
    return None


def update_listbox(manager):
    manager.listbox.delete(0, tk.END)
    for item in manager.scripts:
        if item.get("group") == manager.group_manager.current_group:
            manager.listbox.insert(tk.END, item["display"])


def scan_data_directory(manager):
    added = 0
    updated = 0

    for root, dirs, files in os.walk(manager.data_dir):
        for file_name in files:
            if file_name.endswith('.py'):
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, manager.data_dir).replace('\\', '/')

                relative_dir = os.path.dirname(relative_path)
                if relative_dir == '.' or relative_dir == '':
                    group = DEFAULT_GROUP
                else:
                    group = relative_dir.split('/')[0]

                existing_index = None
                for i, script in enumerate(manager.scripts):
                    if script['storage_path'] == relative_path:
                        existing_index = i
                        break

                if existing_index is not None:
                    manager.scripts[existing_index]["display"] = relative_path
                    manager.scripts[existing_index]["group"] = group
                    updated += 1
                else:
                    manager.scripts.append({
                        "display": relative_path,
                        "storage_path": relative_path,
                        "group": group
                    })
                    added += 1

    groups_set = set()
    for script in manager.scripts:
        groups_set.add(script.get("group", DEFAULT_GROUP))

    groups_changed = False
    for g in groups_set:
        if g not in manager.group_manager.groups:
            manager.group_manager.groups.append(g)
            groups_changed = True

    if groups_changed:
        manager.group_manager.save_groups()
        manager.group_manager.refresh_combo()

    if added > 0 or updated > 0:
        update_listbox(manager)
        manager.status_var.set(f"扫描完成：添加 {added} 个脚本，更新 {updated} 个脚本")
        manager.append_output(f"扫描完成：添加 {added} 个脚本，更新 {updated} 个脚本")


def add_script_from_path(manager, src_path):
    if not os.path.isfile(src_path):
        manager.status_var.set(f"文件不存在：{src_path}")
        manager.append_output(f"[错误] 文件不存在：{src_path}")
        return

    base_name = os.path.basename(src_path)

    dest_abs_path = get_unique_path(manager.data_dir, base_name)
    dest_name = os.path.basename(dest_abs_path)

    try:
        shutil.copy2(src_path, dest_abs_path)
    except PermissionError as e:
        log_error(f"复制脚本失败(权限): {e}")
        manager.append_output(f"[错误] 权限不足，无法复制脚本：{e}")
        from tkinter import messagebox
        messagebox.showerror("复制失败", f"权限不足，无法复制脚本：{e}")
        return
    except OSError as e:
        log_error(f"复制脚本失败: {e}")
        manager.append_output(f"[错误] 无法复制脚本：{e}")
        from tkinter import messagebox
        messagebox.showerror("复制失败", f"无法复制脚本：{e}")
        return

    rel_path = os.path.relpath(dest_abs_path, manager.data_dir).replace('\\', '/')

    new_script = {
        "display": rel_path,
        "storage_path": rel_path,
        "group": manager.group_manager.current_group
    }

    manager.scripts.append(new_script)
    update_listbox(manager)
    manager.status_var.set(f"已添加：{rel_path} (分组：{manager.group_manager.current_group})")
    manager.append_output(f"已添加：{rel_path} (分组：{manager.group_manager.current_group})")

    manager.group_manager.save_groups()

    def output_to_console(message):
        manager.root.after(0, lambda: manager.append_output(message))

    try:
        check_script_deps_and_install(dest_abs_path, rel_path, manager.root, output_callback=output_to_console)
    except (OSError, RuntimeError) as e:
        log_error(f"依赖检查异常: {e}")


def move_script_to_group(manager, item, target_group):
    if item["group"] == target_group:
        return
    old_group = item["group"]

    old_rel_path = item["storage_path"]
    old_abs_path = resolve_path(manager.data_dir, old_rel_path)
    file_name = os.path.basename(old_abs_path)

    if target_group == DEFAULT_GROUP:
        target_dir = manager.data_dir
    else:
        target_dir = os.path.join(manager.data_dir, target_group)
        os.makedirs(target_dir, exist_ok=True)

    new_abs_path = get_unique_path(target_dir, file_name)

    try:
        shutil.move(old_abs_path, new_abs_path)

        item["group"] = target_group
        item["storage_path"] = os.path.relpath(new_abs_path, manager.data_dir).replace('\\', '/')
        item["display"] = item["storage_path"]

        manager.group_manager.save_groups()

        update_listbox(manager)
        manager.status_var.set(f"已将「{item['display']}」从「{old_group}」移动到「{target_group}」")

    except OSError as e:
        log_error(f"移动文件失败: {e}")
        manager.append_output(f"[错误] 移动文件失败：{e}")
        from tkinter import messagebox
        messagebox.showerror("错误", f"移动文件失败：{e}")
