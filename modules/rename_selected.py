import os
import re
from tkinter import messagebox, simpledialog

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

def rename_selected(manager):
    item = manager.get_selected_item()
    if not item:
        return

    old_display = item["display"]
    old_rel_path = item["storage_path"]
    old_abs_path = manager._resolve_path(old_rel_path)
    dir_name = os.path.dirname(old_abs_path)

    new_name_input = simpledialog.askstring(
        "重命名",
        "请输入新的显示名称（不含路径）:",
        initialvalue=os.path.basename(old_rel_path)
    )

    if not new_name_input or not new_name_input.strip():
        manager.status_var.set("重命名已取消")
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
        messagebox.showerror("安全错误", "无效的文件名：路径超出允许范围。")
        manager.status_var.set("重命名失败：不安全的路径")
        return

    name_without_ext = new_name_sanitized[:-len(extension)] if new_name_sanitized.endswith(extension) else new_name_sanitized

    final_abs_path = _generate_unique_path(dir_name, name_without_ext, extension, old_abs_path)

    try:
        if os.path.realpath(final_abs_path) != os.path.realpath(old_abs_path):
            os.rename(old_abs_path, final_abs_path)

        final_rel_path = os.path.relpath(final_abs_path, manager.data_dir).replace('\\', '/')
        item["display"] = final_rel_path
        item["storage_path"] = final_rel_path

        manager.update_listbox()
        manager.status_var.set(f"已重命名：{old_display} -> {final_rel_path}")

        expected_name = new_name_sanitized
        final_display_name = os.path.basename(final_rel_path)
        if final_display_name != expected_name:
            messagebox.showinfo(
                "提示",
                f"由于文件名已存在或包含非法字符，\n实际保存为：{final_display_name}"
            )

    except OSError as e:
        messagebox.showerror("重命名失败", f"无法重命名文件：{e}")
        manager.status_var.set("重命名失败")
    except Exception as e:
        messagebox.showerror("未知错误", f"发生未知错误：{e}")
        manager.status_var.set("重命名失败")
