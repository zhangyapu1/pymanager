"""
编辑脚本 - 用内置编辑器打开脚本内容，保存后自动检查依赖。

功能：
    _edit_content(ctx)：
        1. 获取选中脚本项并解析文件路径
        2. 读取脚本内容（仅支持 UTF-8 编码）
        3. 打开 EditorWindow 编辑器窗口
        4. 设置保存和取消回调

    _on_save(editor, ctx, script_path, item)：
        保存流程（后台线程执行）：
        1. 禁用编辑器按钮，显示保存状态
        2. 使用临时文件写入新内容（原子性保存）
        3. shutil.move 替换原文件
        4. 调用 check_script_deps_and_install 检查依赖
        5. 更新脚本列表显示

安全机制：
    - 使用 tempfile.mkstemp 创建临时文件，避免写入中断导致数据丢失
    - 保存失败时自动清理临时文件
    - 非 UTF-8 编码文件提示错误，不强制编辑
    - 依赖检查在后台线程执行，不阻塞 UI

依赖：modules.dependencies, modules.script_manager, modules.app_context, modules.ui_editor
"""
import threading
import os
import subprocess
import tempfile
import shutil

from modules.dependencies import check_script_deps_and_install
from modules.script_manager import resolve_path
from modules.app_context import AppContext


def _edit_content(ctx: AppContext):
    from modules.ui_editor import EditorWindow

    item = ctx.get_selected_item()
    if not item:
        return

    script_rel_path = item["storage_path"]
    script_path = resolve_path(ctx.data_dir, script_rel_path)

    if not os.path.isfile(script_path):
        msg = "脚本文件不存在"
        ctx.append_output(f"[错误] {msg}")
        ctx.ui.show_error("错误", msg)
        return

    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        msg = "文件编码不是 UTF-8，无法编辑"
        ctx.append_output(f"[错误] {msg}")
        ctx.ui.show_error("读取错误", msg)
        return
    except OSError as e:
        msg = f"无法读取脚本内容：{e}"
        ctx.append_output(f"[错误] {msg}")
        ctx.ui.show_error("读取错误", msg)
        return

    title = f"编辑脚本 - {item['display']}"
    editor = EditorWindow(
        parent=ctx.get_root_window(),
        title=title,
        content=content,
        on_save=lambda ed: _on_save(ed, ctx, script_path, item),
        on_cancel=lambda ed: ed.destroy()
    )


def _on_save(editor, ctx, script_path, item):
    editor.set_buttons_enabled(False)
    ctx.set_status("正在保存并检查依赖...")
    editor.set_cursor("watch")

    new_content = editor.get_content()

    def background_check():
        error_msg = None
        save_success = False

        try:
            dir_name = os.path.dirname(script_path)
            fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                shutil.move(temp_path, script_path)
                save_success = True
            except OSError:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                raise
        except OSError as e:
            error_msg = f"文件保存失败：{e}"

        if save_success and not error_msg:
            try:
                check_script_deps_and_install(script_path, item['display'], ctx.get_root_window(), ui_callback=ctx.ui)
            except (OSError, subprocess.SubprocessError) as e:
                error_msg = f"依赖安装失败：{e}"
            except RuntimeError as e:
                error_msg = f"依赖检查失败：{e}"

        ctx.schedule_callback(lambda: _on_check_complete(editor, ctx, item, error_msg))

    thread = threading.Thread(target=background_check, daemon=True)
    thread.start()


def _on_check_complete(editor, ctx, item, error_msg):
    editor.set_cursor("")

    if not editor.exists():
        return

    editor.set_buttons_enabled(True)

    if error_msg:
        ctx.append_output(f"[错误] {error_msg}")
        ctx.ui.show_error("操作错误", error_msg)
        ctx.set_status("操作失败")
    else:
        msg = f"已保存并更新依赖：{item['display']}"
        ctx.append_output(msg)
        ctx.set_status(msg)
        editor.destroy()
