import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox

from .check_deps import check_and_install_deps

def run_selected(manager):
    item = manager.get_selected_item()
    if not item:
        return

    storage_path = item.get("storage_path")
    display_name = item.get("display", "未知项目")

    if not storage_path:
        manager.append_output("[错误] 未找到可执行文件路径")
        messagebox.showerror("运行错误", "未找到可执行文件路径")
        return

    abs_path = manager._resolve_path(storage_path)

    if not os.path.isfile(abs_path):
        manager.append_output(f"[错误] 文件不存在: {storage_path}")
        messagebox.showerror("运行错误", f"文件不存在: {storage_path}")
        return

    if hasattr(manager, 'running_process') and manager.running_process is not None:
        try:
            if manager.running_process.poll() is None:
                manager.append_output("[提示] 已有脚本正在运行，请先停止当前运行")
                messagebox.showwarning("提示", "已有脚本正在运行，请先停止当前运行")
                return
        except Exception:
            pass

    def _run():
        def output_to_console(message):
            manager.root.after(0, lambda: manager.append_output(message))

        if not check_and_install_deps(abs_path, display_name, manager.root, output_callback=output_to_console):
            manager.root.after(0, lambda: manager.append_output(f"[提示] 依赖未满足，取消运行：{display_name}"))
            return

        manager.root.after(0, lambda: _launch_script(manager, abs_path, storage_path, display_name))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

def _launch_script(manager, abs_path, storage_path, display_name):
    try:
        if hasattr(manager, 'output_text'):
            manager.output_text.delete(1.0, 'end')
        manager.append_output(f"开始运行：{display_name}")
        manager.append_output(f"运行路径：{storage_path}")
        manager.append_output("")

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
                    manager.root.after(0, lambda l=line: _insert_output(manager, l))
            process.stdout.close()
            process.wait()
            exit_msg = f"运行完成，退出码：{process.returncode}"
            manager.root.after(0, lambda: _on_run_complete(manager, display_name, exit_msg))

        output_thread = threading.Thread(target=read_output)
        output_thread.daemon = True
        output_thread.start()

    except FileNotFoundError:
        manager.append_output(f"[错误] 无法找到 Python 解释器或文件: {storage_path}")
        messagebox.showerror("运行错误", f"无法找到 Python 解释器或文件: {storage_path}")
    except OSError as e:
        manager.append_output(f"[错误] 启动失败: {str(e)}")
        messagebox.showerror("运行错误", f"启动失败: {str(e)}")
    except Exception as e:
        manager.append_output(f"[错误] 发生未知错误: {str(e)}")
        messagebox.showerror("运行错误", f"发生未知错误: {str(e)}")

def _insert_output(manager, line):
    manager.append_output(line.rstrip('\n'))

def _on_run_complete(manager, display_name, exit_msg):
    if getattr(manager, '_process_stopped', False):
        return
    manager.append_output(exit_msg)
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
    manager.append_output("运行已被用户停止")
    if hasattr(manager, 'stop_btn'):
        manager.stop_btn.config(state=tk.DISABLED)
