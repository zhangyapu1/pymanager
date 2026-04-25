import os
import sys
import shutil
import threading
import tkinter as tk
from tkinter import messagebox

import modules.updater as updater
from modules.config import BASE_DIR, DATA_DIR, DEFAULT_GROUP
from modules.logger import log_error, log_info, log_output
from modules.drag_drop import parse_dropped_files
from modules.utils import update_title_mode
from modules.group_manager import GroupManager
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
        self.group_manager = GroupManager(self.data_dir, output_callback=self.append_output)

        self.create_widgets()

        try:
            def output_to_console(message):
                self.root.after(0, lambda: self.append_output(message))

            check_self_dependencies(self.root, output_callback=output_to_console)
        except Exception as e:
            log_error(f"依赖检查失败：{str(e)}")
            self.append_output(f"[错误] 依赖检查时出错：{str(e)}")
            messagebox.showerror("初始化错误", f"依赖检查时出错：\n{str(e)}\n\n详细信息已写入 logs/error_log.txt")
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
            self.listbox.bind("<Button-3>", self.show_context_menu)
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

            self.status_var = tk.StringVar()
            self.status_var.set("就绪 | 拖拽 .py 文件自动复制存储，并检查依赖")
            status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)

            self.version_var = tk.StringVar()
            self.version_var.set("版本信息加载中...")
            version_bar = tk.Label(self.root, textvariable=self.version_var, bd=1, relief=tk.SUNKEN, anchor=tk.E, font=('Arial', 8))
            version_bar.pack(side=tk.BOTTOM, fill=tk.X)

        except Exception as e:
            log_error(f"创建界面失败：{str(e)}")
            self.append_output(f"[错误] 无法创建界面：{str(e)}")
            messagebox.showerror("界面错误", f"无法创建界面：{str(e)}\n\n详细信息已写入 logs/error_log.txt")
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
        docstring = self._extract_docstring(abs_path)

        if hasattr(self, 'output_text'):
            self.output_text.delete(1.0, 'end')
            if docstring:
                self.append_output(f"📄 {item['display']}")
                self.append_output("─" * 40)
                self.append_output(docstring)
            else:
                self.append_output(f"📄 {item['display']}")
                self.append_output("（该脚本无头注释）")

    @staticmethod
    def _extract_docstring(file_path):
        if not os.path.isfile(file_path):
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            return None

        stripped = [l.strip() for l in lines]
        non_empty = [i for i, l in enumerate(stripped) if l and not l.startswith('#')]
        if not non_empty:
            comments = [l for l in stripped if l.startswith('#')]
            return '\n'.join(l.lstrip('#').strip() for l in comments if l) or None

        first = non_empty[0]
        line = stripped[first]
        if line.startswith('"""') or line.startswith("'''"):
            quote = line[:3]
            rest = line[3:]
            if rest.endswith(quote) and len(rest) > 0:
                return rest[:-3].strip() or None
            parts = [rest]
            for l in lines[first + 1:]:
                s = l.strip()
                if s.endswith(quote):
                    parts.append(s[:-3])
                    break
                parts.append(s)
            return '\n'.join(parts).strip() or None

        comments = []
        for l in stripped[:first]:
            if l.startswith('#'):
                comments.append(l.lstrip('#').strip())
        return '\n'.join(comments) if comments else None

    # ------------------ 右键菜单 ------------------
    def show_context_menu(self, event):
        selected = self.listbox.curselection()
        if not selected:
            return
        item = self.get_selected_item()
        if not item:
            return

        current_group = item.get("group", DEFAULT_GROUP)
        menu = tk.Menu(self.root, tearoff=0)

        move_menu = tk.Menu(menu, tearoff=0)
        other_groups = [g for g in self.group_manager.groups if g != current_group]

        for group in other_groups:
            move_menu.add_command(label=group, command=lambda g=group: self.move_script_to_group(item, g))

        if not other_groups:
            move_menu.add_command(label="无其他分组", state="disabled")

        move_menu.add_separator()
        move_menu.add_command(label="新建分组...", command=lambda: self.create_group_and_move(item))

        menu.add_cascade(label="移动到分组", menu=move_menu)
        menu.add_separator()
        menu.add_command(label="运行", command=lambda: run_selected(self))
        menu.add_command(label="编辑内容", command=lambda: edit_content(self))
        menu.add_command(label="重命名", command=lambda: rename_selected(self))
        menu.add_command(label="删除", command=lambda: delete_selected(self))
        menu.add_separator()
        menu.add_command(label="刷新列表", command=self.scan_data_directory)

        menu.post(event.x_root, event.y_root)

    def move_script_to_group(self, item, target_group):
        if item["group"] == target_group:
            return
        old_group = item["group"]

        old_rel_path = item["storage_path"]
        old_abs_path = self._resolve_path(old_rel_path)
        file_name = os.path.basename(old_abs_path)

        if target_group == DEFAULT_GROUP:
            target_dir = self.data_dir
        else:
            target_dir = os.path.join(self.data_dir, target_group)
            os.makedirs(target_dir, exist_ok=True)

        new_abs_path = self._get_unique_path(target_dir, file_name)

        try:
            shutil.move(old_abs_path, new_abs_path)

            item["group"] = target_group
            item["storage_path"] = os.path.relpath(new_abs_path, self.data_dir).replace('\\', '/')
            item["display"] = item["storage_path"]

            self.group_manager.save_groups()

            self.update_listbox()
            self.status_var.set(f"已将「{item['display']}」从「{old_group}」移动到「{target_group}」")

        except Exception as e:
            log_error(f"移动文件失败: {str(e)}")
            self.append_output(f"[错误] 移动文件失败：{str(e)}")
            messagebox.showerror("错误", f"移动文件失败：{str(e)}")

    def create_group_and_move(self, item):
        new_group = self.group_manager.new_group(self.root)
        if new_group:
            self.move_script_to_group(item, new_group)

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

    # ------------------ 路径工具 ------------------

    def _resolve_path(self, rel_path):
        if os.path.isabs(rel_path):
            return rel_path
        return os.path.join(self.data_dir, rel_path)

    def _get_unique_path(self, directory, filename):
        path = os.path.join(directory, filename)
        if not os.path.exists(path):
            return path

        name_without_ext, ext = os.path.splitext(filename)
        counter = 1
        while True:
            new_filename = f"{name_without_ext}_{counter}{ext}"
            path = os.path.join(directory, new_filename)
            if not os.path.exists(path):
                return path
            counter += 1

    # ------------------ 核心数据操作 ------------------

    def add_script_from_path(self, src_path):
        if not os.path.isfile(src_path):
            self.status_var.set(f"文件不存在：{src_path}")
            self.append_output(f"[错误] 文件不存在：{src_path}")
            return

        base_name = os.path.basename(src_path)

        dest_abs_path = self._get_unique_path(self.data_dir, base_name)
        dest_name = os.path.basename(dest_abs_path)

        try:
            shutil.copy2(src_path, dest_abs_path)
        except Exception as e:
            log_error(f"复制脚本失败: {str(e)}")
            self.append_output(f"[错误] 无法复制脚本：{e}")
            messagebox.showerror("复制失败", f"无法复制脚本：{e}")
            return

        rel_path = os.path.relpath(dest_abs_path, self.data_dir).replace('\\', '/')

        new_script = {
            "display": rel_path,
            "storage_path": rel_path,
            "group": self.group_manager.current_group
        }

        self.scripts.append(new_script)
        self.update_listbox()
        self.status_var.set(f"已添加：{rel_path} (分组：{self.group_manager.current_group})")
        self.append_output(f"已添加：{rel_path} (分组：{self.group_manager.current_group})")

        self.group_manager.save_groups()

        def output_to_console(message):
            self.root.after(0, lambda: self.append_output(message))

        try:
            check_script_deps_and_install(dest_abs_path, rel_path, self.root, output_callback=output_to_console)
        except Exception as e:
            log_error(f"依赖检查异常: {str(e)}")

    def get_selected_item(self):
        sel = self.listbox.curselection()
        if not sel:
            return None

        display_name = self.listbox.get(sel[0])
        for item in self.scripts:
            if item["display"] == display_name and item.get("group") == self.group_manager.current_group:
                return item
        return None

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for item in self.scripts:
            if item.get("group") == self.group_manager.current_group:
                self.listbox.insert(tk.END, item["display"])

    def scan_data_directory(self):
        added = 0
        updated = 0

        for root, dirs, files in os.walk(self.data_dir):
            for file_name in files:
                if file_name.endswith('.py'):
                    file_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(file_path, self.data_dir).replace('\\', '/')

                    relative_dir = os.path.dirname(relative_path)
                    if relative_dir == '.' or relative_dir == '':
                        group = DEFAULT_GROUP
                    else:
                        group = relative_dir.split('/')[0]

                    existing_index = None
                    for i, script in enumerate(self.scripts):
                        if script['storage_path'] == relative_path:
                            existing_index = i
                            break

                    if existing_index is not None:
                        self.scripts[existing_index]["display"] = relative_path
                        self.scripts[existing_index]["group"] = group
                        updated += 1
                    else:
                        self.scripts.append({
                            "display": relative_path,
                            "storage_path": relative_path,
                            "group": group
                        })
                        added += 1

        groups_set = set()
        for script in self.scripts:
            groups_set.add(script.get("group", DEFAULT_GROUP))

        groups_changed = False
        for g in groups_set:
            if g not in self.group_manager.groups:
                self.group_manager.groups.append(g)
                groups_changed = True

        if groups_changed:
            self.group_manager.save_groups()
            self.group_manager.refresh_combo()

        if added > 0 or updated > 0:
            self.update_listbox()
            self.status_var.set(f"扫描完成：添加 {added} 个脚本，更新 {updated} 个脚本")
            self.append_output(f"扫描完成：添加 {added} 个脚本，更新 {updated} 个脚本")

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
            except Exception as e:
                log_error(f"版本检查异常: {str(e)}")
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

# ================== 启动入口 ==================
if __name__ == "__main__":
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
        except Exception as install_err:
            log_error(f"自动安装失败：{str(install_err)}")
            log_error("自动安装失败，请手动执行：pip install tkinterdnd2 -i https://pypi.tuna.tsinghua.edu.cn/simple")
        sys.exit(1)
    except Exception as e:
        log_error(f"Tkinter 初始化失败：{str(e)}")
        sys.exit(1)

    try:
        app = ScriptManager(root)
        root.mainloop()
    except Exception as e:
        log_error(f"程序运行时发生未捕获异常：{str(e)}")
        try:
            messagebox.showerror("致命错误", f"程序发生错误：\n{str(e)}\n\n详细信息已写入 logs/error_log.txt")
        except:
            pass
        sys.exit(1)
