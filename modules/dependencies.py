"""
依赖管理 - 解析脚本 import 语句并自动安装缺失的第三方包。

核心类：
    DependencyChecker：
        静态工具类，提供依赖检查和安装的完整功能链

        静态方法：
            extract_imports_from_script(path)：
                使用 AST 解析脚本，提取所有 import 和 from...import 语句
                返回模块名集合（如 {'os', 'requests', 'numpy'}）

            is_stdlib_module(module_name)：
                判断模块是否为 Python 标准库
                内置 PY2_REMOVED_MODULES 集合排除 Python 2 已移除模块

            is_package_installed(package_name)：
                使用 importlib.util.find_spec 检查包是否已安装

            get_missing_dependencies(script_path)：
                提取脚本 import 并返回未安装的第三方依赖列表

            verify_imports(script_path)：
                验证脚本所有 import 是否可解析，返回无法导入的模块列表
                用于检测传递依赖缺失

            install_package(package_name, ...)：
                使用 pip 安装包，自动尝试国内镜像源
                支持进度回调和 UI 交互

            fix_package_conflict(module_name, ...)：
                检测并修复包名冲突（如 docx vs python-docx）
                自动卸载冲突包并安装正确版本

常量：
    MIRRORS - 国内 pip 镜像源列表（清华、阿里、中科大）
    SELF_DEPENDENCIES - 框架自身依赖 ['tkinterdnd2', 'ttkbootstrap']
    PACKAGE_CONFLICTS - 包名冲突映射表

函数：
    check_self_dependencies_async(...)：
        异步检查框架自身依赖（tkinterdnd2, ttkbootstrap）
        缺失时自动安装，安装后回调通知需要重启

    check_script_deps_and_install(...)：
        检查单个脚本的依赖并安装缺失项
        支持包冲突修复和 Python 2 兼容垫片

依赖：modules.logger, modules.py2_compat
"""
import sys
import os
import ast
import importlib
import importlib.util
import subprocess
import re
import threading

from modules.logger import log_info, log_warning, log_error
from modules.py2_compat import PY2_REMOVED_MODULES, PY2_SHIM_CONTENT, ensure_py2_shim

MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple",
    "https://pypi.mirrors.ustc.edu.cn/simple"
]
SELF_DEPENDENCIES = ['tkinterdnd2', 'ttkbootstrap']

PACKAGE_NAME_PATTERN = re.compile(r'^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$')

PACKAGE_CONFLICTS = {
    'docx': {
        'correct_package': 'python-docx',
        'conflict_package': 'docx',
        'check_attr': 'ImagePart',
        'description': '旧版 docx 包不兼容 Python 3，需要替换为 python-docx',
    },
}


