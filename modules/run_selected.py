import subprocess
import sys
from tkinter import messagebox

def run_selected(manager):
    item = manager.get_selected_item()
    if not item:
        return
    try:
        subprocess.Popen([sys.executable, item["storage_path"]], shell=True)
        manager.status_var.set(f"正在运行：{item['display']}")
    except Exception as e:
        messagebox.showerror("运行错误", str(e))