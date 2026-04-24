import time
import traceback
import sys

def log_error(error_msg, log_file="error_log.txt"):
    # 获取当前时间戳
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # 初始化日志内容列表，用于高效拼接
    log_lines = []
    
    # 添加第一行：时间戳和错误消息
    log_lines.append(f"{timestamp} - {error_msg}\n")
    
    # 检查是否存在活跃的异常
    # sys.exc_info()[0] 为 None 表示不在异常处理上下文中
    if sys.exc_info()[0] is not None:
        # 获取堆栈跟踪信息
        stack_trace = traceback.format_exc()
        # 只有当堆栈跟踪不为空或不仅仅是 'None' 时才添加
        # traceback.format_exc() 在没有异常时可能返回 'None\n' (取决于Python版本)
        # 在有异常时，它返回格式化的堆栈，通常以换行符结尾
        if stack_trace and stack_trace.strip():
            log_lines.append(stack_trace)
            
    # 将所有行合并为一个字符串
    full_log = "".join(log_lines)
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(full_log)
    except Exception:
        # 忽略日志写入错误，避免影响主业务逻辑
        # 在实际生产代码中，可以考虑记录到 stderr
        pass