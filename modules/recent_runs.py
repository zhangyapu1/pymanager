"""
最近运行 - 记录和查询脚本最近运行时间，用于列表排序和状态显示。

功能：
    record_run(ctx, storage_path)：
        记录脚本运行时间戳
        - 存储在 settings["recent_runs"] 字典中
        - 键为 storage_path，值为 Unix 时间戳
        - 记录后自动保存设置

    get_last_run_time(settings, storage_path)：
        获取脚本最近运行时间戳
        - 未运行过返回 0

    is_recently_run(settings, storage_path, limit=10)：
        判断脚本是否在最近运行的 limit 个脚本中
        - 按时间倒序排列，取前 limit 个
        - 用于列表显示中的"最近运行"分组

    cleanup_recent_runs(settings, max_entries=50)：
        清理过多的运行记录
        - 超过 max_entries 时保留最近的记录
        - 返回是否执行了清理

数据存储：
    settings.json → "recent_runs" 字段
    格式：{"相对路径": Unix时间戳, ...}

依赖：modules.settings_manager
"""
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
