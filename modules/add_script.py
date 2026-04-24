import os
import shutil
from tkinter import filedialog, messagebox

# 优化点：将导入移至模块顶部，避免每次调用函数时重复导入开销
# 假设 modules 包在当前路径下可用
try:
    from modules import check_script_deps_and_install
except ImportError:
    # 如果模块不存在，提供一个空函数或记录日志，防止崩溃
    # 这里为了保持原有功能逻辑，假设环境正确，仅做防御性编程
    check_script_deps_and_install = None

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
    
    # 优化点：增加循环上限，防止极端情况下的无限循环或性能问题
    max_retries = 1000
    while os.path.exists(os.path.join(manager.DATA_DIR, dest_name)):
        if counter > max_retries:
            messagebox.showerror("命名冲突", "无法生成唯一的文件名，请重命名源文件后重试。")
            return
        dest_name = f"{name_without_ext}_{counter}{ext}"
        counter += 1

    storage_path = os.path.join(manager.DATA_DIR, dest_name)

    try:
        shutil.copy2(src_path, storage_path)
    except OSError as e:
        # 优化点：捕获更具体的异常类型，避免掩盖其他严重错误
        messagebox.showerror("复制失败", f"无法复制脚本：{e}")
        return

    # 优化点：直接使用 dest_name，去除不必要的中间变量
    manager.scripts.append({
        "display": dest_name,
        "storage_path": storage_path
    })
    manager.update_listbox()
    manager.status_var.set(f"已添加：{dest_name}")
    
    # 不需要保存脚本列表，因为我们现在基于文件夹结构管理脚本
    
    # 检查并安装依赖
    # 优化点：使用顶部导入的函数，若导入失败则跳过或处理
    if check_script_deps_and_install:
        try:
            check_script_deps_and_install(storage_path, dest_name, manager.root)
        except Exception as dep_e:
            # 依赖安装失败不应阻止脚本添加，但应通知用户
            messagebox.showwarning("依赖警告", f"脚本已添加，但依赖安装失败：{dep_e}")
    else:
        # 如果模块未成功导入，记录日志或静默失败（视具体需求而定）
        pass