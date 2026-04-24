import os
import subprocess
import sys
from tkinter import messagebox

def run_selected(manager):
    item = manager.get_selected_item()
    if not item:
        return
    
    # 获取路径，避免多次字典查找
    storage_path = item.get("storage_path")
    display_name = item.get("display", "未知项目")

    # 基本的路径有效性检查
    if not storage_path:
        messagebox.showerror("运行错误", "未找到可执行文件路径")
        return
        
    if not os.path.isfile(storage_path):
        messagebox.showerror("运行错误", f"文件不存在: {storage_path}")
        return

    try:
        # 安全修复：
        # 1. 移除 shell=True 以防止命令注入攻击。
        # 2. 使用列表形式传递参数，让操作系统直接执行 python 解释器和脚本，
        #    而不是通过 shell 解析字符串。
        subprocess.Popen([sys.executable, storage_path])
        
        manager.status_var.set(f"正在运行：{display_name}")
        
    except FileNotFoundError:
        messagebox.showerror("运行错误", f"无法找到 Python 解释器或文件: {storage_path}")
    except OSError as e:
        messagebox.showerror("运行错误", f"启动失败: {str(e)}")
    except Exception as e:
        # 捕获其他未预见的异常
        messagebox.showerror("运行错误", f"发生未知错误: {str(e)}")