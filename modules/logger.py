import time
import traceback
import sys
import os

# 日志文件路径
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'error_log.txt')

def log_error(error_msg, log_file=None):
    """
    记录错误信息到日志文件
    
    :param error_msg: 错误信息
    :param log_file: 日志文件路径，默认使用 LOG_FILE
    """
    _log('ERROR', error_msg, log_file)

def log_warning(warning_msg, log_file=None):
    """
    记录警告信息到日志文件
    
    :param warning_msg: 警告信息
    :param log_file: 日志文件路径，默认使用 LOG_FILE
    """
    _log('WARNING', warning_msg, log_file)

def log_info(info_msg, log_file=None):
    """
    记录信息到日志文件
    
    :param info_msg: 信息
    :param log_file: 日志文件路径，默认使用 LOG_FILE
    """
    _log('INFO', info_msg, log_file)

def _log(level, message, log_file=None):
    """
    内部日志记录函数
    
    :param level: 日志级别
    :param message: 日志消息
    :param log_file: 日志文件路径，默认使用 LOG_FILE
    """
    # 获取当前时间戳
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # 确定日志文件路径
    if log_file is None:
        log_file = LOG_FILE
    
    # 确保日志文件目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            # 忽略目录创建错误，避免影响主业务逻辑
            pass
    
    # 初始化日志内容列表，用于高效拼接
    log_lines = []
    
    # 添加第一行：时间戳、日志级别和消息
    log_lines.append(f"[{level}] {timestamp} - {message}\n")
    
    # 检查是否存在活跃的异常
    if sys.exc_info()[0] is not None:
        # 获取堆栈跟踪信息
        stack_trace = traceback.format_exc()
        # 只有当堆栈跟踪不为空或不仅仅是 'None' 时才添加
        if stack_trace and stack_trace.strip():
            log_lines.append(stack_trace)
    
    # 添加分隔线
    log_lines.append("=" * 60 + "\n")
    
    # 将所有行合并为一个字符串
    full_log = "".join(log_lines)
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(full_log)
    except Exception:
        # 忽略日志写入错误，避免影响主业务逻辑
        pass