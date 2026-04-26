"""运行脚本 - 执行选中的脚本并管理运行状态。"""
import os
import subprocess
import sys
import threading
import time

from .check_deps import check_and_install_deps
from .script_manager import resolve_path
from .app_context import AppContext
from .logger import log_info
from .recent_runs import record_run


def run_selected(ctx: AppContext):
    item = ctx.get_selected_item()
    if not item:
        return

    storage_path = item.get("storage_path")
    display_name = item.get("display", "未知项目")

    if not storage_path:
        ctx.append_output("[错误] 未找到可执行文件路径")
        ctx.ui.show_error("运行错误", "未找到可执行文件路径")
        return

    abs_path = resolve_path(ctx.data_dir, storage_path)

    if not os.path.isfile(abs_path):
        ctx.append_output(f"[错误] 文件不存在: {storage_path}")
        ctx.ui.show_error("运行错误", f"文件不存在: {storage_path}")
        return

    def _run():
        def output_to_console(message):
            log_info(f"[依赖检查] {message}")
            ctx.schedule_callback(lambda: ctx.append_output(message))

        if not check_and_install_deps(abs_path, display_name, ctx.get_root_window(), ui_callback=ctx.ui, output_callback=output_to_console):
            ctx.schedule_callback(lambda: ctx.append_output(f"[提示] 依赖未满足，取消运行：{display_name}"))
            return

        ctx.schedule_callback(lambda: _launch_script(ctx, abs_path, storage_path, display_name))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def _launch_script(ctx: AppContext, abs_path, storage_path, display_name):
    try:
        ctx.clear_output()
        ctx.append_output(f"开始运行：{display_name}")
        ctx.append_output(f"运行路径：{storage_path}")
        ctx.append_output("")

        script_dir = os.path.dirname(abs_path)
        if not script_dir:
            script_dir = os.getcwd()
        os.makedirs(script_dir, exist_ok=True)

        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

        process = subprocess.Popen(
            [sys.executable, abs_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=script_dir,
            creationflags=creationflags
        )

        pm = ctx.process_manager
        pm.add_process(process, display_name)
        record_run(ctx, storage_path)
        ctx.schedule_callback(lambda: ctx.update_listbox())
        ctx.schedule_callback(lambda: ctx.set_status(f"已启动：{display_name}（独立进程）"))

        def read_output():
            while True:
                try:
                    line = process.stdout.readline()
                except (OSError, ValueError):
                    break
                if not line:
                    if process.poll() is not None:
                        break
                    time.sleep(0.05)
                    continue
                ctx.schedule_callback(lambda l=line: _insert_output(ctx, l))

            try:
                process.stdout.close()
            except (OSError, ValueError):
                pass

            exit_code = process.returncode
            pm.remove_process(process)
            exit_msg = f"运行完成：{display_name}，退出码：{exit_code}"
            ctx.schedule_callback(lambda: _on_run_complete(ctx, display_name, exit_msg))

        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()

    except FileNotFoundError:
        ctx.append_output(f"[错误] 无法找到 Python 解释器或文件: {storage_path}")
        ctx.ui.show_error("运行错误", f"无法找到 Python 解释器或文件: {storage_path}")
    except PermissionError as e:
        ctx.append_output(f"[错误] 权限不足，无法运行: {e}")
        ctx.ui.show_error("运行错误", f"权限不足，无法运行: {e}")
    except OSError as e:
        ctx.append_output(f"[错误] 启动失败: {e}")
        ctx.ui.show_error("运行错误", f"启动失败: {e}")


def _insert_output(ctx: AppContext, line):
    ctx.append_output(line.rstrip('\n'))


def _on_run_complete(ctx: AppContext, display_name, exit_msg):
    ctx.append_output(exit_msg)
    pm = ctx.process_manager
    count = pm.running_count()
    if count == 0:
        ctx.set_status(f"运行完成：{display_name}")
    else:
        ctx.set_status(f"运行完成：{display_name}（还有 {count} 个脚本在运行）")


def stop_running(ctx: AppContext):
    pm = ctx.process_manager
    names = pm.terminate_all()
    if names:
        ctx.set_status(f"已停止运行：{', '.join(names)}")
        ctx.append_output(f"已停止运行：{', '.join(names)}")
    else:
        ctx.set_status("没有正在运行的脚本")
