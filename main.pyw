import os
import sys
import shutil
import threading
import tkinter as tk
from tkinter import messagebox

import modules.updater as updater
from modules.config import BASE_DIR, DATA_DIR, DEFAULT_GROUP, CONFIG_DIR
from modules.logger import log_error, log_info, log_output, cleanup_logs
from modules.settings_manager import load_settings, save_settings
from modules.drag_drop import parse_dropped_files
from modules.utils import update_title_mode, extract_docstring
from modules.group_manager import GroupManager
from modules.script_manager import (
    resolve_path, get_unique_path, get_selected_item,
    update_listbox, scan_data_directory, add_script_from_path,
    move_script_to_group
)
from modules.context_menu import show_context_menu
from modules.add_script import add_script
from modules.run_selected import run_selected, stop_running
from modules.rename_selected import rename_selected
from modules.edit_content import edit_content
from modules.check_deps import check_deps
from modules.delete_selected import delete_selected
from modules.dependencies import check_self_dependencies, check_script_deps_and_install

# ================== 主程序类 ==================

class ScriptManager:
    def __init__(self, root):
        self.root = root
        self.data_dir = DATA_DIR
        self.base_dir = BASE_DIR
        self.scripts = []
        self.running_process = None
        self.settings = load_settings()
        self.group_manager = GroupManager(self.data_dir, output_callback=self.append_output)

        self.create_widgets()

        try:
            def output_to_console(message):
                self.root.after(0, lambda: self.append_output(message))

            check_self_dependencies(self.root, output_callback=output_to_console)
        except (OSError, RuntimeError) as e:
            log_error(f"依赖检查失败：{e}")
            self.append_output(f"[错误] 依赖检查时出错：{e}")
            messagebox.showerror("初始化错误", f"依赖检查时出错：\n{e}\n\n详细信息已写入 logs/error_log.txt")
            sys.exit(1)
        self.scan_data_directory()
        self.setup_drag_drop()
        update_title_mode(self.root)
        self.show_version_info()

    def append_output(self, message):
        log_output(message)
        if hasattr(self, 'output_text'):
            self.output_text.insert(tk.END, message + '\n')
            self.output_text.see(tk.END)

    def _resolve_path(self, rel_path):
        return resolve_path(self.data_dir, rel_path)

    def _get_unique_path(self, directory, filename):
        return get_unique_path(directory, filename)

    def get_selected_item(self):
        return get_selected_item(self)

    def update_listbox(self):
        update_listbox(self)

    def scan_data_directory(self):
        scan_data_directory(self)

    def add_script_from_path(self, src_path):
        add_script_from_path(self, src_path)

    def move_script_to_group(self, item, target_group):
        move_script_to_group(self, item, target_group)

    # ------------------ 界面 ------------------
    def create_widgets(self):
        try:
            top_frame = tk.Frame(self.root)
            top_frame.pack(fill=tk.X, padx=10, pady=5)

            self.group_combo, _, _ = self.group_manager.create_group_widgets(
                top_frame,
                on_group_changed_callback=self.on_group_changed
            )

            buttons = [
                ("➕ 添加脚本", lambda: add_script(self)),
                ("🔍 检查依赖", lambda: check_deps(self)),
                ("🔄 检查更新", lambda: updater.check_for_updates(self.root, show_no_update_msg=True, output_callback=self.append_output)),
                ("🔑 删除Token", lambda: self.delete_token()),
                ("📁 打开程序目录", lambda: self.open_program_dir()),
            ]
            for i, (text, cmd) in enumerate(buttons):
                btn = tk.Button(top_frame, text=text, command=lambda c=cmd: c())
                btn.pack(side=tk.LEFT, padx=5, pady=2)

            content_frame = tk.Frame(self.root)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            left_frame = tk.Frame(content_frame)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

            left_label = tk.Label(left_frame, text="已加载脚本:")
            left_label.pack(anchor=tk.W)

            list_frame = tk.Frame(left_frame)
            list_frame.pack(fill=tk.BOTH, expand=True)

            self.listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, font=('Consolas', 10), width=25)
            self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.listbox.bind('<Double-Button-1>', lambda e: run_selected(self))
            self.listbox.bind("<Button-3>", lambda e: show_context_menu(self, e))
            self.listbox.bind("<<ListboxSelect>>", self.on_script_selected)

            scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.listbox.config(yscrollcommand=scrollbar.set)

            right_frame = tk.Frame(content_frame)
            right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

            output_header = tk.Frame(right_frame)
            output_header.pack(fill=tk.X)

            output_label = tk.Label(output_header, text="运行输出:")
            output_label.pack(side=tk.LEFT)

            self.stop_btn = tk.Button(output_header, text="⏹ 停止运行", command=lambda: stop_running(self), state=tk.DISABLED)
            self.stop_btn.pack(side=tk.RIGHT, padx=5)

            self.output_text = tk.Text(right_frame, font=('Consolas', 10))
            self.output_text.pack(fill=tk.BOTH, expand=True)

            output_scrollbar = tk.Scrollbar(self.output_text, orient=tk.VERTICAL, command=self.output_text.yview)
            output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.output_text.config(yscrollcommand=output_scrollbar.set)

            self.root.geometry("950x600")

            win_cfg = self.settings.get("window", {})
            win_w = win_cfg.get("width", 950)
            win_h = win_cfg.get("height", 600)
            win_x = win_cfg.get("x")
            win_y = win_cfg.get("y")
            if win_x is not None and win_y is not None:
                self.root.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")
            else:
                self.root.geometry(f"{win_w}x{win_h}")

            self.root.protocol("WM_DELETE_WINDOW", self.on_close)

            self.status_var = tk.StringVar()
            self.status_var.set("就绪 | 拖拽 .py 文件自动复制存储，并检查依赖")
            status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)

            self.version_var = tk.StringVar()
            self.version_var.set("版本信息加载中...")
            version_bar = tk.Label(self.root, textvariable=self.version_var, bd=1, relief=tk.SUNKEN, anchor=tk.E, font=('Arial', 8))
            version_bar.pack(side=tk.BOTTOM, fill=tk.X)

        except (tk.TclError, OSError) as e:
            log_error(f"创建界面失败：{e}")
            self.append_output(f"[错误] 无法创建界面：{e}")
            messagebox.showerror("界面错误", f"无法创建界面：{e}\n\n详细信息已写入 logs/error_log.txt")
            sys.exit(1)

    def on_group_changed(self, new_group):
        self.group_manager.current_group = new_group
        self.update_listbox()
        self.append_output(f"当前分组：{new_group}")
        self.status_var.set(f"当前分组：{new_group}")

    def on_script_selected(self, event):
        item = self.get_selected_item()
        if not item:
            return

        abs_path = self._resolve_path(item["storage_path"])
        docstring = extract_docstring(abs_path)

        if hasattr(self, 'output_text'):
            self.output_text.delete(1.0, 'end')
            if docstring:
                self.append_output(f"📄 {item['display']}")
                self.append_output("─" * 40)
                self.append_output(docstring)
            else:
                self.append_output(f"📄 {item['display']}")
                self.append_output("（该脚本无头注释）")

    # ------------------ 拖拽 ------------------
    def setup_drag_drop(self):
        from tkinterdnd2 import DND_FILES
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        files = parse_dropped_files(event.data)
        added = 0
        skipped = 0
        for f in files:
            if not f or not os.path.exists(f):
                skipped += 1
                continue

            if f.lower().endswith('.py'):
                self.add_script_from_path(f)
                added += 1
            else:
                skipped += 1
        self.status_var.set(f"拖拽完成：添加 {added} 个脚本，跳过 {skipped} 个非.py文件")
        self.append_output(f"拖拽完成：添加 {added} 个脚本，跳过 {skipped} 个非.py文件")

    def show_version_info(self):
        def check_version_thread():
            try:
                current_version = updater.CURRENT_VERSION
                latest_version = updater.get_latest_version()

                if latest_version:
                    status = "最新版本" if current_version == latest_version else "有新版本"
                    msg = f"当前版本：{current_version} | 最新版本：{latest_version} | {status}"
                else:
                    msg = f"当前版本：{current_version} | 检查更新失败"
            except (OSError, ValueError) as e:
                log_error(f"版本检查异常: {e}")
                msg = f"当前版本：1.0.0 | 检查更新失败"

            self.root.after(0, lambda: self.version_var.set(msg))

        thread = threading.Thread(target=check_version_thread)
        thread.daemon = True
        thread.start()

    def delete_token(self):
        from modules.token_crypto import delete_api_token, get_api_token
        if not get_api_token():
            self.append_output("[提示] 当前没有保存的 Token。")
            messagebox.showinfo("提示", "当前没有保存的 Token。")
            return
        if messagebox.askyesno("确认删除", "确定要删除已保存的 GitHub API Token 吗？"):
            delete_api_token()
            self.append_output("已删除保存的 Token")
            self.status_var.set("已删除保存的 Token")

    def open_program_dir(self):
        import subprocess
        program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        subprocess.Popen(f'explorer "{program_dir}"')

    def on_close(self):
        try:
            self.root.update_idletasks()
            geometry = self.root.geometry()
            parts = geometry.replace('+', 'x').replace('-', 'x').split('x')
            if len(parts) >= 4:
                self.settings.setdefault("window", {})
                self.settings["window"]["width"] = int(parts[0])
                self.settings["window"]["height"] = int(parts[1])
                self.settings["window"]["x"] = int(parts[2])
                self.settings["window"]["y"] = int(parts[3])
                save_settings(self.settings)
        except (tk.TclError, ValueError, OSError):
            pass
        self.root.destroy()

