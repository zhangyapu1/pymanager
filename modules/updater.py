import os
import sys
import urllib.request
import json
import webbrowser
import shutil
import tempfile
import subprocess
import zipfile
from tkinter import messagebox, simpledialog, ttk
import tkinter as tk

# ================== 配置区域 ==================
CURRENT_VERSION = "1.0.2"
PROJECT_URL = "https://gitee.com/yaopei6678/pymanager"

# 仓库类型: 'gitee' 或 'github'
REPO_TYPE = "gitee"
REPO_OWNER = "yaopei6678"
REPO_NAME = "pymanager"

if REPO_TYPE == "gitee":
    RELEASE_API_URL = f"https://gitee.com/api/v5/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
else:
    RELEASE_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

# 下载超时（秒）
DOWNLOAD_TIMEOUT = 60
# ===========================================

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
TOKEN_FILE = os.path.join(CONFIG_DIR, "api_token.txt")

def get_api_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            token = f.read().strip()
            if token:
                return token
    return os.environ.get("GITEE_TOKEN" if REPO_TYPE == "gitee" else "GITHUB_TOKEN", "")

def save_api_token(token):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(token.strip())

def prompt_for_token(parent):
    token = simpledialog.askstring(
        "API Token",
        f"请输入{REPO_TYPE.capitalize()} Personal Access Token 以提高 API 限额。\n\n"
        "如何获取？\n"
        f"1. 访问 https://{REPO_TYPE}.com/settings/tokens\n"
        "2. 生成新令牌，勾选 'repo' 或 'projects' 权限\n"
        "3. 复制并粘贴到此处。\n\n"
        "若跳过，匿名请求每小时限制 60 次。",
        parent=parent
    )
    if token:
        save_api_token(token)
        return token
    return ""

def is_version_greater(v1, v2):
    try:
        a1 = [int(x) for x in v1.split('.')]
        a2 = [int(x) for x in v2.split('.')]
        max_len = max(len(a1), len(a2))
        a1 += [0] * (max_len - len(a1))
        a2 += [0] * (max_len - len(a2))
        return a1 > a2
    except:
        return v1 > v2

def fetch_latest_version(parent=None):
    token = get_api_token()
    if not token and parent:
        token = prompt_for_token(parent)

    headers = {"User-Agent": f"ScriptManager/{CURRENT_VERSION}"}
    if token:
        if REPO_TYPE == "gitee":
            headers["Authorization"] = f"token {token}"
        else:
            headers["Authorization"] = f"Bearer {token}"
        auth_status = "已认证"
    else:
        auth_status = "未认证"

    try:
        req = urllib.request.Request(RELEASE_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            latest = data.get("name") or data.get("tag_name", "")
            if latest.startswith("v"):
                latest = latest[1:]
            assets = data.get("assets", [])
            # 优先选择 .exe 或 .zip 文件，否则取第一个
            download_url = ""
            for asset in assets:
                name = asset.get("name", "")
                url = asset.get("browser_download_url", "")
                if name.endswith(".exe") or name.endswith(".zip"):
                    download_url = url
                    break
            if not download_url and assets:
                download_url = assets[0].get("browser_download_url", "")
            print(f"[{auth_status}] 最新版本: {latest}, 下载链接: {download_url}")
            return latest, download_url
    except Exception as e:
        print(f"获取版本失败: {e}")
        return None, None

def download_progress_hook(block_num, block_size, total_size, progress_bar, status_label):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, int(downloaded * 100 / total_size))
        progress_bar['value'] = percent
        status_label.config(text=f"下载中... {percent}%")
        progress_bar.update_idletasks()

