import os
import shutil
from tkinter import filedialog, messagebox

try:
    from modules import check_script_deps_and_install
except ImportError:
    check_script_deps_and_install = None

def add_script(manager):
    path = filedialog.askopenfilename(
        title="选择 Python 脚本",
        filetypes=[("Python 文件", "*.py"), ("所有文件", "*.*")]
    )
    if path:
        add_script_from_path(manager, path)

def add_script_from_path(manager, src_path):
    if not os.path.isfile(src_path):
        msg = f"文件不存在：{src_path}"
        manager.append_output(f"[错误] {msg}")
        manager.status_var.set(msg)
        return

    base_name = os.path.basename(src_path)

    dest_abs_path = manager._get_unique_path(manager.data_dir, base_name)

    try:
        shutil.copy2(src_path, dest_abs_path)
    except OSError as e:
        msg = f"无法复制脚本：{e}"
        manager.append_output(f"[错误] {msg}")
        messagebox.showerror("复制失败", msg)
        return

    rel_path = os.path.relpath(dest_abs_path, manager.data_dir).replace('\\', '/')

    manager.scripts.append({
        "display": rel_path,
        "storage_path": rel_path,
        "group": manager.group_manager.current_group
    })
    manager.update_listbox()
    msg = f"已添加：{rel_path}"
    manager.append_output(msg)
    manager.status_var.set(msg)

    if check_script_deps_and_install:
        try:
            check_script_deps_and_install(dest_abs_path, rel_path, manager.root)
        except Exception as dep_e:
            msg = f"脚本已添加，但依赖安装失败：{dep_e}"
            manager.append_output(f"[警告] {msg}")
            messagebox.showwarning("依赖警告", msg)
