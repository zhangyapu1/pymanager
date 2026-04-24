import sys
import ast
import importlib
import importlib.util
import subprocess
import re
import os
import json
from tkinter import messagebox
from modules.logger import log_info, log_warning, log_error

# 定义常量
TUNA_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"
SELF_DEPENDENCIES = ['tkinterdnd2']

# 依赖缓存文件路径
CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'dependency_cache.json')

# 预编译正则表达式用于验证包名
# Python 包名通常允许字母、数字、下划线、连字符和点，且不能以连字符或点开头/结尾（简化版校验）
PACKAGE_NAME_PATTERN = re.compile(r'^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$')

# 依赖缓存
_dependency_cache = {}

# 加载依赖缓存
def _load_cache():
    """
    加载依赖缓存
    """
    global _dependency_cache
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                _dependency_cache = json.load(f)
    except Exception as e:
        log_error(f"加载依赖缓存失败: {str(e)}")

# 保存依赖缓存
def _save_cache():
    """
    保存依赖缓存
    """
    try:
        # 确保缓存文件目录存在
        cache_dir = os.path.dirname(CACHE_FILE)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_dependency_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(f"保存依赖缓存失败: {str(e)}")

# 初始化加载缓存
_load_cache()

class DependencyChecker:
    @staticmethod
    def is_package_installed(package_name):
        """
        检查包是否已安装。
        使用 find_spec 而不是 import_module 以避免执行模块代码带来的副作用和性能开销。
        
        :param package_name: 包名
        :return: 是否已安装
        """
        # 检查缓存
        if package_name in _dependency_cache:
            return _dependency_cache[package_name]
        
        try:
            spec = importlib.util.find_spec(package_name)
            installed = spec is not None
            # 更新缓存
            _dependency_cache[package_name] = installed
            _save_cache()
            return installed
        except Exception:
            # find_spec 在某些极端情况下（如元路径查找器出错）可能抛出异常
            return False

    @staticmethod
    def install_package(package_name, parent_window=None, use_mirror=True):
        """
        安装包
        
        :param package_name: 包名
        :param parent_window: 父窗口
        :param use_mirror: 是否使用镜像
        :return: 是否安装成功
        """
        # 1. 安全性校验：验证包名格式
        if not package_name or not PACKAGE_NAME_PATTERN.match(package_name):
            error_msg = f"无效的包名: {package_name}"
            if parent_window:
                messagebox.showerror("安装失败", error_msg)
            else:
                log_error(error_msg)
            return False

        cmd = [sys.executable, '-m', 'pip', 'install', package_name]
        if use_mirror:
            cmd.extend(['-i', TUNA_MIRROR])
        
        try:
            # 增加 timeout 参数防止无限等待，例如 300秒
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
            # 更新缓存
            _dependency_cache[package_name] = True
            _save_cache()
            log_info(f"成功安装包: {package_name}")
            return True
        except subprocess.TimeoutExpired:
            error_msg = f"安装 {package_name} 超时。"
            if parent_window:
                messagebox.showerror("安装失败", error_msg)
            else:
                log_error(error_msg)
            return False
        except subprocess.CalledProcessError as e:
            if use_mirror:
                # 递归尝试不使用镜像
                return DependencyChecker.install_package(package_name, parent_window, use_mirror=False)
            else:
                # 获取标准错误输出，如果为空则使用标准输出
                stderr = e.stderr.strip() if e.stderr else "未知错误"
                error_msg = f"安装 {package_name} 失败：\n{stderr}"
                if parent_window:
                    messagebox.showerror("安装失败", error_msg)
                else:
                    log_error(error_msg)
                return False

    @staticmethod
    def extract_imports_from_script(script_path):
        """
        从脚本中提取顶层导入模块名。
        注意：如果脚本有语法错误，将返回空集合。
        
        :param script_path: 脚本路径
        :return: 导入的模块集合
        """
        # 检查缓存
        cache_key = f"imports:{script_path}"
        if cache_key in _dependency_cache:
            return set(_dependency_cache[cache_key])
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=script_path)
        except SyntaxError:
            # 语法错误无法解析，返回空集，调用者应知晓此限制
            log_warning(f"脚本 {script_path} 有语法错误，无法解析导入")
            return set()
        except FileNotFoundError:
            log_error(f"脚本文件不存在: {script_path}")
            return set()
        except Exception as e:
            # 其他读取或解析错误
            log_error(f"解析脚本 {script_path} 时出错: {str(e)}")
            return set()
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # 获取顶层模块名，例如 from os.path import join -> os
                    top_module = alias.name.split('.')[0]
                    imports.add(top_module)
            elif isinstance(node, ast.ImportFrom):
                # 忽略相对导入 (level > 0) 和 module 为 None 的情况
                if node.module and node.level == 0:
                    top_module = node.module.split('.')[0]
                    imports.add(top_module)
        
        # 更新缓存
        _dependency_cache[cache_key] = list(imports)
        _save_cache()
        return imports

    @staticmethod
    def is_stdlib_module(module_name):
        """
        判断模块是否为标准库模块。
        
        :param module_name: 模块名
        :return: 是否为标准库模块
        """
        # 检查缓存
        cache_key = f"stdlib:{module_name}"
        if cache_key in _dependency_cache:
            return _dependency_cache[cache_key]
        
        # Python 3.10+ 提供了标准库名称集合
        if hasattr(sys, 'stdlib_module_names'):
            is_stdlib = module_name in sys.stdlib_module_names
            # 更新缓存
            _dependency_cache[cache_key] = is_stdlib
            _save_cache()
            return is_stdlib
        
        # 兼容旧版本 Python
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                # 更新缓存
                _dependency_cache[cache_key] = False
                _save_cache()
                return False
            
            # 内置模块 (如 sys, builtins) 的 origin 通常为 None
            if spec.origin is None:
                # 进一步确认是否是内置模块，通常 find_spec 能找到且 origin 为 None 的是内置的
                # 或者它是命名空间包的一部分，但命名空间包通常不在 stdlib 中除非是特定的
                # 简单的启发式：如果在 sys.builtin_module_names 中，则是标准库
                is_stdlib = module_name in sys.builtin_module_names
                # 更新缓存
                _dependency_cache[cache_key] = is_stdlib
                _save_cache()
                return is_stdlib
            
            # 检查路径是否包含 site-packages 或 dist-packages
            # 标准库通常位于 lib/pythonX.X/ 下，而不含 site-packages
            origin_lower = spec.origin.lower()
            is_stdlib = 'site-packages' not in origin_lower and 'dist-packages' not in origin_lower
            # 更新缓存
            _dependency_cache[cache_key] = is_stdlib
            _save_cache()
            return is_stdlib

        except Exception as e:
            log_error(f"判断模块 {module_name} 是否为标准库时出错: {str(e)}")
            return False

    @classmethod
    def get_missing_dependencies(cls, script_path):
        """
        获取脚本缺失的依赖
        
        :param script_path: 脚本路径
        :return: 缺失的依赖列表
        """
        # 检查缓存
        cache_key = f"missing:{script_path}"
        if cache_key in _dependency_cache:
            return _dependency_cache[cache_key]
        
        required_modules = cls.extract_imports_from_script(script_path)
        missing = []
        for mod in required_modules:
            # 跳过空字符串（理论上不会发生，因为 split('.')[0] 至少有一个字符）
            if not mod:
                continue
                
            if cls.is_stdlib_module(mod):
                continue
            
            if cls.is_package_installed(mod):
                continue
            
            missing.append(mod)
        
        # 更新缓存
        _dependency_cache[cache_key] = missing
        _save_cache()
        return missing

