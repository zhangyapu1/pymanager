import os
import sys
import shutil
import uuid
import traceback
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD

# 导入模块
import modules as actions
import modules.updater as updater
from modules.config import BASE_DIR, DATA_DIR, CONFIG_FILE, DEFAULT_GROUP
from modules.logger import log_error
from modules.storage import save_scripts, load_scripts
from modules.drag_drop import parse_dropped_files
from modules.utils import update_title_mode
from modules.group_manager import GroupManager

# ================== 主程序类 ==================
class ScriptManager:
    def __init__(self, root):
        self.root = root
        self.DATA_DIR = DATA_DIR
        self.CONFIG_FILE = CONFIG_FILE
        self.scripts = []
        self.group_manager = GroupManager(DATA_DIR)

        try:
            actions.check_self_dependencies(self.root)
        except Exception as e:
            log_error(f"依赖检查失败：{str(e)}")
            messagebox.showerror("初始化错误", f"依赖检查时出错：\n{str(e)}\n\n详细信息已写入 error_log.txt")
            sys.exit(1)

        self.create_widgets()
        self.load_scripts()
        self.scan_data_directory()
        self.setup_drag_drop()
        update_title_mode(self.root, DATA_DIR, BASE_DIR)

        self.root.after(3000, lambda: updater.check_for_updates(self.root, show_no_update_msg=False))

    # ------------------ 界面 ------------------
    def create_widgets(self):
        try:
            top_frame = tk.Frame(self.root)
            top_frame.pack(fill=tk.X, padx=10, pady=5)

            # 创建分组控件（GroupManager 内部管理 Combo 状态）
            self.group_combo, _, _ = self.group_manager.create_group_widgets(
                top_frame,
                on_group_changed_callback=self.on_group_changed
            )

            main_frame = tk.Frame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            self.listbox = tk.Listbox(main_frame, selectmode=tk.SINGLE, font=("Consolas", 10))
            self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.listbox.bind('<Double-Button-1>', lambda e: actions.run_selected(self))
            self.listbox.bind("<Button-3>", self.show_context_menu)

            scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.listbox.config(yscrollcommand=scrollbar.set)

            btn_frame = tk.Frame(self.root)
            btn_frame.pack(fill=tk.X, padx=10, pady=5)

            # 按钮列表 - 使用默认参数捕获 lambda，避免闭包问题
            buttons = [
                ("➕ 添加脚本", lambda: actions.add_script(self)),
                ("▶ 运行选中", lambda: actions.run_selected(self)),
                ("✏️ 重命名", lambda: actions.rename_selected(self)),
                ("📝 编辑内容", lambda: actions.edit_content(self)),
                ("🔍 检查依赖", lambda: actions.check_deps(self)),
                ("🔄 检查更新", lambda: updater.check_for_updates(self.root, show_no_update_msg=True)),
                ("❌ 删除选中", lambda: actions.delete_selected(self))
            ]
            for text, cmd in buttons:
                # 使用默认参数固定 cmd，防止循环变量捕获错误
                btn = tk.Button(btn_frame, text=text, command=lambda c=cmd: c())
                btn.pack(side=tk.LEFT, padx=2)

            self.status_var = tk.StringVar()
            self.status_var.set("就绪 | 拖拽 .py 文件自动复制存储，并检查依赖")
            status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        except Exception as e:
            log_error(f"创建界面失败：{str(e)}")
            messagebox.showerror("界面错误", f"无法创建界面：{str(e)}\n\n详细信息已写入 error_log.txt")
            sys.exit(1)

    def on_group_changed(self, new_group):
        self.group_manager.current_group = new_group
        self.update_listbox()
        self.status_var.set(f"当前分组：{new_group}")

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
        menu.add_command(label="运行", command=lambda: actions.run_selected(self))
        menu.add_command(label="编辑内容", command=lambda: actions.edit_content(self))
        menu.add_command(label="重命名", command=lambda: actions.rename_selected(self))
        menu.add_command(label="删除", command=lambda: actions.delete_selected(self))

        menu.post(event.x_root, event.y_root)

    def move_script_to_group(self, item, target_group):
        if item["group"] == target_group:
            return
        old_group = item["group"]
        item["group"] = target_group
        self.save_scripts()
        self.update_listbox()
        self.status_var.set(f"已将「{item['display']}」从「{old_group}」移动到「{target_group}」")

    def create_group_and_move(self, item):
        new_group = self.group_manager.new_group(self.root)
        if new_group:
            self.move_script_to_group(item, new_group)

    # ------------------ 拖拽 ------------------
    def setup_drag_drop(self):
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        files = parse_dropped_files(event.data)
        added = 0
        skipped = 0
        for f in files:
            if f.lower().endswith('.py'):
                self.add_script_from_path(f)
                added += 1
            else:
                skipped += 1
        self.status_var.set(f"拖拽完成：添加 {added} 个脚本，跳过 {skipped} 个非.py文件")

    # ------------------ 核心数据操作 ------------------
    def add_script_from_path(self, src_path):
        if not os.path.isfile(src_path):
            self.status_var.set(f"文件不存在：{src_path}")
            return

        base_name = os.path.basename(src_path)
        dest_name = base_name
        counter = 1
        name_without_ext, ext = os.path.splitext(base_name)
        while os.path.exists(os.path.join(DATA_DIR, dest_name)):
            dest_name = f"{name_without_ext}_{counter}{ext}"
            counter += 1

        storage_path = os.path.join(DATA_DIR, dest_name)
        try:
            shutil.copy2(src_path, storage_path)
        except Exception as e:
            messagebox.showerror("复制失败", f"无法复制脚本：{e}")
            return

        display_name = dest_name
        self.scripts.append({
            "display": display_name,
            "storage_path": storage_path,
            "group": self.group_manager.current_group
        })
        self.update_listbox()
        self.status_var.set(f"已添加：{display_name} (分组：{self.group_manager.current_group})")
        self.save_scripts()
        actions.check_script_deps_and_install(storage_path, display_name, self.root)

    def get_selected_item(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("未选中", "请先选择一个脚本")
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

    def save_scripts(self):
        save_scripts(self.scripts, CONFIG_FILE)

    def load_scripts(self):
        scripts, groups_set = load_scripts(CONFIG_FILE, self.group_manager.groups)
        self.scripts = scripts
        for g in groups_set:
            if g not in self.group_manager.groups:
                self.group_manager.groups.append(g)
        self.group_manager.save_groups()
        # 刷新分组下拉菜单（由 GroupManager 负责）
        self.group_manager.refresh_combo()
        self.update_listbox()
        self.status_var.set(f"已加载 {len(self.scripts)} 个脚本")
        
    def scan_data_directory(self):
        """扫描data目录下的py文件，自动添加到脚本列表"""
        added = 0
        updated = 0
        
        # 遍历data目录下的所有py文件
        for file_name in os.listdir(DATA_DIR):
            if file_name.endswith('.py'):
                file_path = os.path.join(DATA_DIR, file_name)
                
                # 检查是否已存在
                existing_index = None
                for i, script in enumerate(self.scripts):
                    if script['display'] == file_name:
                        existing_index = i
                        break
                
                if existing_index is not None:
                    # 已存在，更新信息
                    self.scripts[existing_index] = {
                        "display": file_name,
                        "storage_path": file_path,
                        "group": self.scripts[existing_index].get("group", DEFAULT_GROUP)
                    }
                    updated += 1
                else:
                    # 不存在，添加新脚本
                    self.scripts.append({
                        "display": file_name,
                        "storage_path": file_path,
                        "group": DEFAULT_GROUP
                    })
                    added += 1
        
        if added > 0 or updated > 0:
            self.save_scripts()
            self.update_listbox()
            self.status_var.set(f"扫描完成：添加 {added} 个脚本，更新 {updated} 个脚本")

# ================== 启动入口 ==================
if __name__ == "__main__":
    def restart_app():
        """自动重启当前程序"""
        os.execv(sys.executable, [sys.executable] + sys.argv)

    try:
        root = TkinterDnD.Tk()
    except ImportError as e:
        log_error(f"缺少 tkinterdnd2：{str(e)}")
        try:
            import subprocess
            print("正在尝试自动安装 tkinterdnd2...")
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-i', "https://pypi.tuna.tsinghua.edu.cn/simple", 'tkinterdnd2'],
                check=True
            )
            print("安装成功，程序将自动重启。")
            restart_app()
        except Exception as install_err:
            log_error(f"自动安装失败：{str(install_err)}")
            print("自动安装失败，请手动执行：pip install tkinterdnd2 -i https://pypi.tuna.tsinghua.edu.cn/simple")
        sys.exit(1)
    except Exception as e:
        log_error(f"Tkinter 初始化失败：{str(e)}")
        print(e)
        sys.exit(1)

    try:
        app = ScriptManager(root)
        root.mainloop()
    except Exception as e:
        log_error(f"程序运行时发生未捕获异常：{str(e)}")
        try:
            messagebox.showerror("致命错误", f"程序发生错误：\n{str(e)}\n\n详细信息已写入 error_log.txt")
        except:
            pass
        sys.exit(1)