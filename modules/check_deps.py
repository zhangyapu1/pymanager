import threading
import tkinter as tk

from .dependencies import DependencyChecker, check_script_deps_and_install
from .script_manager import resolve_path

def check_and_install_deps(abs_path, display_name, parent_root=None, output_callback=None):
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
            output_callback(f"\n缺少依赖：{', '.join(missing)}")
        else:
            output_callback(f"\n所有依赖已满足")
        output_callback("")

    if not missing:
        return True

    result = check_script_deps_and_install(
        abs_path,
        display_name,
        parent_root,
        output_callback=output_callback
    )

    if result is True:
        return True
    return False

def check_deps(manager):
    def _run_check():
        try:
            item = manager.get_selected_item()

            if not item:
                manager.root.after(0, lambda: manager.status_var.set("未选中任何脚本，无法检查依赖"))
                return

            display_name = item.get("display")
            storage_path = item.get("storage_path")

            if not display_name or not storage_path:
                manager.root.after(0, lambda: manager.status_var.set("选中脚本信息不完整，无法检查依赖"))
                return

            abs_path = resolve_path(manager.data_dir, storage_path)

            manager.root.after(0, lambda: manager.status_var.set(f"正在检查脚本「{display_name}」的依赖"))

            def output_to_console(message):
                manager.root.after(0, lambda: manager.append_output(message))

            ok = check_and_install_deps(abs_path, display_name, manager.root, output_callback=output_to_console)

            if ok:
                msg = f"依赖检查完成：{display_name} 所有依赖已满足"
            else:
                msg = f"依赖检查完成：{display_name} 仍缺少部分依赖"

            manager.root.after(0, lambda: manager.append_output(msg))
            manager.root.after(0, lambda: manager.status_var.set(msg))

        except (OSError, RuntimeError) as e:
            error_msg = str(e) if str(e) else "未知错误"
            manager.root.after(0, lambda: manager.append_output(f"[错误] 检查依赖时发生错误: {error_msg}"))
            manager.root.after(0, lambda: manager.status_var.set(f"检查依赖时发生错误: {error_msg}"))

    thread = threading.Thread(target=_run_check, daemon=True)
    thread.start()
