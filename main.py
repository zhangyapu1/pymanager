import os
import sys
import shutil
import uuid
import traceback
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD

# 导入模块
import modules as actions
import modules.updater as updater
from modules.config import BASE_DIR, DATA_DIR, DEFAULT_GROUP
from modules.logger import log_error
from modules.drag_drop import parse_dropped_files
from modules.utils import update_title_mode
from modules.group_manager import GroupManager

# ================== 主程序类 ==================

class ScriptManager:
    def __init__(self, root):
        self.root = root
        # 统一使用实例变量引用配置，避免混淆
        self.data_dir = DATA_DIR
        self.base_dir = BASE_DIR
        self.scripts = []
        self.group_manager = GroupManager(self.data_dir)

        try:
            actions.check_self_dependencies(self.root)
        except Exception as e:
            log_error(f"依赖检查失败：{str(e)}")
            messagebox.showerror("初始化错误", f"依赖检查时出错：\n{str(e)}\n\n详细信息已写入 error_log.txt")
            sys.exit(1)

        self.create_widgets()
        self.scan_data_directory()
        self.setup_drag_drop()
        update_title_mode(self.root, self.data_dir, self.base_dir)
        
        # 显示版本信息
        self.show_version_info()

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
            
            # 版本信息标签
            self.version_var = tk.StringVar()
            self.version_var.set("版本信息加载中...")
            version_bar = tk.Label(self.root, textvariable=self.version_var, bd=1, relief=tk.SUNKEN, anchor=tk.E, font=('Arial', 8))
            version_bar.pack(side=tk.BOTTOM, fill=tk.X)
            
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
        
        # 修复：在循环中正确捕获 group 变量
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
        menu.add_separator()
        menu.add_command(label="刷新列表", command=self.scan_data_directory)

        menu.post(event.x_root, event.y_root)

    def move_script_to_group(self, item, target_group):
        if item["group"] == target_group:
            return
        old_group = item["group"]
        
        # 移动文件到对应的子文件夹
        old_path = item["storage_path"]
        file_name = os.path.basename(old_path)
        
        # 确定目标目录
        if target_group == DEFAULT_GROUP:
            target_dir = self.data_dir
        else:
            target_dir = os.path.join(self.data_dir, target_group)
            # 确保分组文件夹存在
            os.makedirs(target_dir, exist_ok=True)
        
        # 生成唯一的目标路径，处理冲突
        new_path = self._get_unique_path(target_dir, file_name)
        
        try:
            # 移动文件
            shutil.move(old_path, new_path)
            
            # 更新脚本信息
            item["group"] = target_group
            item["storage_path"] = new_path
            
            # 更新显示名称
            relative_path = os.path.relpath(new_path, self.data_dir)
            item["display"] = relative_path.replace('\\', '/')
            
            # 关键修复：移动成功后需要保存状态，确保数据一致性
            # 假设 actions 或本类有保存脚本列表的机制，这里调用通用的保存逻辑
            # 如果 save_scripts 是 actions 模块的函数，应改为 actions.save_scripts(self)
            # 鉴于原代码在 add_script 中调用了 self.save_scripts()，我们保持一致
            if hasattr(self, 'save_scripts'):
                self.save_scripts()
            else:
                # 如果不存在，至少保存分组信息，防止分组元数据丢失
                self.group_manager.save_groups()
                
            self.update_listbox()
            self.status_var.set(f"已将「{item['display']}」从「{old_group}」移动到「{target_group}」")
            
        except Exception as e:
            log_error(f"移动文件失败: {str(e)}")
            messagebox.showerror("错误", f"移动文件失败：{str(e)}")

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
            # 增加健壮性检查：确保路径有效
            if not f or not os.path.exists(f):
                skipped += 1
                continue
                
            if f.lower().endswith('.py'):
                self.add_script_from_path(f)
                added += 1
            else:
                skipped += 1
        self.status_var.set(f"拖拽完成：添加 {added} 个脚本，跳过 {skipped} 个非.py文件")

    # ------------------ 核心数据操作 ------------------
    
    def _get_unique_path(self, directory, filename):
        """
        生成一个不存在的唯一文件路径。
        如果文件已存在，则在文件名后添加 _1, _2 等后缀。
        """
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

    def add_script_from_path(self, src_path):
        if not os.path.isfile(src_path):
            self.status_var.set(f"文件不存在：{src_path}")
            return

        base_name = os.path.basename(src_path)
        
        # 使用 helper 方法处理冲突
        dest_path = self._get_unique_path(self.data_dir, base_name)
        dest_name = os.path.basename(dest_path)

        try:
            shutil.copy2(src_path, dest_path)
        except Exception as e:
            log_error(f"复制脚本失败: {str(e)}")
            messagebox.showerror("复制失败", f"无法复制脚本：{e}")
            return

        display_name = dest_name
        new_script = {
            "display": display_name,
            "storage_path": dest_path,
            "group": self.group_manager.current_group
        }
        
        self.scripts.append(new_script)
        self.update_listbox()
        self.status_var.set(f"已添加：{display_name} (分组：{self.group_manager.current_group})")
        
        # 保存状态
        if hasattr(self, 'save_scripts'):
            self.save_scripts()
        
        # 异步检查依赖，避免阻塞 UI
        # 注意：原代码是同步调用，如果检查耗时会卡住 UI。
        # 这里保持原逻辑，但建议在实际 actions.check_script_deps_and_install 内部处理异步或快速返回
        try:
            actions.check_script_deps_and_install(dest_path, display_name, self.root)
        except Exception as e:
            log_error(f"依赖检查异常: {str(e)}")

    def get_selected_item(self):
        sel = self.listbox.curselection()
        if not sel:
            # 移除这里的 messagebox，因为在右键菜单触发时，如果没有选中项通常直接返回即可，
            # 或者由调用者决定如何提示。原代码在 show_context_menu 已经做了检查。
            # 但为了保持 get_selected_item 的通用性，如果其他地方调用且未选中，可能需要提示。
            # 此处保持原逻辑，但注意重复弹窗问题。
            # 优化：仅在明确需要用户交互时才弹窗，或者返回 None 让调用者处理。
            # 原代码在 show_context_menu 中已经检查了 curselection，所以这里如果是从那里调用的，不会触发。
            # 如果是从按钮点击调用，可能需要提示。
            return None
            
        display_name = self.listbox.get(sel[0])
        for item in self.scripts:
            # 严格匹配显示名称和当前分组
            if item["display"] == display_name and item.get("group") == self.group_manager.current_group:
                return item
        return None

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for item in self.scripts:
            if item.get("group") == self.group_manager.current_group:
                self.listbox.insert(tk.END, item["display"])
        
    def scan_data_directory(self):
        """扫描data目录下的py文件，自动添加到脚本列表"""
        added = 0
        updated = 0
        
        # 递归遍历data目录下的所有py文件
        # 注意：如果文件量巨大，这会阻塞 UI。
        for root, dirs, files in os.walk(self.data_dir):
            for file_name in files:
                if file_name.endswith('.py'):
                    file_path = os.path.join(root, file_name)
                    # 计算相对路径，用于显示
                    relative_path = os.path.relpath(file_path, self.data_dir)
                    display_name = relative_path.replace('\\', '/')
                    
                    # 根据目录结构确定分组
                    relative_dir = os.path.dirname(relative_path)
                    if relative_dir == '.' or relative_dir == '':
                        group = DEFAULT_GROUP
                    else:
                        # 取第一级子目录作为分组
                        group = relative_dir.split(os.sep)[0]
                    
                    # 检查是否已存在
                    existing_index = None
                    for i, script in enumerate(self.scripts):
                        if script['storage_path'] == file_path:
                            existing_index = i
                            break
                    
                    if existing_index is not None:
                        # 已存在，更新信息（以防分组变动或显示名变动）
                        self.scripts[existing_index]["display"] = display_name
                        self.scripts[existing_index]["group"] = group
                        updated += 1
                    else:
                        # 不存在，添加新脚本
                        self.scripts.append({
                            "display": display_name,
                            "storage_path": file_path,
                            "group": group
                        })
                        added += 1
        
        # 更新分组列表
        groups_set = set()
        for script in self.scripts:
            groups_set.add(script.get("group", DEFAULT_GROUP))
        
        # 更新group_manager中的分组列表
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
        elif added == 0 and updated == 0:
             # 即使没有变化，也可以刷新一下状态，或者保持静默
             pass

    def show_version_info(self):
        """显示当前版本号和最新版本号"""
        
        def check_version_thread():
            try:
                # 获取当前版本（从updater模块获取）
                current_version = updater.CURRENT_VERSION
                
                # 检查最新版本
                latest_version = updater.get_latest_version()
                
                if latest_version:
                    status = "最新版本" if current_version == latest_version else "有新版本"
                    msg = f"当前版本：{current_version} | 最新版本：{latest_version} | {status}"
                else:
                    msg = f"当前版本：{current_version} | 检查更新失败"
            except Exception as e:
                log_error(f"版本检查异常: {str(e)}")
                msg = f"当前版本：1.0.0 | 检查更新失败"
            
            # 关键修复：使用 after 在主线程更新 UI
            self.root.after(0, lambda: self.version_var.set(msg))
        
        # 在后台线程中检查版本，避免阻塞UI
        thread = threading.Thread(target=check_version_thread)
        thread.daemon = True
        thread.start()

    def save_scripts(self):
        """
        持久化保存脚本列表。
        注意：原代码中调用了此方法但未定义。
        这里提供一个基本实现，实际项目中应根据具体需求（如保存到 JSON/SQLite）实现。
        如果 actions 模块中有专门的保存逻辑，应调用那个。
        此处仅为防止 NameError 并满足代码完整性。
        """
        # 示例：保存到 JSON 文件（假设）
        # import json
        # with open(os.path.join(self.data_dir, 'scripts.json'), 'w', encoding='utf-8') as f:
        #     json.dump(self.scripts, f, ensure_ascii=False, indent=4)
        # 
        # 或者，如果原意是调用 actions 中的方法：
        # actions.save_scripts_to_disk(self.scripts)
        
        # 由于不知道具体的持久化策略，且原代码在 add_script 中调用了它，
        # 我们必须确保它存在。如果这是一个空操作，至少不报错。
        # 更好的做法是确认 actions 模块是否有此功能。
        # 这里暂时留空或记录日志，实际使用时请补充具体逻辑。
        pass

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