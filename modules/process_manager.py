"""进程管理 - 管理脚本运行子进程的生命周期。"""
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
