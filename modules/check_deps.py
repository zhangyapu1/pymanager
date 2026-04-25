import logging
import threading
import tkinter as tk

logger = logging.getLogger(__name__)

def check_deps(manager):
    def _run_check():
        try:
            from .dependencies import check_script_deps_and_install

            item = manager.get_selected_item()

            if not item:
                manager.root.after(0, lambda: manager.status_var.set("未选中任何脚本，无法检查依赖"))
                return

            display_name = item.get("display")
            storage_path = item.get("storage_path")

            if not display_name or not storage_path:
                manager.root.after(0, lambda: manager.status_var.set("选中脚本信息不完整，无法检查依赖"))
                return

            abs_path = manager._resolve_path(storage_path)

            manager.root.after(0, lambda: manager.status_var.set(f"正在检查脚本「{display_name}」的依赖"))

            def output_to_console(message):
                manager.root.after(0, lambda: manager._append_output(message))

            result = check_script_deps_and_install(
                abs_path,
                display_name,
                manager.root,
                output_callback=output_to_console
            )

            if result is True:
                msg = f"依赖检查完成：{display_name} 所有依赖已满足"
            elif result is False:
                msg = f"依赖检查完成：{display_name} 仍缺少部分依赖"
            elif result is None:
                msg = f"已取消依赖检查：{display_name}"
            else:
                msg = f"依赖检查异常：{display_name} 返回状态未知 ({result})"

            manager.root.after(0, lambda: manager.status_var.set(msg))

        except Exception as e:
            logger.error(f"检查依赖时发生错误: {e}", exc_info=True)
            error_msg = str(e) if str(e) else "未知错误"
            manager.root.after(0, lambda: manager.status_var.set(f"检查依赖时发生错误: {error_msg}"))

    thread = threading.Thread(target=_run_check, daemon=True)
    thread.start()
