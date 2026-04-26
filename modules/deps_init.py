"""启动依赖检查 - 应用启动时检查并安装框架自身缺失的依赖。"""
import sys
import threading

from modules.logger import log_error, log_info
from modules.dependencies import check_self_dependencies_async


def run_startup_deps_check(ctx):
    ctx.append_output("─── 框架依赖检查 ───")

    def on_deps_complete(needs_restart=False):
        if needs_restart:
            def _restart():
                ctx.ui.show_info("需要重启", "已安装缺失的依赖，需要重新启动程序才能生效。\n点击确定后程序将自动重启。")
                import subprocess
                subprocess.Popen([sys.executable] + sys.argv)
                ctx.get_root_window().destroy()
            ctx.schedule_callback(_restart)

    def run_check():
        try:
            def output_to_console(message):
                log_info(f"[框架依赖] {message}")
                ctx.schedule_callback(lambda: ctx.append_output(message))

            check_self_dependencies_async(
                output_callback=output_to_console,
                ui_callback=ctx.ui,
                on_complete=on_deps_complete
            )
        except (OSError, RuntimeError) as e:
            log_error(f"依赖检查失败：{e}")
            ctx.schedule_callback(lambda: ctx.append_output(f"[错误] 依赖检查时出错：{e}"))

    thread = threading.Thread(target=run_check, daemon=True)
    thread.start()
