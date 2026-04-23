import sys
import subprocess
import urllib.request
import json
import webbrowser
from tkinter import messagebox

# ================== 配置区域 ==================
# 当前程序的版本号，请按实际版本手动更新
CURRENT_VERSION = "0.9.5"

# 使用 GitHub API 获取仓库的最新 Release 信息
UPDATE_CHECK_URL = "https://api.github.com/repos/zhangyapu1/pymanager/releases/latest"

# 下载页面 URL，当没有直接下载链接时，会打开该页面
UPDATE_DOWNLOAD_URL = "https://github.com/zhangyapu1/pymanager/releases/latest"
# ===========================================

def get_latest_version():
    """
    从 GitHub API 获取最新版本号，返回 (version, download_url) 或 (None, None)
    """
    try:
        req = urllib.request.Request(UPDATE_CHECK_URL, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

            # 优先使用 'name' 字段作为版本号，其次使用 'tag_name'
            latest = data.get("name", "")
            if not latest:
                latest = data.get("tag_name", "")
            # 去除可能存在的 'v' 前缀
            if latest.startswith("v"):
                latest = latest[1:]

            download = data.get("assets", [{}])[0].get("browser_download_url", "")
            return latest, download
    except Exception as e:
        print(f"检查更新失败：{e}")
        return None, None

def check_for_updates(parent_root=None, show_no_update_msg=True):
    """
    检查更新，返回是否需要更新。
    若 show_no_update_msg=True，则无更新时弹出提示。
    """
    latest, download_url = get_latest_version()
    if latest is None:
        if show_no_update_msg:
            messagebox.showerror("检查更新失败", "无法连接到更新服务器，请检查网络或稍后重试。", parent=parent_root)
        return False

    if latest > CURRENT_VERSION:
        msg = f"发现新版本 v{latest}（当前版本 v{CURRENT_VERSION}）\n\n是否前往下载页面？"
        if messagebox.askyesno("软件更新", msg, parent=parent_root):
            if download_url:
                webbrowser.open(download_url)
            else:
                webbrowser.open(UPDATE_DOWNLOAD_URL)
        return True
    else:
        if show_no_update_msg:
            messagebox.showinfo("检查更新", f"当前已是最新版本 v{CURRENT_VERSION}", parent=parent_root)
        return False