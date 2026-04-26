import os
import sys

sys.dont_write_bytecode = True

import threading
import tkinter as tk
import tkinter.font
from tkinter import messagebox

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

import modules.updater as updater
from modules.config import BASE_DIR, DATA_DIR, DEFAULT_GROUP, CONFIG_DIR
from modules.logger import log_error, log_info, log_output, cleanup_logs
from modules.settings_manager import load_settings, save_settings
from modules.drag_drop import parse_dropped_files
from modules.utils import update_title_mode, extract_docstring
from modules.group_manager import GroupManager
from modules.script_manager import (
    resolve_path, get_unique_path, scan_data_directory, add_script_from_path,
    move_script_to_group
)
from modules.ui_builder import create_widgets
from modules.ui_callback import UICallback
from modules.dependencies import check_self_dependencies_async


class ScriptManager:
    def __init__(self, root):
        self._root = root
        self.data_dir = DATA_DIR
        self.base_dir = BASE_DIR
        self.scripts = []
        self._running_process = None
        self._process_stopped = False
        self.settings = load_settings()
        self.ui = UICallback(root)
        self.group_manager = GroupManager(self.data_dir, output_callback=self.append_output, ui_callback=self.ui)

        self._listbox = None
        self._output_text = None
        self._stop_btn = None
        self._status_var = None
        self._version_var = None
        self._group_combo = None

        self.create_widgets = lambda: create_widgets(self)
        self.create_widgets()

        self.append_output("─── 框架依赖检查 ───")

        def on_deps_complete(needs_restart=False):
            if needs_restart:
                def _restart():
                    self.ui.show_info("需要重启", "已安装缺失的依赖，需要重新启动程序才能生效。\n点击确定后程序将自动重启。")
                    import subprocess
                    subprocess.Popen([sys.executable] + sys.argv)
                    self._root.destroy()
                self.schedule_callback(_restart)

        def run_deps_check():
            try:
                def output_to_console(message):
                    log_info(f"[框架依赖] {message}")
                    self.schedule_callback(lambda: self.append_output(message))

                check_self_dependencies_async(
                    output_callback=output_to_console,
                    ui_callback=self.ui,
                    on_complete=on_deps_complete
                )
            except (OSError, RuntimeError) as e:
                log_error(f"依赖检查失败：{e}")
                self.schedule_callback(lambda: self.append_output(f"[错误] 依赖检查时出错：{e}"))

        thread = threading.Thread(target=run_deps_check, daemon=True)
        thread.start()
        self.scan_data_directory()
        self.setup_drag_drop()
        update_title_mode(self._root)
        self.show_version_info()

    def append_output(self, message):
        log_output(message)
        if self._output_text:
            self._output_text.insert(tk.END, message + '\n')
            self._output_text.see(tk.END)

    def clear_output(self):
        if self._output_text:
            self._output_text.delete(1.0, 'end')

    def set_status(self, message):
        if self._status_var:
            self._status_var.set(message)

    def set_version_info(self, message):
        if self._version_var:
            self._version_var.set(message)

    def get_selected_item(self):
        if not self._listbox:
            return None
        sel = self._listbox.curselection()
        if not sel:
            return None
        display_name = self._listbox.get(sel[0])
        for item in self.scripts:
            if item["display"] == display_name and item.get("group") == self.group_manager.current_group:
                return item
        return None

    def update_listbox(self):
        if not self._listbox:
            return
        self._listbox.delete(0, tk.END)
        for item in self.scripts:
            if item.get("group") == self.group_manager.current_group:
                self._listbox.insert(tk.END, item["display"])

    def scan_data_directory(self):
        scan_data_directory(self)

    def add_script(self, script):
        self.scripts.append(script)

    def remove_script(self, script):
        try:
            self.scripts.remove(script)
        except ValueError:
            pass

    def find_script_by_path(self, storage_path):
        for i, script in enumerate(self.scripts):
            if script['storage_path'] == storage_path:
                return i
        return None

    def update_script(self, index, display, group):
        self.scripts[index]["display"] = display
        self.scripts[index]["group"] = group

    def get_groups(self):
        return list(self.group_manager.groups)

    def get_current_group(self):
        return self.group_manager.current_group

    def add_group(self, group):
        if group not in self.group_manager.groups:
            self.group_manager.groups.append(group)

    def get_running_process(self):
        return self._running_process

    def set_running_process(self, process):
        self._running_process = process

    def is_process_stopped(self):
        return self._process_stopped

    def set_process_stopped(self, stopped):
        self._process_stopped = stopped

    def set_stop_button_enabled(self, enabled):
        if self._stop_btn:
            self._stop_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def schedule_callback(self, callback):
        self._root.after(0, callback)

    def get_root_window(self):
        return self._root

    def set_listbox(self, listbox):
        self._listbox = listbox

    def set_output_text(self, text_widget):
        self._output_text = text_widget

    def set_stop_button(self, button):
        self._stop_btn = button

    def set_status_var(self, var):
        self._status_var = var

    def set_version_var(self, var):
        self._version_var = var

    def set_group_combo(self, combo):
        self._group_combo = combo

    def refresh_group_combo(self):
        if self._group_combo:
            self._group_combo['values'] = self.get_groups()
            self._group_combo.set(self.get_current_group())

    def on_group_changed(self, new_group):
        self.group_manager.current_group = new_group
        self.update_listbox()
        self.append_output(f"当前分组：{new_group}")
        self.set_status(f"当前分组：{new_group}")

    def on_script_selected(self, event):
        item = self.get_selected_item()
        if not item:
            return

        abs_path = resolve_path(self.data_dir, item["storage_path"])
        docstring = extract_docstring(abs_path)

        self.clear_output()
        if docstring:
            self.append_output(f"\U0001f4c4 {item['display']}")
            self.append_output("\u2500" * 40)
            self.append_output(docstring)
        else:
            self.append_output(f"\U0001f4c4 {item['display']}")
            self.append_output("\uff08\u8be5\u811a\u672c\u65e0\u5934\u6ce8\u91ca\uff09")

    def on_close(self):
        try:
            self._root.update_idletasks()
            geometry = self._root.geometry()
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
        self._root.destroy()

    def delete_token(self):
        from modules.token_crypto import delete_api_token, get_api_token
        if not get_api_token():
            self.append_output("[提示] 当前没有保存的 Token。")
            self.ui.show_info("提示", "当前没有保存的 Token。")
            return
        if self.ui.ask_yes_no("确认删除", "确定要删除已保存的 GitHub API Token 吗？"):
            delete_api_token()
            self.append_output("已删除保存的 Token")
            self.set_status("已删除保存的 Token")

    def open_program_dir(self):
        import subprocess
        program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        subprocess.Popen(f'explorer "{program_dir}"')

    def setup_drag_drop(self):
        if not HAS_TKDND:
            self.append_output("[提示] tkinterdnd2 未安装，拖拽功能不可用。安装后将自动启用。")
            return
        from tkinterdnd2 import DND_FILES
        self._listbox.drop_target_register(DND_FILES)
        self._listbox.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        files = parse_dropped_files(event.data)
        added = 0
        skipped = 0
        for f in files:
            if not f or not os.path.exists(f):
                skipped += 1
                continue

            if f.lower().endswith('.py'):
                add_script_from_path(self, f)
                added += 1
            else:
                skipped += 1
        self.set_status(f"拖拽完成：添加 {added} 个脚本，跳过 {skipped} 个非.py文件")
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

            self.schedule_callback(lambda: self.set_version_info(msg))

        thread = threading.Thread(target=check_version_thread)
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    cleanup_logs()

    try:
        if HAS_TKDND:
            root = TkinterDnD.Tk()
        else:
            root = tk.Tk()

        if HAS_TTKBOOTSTRAP:
            style = ttkb.Style(theme="litera")
            style.configure("TButton", padding=(10, 4))
            style.configure("TLabel", padding=2)
            style.configure("TCombobox", padding=(6, 4))
            style.configure(".", font=("Microsoft YaHei UI", 9))
            style.configure("TFrame", background="#f3f3f3")
        else:
            default_font = tk.font.Font(family="Microsoft YaHei UI", size=9)
            root.option_add("*Font", default_font)

        root.configure(bg="#f3f3f3")
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
