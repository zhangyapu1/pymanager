"""
脚本选择 - 处理脚本列表选中事件，在输出区域显示脚本 docstring。

功能：
    on_script_selected(ctx, event)：
        当用户在脚本列表中选中一个脚本时触发
        1. 获取选中脚本项
        2. 解析脚本文件的绝对路径
        3. 使用 extract_docstring 提取脚本的模块级 docstring
        4. 清空输出区域
        5. 显示脚本名和 docstring 内容
        6. 无 docstring 时显示"该脚本无头注释"

输出格式：
    📄 分组名/脚本名.py
    ────────────────────────────────────────
    脚本的 docstring 内容...

依赖：modules.script_manager, modules.utils
"""
from modules.script_manager import resolve_path
from modules.utils import extract_docstring


def on_script_selected(ctx, event):
    item = ctx.get_selected_item()
    if not item:
        return

    abs_path = resolve_path(ctx.data_dir, item["storage_path"])
    docstring = extract_docstring(abs_path)

    ctx.clear_output()
    if docstring:
        ctx.append_output(f"\U0001f4c4 {item['display']}")
        ctx.append_output("\u2500" * 40)
        ctx.append_output(docstring)
    else:
        ctx.append_output(f"\U0001f4c4 {item['display']}")
        ctx.append_output("\uff08\u8be5\u811a\u672c\u65e0\u5934\u6ce8\u91ca\uff09")
