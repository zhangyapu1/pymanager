import time
import traceback
import sys
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error_log.txt')
OUTPUT_LOG_FILE = os.path.join(LOG_DIR, 'output_log.txt')

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
