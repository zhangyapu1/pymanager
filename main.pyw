import os
import sys
import shutil
import threading
import tkinter as tk
from tkinter import messagebox

# 导入模块
import modules.updater as updater
from modules.config import BASE_DIR, DATA_DIR, DEFAULT_GROUP
from modules.logger import log_error
from modules.drag_drop import parse_dropped_files
from modules.utils import update_title_mode
from modules.group_manager import GroupManager
from modules.add_script import add_script
from modules.run_selected import run_selected
from modules.rename_selected import rename_selected
from modules.edit_content import edit_content
from modules.check_deps import check_deps
from modules.delete_selected import delete_selected
from modules.dependencies import check_self_dependencies, check_script_deps_and_install

# ================== 主程序类 ==================

class ScriptManager:
    def __init__(self, root):
        self.root = root
        # 统一使用实例变量引用配置，避免混淆
        self.data_dir = DATA_DIR
        self.base_dir = BASE_DIR
        self.scripts = []
        self.group_manager = GroupManager(self.data_dir)

        self.create_widgets()

        try:
            # 定义输出回调函数
            def output_to_console(message):
                """输出信息到运行输出窗口"""
                self.output_text.insert(tk.END, message + '\n')
                self.output_text.see(tk.END)
            
            check_self_dependencies(self.root, output_callback=output_to_console)
        except Exception as e:
            log_error(f"依赖检查失败：{str(e)}")
            messagebox.showerror("初始化错误", f"依赖检查时出错：\n{str(e)}\n\n详细信息已写入 error_log.txt")
            sys.exit(1)
        self.scan_data_directory()
        self.setup_drag_drop()
        update_title_mode(self.root)
        
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
            main_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)

            self.listbox = tk.Listbox(main_frame, selectmode=tk.SINGLE, font=('Consolas', 10))
            self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.listbox.bind('<Double-Button-1>', lambda e: run_selected(self))
            self.listbox.bind("<Button-3>", self.show_context_menu)

            scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.listbox.config(yscrollcommand=scrollbar.set)

            btn_frame = tk.Frame(self.root)
            btn_frame.pack(fill=tk.X, padx=10, pady=5)

            # 按钮列表 - 使用默认参数捕获 lambda，避免闭包问题
            buttons = [
                ("➕ 添加脚本", lambda: add_script(self)),
                ("🔍 检查依赖", lambda: check_deps(self)),
                ("🔄 检查更新", lambda: updater.check_for_updates(self.root, show_no_update_msg=True)),
                ("🔑 删除Token", lambda: self.delete_token()),
                ("📁 打开程序目录", lambda: self.open_program_dir()),
            ]
            for i, (text, cmd) in enumerate(buttons):
                btn = tk.Button(btn_frame, text=text, command=lambda c=cmd: c())
                btn.pack(side=tk.LEFT, padx=5, pady=2)

            # 输出窗口
            output_frame = tk.Frame(self.root)
            output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            output_label = tk.Label(output_frame, text="运行输出:")
            output_label.pack(anchor=tk.W)
            
            # 加高运行输出框
            self.output_text = tk.Text(output_frame, font=('Consolas', 10))
            self.output_text.pack(fill=tk.BOTH, expand=True)
            
            output_scrollbar = tk.Scrollbar(self.output_text, orient=tk.VERTICAL, command=self.output_text.yview)
            output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.output_text.config(yscrollcommand=output_scrollbar.set)
            
            # 设置窗口初始大小，确保输出窗口有足够的高度
            self.root.geometry("800x600")
            
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
        from tkinterdnd2 import DND_FILES
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
        
        self.group_manager.save_groups()
        
        # 异步检查依赖，避免阻塞 UI
        def output_to_console(message):
            """输出信息到运行输出窗口"""
            self.output_text.insert(tk.END, message + '\n')
            self.output_text.see(tk.END)
        
        try:
            check_script_deps_and_install(dest_path, display_name, self.root, output_callback=output_to_console)
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

    def delete_token(self):
        from modules.token_crypto import delete_api_token, get_api_token
        if not get_api_token():
            messagebox.showinfo("提示", "当前没有保存的 Token。")
            return
        if messagebox.askyesno("确认删除", "确定要删除已保存的 GitHub API Token 吗？"):
            delete_api_token()
            self.status_var.set("已删除保存的 Token")

    def open_program_dir(self):
        import subprocess
        program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        subprocess.Popen(f'explorer "{program_dir}"')

# ================== 启动入口 ==================
if __name__ == "__main__":
    def restart_app():
        """自动重启当前程序"""
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