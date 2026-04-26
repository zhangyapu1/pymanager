"""
设置管理 - 应用配置和分组元数据的读写，支持默认值合并。

核心函数：
    load_settings()：
        加载应用设置，自动合并默认值
        - 读取 config/settings.json
        - 与 SETTINGS_DEFAULTS 深度合并（字典类型合并，列表类型覆盖）
        - 缺失的配置项自动填充默认值

    save_settings(settings)：
        保存应用设置到 config/settings.json

    load_groups_meta()：
        加载分组元数据（排序信息等）从 config/groups_meta.json

    save_groups_meta(meta)：
        保存分组元数据到 config/groups_meta.json

底层函数：
    load_json(filename, default=None)：
        通用 JSON 文件读取
        - 文件不存在或解析失败返回默认值

    save_json(filename, data)：
        通用 JSON 文件写入
        - 自动创建配置目录
        - 使用 indent=2 和 ensure_ascii=False 格式化

    ensure_config_dir()：
        确保配置目录存在

默认配置（SETTINGS_DEFAULTS）：
    window:
        width: 950, height: 600, x: None, y: None
    log:
        retain_days: 7, max_file_size_mb: 1
    favorites: []
    script_icons: {}

配置文件路径：config/ 目录（由 modules.config.BASE_DIR 确定）

依赖：modules.config
"""
import json
import os
from modules.config import BASE_DIR

CONFIG_DIR = os.path.join(BASE_DIR, "config")


def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_json(filename, default=None):
    filepath = os.path.join(CONFIG_DIR, filename)
    if not os.path.exists(filepath):
        return default if default is not None else {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default if default is not None else {}


def save_json(filename, data):
    ensure_config_dir()
    filepath = os.path.join(CONFIG_DIR, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


SETTINGS_DEFAULTS = {
    "window": {
        "width": 950,
        "height": 600,
        "x": None,
        "y": None
    },
    "log": {
        "retain_days": 7,
        "max_file_size_mb": 1
    },
    "favorites": [],
    "script_icons": {}
}


def load_settings():
    saved = load_json("settings.json", {})
    merged = {}
    for section, defaults in SETTINGS_DEFAULTS.items():
        if isinstance(defaults, dict) and not isinstance(defaults, list):
            merged[section] = {**defaults, **saved.get(section, {})}
        else:
            merged[section] = saved.get(section, defaults)
    return merged


def save_settings(settings):
    return save_json("settings.json", settings)


def load_groups_meta():
    return load_json("groups_meta.json", {})


def save_groups_meta(meta):
    return save_json("groups_meta.json", meta)
