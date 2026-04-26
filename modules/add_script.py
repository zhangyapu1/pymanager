from modules.script_manager import add_script_from_path as _add_script_from_path
from modules.app_context import AppContext


def add_script(ctx: AppContext):
    path = ctx.ui.ask_open_filename(
        "选择 Python 脚本",
        [("Python 文件", "*.py"), ("所有文件", "*.*")]
    )
    if path:
        _add_script_from_path(ctx, path)
