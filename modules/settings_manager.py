"""
设置管理 - 应用配置和分组元数据的读写，支持默认值合并。

核心函数：
    load_settings()：
        加载应用设置，自动合并默认值
        - 读取 config/app_config.json 中的 window, log, favorites, script_icons, recent_runs 部分

    save_settings(settings)：
        保存应用设置到 config/app_config.json

    load_groups_meta()：
        加载分组元数据（排序信息等）从 config/app_config.json 中的 groups_meta 部分

    save_groups_meta(meta)：
        保存分组元数据到 config/app_config.json 中的 groups_meta 部分

底层函数：
    load_app_config() / save_app_config()：
        从 modules.config 导入的统一配置读写函数

配置文件路径：config/app_config.json（由 modules.config.APP_CONFIG_FILE 确定）

依赖：modules.config
"""
from modules.config import load_app_config, save_app_config


def load_settings():
    """加载应用设置（从统一配置中读取 window, log, favorites, script_icons, recent_runs）"""
    app_config = load_app_config()
    return {
        "window": app_config["window"],
        "log": app_config["log"],
        "favorites": app_config["favorites"],
        "script_icons": app_config["script_icons"],
        "recent_runs": app_config["recent_runs"]
    }


def save_settings(settings):
    """保存应用设置（将 window, log, favorites, script_icons, recent_runs 保存到统一配置中）"""
    app_config = load_app_config()
    for key in ["window", "log", "favorites", "script_icons", "recent_runs"]:
        if key in settings:
            app_config[key] = settings[key]
    return save_app_config(app_config)


def load_groups_meta():
    """加载分组元数据（从统一配置中读取 groups_meta）"""
    app_config = load_app_config()
    return app_config.get("groups_meta", {})


def save_groups_meta(meta):
    """保存分组元数据（将 groups_meta 保存到统一配置中）"""
    app_config = load_app_config()
    app_config["groups_meta"] = meta
    return save_app_config(app_config)
