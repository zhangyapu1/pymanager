import logging
import threading
# 假设 manager 有 access to a logger, or define one here
logger = logging.getLogger(__name__)

def check_deps(manager):
    """
    检查选中脚本的依赖，并给出明确的状态反馈。
    注意：当前实现为同步阻塞，耗时操作会导致 UI 短暂无响应。
    """
    def _run_check():
        try:
            # 局部导入以避免循环导入
            from .dependencies import check_script_deps_and_install
            
            item = manager.get_selected_item()
            
            # 1. 验证选中项及其必要字段
            if not item:
                manager.status_var.set("未选中任何脚本，无法检查依赖")
                return

            # 安全获取字段，防止 KeyError
            display_name = item.get("display")
            storage_path = item.get("storage_path")

            if not display_name or not storage_path:
                manager.status_var.set("选中脚本信息不完整，无法检查依赖")
                return

            # 在后台线程中更新 UI 需要小心，这里假设 status_var.set 是线程安全的 
            # 或者使用 manager.root.after 来调度 UI 更新
            manager.status_var.set(f"正在检查脚本「{display_name}」的依赖...")
            
            # 强制刷新状态栏，确保用户看到“正在检查”
            try:
                manager.root.update_idletasks()
            except Exception:
                pass

            # 执行依赖检查 (耗时操作)
            result = check_script_deps_and_install(
                storage_path,
                display_name,
                manager.root
            )

            # 2. 明确处理结果状态
            if result is True:
                manager.status_var.set(f"依赖检查完成：{display_name} 所有依赖已满足")
            elif result is False:
                manager.status_var.set(f"依赖检查完成：{display_name} 仍缺少部分依赖")
            elif result is None:
                # 恢复对取消操作的处理
                manager.status_var.set(f"已取消依赖检查：{display_name}")
            else:
                # 处理非标准返回值
                manager.status_var.set(f"依赖检查异常：{display_name} 返回状态未知 ({result})")

        except Exception as e:
            # 3. 全局异常捕获，记录日志并提供反馈
            logger.error(f"检查依赖时发生错误: {e}", exc_info=True)
            error_msg = str(e) if str(e) else "未知错误"
            manager.status_var.set(f"检查依赖时发生错误: {error_msg}")

    # 启动后台线程以避免 UI 阻塞
    # 注意：如果 check_script_deps_and_install 内部有 UI 操作，这种方式可能需要调整
    # 这里假设它可以安全地在后台运行，或者其 UI 交互是通过 manager.root 进行的
    thread = threading.Thread(target=_run_check, daemon=True)
    thread.start()