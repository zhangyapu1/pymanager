import os
import sys
import shutil
import subprocess
import pickle
import uuid
import ast
import importlib
import tempfile
import zipfile
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD

# ================== 配置 ==================
# 判断是否为便携模式：如果程序所在目录存在 "data" 文件夹，则使用该文件夹，否则使用用户目录
if getattr(sys, 'frozen', False):
    # 打包成 exe 时，程序所在目录为 sys.executable 的目录
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PORTABLE_DATA_DIR = os.path.join(BASE_DIR, "data")
if os.path.exists(PORTABLE_DATA_DIR):
    DATA_DIR = PORTABLE_DATA_DIR
else:
    DATA_DIR = os.path.join(os.path.expanduser("~"), ".pymanager_scripts")

CONFIG_FILE = os.path.join(DATA_DIR, "scripts.dat")
os.makedirs(DATA_DIR, exist_ok=True)

# 自身依赖列表
SELF_DEPENDENCIES = ['tkinterdnd2']
# 清华大学镜像源
TUNA_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"

# ================== 依赖检查工具 ==================
class DependencyChecker:
    @staticmethod
    def is_package_installed(package_name):
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False

    @staticmethod
    def install_package(package_name, parent_window=None, use_mirror=True):
        cmd = [sys.executable, '-m', 'pip', 'install', package_name]
        if use_mirror:
            cmd.extend(['-i', TUNA_MIRROR])
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            if use_mirror:
                return DependencyChecker.install_package(package_name, parent_window, use_mirror=False)
            else:
                error_msg = f"安装 {package_name} 失败：\n{e.stderr}"
                if parent_window:
                    messagebox.showerror("安装失败", error_msg)
                else:
                    print(error_msg)
                return False

    @staticmethod
    def extract_imports_from_script(script_path):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
        except Exception:
            return set()
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_module = alias.name.split('.')[0]
                    imports.add(top_module)
            elif isinstance(node, ast.ImportFrom):
                if node.module and not node.module.startswith('.'):
                    top_module = node.module.split('.')[0]
                    imports.add(top_module)
        return imports

    @staticmethod
    def is_stdlib_module(module_name):
        if hasattr(sys, 'stdlib_module_names'):
            return module_name in sys.stdlib_module_names
        try:
            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin and 'site-packages' not in spec.origin:
                return True
        except Exception:
            pass
        return False

    @classmethod
    def get_missing_dependencies(cls, script_path):
        required_modules = cls.extract_imports_from_script(script_path)
        missing = []
        for mod in required_modules:
            if cls.is_stdlib_module(mod):
                continue
            if cls.is_package_installed(mod):
                continue
            missing.append(mod)
        return missing

