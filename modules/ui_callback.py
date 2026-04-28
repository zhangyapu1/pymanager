"""
UI 回调 - 封装 Tkinter 对话框操作，实现 UICallbackProtocol 接口。

类 UICallback：
    对 Tkinter 的 messagebox、simpledialog、filedialog 进行封装，
    提供统一的对话框接口，供各模块通过 AppContext.ui 调用。

    方法：
        show_error(title, message, parent=None)：
            显示错误对话框（红色图标）

        show_warning(title, message, parent=None)：
            显示警告对话框（黄色图标）

        show_info(title, message, parent=None)：
            显示信息对话框（蓝色图标）

        ask_yes_no(title, message, parent=None)：
            显示确认对话框，返回布尔值

        ask_string(title, prompt, parent=None, initialvalue="")：
            显示输入对话框，返回用户输入的字符串或 None

        ask_open_filename(title, filetypes)：
            显示文件选择对话框，返回文件路径或空字符串

        show_update_dialog(title, message, changelog, parent=None)：
            显示更新对话框，包含版本信息和更新内容

    parent 参数：
        所有方法支持指定父窗口，未指定时使用初始化时传入的 root

依赖：tkinter.messagebox, tkinter.simpledialog, tkinter.filedialog
"""
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, scrolledtext


class UICallback:
    def __init__(self, root=None):
        self.root = root

    def show_error(self, title, message, parent=None):
        messagebox.showerror(title, message, parent=parent or self.root)

    def show_warning(self, title, message, parent=None):
        messagebox.showwarning(title, message, parent=parent or self.root)

    def show_info(self, title, message, parent=None):
        messagebox.showinfo(title, message, parent=parent or self.root)

    def ask_yes_no(self, title, message, parent=None):
        return messagebox.askyesno(title, message, parent=parent or self.root)

    def ask_string(self, title, prompt, parent=None, initialvalue=""):
        return simpledialog.askstring(title, prompt, parent=parent or self.root, initialvalue=initialvalue or "")

    def ask_open_filename(self, title, filetypes):
        return filedialog.askopenfilename(title=title, filetypes=filetypes)

    def show_update_dialog(self, title, message, changelog, parent=None):
        """显示更新对话框，包含版本信息和更新内容"""
        parent_win = parent or self.root

        dialog = tk.Toplevel(parent_win)
        dialog.title(title)
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        dialog.transient(parent_win)
        dialog.grab_set()

        # 主信息
        msg_label = tk.Label(dialog, text=message, wraplength=450, justify=tk.LEFT, font=("", 10))
        msg_label.pack(padx=20, pady=15, fill=tk.X)

        # 分隔线
        separator = tk.Frame(dialog, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=20, pady=5)

        # 更新内容标签
        changelog_label = tk.Label(dialog, text="📋 更新内容：", font=("", 10, "bold"))
        changelog_label.pack(padx=20, pady=(10, 5), anchor=tk.W)

        # 更新内容文本框
        text_area = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, width=60, height=15, font=("", 9))
        if changelog:
            text_area.insert(tk.END, changelog)
        else:
            text_area.insert(tk.END, "暂无更新说明")
        text_area.config(state=tk.DISABLED)
        text_area.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        # 按钮框架
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=15)

        result = [False]

        def on_yes():
            result[0] = True
            dialog.destroy()

        def on_no():
            result[0] = False
            dialog.destroy()

        yes_btn = tk.Button(btn_frame, text="立即更新", width=15, command=on_yes, bg="#4CAF50", fg="white")
        yes_btn.pack(side=tk.RIGHT, padx=10)

        no_btn = tk.Button(btn_frame, text="稍后再说", width=15, command=on_no)
        no_btn.pack(side=tk.RIGHT, padx=10)

        # 居中显示
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        dialog.wait_window()
        return result[0]
