import os
from tkinter import messagebox

def delete_selected(manager):
    item = manager.get_selected_item()
    if not item:
        return
    
    # 获取显示名称和路径，避免多次字典查找
    display_name = item['display']
    storage_path = item["storage_path"]

    if messagebox.askyesno("确认删除", f"从管理器中移除\n{display_name}\n（内部存储的副本也会被删除）"):
        file_deleted = False
        try:
            os.remove(storage_path)
            file_deleted = True
        except FileNotFoundError:
            # 如果文件已经不存在，视为删除成功（目标达成）
            file_deleted = True
        except OSError as e:
            # 如果是权限问题或其他IO错误，删除失败
            messagebox.showwarning("删除警告", f"无法删除内部文件：{e}\n该项目将从列表中保留。")
            return  # 关键：如果文件没删掉，不要从列表中移除，保持一致性

        # 只有文件确实被删除（或已不存在）后，才更新内存结构和UI
        try:
            manager.scripts.remove(item)
        except ValueError:
            # 理论上不应该发生，除非并发修改，防御性编程
            pass
        
        manager.update_listbox()
        # 不需要保存脚本列表，因为我们现在基于文件夹结构管理脚本
        manager.status_var.set(f"已移除：{display_name}")