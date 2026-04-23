import os
from tkinter import messagebox

def delete_selected(manager):
    item = manager.get_selected_item()
    if not item:
        return
    if messagebox.askyesno("确认删除", f"从管理器中移除\n{item['display']}\n（内部存储的副本也会被删除）"):
        try:
            if os.path.exists(item["storage_path"]):
                os.remove(item["storage_path"])
        except Exception as e:
            messagebox.showwarning("删除警告", f"无法删除内部文件：{e}")
        manager.scripts.remove(item)
        manager.update_listbox()
        manager.save_scripts()
        manager.status_var.set(f"已移除：{item['display']}")