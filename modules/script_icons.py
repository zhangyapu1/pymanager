"""
脚本图标 - 管理脚本的自定义图标显示，通过右键菜单设置。

功能：
    get_script_icon(settings, storage_path)：
        获取脚本的自定义图标字符
        - 从 settings["script_icons"] 字典中读取
        - 未设置时返回空字符串

    set_script_icon(ctx, storage_path, icon)：
        设置脚本的自定义图标
        - icon 非空时写入 settings["script_icons"]
        - icon 为空时移除该脚本的图标设置
        - 保存设置后刷新列表显示

可用图标（ICON_OPTIONS）：
    无图标、📋列表、⚙设置、📝笔记、📊图表、🌐网络、💾保存、
    🔧工具、📁文件夹、🔍搜索、🛠维修、☀太阳、🌙月亮、🚀火箭、
    ⭐星标、🔖书签、📦包裹、📄文档、🎯目标、🔐锁定

数据存储：
    settings.json → "script_icons" 字段
    格式：{"相对路径": "图标字符", ...}

依赖：modules.settings_manager
"""
from modules.settings_manager import save_settings

ICON_OPTIONS = [
    ("无图标", ""),
    ("📋 列表", "\U0001f4cb"),
    ("⚙️ 设置", "\u2699\ufe0f"),
    ("📝 笔记", "\U0001f4dd"),
    ("📊 图表", "\U0001f4ca"),
    ("🌐 网络", "\U0001f310"),
    ("💾 保存", "\U0001f4be"),
    ("🔧 工具", "\U0001f527"),
    ("📁 文件夹", "\U0001f4c1"),
    ("🔍 搜索", "\U0001f50d"),
    ("🛠️ 维修", "\U0001f6e0\ufe0f"),
    ("☀️ 太阳", "\u2600\ufe0f"),
    ("🌙 月亮", "\U0001f319"),
    ("🚀 火箭", "\U0001f680"),
    ("⭐ 星标", "\u2b50"),
    ("🔖 书签", "\U0001f516"),
    ("📦 包裹", "\U0001f4e6"),
    ("📄 文档", "\U0001f4c4"),
    ("🎯 目标", "\U0001f3af"),
    ("🔐 锁定", "\U0001f510"),
]


def get_script_icon(settings, storage_path):
    return settings.get("script_icons", {}).get(storage_path, "")


def set_script_icon(ctx, storage_path, icon):
    icons = ctx.settings.setdefault("script_icons", {})
    if icon:
        icons[storage_path] = icon
    else:
        icons.pop(storage_path, None)
    save_settings(ctx.settings)
    ctx.update_listbox()
