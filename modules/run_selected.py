import os
import subprocess
import sys
import threading

from .check_deps import check_and_install_deps
from .script_manager import resolve_path
from .app_context import AppContext
from .logger import log_info


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

    running = ctx.get_running_process()
    if running is not None:
        try:
            if running.poll() is None:
                ctx.append_output("[提示] 已有脚本正在运行，请先停止当前运行")
                ctx.ui.show_warning("提示", "已有脚本正在运行，请先停止当前运行")
                return
        except (OSError, subprocess.SubprocessError):
            pass

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

        process = subprocess.Popen(
            [sys.executable, abs_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=script_dir
        )

        ctx.set_running_process(process)
        ctx.set_process_stopped(False)
        ctx.set_status(f"正在运行：{display_name}")
        ctx.set_stop_button_enabled(True)

        def read_output():
            for line in iter(process.stdout.readline, ''):
                if line:
                    ctx.schedule_callback(lambda l=line: _insert_output(ctx, l))
            process.stdout.close()
            process.wait()
            exit_msg = f"运行完成，退出码：{process.returncode}"
            ctx.schedule_callback(lambda: _on_run_complete(ctx, display_name, exit_msg))

        output_thread = threading.Thread(target=read_output)
        output_thread.daemon = True
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
    if ctx.is_process_stopped():
        return
    ctx.append_output(exit_msg)
    ctx.set_running_process(None)
    ctx.set_status(f"运行完成：{display_name}")
    ctx.set_stop_button_enabled(False)


def stop_running(ctx: AppContext):
    running = ctx.get_running_process()
    if running is not None:
        try:
            if running.poll() is None:
                ctx.set_process_stopped(True)
                running.terminate()
                ctx.schedule_callback(lambda: _on_stopped(ctx))
        except (OSError, subprocess.SubprocessError) as e:
            err = str(e)
            ctx.schedule_callback(lambda: ctx.set_status(f"停止失败: {err}"))
        finally:
            ctx.set_running_process(None)


def _on_stopped(ctx: AppContext):
    ctx.set_status("已停止运行")
    ctx.append_output("运行已被用户停止")
    ctx.set_stop_button_enabled(False)