def download_file(url, dest_path, parent):
    progress_win = tk.Toplevel(parent)
    progress_win.title("正在下载更新")
    progress_win.geometry("400x150")
    progress_win.transient(parent)
    progress_win.grab_set()
    tk.Label(progress_win, text="正在下载新版本，请稍候...").pack(pady=10)
    progress_bar = ttk.Progressbar(progress_win, length=300, mode='determinate')
    progress_bar.pack(pady=5)
    status_label = tk.Label(progress_win, text="开始下载...")
    status_label.pack(pady=5)

    def hook(block, bs, size):
        # 由于 urlretrieve 不支持直接更新进度条，需要自定义
        pass

    try:
        # 使用urlretrieve 但无法实时进度，改用 urllib.request 分块下载
        req = urllib.request.Request(url, headers={"User-Agent": "ScriptManager"})
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            with open(dest_path, 'wb') as out_file:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = int(downloaded * 100 / total_size)
                        progress_bar['value'] = percent
                        status_label.config(text=f"下载中... {percent}%")
                    progress_win.update_idletasks()
        progress_win.destroy()
        return True
    except Exception as e:
        progress_win.destroy()
        messagebox.showerror("下载失败", f"下载更新文件时出错：{e}", parent=parent)
        return False

def apply_update(download_path, parent):
    """解压或复制文件，并启动更新脚本"""
    current_exe = sys.argv[0] if getattr(sys, 'frozen', False) else sys.argv[0]
    current_dir = os.path.dirname(current_exe)

    # 判断下载的是压缩包还是单文件
    if download_path.endswith('.zip'):
        # 解压到临时目录
        extract_dir = tempfile.mkdtemp()
        try:
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            # 假设解压后主程序名为 ScriptManager.exe 或 ScriptManager.pyw
            # 需要查找并确定新文件
            new_exe = None
            for root, dirs, files in os.walk(extract_dir):
                for f in files:
                    if f.endswith('.exe') or f.endswith('.pyw') or f == 'main.py':
                        new_exe = os.path.join(root, f)
                        break
                if new_exe:
                    break
            if not new_exe:
                raise Exception("压缩包中未找到可执行文件")
        except Exception as e:
            messagebox.showerror("解压失败", f"解压更新包失败：{e}", parent=parent)
            return False
    else:
        # 直接下载的可执行文件
        new_exe = download_path
        extract_dir = None

    # 备份旧文件
    backup_path = current_exe + ".backup"
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        shutil.copy2(current_exe, backup_path)
    except Exception as e:
        messagebox.showwarning("备份警告", f"备份旧版本失败：{e}，更新可能无法继续")

    # 创建更新脚本（批处理或Python脚本）
    script_path = os.path.join(tempfile.gettempdir(), "update_script.bat")
    with open(script_path, "w", encoding='utf-8') as f:
        f.write(f"""
@echo off
timeout /t 2 /nobreak >nul
taskkill /f /im "{os.path.basename(current_exe)}" 2>nul
del /f /q "{current_exe}" 2>nul
copy /y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
""")

    # 执行更新脚本并退出
    subprocess.Popen([script_path], shell=True)
    # 关闭当前程序
    parent.quit()
    sys.exit(0)

def auto_update(parent, download_url):
    """自动下载并更新"""
    # 询问使用自动更新还是手动下载
    if not messagebox.askyesno("自动更新", "发现新版本，是否自动下载并安装？\n（自动更新将替换当前程序）", parent=parent):
        webbrowser.open(download_url)
        return

    # 下载到临时文件
    temp_dir = tempfile.gettempdir()
    file_name = download_url.split('/')[-1] or "update.zip"
    dest_path = os.path.join(temp_dir, file_name)

    if not download_file(download_url, dest_path, parent):
        return

    # 应用更新
    apply_update(dest_path, parent)

# 以下是原有的 check_for_updates 函数，修改为调用 auto_update
def check_for_updates(parent_root=None, show_no_update_msg=True):
    latest, download_url = fetch_latest_version(parent_root)
    if latest is None:
        if show_no_update_msg:
            messagebox.showerror("检查更新失败", "无法获取最新版本信息，请检查网络。", parent=parent_root)
        return False
    if is_version_greater(latest, CURRENT_VERSION):
        msg = f"发现新版本 v{latest}（当前版本 v{CURRENT_VERSION}）\n\n是否自动更新？"
        if messagebox.askyesno("软件更新", msg, parent=parent_root):
            auto_update(parent_root, download_url)
        else:
            webbrowser.open(download_url)
        return True
    else:
        if show_no_update_msg:
            messagebox.showinfo("检查更新", f"当前已是最新版本 v{CURRENT_VERSION}", parent=parent_root)
        return False