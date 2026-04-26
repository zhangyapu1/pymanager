"""
日志模块 - 错误日志、输出日志的记录与自动清理。

日志文件：
    ERROR_LOG_FILE  - logs/error_log.txt，记录错误和警告信息
    OUTPUT_LOG_FILE - logs/output_log.txt，记录程序输出信息

日志级别函数：
    log_error(error_msg)   - 记录 ERROR 级别日志，自动附加异常堆栈
    log_warning(warning_msg) - 记录 WARNING 级别日志
    log_info(info_msg)     - 记录 INFO 级别日志
    log_output(message)    - 记录程序输出到 OUTPUT_LOG_FILE

日志格式：
    [{LEVEL}] {timestamp} - {message}
    {stack_trace}（如有异常）
    ============================================================

配置读取：
    _get_log_settings()：
        从 settings.json 的 "log" 字段读取配置
        - retain_days：日志保留天数，默认 7 天
        - max_file_size_mb：单文件最大大小，默认 1 MB

自动清理：
    cleanup_logs(log_dir, retention_days, max_size)：
        1. 删除超过保留天数的日志文件
        2. 截断超过最大大小的日志文件（保留后半部分）
        3. 在应用启动时自动调用

常量：
    LOG_DIR          - 日志目录路径
    LOG_RETENTION_DAYS - 默认保留天数 7
    LOG_MAX_SIZE     - 默认最大文件大小 1MB

依赖：modules.settings_manager（可选，缺失时使用默认配置）
"""
import time
import traceback
import sys
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error_log.txt')
OUTPUT_LOG_FILE = os.path.join(LOG_DIR, 'output_log.txt')

LOG_RETENTION_DAYS = 7
LOG_MAX_SIZE = 1 * 1024 * 1024


def _get_log_settings():
    try:
        from modules.settings_manager import load_settings
        settings = load_settings()
        log_cfg = settings.get("log", {})
        return {
            "retain_days": log_cfg.get("retain_days", LOG_RETENTION_DAYS),
            "max_file_size_mb": log_cfg.get("max_file_size_mb", LOG_MAX_SIZE // (1024 * 1024))
        }
    except (ImportError, OSError, ValueError):
        return {"retain_days": LOG_RETENTION_DAYS, "max_file_size_mb": LOG_MAX_SIZE // (1024 * 1024)}

def _ensure_dir(log_file):
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError:
            pass

def log_error(error_msg, log_file=None):
    _log('ERROR', error_msg, log_file or ERROR_LOG_FILE)

def log_warning(warning_msg, log_file=None):
    _log('WARNING', warning_msg, log_file or ERROR_LOG_FILE)

def log_info(info_msg, log_file=None):
    _log('INFO', info_msg, log_file or ERROR_LOG_FILE)

def log_output(message):
    _ensure_dir(OUTPUT_LOG_FILE)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(OUTPUT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except OSError:
        pass

def _log(level, message, log_file):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    _ensure_dir(log_file)
    log_lines = []
    log_lines.append(f"[{level}] {timestamp} - {message}\n")
    if sys.exc_info()[0] is not None:
        stack_trace = traceback.format_exc()
        if stack_trace and stack_trace.strip():
            log_lines.append(stack_trace)
    log_lines.append("=" * 60 + "\n")
    full_log = "".join(log_lines)
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(full_log)
    except OSError:
        pass

def cleanup_logs(log_dir=None, retention_days=None, max_size=None):
    log_dir = log_dir or LOG_DIR

    log_settings = _get_log_settings()
    retention_days = retention_days if retention_days is not None else log_settings["retain_days"]
    if max_size is None:
        max_size = log_settings["max_file_size_mb"] * 1024 * 1024

    if not os.path.isdir(log_dir):
        return

    now = time.time()
    cutoff = now - retention_days * 86400

    try:
        for filename in os.listdir(log_dir):
            filepath = os.path.join(log_dir, filename)
            if not os.path.isfile(filepath):
                continue

            try:
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
                    continue
            except OSError:
                pass

            try:
                if os.path.getsize(filepath) > max_size:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(0, 2)
                        file_size = f.tell()
                        f.seek(max(0, file_size - max_size))
                        f.readline()
                        remaining = f.read()
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(remaining)
            except (OSError, UnicodeDecodeError):
                pass
    except OSError:
        pass
