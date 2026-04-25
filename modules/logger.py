import time
import traceback
import sys
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error_log.txt')
OUTPUT_LOG_FILE = os.path.join(LOG_DIR, 'output_log.txt')

LOG_RETENTION_DAYS = 7
LOG_MAX_SIZE = 1 * 1024 * 1024

def _ensure_dir(log_file):
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
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
    except Exception:
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
    except Exception:
        pass

def cleanup_logs(log_dir=None, retention_days=None, max_size=None):
    log_dir = log_dir or LOG_DIR
    retention_days = retention_days if retention_days is not None else LOG_RETENTION_DAYS
    max_size = max_size if max_size is not None else LOG_MAX_SIZE

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
            except Exception:
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
            except Exception:
                pass
    except Exception:
        pass