def check_self_dependencies(parent_root=None):
    """检查主程序自身依赖，如果缺失则询问安装，安装后退出"""
    missing = []
    for pkg in SELF_DEPENDENCIES:
        if not DependencyChecker.is_package_installed(pkg):
            missing.append(pkg)
    
    if missing:
        msg = f"缺少必要依赖：{', '.join(missing)}，是否立即安装？（将使用加速镜像源）"
        if messagebox.askyesno("缺少依赖", msg):
            all_success = True
            for pkg in missing:
                success = DependencyChecker.install_package(pkg, parent_root)
                if success:
                    messagebox.showinfo("安装成功", f"{pkg} 安装成功，请重启程序。")
                else:
                    messagebox.showerror("安装失败", f"{pkg} 安装失败，请手动安装。")
                    all_success = False
            
            # 无论成功与否，都退出，让用户重启以确保环境干净
            # 如果部分失败，用户重启后再次运行仍会提示，或者用户需手动处理
            sys.exit(0)
        else:
            messagebox.showwarning("警告", "缺少依赖，程序可能无法正常工作。")

def check_script_deps_and_install(script_path, display_name, parent_root=None):
    """检查单个脚本的依赖并安装"""
    missing = DependencyChecker.get_missing_dependencies(script_path)
    if not missing:
        return True
    
    msg = f"脚本「{display_name}」缺少以下依赖：\n{', '.join(missing)}\n是否立即安装？（将使用加速镜像源）"
    if messagebox.askyesno("缺少依赖", msg):
        for pkg in missing:
            DependencyChecker.install_package(pkg, parent_root)
        
        # 重新检查哪些还没装上
        still_missing = [p for p in missing if not DependencyChecker.is_package_installed(p)]
        
        if still_missing:
            messagebox.showwarning("部分依赖未安装", f"下列依赖未成功安装：{', '.join(still_missing)}")
            return False
        else:
            messagebox.showinfo("完成", "所有缺失依赖已安装")
            return True
    else:
        return False