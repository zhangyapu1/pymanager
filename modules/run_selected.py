import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox

def run_selected(manager):
    item = manager.get_selected_item()
    if not item:
        return

    storage_path = item.get("storage_path")
    display_name = item.get("display", "未知项目")

    if not storage_path:
        messagebox.showerror("运行错误", "未找到可执行文件路径")
        return

    abs_path = manager._resolve_path(storage_path)

    if not os.path.isfile(abs_path):
        messagebox.showerror("运行错误", f"文件不存在: {storage_path}")
        return

    if hasattr(manager, 'running_process') and manager.running_process is not None:
        try:
            if manager.running_process.poll() is None:
                messagebox.showwarning("提示", "已有脚本正在运行，请先停止当前运行")
                return
        except Exception:
            pass

    try:
        if hasattr(manager, 'output_text'):
            manager.output_text.delete(1.0, 'end')
            manager.output_text.insert('end', f"开始运行：{display_name}\n")
            manager.output_text.insert('end', f"运行路径：{storage_path}\n\n")

        script_dir = os.path.dirname(abs_path)
        if not script_dir:
            script_dir = os.getcwd()
        os.makedirs(script_dir, exist_ok=True)

        process = subprocess.Popen(
            [sys.executable, abs_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=script_dir
        )

        manager.running_process = process
        manager._process_stopped = False
        manager.status_var.set(f"正在运行：{display_name}")

        if hasattr(manager, 'stop_btn'):
            manager.stop_btn.config(state=tk.NORMAL)

        def read_output():
            for line in iter(process.stdout.readline, ''):
                if line:
                    if hasattr(manager, 'output_text'):
                        manager.root.after(0, lambda l=line: _insert_output(manager, l))
            process.stdout.close()
            process.wait()
            exit_msg = f"\n运行完成，退出码：{process.returncode}\n"
            manager.root.after(0, lambda: _on_run_complete(manager, display_name, exit_msg))

        output_thread = threading.Thread(target=read_output)
        output_thread.daemon = True
        output_thread.start()

    except FileNotFoundError:
        messagebox.showerror("运行错误", f"无法找到 Python 解释器或文件: {storage_path}")
    except OSError as e:
        messagebox.showerror("运行错误", f"启动失败: {str(e)}")
    except Exception as e:
        messagebox.showerror("运行错误", f"发生未知错误: {str(e)}")

def _insert_output(manager, line):
    if hasattr(manager, 'output_text'):
        manager.output_text.insert('end', line)
        manager.output_text.see('end')

def _on_run_complete(manager, display_name, exit_msg):
    if getattr(manager, '_process_stopped', False):
        return
    if hasattr(manager, 'output_text'):
        manager.output_text.insert('end', exit_msg)
        manager.output_text.see('end')
    manager.running_process = None
    manager.status_var.set(f"运行完成：{display_name}")
    if hasattr(manager, 'stop_btn'):
        manager.stop_btn.config(state=tk.DISABLED)

def stop_running(manager):
    if hasattr(manager, 'running_process') and manager.running_process is not None:
        try:
            if manager.running_process.poll() is None:
                manager._process_stopped = True
                manager.running_process.terminate()
                manager.root.after(0, lambda: _on_stopped(manager))
        except Exception as e:
            err = str(e)
            manager.root.after(0, lambda: manager.status_var.set(f"停止失败: {err}"))
        finally:
            manager.running_process = None

def _on_stopped(manager):
    manager.status_var.set("已停止运行")
    if hasattr(manager, 'output_text'):
        manager.output_text.insert('end', "\n运行已被用户停止\n")
        manager.output_text.see('end')
    if hasattr(manager, 'stop_btn'):
        manager.stop_btn.config(state=tk.DISABLED)
