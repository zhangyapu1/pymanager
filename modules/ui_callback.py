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

    parent 参数：
        所有方法支持指定父窗口，未指定时使用初始化时传入的 root

依赖：tkinter.messagebox, tkinter.simpledialog, tkinter.filedialog
"""
from tkinter import messagebox, simpledialog, filedialog


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
