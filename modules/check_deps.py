import threading

from .dependencies import DependencyChecker, check_script_deps_and_install
from .script_manager import resolve_path
from .app_context import AppContext
from .logger import log_info, log_warning, log_error


def check_and_install_deps(abs_path, display_name, parent_root=None, ui_callback=None, output_callback=None):
    all_imports = DependencyChecker.extract_imports_from_script(abs_path)
    third_party = sorted(mod for mod in all_imports if not DependencyChecker.is_stdlib_module(mod))

    if output_callback:
        output_callback(f"─── 脚本「{display_name}」依赖检查 ───")
        output_callback(f"扫描到的所有导入：{', '.join(sorted(all_imports)) or '无'}")
        output_callback(f"第三方依赖：{', '.join(third_party) or '无'}")

        if third_party:
            output_callback("")
            for mod in third_party:
                installed = DependencyChecker.is_package_installed(mod)
                status = "已安装" if installed else "未安装"
                output_callback(f"  {mod}: {status}")

    missing = DependencyChecker.get_missing_dependencies(abs_path)

    if output_callback:
        if missing:
            output_callback(f"\n缺少直接依赖：{', '.join(missing)}")
        else:
            output_callback(f"\n直接依赖已满足，正在验证传递依赖...")

    if missing:
        result = check_script_deps_and_install(
            abs_path,
            display_name,
            parent_root,
            ui_callback=ui_callback,
            output_callback=output_callback
        )

        if result is not True:
            return False

    transitive_missing = DependencyChecker.verify_imports(abs_path, output_callback=output_callback)

    if transitive_missing:
        if output_callback:
            output_callback(f"\n发现传递依赖缺失：{', '.join(transitive_missing)}")

        msg = f"脚本「{display_name}」的依赖包缺少以下传递依赖：\n{', '.join(transitive_missing)}\n是否立即安装？（将使用加速镜像源）"
        if ui_callback:
            confirmed = ui_callback.ask_yes_no("缺少传递依赖", msg, parent=parent_root)
        else:
            confirmed = False

        if confirmed:
            for pkg in transitive_missing:
                DependencyChecker.install_package(pkg, parent_root, output_callback=output_callback, ui_callback=ui_callback)

            still_missing = DependencyChecker.verify_imports(abs_path)
            if still_missing:
                warn_msg = f"传递依赖仍未满足：{', '.join(still_missing)}"
                if output_callback:
                    output_callback(f"[警告] {warn_msg}")
                if ui_callback:
                    ui_callback.show_warning("部分依赖未安装", warn_msg, parent=parent_root)
                return False
            else:
                if output_callback:
                    output_callback("所有传递依赖已安装")
                return True
        else:
            return False

    if output_callback:
        output_callback("所有依赖已满足")
        output_callback("")

    return True


def check_deps(ctx: AppContext):
    def _run_check():
        try:
            item = ctx.get_selected_item()

            if not item:
                ctx.schedule_callback(lambda: ctx.set_status("未选中任何脚本，无法检查依赖"))
                return

            display_name = item.get("display")
            storage_path = item.get("storage_path")

            if not display_name or not storage_path:
                ctx.schedule_callback(lambda: ctx.set_status("选中脚本信息不完整，无法检查依赖"))
                return

            abs_path = resolve_path(ctx.data_dir, storage_path)

            ctx.schedule_callback(lambda: ctx.set_status(f"正在检查脚本「{display_name}」的依赖"))

            def output_to_console(message):
                log_info(f"[依赖检查] {message}")
                ctx.schedule_callback(lambda: ctx.append_output(message))

            ok = check_and_install_deps(abs_path, display_name, ctx.get_root_window(), ui_callback=ctx.ui, output_callback=output_to_console)

            if ok:
                msg = f"依赖检查完成：{display_name} 所有依赖已满足"
            else:
                msg = f"依赖检查完成：{display_name} 仍缺少部分依赖"

            ctx.schedule_callback(lambda: ctx.append_output(msg))
            ctx.schedule_callback(lambda: ctx.set_status(msg))

        except (OSError, RuntimeError) as e:
            error_msg = str(e) if str(e) else "未知错误"
            ctx.schedule_callback(lambda: ctx.append_output(f"[错误] 检查依赖时发生错误: {error_msg}"))
            ctx.schedule_callback(lambda: ctx.set_status(f"检查依赖时发生错误: {error_msg}"))

    thread = threading.Thread(target=_run_check, daemon=True)
    thread.start()
