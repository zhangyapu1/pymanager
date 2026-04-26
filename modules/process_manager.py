"""
进程管理 - 管理脚本运行子进程的生命周期，支持并发运行和统一终止。

类 ProcessManager：
    线程安全地管理多个子进程的注册、查询和终止。

    核心属性：
        _processes - 字典 {subprocess.Popen: str}，进程对象到名称的映射
        _lock      - threading.Lock，保证线程安全

    方法：
        add_process(process, name="")：
            注册一个运行中的子进程

        remove_process(process)：
            注销一个子进程（通常在进程结束后调用）

        running_count()：
            返回当前运行中的进程数量
            同时清理已结束的进程

        is_running()：
            判断是否有进程正在运行

        get_running_names()：
            返回所有运行中进程的名称列表
            同时清理已结束的进程

        terminate_all()：
            终止所有运行中的进程并清空注册表
            返回被终止的进程名称列表

        cleanup_dead()：
            清理已结束的进程，从注册表中移除

线程安全：
    所有公共方法使用 _lock 保护，支持从不同线程调用
    进程状态检查使用 poll() 方法，捕获 OSError/SubprocessError 异常

依赖：subprocess, threading
"""
import subprocess
import threading


class ProcessManager:
    def __init__(self):
        self._processes = {}
        self._lock = threading.Lock()

    def add_process(self, process, name=""):
        with self._lock:
            self._processes[process] = name

    def remove_process(self, process):
        with self._lock:
            self._processes.pop(process, None)

    def running_count(self):
        with self._lock:
            count = 0
            for p in list(self._processes):
                try:
                    if p.poll() is None:
                        count += 1
                    else:
                        self._processes.pop(p, None)
                except (OSError, subprocess.SubprocessError):
                    self._processes.pop(p, None)
            return count

    def is_running(self):
        return self.running_count() > 0

    def get_running_names(self):
        with self._lock:
            names = []
            dead = []
            for p, name in self._processes.items():
                try:
                    if p.poll() is None:
                        names.append(name)
                    else:
                        dead.append(p)
                except (OSError, subprocess.SubprocessError):
                    dead.append(p)
            for p in dead:
                self._processes.pop(p, None)
            return names

    def terminate_all(self):
        with self._lock:
            names = []
            for p, name in list(self._processes.items()):
                try:
                    if p.poll() is None:
                        p.terminate()
                        names.append(name)
                except (OSError, subprocess.SubprocessError):
                    pass
            self._processes.clear()
            return names

    def cleanup_dead(self):
        with self._lock:
            dead = []
            for p in list(self._processes):
                try:
                    if p.poll() is not None:
                        dead.append(p)
                except (OSError, subprocess.SubprocessError):
                    dead.append(p)
            for p in dead:
                self._processes.pop(p, None)
