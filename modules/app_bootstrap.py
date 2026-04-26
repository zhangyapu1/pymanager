"""应用启动引导 - 初始化窗口、主题和全局样式。"""
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