class DependencyChecker:
    @staticmethod
    def fix_package_conflict(module_name, output_callback=None):
        if module_name not in PACKAGE_CONFLICTS:
            return False

        conflict = PACKAGE_CONFLICTS[module_name]
        check_attr = conflict['check_attr']
        correct_pkg = conflict['correct_package']
        conflict_pkg = conflict['conflict_package']

        try:
            mod = importlib.import_module(module_name)
            if hasattr(mod, check_attr):
                return False
        except Exception:
            pass

        if output_callback:
            output_callback(f"[包冲突] {conflict['description']}")
            output_callback(f"[包冲突] 正在卸载旧版 {conflict_pkg} 并安装 {correct_pkg}...")

        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', '-y', conflict_pkg],
                capture_output=True, text=True
            )
        except Exception as e:
            if output_callback:
                output_callback(f"[错误] 卸载 {conflict_pkg} 失败：{e}")
            return False

        success = DependencyChecker.install_package(correct_pkg, output_callback=output_callback)
        if success:
            for key in list(sys.modules.keys()):
                if key.startswith(module_name):
                    del sys.modules[key]
            if output_callback:
                output_callback(f"[包冲突] 已替换为 {correct_pkg}")
        else:
            if output_callback:
                output_callback(f"[错误] 安装 {correct_pkg} 失败")
        return success

    @staticmethod
    def is_package_installed(package_name):
        try:
            spec = importlib.util.find_spec(package_name)
            return spec is not None
        except (ModuleNotFoundError, ValueError, ImportError):
            return False

    @staticmethod
    def install_package(package_name, parent_window=None, use_mirror=True, output_callback=None, ui_callback=None):
        if not package_name or not PACKAGE_NAME_PATTERN.match(package_name):
            error_msg = f"无效的包名: {package_name}"
            if output_callback:
                output_callback(f"[错误] {error_msg}")
            if ui_callback:
                ui_callback.show_error("安装失败", error_msg, parent=parent_window)
            else:
                log_error(error_msg)
            return False

        base_cmd = [sys.executable, '-m', 'pip', 'install', package_name, '--progress-bar', 'on']

        sources_to_try = []
        if use_mirror:
            sources_to_try = MIRRORS.copy()
        sources_to_try.append(None)

        def output(message):
            log_info(message)
            if output_callback:
                output_callback(message)

        output(f"开始安装依赖: {package_name}")

        for i, mirror in enumerate(sources_to_try):
            if mirror:
                source_name = mirror.split('/')[2]
                output(f"尝试源 {i+1}/{len(sources_to_try)}: {source_name}")
            else:
                output("尝试官方源...")

            cmd = base_cmd.copy()
            if mirror:
                cmd.extend(['-i', mirror])

            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line:
                        output(line)

                process.stdout.close()
                process.wait()

                if process.returncode == 0:
                    success_msg = f"成功安装包: {package_name} (源: {mirror or '官方源'})"
                    output(success_msg)
                    return True
                else:
                    raise subprocess.CalledProcessError(process.returncode, cmd)

            except subprocess.TimeoutExpired:
                error_msg = f"安装 {package_name} 超时 (源: {mirror or '官方源'})"
                output(f"{error_msg}，尝试下一个源...")
                log_warning(error_msg)
                continue
            except subprocess.CalledProcessError:
                error_msg = f"安装 {package_name} 失败 (源: {mirror or '官方源'})"
                output(f"{error_msg}，尝试下一个源...")
                log_warning(error_msg)
                continue
            except (FileNotFoundError, OSError) as e:
                error_msg = f"安装 {package_name} 异常 (源: {mirror or '官方源'}): {e}"
                output(f"{error_msg}，尝试下一个源...")
                log_warning(error_msg)
                continue

        error_msg = f"所有源都无法安装 {package_name}"
        output(error_msg)
        if ui_callback:
            ui_callback.show_error("安装失败", error_msg, parent=parent_window)
        else:
            log_error(error_msg)
        return False

    @staticmethod
    def extract_imports_from_script(script_path):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=script_path)
        except SyntaxError:
            log_warning(f"脚本 {script_path} 有语法错误，无法解析导入")
            return set()
        except FileNotFoundError:
            log_error(f"脚本文件不存在: {script_path}")
            return set()
        except (OSError, UnicodeDecodeError) as e:
            log_error(f"解析脚本 {script_path} 时出错: {e}")
            return set()

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_module = alias.name.split('.')[0]
                    imports.add(top_module)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    top_module = node.module.split('.')[0]
                    imports.add(top_module)

        return imports

    @staticmethod
    def is_stdlib_module(module_name):
        if module_name in PY2_REMOVED_MODULES:
            return True
        if hasattr(sys, 'stdlib_module_names'):
            return module_name in sys.stdlib_module_names

        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                return False

            if spec.origin is None:
                return module_name in sys.builtin_module_names

            origin_lower = spec.origin.lower()
            return 'site-packages' not in origin_lower and 'dist-packages' not in origin_lower

        except (ModuleNotFoundError, ValueError, ImportError, OSError) as e:
            log_error(f"判断模块 {module_name} 是否为标准库时出错: {e}")
            return False

    @classmethod
    def detect_conflict(cls, module_name):
        """检测模块是否是冲突包（存在但版本不正确）"""
        if module_name not in PACKAGE_CONFLICTS:
            return None
        conflict = PACKAGE_CONFLICTS[module_name]
        check_attr = conflict['check_attr']
        try:
            mod = importlib.import_module(module_name)
            if hasattr(mod, check_attr):
                return None
            return conflict
        except Exception:
            return None

    @classmethod
    def get_missing_dependencies(cls, script_path):
        required_modules = cls.extract_imports_from_script(script_path)
        missing = []
        for mod in required_modules:
            if not mod:
                continue
            if cls.is_stdlib_module(mod):
                continue
            
            # 检查该模块是否是冲突包的冲突名称
            conflict_for_mod = None
            for conflict_name, conflict_info in PACKAGE_CONFLICTS.items():
                if conflict_info['conflict_package'] == mod:
                    conflict_for_mod = conflict_info
                    break
            
            if cls.is_package_installed(mod):
                conflict = cls.detect_conflict(mod)
                if conflict:
                    correct_pkg = conflict['correct_package']
                    if not cls.is_package_installed(correct_pkg):
                        missing.append(correct_pkg)
                continue
            
            # 如果模块未安装，但它是冲突包的冲突名称，则添加正确的包名
            if conflict_for_mod:
                correct_pkg = conflict_for_mod['correct_package']
                if not cls.is_package_installed(correct_pkg):
                    missing.append(correct_pkg)
            else:
                missing.append(mod)

        return missing

    @classmethod
    def verify_imports(cls, script_path, output_callback=None):
        required_modules = cls.extract_imports_from_script(script_path)
        transitive_missing = []
        shimmed = []
        fixed_conflicts = []
        for mod in required_modules:
            if not mod or cls.is_stdlib_module(mod):
                continue
            try:
                importlib.import_module(mod)
            except ModuleNotFoundError as e:
                missing_mod = e.name
                if missing_mod and missing_mod in PY2_SHIM_CONTENT and missing_mod not in shimmed:
                    if ensure_py2_shim(missing_mod, output_callback):
                        shimmed.append(missing_mod)
                        for key in list(sys.modules.keys()):
                            if key.startswith(mod) or key == missing_mod:
                                del sys.modules[key]
                        try:
                            importlib.import_module(mod)
                            if output_callback:
                                output_callback(f"[兼容性修复] {mod} 导入成功（已修复 Python 2 兼容性）")
                            continue
                        except Exception:
                            pass

                if missing_mod and not cls.is_stdlib_module(missing_mod):
                    if missing_mod not in transitive_missing:
                        transitive_missing.append(missing_mod)
                        if output_callback:
                            output_callback(f"[传递依赖缺失] {mod} -> {missing_mod}")
                else:
                    if output_callback:
                        output_callback(f"[警告] {mod} 导入失败：依赖了 Python 2 模块 '{missing_mod}'，该包可能不兼容 Python 3，但仍可尝试运行")
            except ImportError as e:
                conflict_fixed = False
                for conflict_mod in PACKAGE_CONFLICTS:
                    if conflict_mod not in fixed_conflicts:
                        try:
                            conflict_mod_obj = importlib.import_module(conflict_mod)
                            check_attr = PACKAGE_CONFLICTS[conflict_mod]['check_attr']
                            if not hasattr(conflict_mod_obj, check_attr):
                                if cls.fix_package_conflict(conflict_mod, output_callback):
                                    fixed_conflicts.append(conflict_mod)
                                    for key in list(sys.modules.keys()):
                                        if key.startswith(conflict_mod):
                                            del sys.modules[key]
                                    for key in list(sys.modules.keys()):
                                        if key.startswith(mod):
                                            del sys.modules[key]
                                    try:
                                        importlib.import_module(mod)
                                        if output_callback:
                                            output_callback(f"[包冲突修复] {mod} 导入成功（已替换 {conflict_mod} 为正确版本）")
                                        conflict_fixed = True
                                        break
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                if not conflict_fixed and output_callback:
                    output_callback(f"[警告] 导入 {mod} 时出错：{type(e).__name__}: {e}")
            except Exception as e:
                if output_callback:
                    output_callback(f"[警告] 导入 {mod} 时出错（非模块缺失，可能是包内部兼容性问题）：{type(e).__name__}: {e}")

        return transitive_missing


