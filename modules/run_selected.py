import os
import subprocess
import sys
import threading
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
        # 清空输出窗口
        if hasattr(manager, 'output_text'):
            manager.output_text.delete(1.0, 'end')
            manager.output_text.insert('end', f"开始运行：{display_name}\n")
            manager.output_text.insert('end', f"运行路径：{storage_path}\n\n")
        
        # 安全修复：
        # 1. 移除 shell=True 以防止命令注入攻击。
        # 2. 使用列表形式传递参数，让操作系统直接执行 python 解释器和脚本，
        #    而不是通过 shell 解析字符串。
        # 3. 捕获 stdout 和 stderr 以便实时显示
        # 4. 确保脚本在其所在目录运行，解决权限问题
        script_dir = os.path.dirname(storage_path)
        # 如果目录不存在，使用当前目录
        if not script_dir:
            script_dir = os.getcwd()
        # 确保目录存在
        os.makedirs(script_dir, exist_ok=True)
        
        process = subprocess.Popen(
            [sys.executable, storage_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=script_dir
        )
        
        manager.status_var.set(f"正在运行：{display_name}")
        
        # 在后台线程中读取输出
        def read_output():
            for line in iter(process.stdout.readline, ''):
                if line:
                    if hasattr(manager, 'output_text'):
                        manager.output_text.insert('end', line)
                        manager.output_text.see('end')
            process.stdout.close()
            process.wait()
            if hasattr(manager, 'output_text'):
                manager.output_text.insert('end', f"\n运行完成，退出码：{process.returncode}\n")
                manager.output_text.see('end')
            manager.status_var.set(f"运行完成：{display_name}")
        
        # 启动后台线程
        output_thread = threading.Thread(target=read_output)
        output_thread.daemon = True
        output_thread.start()
        
    except FileNotFoundError:
        messagebox.showerror("运行错误", f"无法找到 Python 解释器或文件: {storage_path}")
    except OSError as e:
        messagebox.showerror("运行错误", f"启动失败: {str(e)}")
    except Exception as e:
        # 捕获其他未预见的异常
        messagebox.showerror("运行错误", f"发生未知错误: {str(e)}")