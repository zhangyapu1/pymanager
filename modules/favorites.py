"""
收藏功能 - 管理脚本收藏状态，收藏的脚本在列表中置顶显示。

功能：
    is_favorite(settings, storage_path)：
        检查脚本是否在收藏列表中
        - 收藏列表存储在 settings["favorites"] 数组中
        - 返回布尔值

    toggle_favorite(ctx, storage_path)：
        切换脚本的收藏状态
        - 已收藏：从列表移除，输出"已取消收藏"
        - 未收藏：添加到列表，输出"已收藏"
        - 操作后自动保存设置并刷新列表显示

数据存储：
    settings.json → "favorites" 字段，值为 storage_path 字符串数组

依赖：modules.settings_manager
"""
from modules.settings_manager import save_settings


def is_favorite(settings, storage_path):
    return storage_path in settings.get("favorites", [])


def toggle_favorite(ctx, storage_path):
    favorites = ctx.settings.setdefault("favorites", [])
    if storage_path in favorites:
        favorites.remove(storage_path)
        ctx.append_output(f"已取消收藏：{storage_path}")
        ctx.set_status(f"已取消收藏：{storage_path}")
    else:
        favorites.append(storage_path)
        ctx.append_output(f"已收藏：{storage_path}")
        ctx.set_status(f"已收藏：{storage_path}")
    save_settings(ctx.settings)
    ctx.update_listbox()
