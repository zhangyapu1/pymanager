import sys
import ast
import importlib
import subprocess
from tkinter import messagebox

TUNA_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"
SELF_DEPENDENCIES = ['tkinterdnd2']

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

def check_self_dependencies(parent_root=None):
    """检查主程序自身依赖，如果缺失则询问安装，安装后退出重启"""
    missing = []
    for pkg in SELF_DEPENDENCIES:
        if not DependencyChecker.is_package_installed(pkg):
            missing.append(pkg)
    if missing:
        msg = f"缺少必要依赖：{', '.join(missing)}，是否立即安装？（将使用清华大学镜像源加速）"
        if messagebox.askyesno("缺少依赖", msg):
            for pkg in missing:
                if DependencyChecker.install_package(pkg, parent_root):
                    messagebox.showinfo("安装成功", f"{pkg} 安装成功，请重启程序。")
                else:
                    messagebox.showerror("安装失败", f"{pkg} 安装失败，请手动安装。")
            sys.exit(0)
        else:
            messagebox.showwarning("警告", "缺少依赖，程序可能无法正常工作。")

def check_script_deps_and_install(script_path, display_name, parent_root=None):
    """检查单个脚本的依赖并安装"""
    missing = DependencyChecker.get_missing_dependencies(script_path)
    if not missing:
        return True
    msg = f"脚本「{display_name}」缺少以下依赖：\n{', '.join(missing)}\n是否立即安装？（将使用清华大学镜像源加速）"
    if messagebox.askyesno("缺少依赖", msg):
        for pkg in missing:
            if DependencyChecker.install_package(pkg, parent_root):
                pass
            else:
                messagebox.showerror("安装失败", f"{pkg} 安装失败，请手动处理。")
        still_missing = [p for p in missing if not DependencyChecker.is_package_installed(p)]
        if still_missing:
            messagebox.showwarning("部分依赖未安装", f"下列依赖未成功安装：{', '.join(still_missing)}")
            return False
        else:
            messagebox.showinfo("完成", "所有缺失依赖已安装")
            return True
    else:
        return False