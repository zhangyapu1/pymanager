"""
应用启动引导 - 初始化窗口、主题和全局样式，启动主事件循环。

功能：
    - 创建根窗口：优先使用 tkinterdnd2（支持拖放），回退到标准 Tk
    - 主题配置：使用 ttkbootstrap 的 litera 主题，统一全局样式
    - 全局样式：
        - 背景色 #f0f0f0，前景色 #1a1a1a
        - 字体 Microsoft YaHei UI 9pt
        - 状态栏和版本栏使用专用 TLabel 样式
    - 启动流程：
        1. 清理过期日志（cleanup_logs）
        2. 创建根窗口并应用主题
        3. 调用 app_factory 构建应用界面
        4. 进入 mainloop
    - 异常处理：捕获 Tkinter 初始化失败和运行时未捕获异常，
      写入错误日志并弹出提示

可选依赖：
    - ttkbootstrap：提供现代主题支持，缺失时回退到标准 ttk
    - tkinterdnd2：提供拖放支持，缺失时回退到标准 Tk

依赖：modules.logger
"""
import sys
import tkinter as tk
import tkinter.font

from modules.logger import log_error, cleanup_logs

try:
    import ttkbootstrap as ttkb
    HAS_TTKBOOTSTRAP = True
except ImportError:
    HAS_TTKBOOTSTRAP = False

try:
    from tkinterdnd2 import TkinterDnD
    HAS_TKDND = True
except ImportError:
    HAS_TKDND = False


def create_root_window():
    if HAS_TKDND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    if HAS_TTKBOOTSTRAP:
        style = ttkb.Style(theme="litera")
        style.configure("TButton", padding=(10, 4))
        style.configure("TLabel", padding=2, background="#f0f0f0", foreground="#1a1a1a")
        style.configure("TCombobox", padding=(6, 4))
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabelframe", background="#f0f0f0")
        style.configure("TLabelframe.Label", background="#f0f0f0", foreground="#1a1a1a")
        style.configure("Status.TLabel", background="#f0f0f0", foreground="#1a1a1a", font=("Microsoft YaHei UI", 9))
        style.configure("Version.TLabel", background="#f0f0f0", foreground="#1a1a1a", font=("Microsoft YaHei UI", 8))
        style.configure(".", font=("Microsoft YaHei UI", 9), background="#f0f0f0")
    else:
        default_font = tk.font.Font(family="Microsoft YaHei UI", size=9)
        root.option_add("*Font", default_font)
        root.option_add("*TLabel.background", "#f0f0f0")

    root.configure(bg="#f0f0f0")
    return root


def bootstrap(app_factory):
    cleanup_logs()

    try:
        root = create_root_window()
    except (ImportError, tk.TclError) as e:
        log_error(f"Tkinter 初始化失败：{e}")
        sys.exit(1)

    try:
        app_factory(root)
        root.mainloop()
    except Exception as e:
        import traceback
        from tkinter import messagebox
        log_error(f"程序运行时发生未捕获异常：{e}\n{traceback.format_exc()}")
        try:
            messagebox.showerror("致命错误", f"程序发生错误：\n{e}\n\n详细信息已写入 logs/error_log.txt")
        except (tk.TclError, OSError):
            pass
        sys.exit(1)
