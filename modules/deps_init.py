"""
启动依赖检查 - 应用启动时异步检查并安装框架自身缺失的依赖。

功能：
    run_startup_deps_check(ctx)：
        1. 输出"框架依赖检查"标题
        2. 在后台线程中执行依赖检查
        3. 通过 output_to_console 回调将检查信息输出到控制台
        4. 使用 ctx.schedule_callback 确保线程安全的 UI 更新
        5. 安装完成后通过 on_deps_complete 回调：
           - 如需重启：弹出提示对话框，确认后自动重启程序
           - 无需重启：静默完成

框架自身依赖：
    - tkinterdnd2：拖放支持
    - ttkbootstrap：现代主题支持

异常处理：
    - OSError / RuntimeError：记录错误日志并输出提示
    - 所有 UI 操作通过 schedule_callback 调度到主线程

依赖：modules.logger, modules.dependencies
"""
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
