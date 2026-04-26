"""列表显示 - 更新脚本列表的显示内容，包括图标、收藏标记等。"""
import tkinter as tk

from modules.favorites import is_favorite
from modules.script_icons import get_script_icon
from modules.recent_runs import get_last_run_time


def update_listbox(ui_state, scripts, settings, current_group, search_keyword=""):
    listbox = ui_state.listbox
    if not listbox:
        return
    listbox.delete(0, tk.END)
    ui_state.listbox_items = []

    keyword = search_keyword.strip().lower()

    favorites_list = settings.get("favorites", [])
    fav_items = []
    recent_items = []
    normal_items = []
    for item in scripts:
        if item.get("group") != current_group:
            continue
        if keyword and keyword not in item["display"].lower() and keyword not in item["storage_path"].lower():
            continue
        if item["storage_path"] in favorites_list:
            fav_items.append(item)
        elif get_last_run_time(settings, item["storage_path"]) > 0:
            recent_items.append(item)
        else:
            normal_items.append(item)

    recent_items.sort(key=lambda x: get_last_run_time(settings, x["storage_path"]), reverse=True)

    for item in fav_items:
        icon = get_script_icon(settings, item["storage_path"])
        prefix = f"{icon} " if icon else "\u2b50 "
        listbox.insert(tk.END, f"{prefix}{item['display']}")
        ui_state.listbox_items.append(item)

    for item in recent_items:
        icon = get_script_icon(settings, item["storage_path"])
        if icon:
            listbox.insert(tk.END, f"{icon} {item['display']}")
        else:
            listbox.insert(tk.END, item["display"])
        ui_state.listbox_items.append(item)

    for item in normal_items:
        icon = get_script_icon(settings, item["storage_path"])
        if icon:
            listbox.insert(tk.END, f"{icon} {item['display']}")
        else:
            listbox.insert(tk.END, item["display"])
        ui_state.listbox_items.append(item)
