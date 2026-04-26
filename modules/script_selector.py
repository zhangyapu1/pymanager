"""脚本选择 - 处理脚本列表选中事件，更新详情显示。"""
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
