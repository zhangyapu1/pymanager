import os
import sys
import shutil
import pickle
import uuid
import traceback
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD

# 导入功能模块
import modules as actions

# ================== 错误日志 ==================
def log_error(error_msg):
    import time
    with open("error_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")

# ================== 配置 ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "scripts.dat")
os.makedirs(DATA_DIR, exist_ok=True)

# ================== 主程序类 ==================
class ScriptManager:
    def __init__(self, root):
        self.root = root
        self.DATA_DIR = DATA_DIR
        self.CONFIG_FILE = CONFIG_FILE
        self.scripts = []

        try:
            actions.check_self_dependencies(self.root)
        except Exception as e:
            error_msg = f"依赖检查失败：{str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            messagebox.showerror("初始化错误", f"依赖检查时出错：\n{str(e)}\n\n详细信息已写入 error_log.txt")
            sys.exit(1)

        self.create_widgets()
        self.load_scripts()
        self.setup_drag_drop()
        self.root.title("Python 脚本管理器")

    # ------------------ 界面 ------------------
    def create_widgets(self):
        try:
            main_frame = tk.Frame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            self.listbox = tk.Listbox(main_frame, selectmode=tk.SINGLE, font=("Consolas", 10))
            self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.listbox.bind('<Double-Button-1>', lambda e: actions.run_selected(self))

            scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.listbox.config(yscrollcommand=scrollbar.set)

            btn_frame = tk.Frame(self.root)
            btn_frame.pack(fill=tk.X, padx=10, pady=5)

            buttons = [
                ("➕ 添加脚本", lambda: actions.add_script(self)),
                ("▶ 运行选中", lambda: actions.run_selected(self)),
                ("✏️ 重命名", lambda: actions.rename_selected(self)),
                ("📝 编辑内容", lambda: actions.edit_content(self)),
                ("🔍 检查依赖", lambda: actions.check_deps(self)),
                ("❌ 删除选中", lambda: actions.delete_selected(self))
            ]
            for text, cmd in buttons:
                btn = tk.Button(btn_frame, text=text, command=cmd)
                btn.pack(side=tk.LEFT, padx=2)

            self.status_var = tk.StringVar()
            self.status_var.set("就绪 | 拖拽 .py 文件自动复制存储，并检查依赖")
            status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        except Exception as e:
            error_msg = f"创建界面失败：{str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            messagebox.showerror("界面错误", f"无法创建界面：{str(e)}\n\n详细信息已写入 error_log.txt")
            sys.exit(1)

    # ------------------ 拖拽 ------------------
    def setup_drag_drop(self):
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        raw = event.data
        files = self.parse_dropped_files(raw)
        for f in files:
            if f.lower().endswith('.py'):
                actions.add_script_from_path(self, f)
            else:
                self.status_var.set(f"跳过非 .py 文件：{os.path.basename(f)}")

    def parse_dropped_files(self, raw):
        import re
        files = []
        raw = raw.strip('{}')
        pattern = r'\{([^{}]+)\}|([^\s]+)'
        for match in re.findall(pattern, raw):
            p = match[0] if match[0] else match[1]
            if p:
                files.append(p)
        return files

    # ------------------ 核心数据操作 ------------------
    def get_selected_item(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("未选中", "请先选择一个脚本")
            return None
        return self.scripts[sel[0]]

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for item in self.scripts:
            self.listbox.insert(tk.END, item["display"])

    def save_scripts(self):
        try:
            with open(CONFIG_FILE, 'wb') as f:
                pickle.dump(self.scripts, f)
        except Exception as e:
            log_error(f"保存配置失败：{str(e)}\n{traceback.format_exc()}")
            print(f"保存配置失败：{e}")

    def load_scripts(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'rb') as f:
                    self.scripts = pickle.load(f)
                valid = []
                for item in self.scripts:
                    if os.path.exists(item["storage_path"]):
                        valid.append(item)
                    else:
                        print(f"警告：脚本 {item['display']} 内部文件丢失，已忽略")
                self.scripts = valid
                self.update_listbox()
                self.status_var.set(f"已加载 {len(self.scripts)} 个脚本")
            except Exception as e:
                log_error(f"加载配置失败：{str(e)}\n{traceback.format_exc()}")
                print(f"加载配置失败：{e}")

# ================== 启动入口 ==================
if __name__ == "__main__":
    import time
    try:
        root = TkinterDnD.Tk()
    except ImportError as e:
        error_msg = f"缺少 tkinterdnd2：{str(e)}\n{traceback.format_exc()}"
        log_error(error_msg)
        try:
            import subprocess
            print("正在尝试自动安装 tkinterdnd2...")
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-i', "https://pypi.tuna.tsinghua.edu.cn/simple", 'tkinterdnd2'],
                check=True
            )
            print("安装成功，请重新运行程序。")
        except Exception as install_err:
            log_error(f"自动安装失败：{str(install_err)}\n{traceback.format_exc()}")
            print("自动安装失败，请手动执行：pip install tkinterdnd2 -i https://pypi.tuna.tsinghua.edu.cn/simple")
        sys.exit(1)
    except Exception as e:
        error_msg = f"Tkinter 初始化失败：{str(e)}\n{traceback.format_exc()}"
        log_error(error_msg)
        print(error_msg)
        sys.exit(1)

    try:
        app = ScriptManager(root)
        root.mainloop()
    except Exception as e:
        error_msg = f"程序运行时发生未捕获异常：{str(e)}\n{traceback.format_exc()}"
        log_error(error_msg)
        try:
            messagebox.showerror("致命错误", f"程序发生错误：\n{str(e)}\n\n详细信息已写入 error_log.txt")
        except:
            pass
        sys.exit(1)