# ================== 启动入口 ==================
if __name__ == "__main__":
    cleanup_logs()

    def restart_app():
        import subprocess
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)

    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError as e:
        log_error(f"缺少 tkinterdnd2：{str(e)}")
        try:
            import subprocess
            log_info("正在尝试自动安装 tkinterdnd2...")
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-i', "https://pypi.tuna.tsinghua.edu.cn/simple", 'tkinterdnd2'],
                check=True
            )
            log_info("安装成功，程序将自动重启。")
            restart_app()
        except (subprocess.SubprocessError, OSError) as install_err:
            log_error(f"自动安装失败：{install_err}")
            log_error("自动安装失败，请手动执行：pip install tkinterdnd2 -i https://pypi.tuna.tsinghua.edu.cn/simple")
        sys.exit(1)
    except (ImportError, tk.TclError) as e:
        log_error(f"Tkinter 初始化失败：{e}")
        sys.exit(1)

    try:
        app = ScriptManager(root)
        root.mainloop()
    except Exception as e:
        import traceback
        log_error(f"程序运行时发生未捕获异常：{e}\n{traceback.format_exc()}")
        try:
            messagebox.showerror("致命错误", f"程序发生错误：\n{e}\n\n详细信息已写入 logs/error_log.txt")
        except (tk.TclError, OSError):
            pass
        sys.exit(1)
