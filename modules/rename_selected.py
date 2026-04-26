"""重命名脚本 - 重命名选中的脚本文件。"""
import os
import re

from modules.script_manager import resolve_path
from modules.app_context import AppContext


def _sanitize_filename(name: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    sanitized = sanitized.strip().strip('.')
    if not sanitized:
        sanitized = "unnamed"
    return sanitized


def _generate_unique_path(dir_name: str, base_name: str, extension: str, original_path: str) -> str:
    candidate_name = f"{base_name}{extension}"
    candidate_path = os.path.join(dir_name, candidate_name)

    counter = 1
    while os.path.exists(candidate_path) and os.path.realpath(candidate_path) != os.path.realpath(original_path):
        candidate_name = f"{base_name}_{counter}{extension}"
        candidate_path = os.path.join(dir_name, candidate_name)
        counter += 1

    return candidate_path


def rename_selected(ctx: AppContext):
    item = ctx.get_selected_item()
    if not item:
        return

    old_display = item["display"]
    old_rel_path = item["storage_path"]
    old_abs_path = resolve_path(ctx.data_dir, old_rel_path)
    dir_name = os.path.dirname(old_abs_path)

    new_name_input = ctx.ui.ask_string(
        "重命名",
        "请输入新的显示名称（不含路径）:",
        initialvalue=os.path.basename(old_rel_path)
    )

    if not new_name_input or not new_name_input.strip():
        ctx.append_output("重命名已取消")
        ctx.set_status("重命名已取消")
        return

    new_name_stripped = new_name_input.strip()
    new_name_sanitized = _sanitize_filename(new_name_stripped)

    extension = '.py'
    if not new_name_sanitized.lower().endswith(extension):
        new_name_sanitized += extension

    base_name_with_ext = os.path.basename(new_name_sanitized)
    if not base_name_with_ext or base_name_with_ext == extension:
        new_name_sanitized = f"script{extension}"

    new_abs_path = os.path.join(dir_name, new_name_sanitized)

    real_dir = os.path.realpath(dir_name)
    real_new_path = os.path.realpath(new_abs_path)

    if not real_new_path.startswith(real_dir + os.sep) and real_new_path != real_dir:
        msg = "无效的文件名：路径超出允许范围。"
        ctx.append_output(f"[错误] {msg}")
        ctx.ui.show_error("安全错误", msg)
        ctx.set_status("重命名失败：不安全的路径")
        return

    name_without_ext = new_name_sanitized[:-len(extension)] if new_name_sanitized.endswith(extension) else new_name_sanitized

    final_abs_path = _generate_unique_path(dir_name, name_without_ext, extension, old_abs_path)

    try:
        if os.path.realpath(final_abs_path) != os.path.realpath(old_abs_path):
            os.rename(old_abs_path, final_abs_path)

        final_rel_path = os.path.relpath(final_abs_path, ctx.data_dir).replace('\\', '/')
        item["display"] = final_rel_path
        item["storage_path"] = final_rel_path

        ctx.update_listbox()
        msg = f"已重命名：{old_display} -> {final_rel_path}"
        ctx.append_output(msg)
        ctx.set_status(msg)

        expected_name = new_name_sanitized
        final_display_name = os.path.basename(final_rel_path)
        if final_display_name != expected_name:
            info_msg = f"由于文件名已存在或包含非法字符，实际保存为：{final_display_name}"
            ctx.append_output(f"[提示] {info_msg}")
            ctx.ui.show_info("提示", info_msg)

    except OSError as e:
        msg = f"无法重命名文件：{e}"
        ctx.append_output(f"[错误] {msg}")
        ctx.ui.show_error("重命名失败", msg)
        ctx.set_status("重命名失败")
