"""
模块包初始化 - 统一导出核心功能接口，简化外部导入路径。

导出分类：
    脚本操作：
        add_script          - 通过文件对话框添加脚本
        run_selected        - 运行选中脚本
        stop_running        - 停止正在运行的脚本
        rename_selected     - 重命名选中脚本
        edit_content        - 编辑脚本内容（延迟导入，避免循环依赖）
        check_deps          - 检查脚本依赖
        delete_selected     - 删除选中脚本

    脚本管理：
        resolve_path        - 解析脚本相对/绝对路径
        get_unique_path     - 生成不冲突的文件路径
        scan_data_directory - 扫描 data 目录下的脚本
        add_script_from_path- 从指定路径添加脚本
        move_script_to_group- 将脚本移动到指定分组

    UI 与配置：
        show_context_menu   - 显示右键上下文菜单
        extract_docstring   - 提取 Python 文件的 docstring
        load_settings       - 加载应用设置
        save_settings       - 保存应用设置
        load_groups_meta    - 加载分组元数据
        save_groups_meta    - 保存分组元数据

    依赖管理：
        check_self_dependencies_async      - 异步检查框架自身依赖
        check_script_deps_and_install      - 检查并安装脚本依赖
"""
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
