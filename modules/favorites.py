"""收藏功能 - 管理脚本收藏状态。"""
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
