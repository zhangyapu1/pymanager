"""最近运行 - 记录和查询脚本最近运行时间。"""
import time

from modules.settings_manager import save_settings


def record_run(ctx, storage_path):
    recent = ctx.settings.setdefault("recent_runs", {})
    recent[storage_path] = time.time()
    save_settings(ctx.settings)


def get_last_run_time(settings, storage_path):
    recent = settings.get("recent_runs", {})
    return recent.get(storage_path, 0)


def is_recently_run(settings, storage_path, limit=10):
    recent = settings.get("recent_runs", {})
    if storage_path not in recent:
        return False
    sorted_runs = sorted(recent.items(), key=lambda x: x[1], reverse=True)
    return any(path == storage_path for path, _ in sorted_runs[:limit])


def cleanup_recent_runs(settings, max_entries=50):
    recent = settings.get("recent_runs", {})
    if len(recent) <= max_entries:
        return False
    sorted_runs = sorted(recent.items(), key=lambda x: x[1], reverse=True)
    settings["recent_runs"] = dict(sorted_runs[:max_entries])
    return True
