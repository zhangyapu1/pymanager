import sys
import subprocess
import urllib.request
import json
import webbrowser
from tkinter import messagebox

# ================== 配置区域 ==================
CURRENT_VERSION = "0.9.5"
UPDATE_CHECK_URL = "https://api.github.com/repos/zhangyapu1/pymanager/releases/latest"
UPDATE_DOWNLOAD_URL = "https://github.com/zhangyapu1/pymanager/releases/latest"
# 可选：使用代理（如果公司网络需要 proxy，可在此设置）
PROXY = None   # 例如 "http://127.0.0.1:7890"
# ===========================================

def get_latest_version():
    try:
        req = urllib.request.Request(
            UPDATE_CHECK_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        if PROXY:
            handler = urllib.request.ProxyHandler({'https': PROXY, 'http': PROXY})
            opener = urllib.request.build_opener(handler)
            urllib.request.install_opener(opener)

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            latest = data.get("name") or data.get("tag_name", "")
            if latest.startswith("v"):
                latest = latest[1:]
            download = data.get("assets", [{}])[0].get("browser_download_url", "")
            return latest, download
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("仓库尚未创建 Release，请稍后设置版本")
        else:
            print(f"HTTP 错误：{e.code}")
        return None, None
    except Exception as e:
        print(f"网络请求失败：{e}")
        return None, None

def check_for_updates(parent_root=None, show_no_update_msg=True):
    latest, download_url = get_latest_version()
    if latest is None:
        if show_no_update_msg:
            messagebox.showerror(
                "检查更新失败",
                "无法连接到 GitHub API。\n请检查网络连接或稍后重试。\n你也可以手动访问：\n" + UPDATE_DOWNLOAD_URL,
                parent=parent_root
            )
        return False

    if latest > CURRENT_VERSION:
        msg = f"发现新版本 v{latest}（当前 v{CURRENT_VERSION}）\n\n是否前往下载页面？"
        if messagebox.askyesno("软件更新", msg, parent=parent_root):
            webbrowser.open(download_url if download_url else UPDATE_DOWNLOAD_URL)
        return True
    else:
        if show_no_update_msg:
            messagebox.showinfo("检查更新", f"当前已是最新版本 v{CURRENT_VERSION}", parent=parent_root)
        return False