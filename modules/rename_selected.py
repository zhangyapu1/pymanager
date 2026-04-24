import os
from tkinter import messagebox, simpledialog

def rename_selected(manager):
    item = manager.get_selected_item()
    if not item:
        return
    old_display = item["display"]
    new_name = simpledialog.askstring("重命名", "请输入新的显示名称（不含路径）:", initialvalue=old_display)
    if not new_name or not new_name.strip():
        manager.status_var.set("重命名已取消")
        return
    new_name = new_name.strip()
    if not new_name.endswith('.py'):
        new_name += '.py'
    
    old_path = item["storage_path"]
    dir_name = os.path.dirname(old_path)
    new_path = os.path.join(dir_name, new_name)
    
    base_name = new_name[:-3]
    counter = 1
    while os.path.exists(new_path) and new_path != old_path:
        new_path = os.path.join(dir_name, f"{base_name}_{counter}.py")
        counter += 1
    
    try:
        if new_path != old_path:
            os.rename(old_path, new_path)
        item["display"] = os.path.basename(new_path)
        item["storage_path"] = new_path
        manager.update_listbox()
        # 不需要保存脚本列表，因为我们现在基于文件夹结构管理脚本
        manager.status_var.set(f"已重命名：{old_display} -> {item['display']}")
        if item["display"] != new_name:
            messagebox.showinfo("提示", f"由于文件名已存在，实际保存为：{item['display']}")
    except Exception as e:
        messagebox.showerror("重命名失败", f"无法重命名文件：{e}")
        manager.status_var.set("重命名失败")