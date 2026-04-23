import os
import shutil
from tkinter import filedialog, messagebox

def add_script(manager):
    """通过文件对话框添加脚本"""
    path = filedialog.askopenfilename(
        title="选择 Python 脚本",
        filetypes=[("Python 文件", "*.py"), ("所有文件", "*.*")]
    )
    if path:
        add_script_from_path(manager, path)

def add_script_from_path(manager, src_path):
    """直接通过路径添加脚本（供拖拽使用）"""
    if not os.path.isfile(src_path):
        manager.status_var.set(f"文件不存在：{src_path}")
        return

    # 获取源文件的文件名（含扩展名）
    base_name = os.path.basename(src_path)

    # 处理重名：如果 data 目录中已存在同名文件，则添加序号
    dest_name = base_name
    counter = 1
    name_without_ext, ext = os.path.splitext(base_name)
    while os.path.exists(os.path.join(manager.DATA_DIR, dest_name)):
        dest_name = f"{name_without_ext}_{counter}{ext}"
        counter += 1

    storage_path = os.path.join(manager.DATA_DIR, dest_name)

    try:
        shutil.copy2(src_path, storage_path)
    except Exception as e:
        messagebox.showerror("复制失败", f"无法复制脚本：{e}")
        return

    display_name = dest_name   # 显示名与存储文件名一致
    manager.scripts.append({
        "display": display_name,
        "storage_path": storage_path
    })
    manager.update_listbox()
    manager.status_var.set(f"已添加：{display_name}")
    manager.save_scripts()
    # 检查并安装依赖
    from modules import check_script_deps_and_install
    check_script_deps_and_install(storage_path, display_name, manager.root)