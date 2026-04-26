"""
Python 2 兼容垫片 - 为 Python 2 模块名创建兼容性垫片文件。

常量：
    PY2_REMOVED_MODULES - Python 2 已移除模块名集合
    PY2_SHIM_CONTENT    - 模块名 → 垫片代码映射

核心函数：
    ensure_py2_shim(module_name, output_callback)：
        在 site-packages 目录下为指定模块创建 .py 兼容垫片
        - 自动检测 site-packages 路径
        - 已存在则跳过
        - 返回 True/False 表示成功/失败

    get_site_packages_dir()：
        获取 site-packages 目录路径

依赖：modules.logger
"""
import sys
import os

from modules.logger import log_info, log_error

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


def get_site_packages_dir():
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

    site_dir = get_site_packages_dir()
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
