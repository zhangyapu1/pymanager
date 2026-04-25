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
    }
}


def load_settings():
    saved = load_json("settings.json", {})
    merged = {}
    for section, defaults in SETTINGS_DEFAULTS.items():
        merged[section] = {**defaults, **saved.get(section, {})}
    return merged


def save_settings(settings):
    return save_json("settings.json", settings)


def load_groups_meta():
    return load_json("groups_meta.json", {})


def save_groups_meta(meta):
    return save_json("groups_meta.json", meta)
