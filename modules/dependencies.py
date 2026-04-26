"""依赖管理 - 解析脚本 import 语句并自动安装缺失的第三方包。"""
import sys
import os
import ast
import importlib
import importlib.util
import subprocess
import re
import time
import threading

from modules.logger import log_info, log_warning, log_error

MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple",
    "https://pypi.mirrors.ustc.edu.cn/simple"
]
SELF_DEPENDENCIES = ['tkinterdnd2', 'ttkbootstrap']

PACKAGE_NAME_PATTERN = re.compile(r'^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$')

PY2_REMOVED_MODULES = frozenset({
    'exceptions', 'Queue', 'SocketServer', 'ConfigParser',
    'Cookie', 'Cookielib', 'copy_reg', 'cPickle', 'cStringIO',
    'HTMLParser', 'httplib', 'BaseHTTPServer', 'SimpleHTTPServer',
    'CGIHTTPServer', 'urlparse', 'robotparser', 'xmlrpclib',
    'DocXMLRPCServer', 'SimpleXMLRPCServer', 'Tkinter',
    'Dialog', 'FileDialog', 'ScrolledText', 'Tix', 'ttk',
    'tkColorChooser', 'tkCommonDialog', 'tkFileDialog',
    'tkFont', 'tkMessageBox', 'tkSimpleDialog',
    '__builtin__', '_winreg', 'winreg', 'thread',
    'dummy_thread', 'UserDict', 'UserList', 'UserString',
    'commands', 'dircache', 'fpformat', 'hotshot',
    'ihooks', 'imputil', 'md5', 'mhlib', 'mimetools',
    'MimeWriter', 'mimify', 'multifile', 'new', 'popen2',
    'posixfile', 'pre', 'profile', 'pstats', 'rexec',
    'rfc822', 'sets', 'sgmllib', 'sha', 'sre',
    'statvfs', 'sunaudiodev', 'tempita', 'toaiff',
})

PACKAGE_CONFLICTS = {
    'docx': {
        'correct_package': 'python-docx',
        'conflict_package': 'docx',
        'check_attr': 'ImagePart',
        'description': '旧版 docx 包不兼容 Python 3，需要替换为 python-docx',
    },
}

PY2_SHIM_CONTENT = {
    'exceptions': '''import builtins
PendingDeprecationWarning = builtins.PendingDeprecationWarning
DeprecationWarning = builtins.DeprecationWarning
Warning = builtins.Warning
''',
    'Queue': '''from queue import Queue, PriorityQueue, LifoQueue
''',
    'SocketServer': '''from socketserver import *
''',
    'ConfigParser': '''from configparser import *
''',
    'Cookie': '''from http.cookies import *
''',
    'Cookielib': '''from http import cookiejar as *
''',
    'copy_reg': '''import copyreg
''',
    'htmlentitydefs': '''from html.entities import *
''',
    'HTMLParser': '''from html.parser import *
''',
    'httplib': '''from http.client import *
''',
    'urlparse': '''from urllib.parse import *
''',
    'robotparser': '''from urllib import robotparser
''',
    'xmlrpclib': '''from xmlrpc.client import *
''',
    'UserDict': '''from collections import UserDict
''',
    'UserList': '''from collections import UserList
''',
    'UserString': '''from collections import UserString
''',
    '__builtin__': '''import builtins
''',
    '_winreg': '''import winreg
''',
    'thread': '''import _thread
''',
    'dummy_thread': '''import _dummy_thread
''',
    'sets': '''from builtins import set
''',
    'sgmllib': '''class SGMLParser:
    pass
''',
}


def _get_site_packages_dir():
    for path in sys.path:
        if path.endswith('site-packages') and os.path.isdir(path):
            return path
    try:
        import site
        paths = site.getsitepackages()
        for p in paths:
            if p.endswith('site-packages') and os.path.isdir(p):
                return p
    except (AttributeError, OSError):
        pass
    return None


def ensure_py2_shim(module_name, output_callback=None):
    if module_name not in PY2_SHIM_CONTENT:
        return False

    site_dir = _get_site_packages_dir()
    if not site_dir:
        if output_callback:
            output_callback(f"[错误] 无法找到 site-packages 目录，无法创建兼容垫片")
        return False

    shim_path = os.path.join(site_dir, module_name + '.py')
    if os.path.exists(shim_path):
        return True

    content = PY2_SHIM_CONTENT[module_name]
    try:
        with open(shim_path, 'w', encoding='utf-8') as f:
            f.write(f"# Auto-generated Python 2 compatibility shim for '{module_name}'\n")
            f.write(f"# Created by pymanager\n\n")
            f.write(content)
        if output_callback:
            output_callback(f"[兼容性修复] 已创建 Python 2 兼容垫片：{module_name}.py")
        log_info(f"已创建 Python 2 兼容垫片：{shim_path}")
        return True
    except OSError as e:
        if output_callback:
            output_callback(f"[错误] 创建兼容垫片失败：{e}")
        log_error(f"创建兼容垫片失败：{e}")
        return False


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
    def get_missing_dependencies(cls, script_path):
        required_modules = cls.extract_imports_from_script(script_path)
        missing = []
        for mod in required_modules:
            if not mod:
                continue
            if cls.is_stdlib_module(mod):
                continue
            if cls.is_package_installed(mod):
                continue
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
            DependencyChecker.install_package(pkg, parent_root, output_callback=output_callback, ui_callback=ui_callback)

        still_missing = [p for p in missing if not DependencyChecker.is_package_installed(p)]

        if still_missing:
            warn_msg = f"下列依赖未成功安装：{', '.join(still_missing)}"
            if output_callback:
                output_callback(f"[警告] {warn_msg}")
            if ui_callback:
                ui_callback.show_warning("部分依赖未安装", warn_msg, parent=parent_root)
            return False
        else:
            info_msg = "所有缺失依赖已安装"
            if output_callback:
                output_callback(info_msg)
            if ui_callback:
                ui_callback.show_info("完成", info_msg, parent=parent_root)
            return True
    else:
        return False