def check_self_dependencies_async(output_callback=None, ui_callback=None, on_complete=None):
    missing = []
    for pkg in SELF_DEPENDENCIES:
        if not DependencyChecker.is_package_installed(pkg):
            missing.append(pkg)

    if not missing:
        if output_callback:
            output_callback("框架依赖检查通过，所有依赖已就绪。")
        if on_complete:
            on_complete(needs_restart=False)
        return

    if output_callback:
        output_callback(f"缺少框架依赖：{', '.join(missing)}")
        output_callback("正在自动安装...")

    all_success = True
    for pkg in missing:
        success = DependencyChecker.install_package(pkg, output_callback=output_callback, ui_callback=ui_callback)
        if success:
            if output_callback:
                output_callback(f"{pkg} 安装成功。")
        else:
            if output_callback:
                output_callback(f"[错误] {pkg} 安装失败，请手动执行：pip install {pkg}")
            all_success = False

    if all_success:
        if output_callback:
            output_callback("所有框架依赖安装完成，需要重启程序才能生效。")
        if on_complete:
            on_complete(needs_restart=True)
    else:
        if output_callback:
            output_callback("[警告] 部分依赖安装失败，程序可能无法正常工作。")
        if on_complete:
            on_complete(needs_restart=False)


def check_script_deps_and_install(script_path, display_name, parent_root=None, output_callback=None, ui_callback=None):
    missing = DependencyChecker.get_missing_dependencies(script_path)
    if not missing:
        return True

    msg = f"脚本「{display_name}」缺少以下依赖：\n{', '.join(missing)}\n是否立即安装？（将使用加速镜像源）"
    if output_callback:
        output_callback(msg.replace('\n', ' '))

    if ui_callback:
        confirmed = ui_callback.ask_yes_no("缺少依赖", msg, parent=parent_root)
    else:
        confirmed = False

    if confirmed:
        for pkg in missing:
            conflict_to_fix = None
            for conflict_name, conflict_info in PACKAGE_CONFLICTS.items():
                if conflict_info['correct_package'] == pkg:
                    conflict_to_fix = conflict_name
                    break

            if conflict_to_fix:
                DependencyChecker.fix_package_conflict(conflict_to_fix, output_callback=output_callback)
            else:
                DependencyChecker.install_package(pkg, parent_root, output_callback=output_callback, ui_callback=ui_callback)

        still_missing = [p for p in missing if not DependencyChecker.is_package_installed(p)]
