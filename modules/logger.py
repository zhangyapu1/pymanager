import time
import traceback

def log_error(error_msg, log_file="error_log.txt"):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")
        f.write(traceback.format_exc() + "\n")