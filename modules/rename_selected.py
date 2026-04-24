import os
import re
from tkinter import messagebox, simpledialog

def _sanitize_filename(name: str) -> str:
    """
    清理文件名，移除或替换非法字符。
    针对 Windows 和 Unix 常见非法字符进行处理。
    """
    # 移除或替换常见的非法字符: < > : " / \ | ? *
    # 这里选择替换为下划线，以保持文件名可读性
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    # 去除首尾空格和点（Windows 不允许文件名以点或空格结尾）
    sanitized = sanitized.strip().strip('.')
    if not sanitized:
        sanitized = "unnamed"
    return sanitized

def _generate_unique_path(dir_name: str, base_name: str, extension: str, original_path: str) -> str:
    """
    生成一个不存在的唯一文件路径。
    如果基础名称可用，则返回基础路径；否则添加计数器。
    """
    candidate_name = f"{base_name}{extension}"
    candidate_path = os.path.join(dir_name, candidate_name)
    
    counter = 1
    # 检查文件是否存在，且不是原文件本身（允许原地重命名，即大小写变更等场景，虽然os.rename在同一路径下可能行为不同，但此处逻辑主要是避免覆盖其他文件）
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
    old_path = item["storage_path"]
    
    # 获取原始目录，用于后续安全校验
    dir_name = os.path.dirname(old_path)
    
    # 1. 获取用户输入
    new_name_input = simpledialog.askstring(
        "重命名", 
        "请输入新的显示名称（不含路径）:", 
        initialvalue=old_display
    )
    
    # 2. 验证输入是否为空
    if not new_name_input or not new_name_input.strip():
        manager.status_var.set("重命名已取消")
        return
    
    # 3. 清理和格式化文件名
    new_name_stripped = new_name_input.strip()
    new_name_sanitized = _sanitize_filename(new_name_stripped)
    
    # 确保扩展名正确
    extension = '.py'
    if not new_name_sanitized.lower().endswith(extension):
        new_name_sanitized += extension
    
    # 再次检查清理后的文件名是否有效（防止全是非法字符导致变成空）
    base_name_with_ext = os.path.basename(new_name_sanitized)
    if not base_name_with_ext or base_name_with_ext == extension:
         # 如果清理后只剩下扩展名或为空，给予默认名
         base_name_clean = "script"
         new_name_sanitized = f"{base_name_clean}{extension}"
    
    # 4. 构建新路径并进行安全校验
    new_path = os.path.join(dir_name, new_name_sanitized)
    
    # 安全检查：确保新路径仍在原目录下，防止路径遍历攻击
    real_dir = os.path.realpath(dir_name)
    real_new_path = os.path.realpath(new_path)
    
    # 注意：os.path.realpath 会解析符号链接。如果新路径尚未存在，realpath 可能基于父目录解析。
    # 更严格的检查是确保新路径以原目录开头
    if not real_new_path.startswith(real_dir + os.sep) and real_new_path != real_dir:
        messagebox.showerror("安全错误", "无效的文件名：路径超出允许范围。")
        manager.status_var.set("重命名失败：不安全的路径")
        return

    # 5. 处理文件名冲突，生成唯一路径
    # 提取不带扩展名的基础名用于冲突处理逻辑
    name_without_ext = new_name_sanitized[:-len(extension)] if new_name_sanitized.endswith(extension) else new_name_sanitized
    
    final_path = _generate_unique_path(dir_name, name_without_ext, extension, old_path)
    
    # 6. 执行重命名
    try:
        # 只有当路径真正改变时才执行系统重命名
        if os.path.realpath(final_path) != os.path.realpath(old_path):
            os.rename(old_path, final_path)
        
        # 更新数据模型
        final_display_name = os.path.basename(final_path)
        item["display"] = final_display_name
        item["storage_path"] = final_path
        
        # 更新 UI
        manager.update_listbox()
        
        # 设置状态栏
        manager.status_var.set(f"已重命名：{old_display} -> {final_display_name}")
        
        # 如果最终文件名与用户期望的不一致（因为冲突或非法字符清理），提示用户
        expected_name = new_name_sanitized
        if final_display_name != expected_name:
            messagebox.showinfo(
                "提示", 
                f"由于文件名已存在或包含非法字符，\n实际保存为：{final_display_name}"
            )
            
    except OSError as e:
        # 专门捕获操作系统相关的 IO 错误
        messagebox.showerror("重命名失败", f"无法重命名文件：{e}")
        manager.status_var.set("重命名失败")
    except Exception as e:
        # 捕获其他未预见的错误
        messagebox.showerror("未知错误", f"发生未知错误：{e}")
        manager.status_var.set("重命名失败")