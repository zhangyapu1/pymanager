"""
添加脚本 - 通过文件选择对话框将 Python 脚本添加到当前分组。

功能：
    - 弹出文件选择对话框，支持 .py 文件和所有文件类型过滤
    - 选择文件后调用 script_manager.add_script_from_path 完成添加
    - 脚本会被复制到 data/当前分组/ 目录下

调用方式：
    add_script(ctx)  # ctx 为 AppContext 实例

依赖：modules.script_manager, modules.app_context
"""
from modules.script_manager import add_script_from_path as _add_script_from_path
from modules.app_context import AppContext


def add_script(ctx: AppContext):
    path = ctx.ui.ask_open_filename(
        "选择 Python 脚本",
        [("Python 文件", "*.py"), ("所有文件", "*.*")]
    )
    if path:
        _add_script_from_path(ctx, path)