# ================== 主程序 ==================
class ScriptManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 脚本管理器")
        self.root.geometry("750x500")
        self.scripts = []
        self.deps_checker = DependencyChecker()
        self.check_self_dependencies()
        self.create_widgets()
        self.load_scripts()
        self.setup_drag_drop()
        self.update_title_mode()

    def update_title_mode(self):
        """窗口标题显示当前模式（便携/非便携）"""
        if DATA_DIR == PORTABLE_DATA_DIR:
            mode = "便携模式"
        else:
            mode = "本地模式"
        self.root.title(f"Python 脚本管理器 - {mode}")

    def check_self_dependencies(self):
        missing = []
        for pkg in SELF_DEPENDENCIES:
            if not self.deps_checker.is_package_installed(pkg):
                missing.append(pkg)
        if missing:
            msg = f"缺少必要依赖：{', '.join(missing)}，是否立即安装？（将使用清华大学镜像源加速）"
            if messagebox.askyesno("缺少依赖", msg):
                for pkg in missing:
                    if self.deps_checker.install_package(pkg, self.root):
                        messagebox.showinfo("安装成功", f"{pkg} 安装成功，请重启程序。")
                    else:
                        messagebox.showerror("安装失败", f"{pkg} 安装失败，请手动安装。")
                sys.exit(0)
            else:
                messagebox.showwarning("警告", "缺少依赖，程序可能无法正常工作。")

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.listbox = tk.Listbox(main_frame, selectmode=tk.SINGLE, font=("Consolas", 10))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind('<Double-Button-1>', self.run_selected)

        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        buttons = [
            ("➕ 添加脚本", self.add_script),
            ("▶ 运行选中", self.run_selected),
            ("✏️ 重命名", self.rename_selected),
            ("📝 编辑内容", self.edit_content_selected),
            ("✏ 外部编辑", self.edit_selected),
            ("🔍 检查依赖", self.check_selected_deps),
            ("💾 备份迁移", self.backup_and_migrate),  # 新增
            ("❌ 删除选中", self.delete_selected)
        ]
        for text, cmd in buttons:
            btn = tk.Button(btn_frame, text=text, command=cmd)
            btn.pack(side=tk.LEFT, padx=2)

        self.status_var = tk.StringVar()
        self.status_var.set("就绪 | 拖拽 .py 文件自动复制存储，并检查依赖")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_drag_drop(self):
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        raw = event.data
        files = self.parse_dropped_files(raw)
        for f in files:
            if f.lower().endswith('.py'):
                self.add_script_from_path(f)
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

    def add_script(self):
        path = filedialog.askopenfilename(
            title="选择 Python 脚本",
            filetypes=[("Python 文件", "*.py"), ("所有文件", "*.*")]
        )
        if path:
            self.add_script_from_path(path)

    def add_script_from_path(self, src_path):
        if not os.path.isfile(src_path):
            self.status_var.set(f"文件不存在：{src_path}")
            return
        unique_name = f"{uuid.uuid4().hex}.py"
        storage_path = os.path.join(DATA_DIR, unique_name)
        try:
            shutil.copy2(src_path, storage_path)
        except Exception as e:
            messagebox.showerror("复制失败", f"无法复制脚本：{e}")
            return
        display_name = os.path.basename(src_path)
        self.scripts.append({
            "display": display_name,
            "storage_path": storage_path
        })
        self.update_listbox()
        self.status_var.set(f"已添加：{display_name}")
        self.save_scripts()
        self.check_script_deps_and_install(storage_path, display_name)

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for item in self.scripts:
            self.listbox.insert(tk.END, item["display"])

    def get_selected_item(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("未选中", "请先选择一个脚本")
            return None
        return self.scripts[sel[0]]

    def run_selected(self, event=None):
        item = self.get_selected_item()
        if not item:
            return
        path = item["storage_path"]
        try:
            subprocess.Popen([sys.executable, path], shell=True)
            self.status_var.set(f"正在运行：{item['display']}")
        except Exception as e:
            messagebox.showerror("运行错误", str(e))

    def edit_selected(self):
        item = self.get_selected_item()
        if not item:
            return
        path = item["storage_path"]
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
            self.status_var.set(f"正在编辑：{item['display']}")
        except Exception as e:
            messagebox.showerror("编辑错误", str(e))

    def rename_selected(self):
        item = self.get_selected_item()
        if not item:
            return
        new_name = simpledialog.askstring("重命名", "请输入新的显示名称（不含路径）:", initialvalue=item["display"])
        if new_name and new_name.strip():
            new_name = new_name.strip()
            if not new_name.endswith('.py'):
                new_name += '.py'
            old_display = item["display"]
            item["display"] = new_name
            self.update_listbox()
            self.save_scripts()
            self.status_var.set(f"已重命名：{old_display} -> {new_name}")
        else:
            self.status_var.set("重命名已取消")

    def edit_content_selected(self):
        item = self.get_selected_item()
        if not item:
            return
        script_path = item["storage_path"]
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("读取错误", f"无法读取脚本内容：{e}")
            return

        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"编辑脚本 - {item['display']}")
        edit_win.geometry("800x600")

        text_widget = tk.Text(edit_win, wrap=tk.NONE, font=("Consolas", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_widget.insert("1.0", content)

        scroll_y = tk.Scrollbar(text_widget, orient=tk.VERTICAL, command=text_widget.yview)
        scroll_x = tk.Scrollbar(text_widget, orient=tk.HORIZONTAL, command=text_widget.xview)
        text_widget.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        def save_content():
            new_content = text_widget.get("1.0", tk.END)
            try:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                self.status_var.set(f"已保存：{item['display']}")
                edit_win.destroy()
                self.check_script_deps_and_install(script_path, item['display'])
            except Exception as e:
                messagebox.showerror("保存错误", f"保存失败：{e}")

        btn_frame = tk.Frame(edit_win)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="保存", command=save_content).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="取消", command=edit_win.destroy).pack(side=tk.RIGHT, padx=5)

    def check_script_deps_and_install(self, script_path, display_name):
        missing = self.deps_checker.get_missing_dependencies(script_path)
        if not missing:
            self.status_var.set(f"依赖检查：{display_name} 所有第三方依赖已满足")
            return
        msg = f"脚本「{display_name}」缺少以下依赖：\n{', '.join(missing)}\n是否立即安装？（将使用清华大学镜像源加速）"
        if messagebox.askyesno("缺少依赖", msg):
            for pkg in missing:
                if self.deps_checker.install_package(pkg, self.root):
                    self.status_var.set(f"已安装：{pkg}")
                else:
                    messagebox.showerror("安装失败", f"{pkg} 安装失败，请手动处理。")
            still_missing = [p for p in missing if not self.deps_checker.is_package_installed(p)]
            if still_missing:
                messagebox.showwarning("部分依赖未安装", f"下列依赖未成功安装：{', '.join(still_missing)}")
            else:
                messagebox.showinfo("完成", "所有缺失依赖已安装")
        else:
            self.status_var.set(f"已跳过依赖安装：{display_name}")

    def check_selected_deps(self):
        item = self.get_selected_item()
        if not item:
            return
        self.check_script_deps_and_install(item["storage_path"], item["display"])

    def backup_and_migrate(self):
        """备份迁移工具：将本程序和数据目录打包成 ZIP"""
        # 选择保存路径
        save_path = filedialog.asksaveasfilename(
            title="保存备份文件",
            defaultextension=".zip",
            filetypes=[("ZIP 压缩文件", "*.zip"), ("所有文件", "*.*")]
        )
        if not save_path:
            self.status_var.set("备份取消")
            return

        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        try:
            # 1. 复制本程序文件（自身）
            if getattr(sys, 'frozen', False):
                # 打包成 exe
                self_file = sys.executable
                dest_main = os.path.join(temp_dir, os.path.basename(self_file))
            else:
                # 脚本模式：复制当前 .py 或 .pyw 文件
                self_file = os.path.abspath(sys.argv[0])
                # 重命名为 ScriptManager.pyw 便于双击无控制台
                base_name = os.path.splitext(os.path.basename(self_file))[0]
                if self_file.endswith('.pyw'):
                    dest_main = os.path.join(temp_dir, "ScriptManager.pyw")
                else:
                    dest_main = os.path.join(temp_dir, "ScriptManager.py")
            shutil.copy2(self_file, dest_main)

            # 2. 复制数据目录中的所有脚本到 temp_dir/data/
            data_backup_dir = os.path.join(temp_dir, "data")
            shutil.copytree(DATA_DIR, data_backup_dir, dirs_exist_ok=True)

            # 3. 生成启动说明文件
            readme_content = f"""脚本管理器备份包使用说明

本备份包包含：
- 脚本管理器程序
- 所有已添加的脚本（已存储在 data 文件夹中）

使用方法（在其他电脑上）：
1. 确保已安装 Python 3.7+ 和 pip。
2. 解压本 ZIP 文件到任意目录。
3. （可选）安装必要依赖：打开命令行，进入解压目录，执行：
   pip install -r requirements.txt
4. 运行程序：
   - Windows: 双击 "ScriptManager.pyw"（无控制台）或 "start.bat"
   - Linux/macOS: 在终端执行 "python3 ScriptManager.py" 或 "python3 ScriptManager.pyw"

程序启动后会自动以便携模式运行（使用同目录下的 data 文件夹），无需重新添加脚本。

注意：如果目标电脑缺少 tkinterdnd2，程序启动时会自动提示安装。
生成时间：{self.get_current_time()}
"""
            readme_path = os.path.join(temp_dir, "启动说明.txt")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)

            # 4. 生成 requirements.txt（包含自身依赖）
            req_path = os.path.join(temp_dir, "requirements.txt")
            with open(req_path, 'w', encoding='utf-8') as f:
                f.write("tkinterdnd2\n")

            # 5. 生成 start.bat（Windows 快捷启动）
            bat_path = os.path.join(temp_dir, "start.bat")
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write("@echo off\n")
                f.write("echo 正在启动脚本管理器...\n")
                f.write("start \"\" pythonw ScriptManager.pyw\n")
                f.write("echo 启动完成，如果无窗口弹出请检查 Python 环境。\n")
                f.write("pause\n")

            # 6. 打包成 ZIP
            shutil.make_archive(save_path[:-4], 'zip', temp_dir)
            self.status_var.set(f"备份成功！已保存至：{save_path}")
            messagebox.showinfo("备份完成", f"备份文件已生成：\n{save_path}\n\n该文件可迁移到其他电脑使用。")
        except Exception as e:
            messagebox.showerror("备份失败", f"打包过程中出错：{str(e)}")
            self.status_var.set("备份失败")
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

    def get_current_time(self):
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def delete_selected(self):
        item = self.get_selected_item()
        if not item:
            return
        if messagebox.askyesno("确认删除", f"从管理器中移除\n{item['display']}\n（内部存储的副本也会被删除）"):
            try:
                if os.path.exists(item["storage_path"]):
                    os.remove(item["storage_path"])
            except Exception as e:
                messagebox.showwarning("删除警告", f"无法删除内部文件：{e}")
            self.scripts.remove(item)
            self.update_listbox()
            self.save_scripts()
            self.status_var.set(f"已移除：{item['display']}")

    def save_scripts(self):
        try:
            with open(CONFIG_FILE, 'wb') as f:
                pickle.dump(self.scripts, f)
        except Exception as e:
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
                print(f"加载配置失败：{e}")

# ================== 启动 ==================
if __name__ == "__main__":
    try:
        root = TkinterDnD.Tk()
    except ImportError:
        print("缺少 tkinterdnd2，正在尝试从清华镜像自动安装...")
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-i', TUNA_MIRROR, 'tkinterdnd2'],
                check=True
            )
            print("安装成功，请重新运行程序。")
        except Exception:
            print("自动安装失败，请手动执行：pip install tkinterdnd2")
        sys.exit(1)
    app = ScriptManager(root)
    root.mainloop()