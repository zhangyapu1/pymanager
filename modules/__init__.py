"""模块包初始化，导出核心功能接口。"""
from .add_script import add_script
from .run_selected import run_selected, stop_running
from .rename_selected import rename_selected
from .check_deps import check_deps
from .delete_selected import delete_selected
from .dependencies import check_self_dependencies_async, check_script_deps_and_install
from .script_manager import (
    resolve_path, get_unique_path,
    scan_data_directory, add_script_from_path,
    move_script_to_group
)
from .context_menu import show_context_menu
from .utils import extract_docstring
from .settings_manager import load_settings, save_settings, load_groups_meta, save_groups_meta


def edit_content(*args, **kwargs):
    from .edit_content import _edit_content
    return _edit_content(*args, **kwargs)

__all__ = [
    "add_script",
    "add_script_from_path",
    "run_selected",
    "stop_running",
    "rename_selected",
    "edit_content",
    "check_deps",
    "delete_selected",
    "check_self_dependencies",
    "check_script_deps_and_install",
    "resolve_path",
    "get_unique_path",
    "scan_data_directory",
    "add_script_from_path",
    "move_script_to_group",
    "show_context_menu",
    "extract_docstring",
    "load_settings",
    "save_settings",
    "load_groups_meta",
    "save_groups_meta",
]
