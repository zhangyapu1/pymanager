# 移除了未使用的 import os

def update_title_mode(root, data_dir, base_dir):
    """
    更新窗口标题。
    
    注意: data_dir 和 base_dir 参数当前未被使用，保留以维持接口兼容性。
    """
    # 增加健壮性检查：确保 root 对象存在且具有 title 方法
    if root is None:
        return
    
    if not hasattr(root, 'title'):
        # 如果 root 不是预期的 Tkinter 窗口对象，可以选择记录日志或静默失败
        # 这里选择静默返回以避免崩溃，符合“友好”但“严苛”的错误预防原则
        return

    try:
        root.title("Python 脚本管理器")
    except Exception:
        # 捕获可能的异常（例如窗口已被销毁），防止程序崩溃
        pass