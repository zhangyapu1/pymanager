import os
from tkinter import messagebox

def delete_selected(manager):
    item = manager.get_selected_item()
    if not item:
        return

    display_name = item['display']
    storage_path = item["storage_path"]
    abs_path = manager._resolve_path(storage_path)

    if messagebox.askyesno("确认删除", f"从管理器中移除\n{display_name}\n（内部存储的副本也会被删除）"):
        file_deleted = False
        try:
            os.remove(abs_path)
            file_deleted = True
        except FileNotFoundError:
            file_deleted = True
        except OSError as e:
            messagebox.showwarning("删除警告", f"无法删除内部文件：{e}\n该项目将从列表中保留。")
            return

        try:
            manager.scripts.remove(item)
        except ValueError:
            pass

        manager.update_listbox()
        manager.status_var.set(f"已移除：{display_name}")
