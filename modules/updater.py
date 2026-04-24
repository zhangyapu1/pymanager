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
CURRENT_VERSION = "1.0.4"
PROJECT_URL = "https://github.com/zhangyapu1/pymanager"

REPO_OWNER = "zhangyapu1"
REPO_NAME = "pymanager"
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
    return os.environ.get("GITHUB_TOKEN", "")

def save_api_token(token):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(token.strip())

def prompt_for_token(parent):
    token = simpledialog.askstring(
        "API Token",
        "请输入GitHub Personal Access Token 以提高 API 限额。\n\n"
        "如何获取？\n"
        "1. 访问 https://github.com/settings/tokens\n"
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
        headers["Authorization"] = f"Bearer {token}"
        auth_status = "已认证"
    else:
        auth_status = "未认证"

    try:
        print(f"请求URL: {RELEASE_API_URL}")
        print(f"请求头: {headers}")
        req = urllib.request.Request(RELEASE_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"响应状态码: {resp.status}")
            data = json.loads(resp.read().decode())
            print(f"API响应: {data}")
            # 优先使用tag_name，确保获取到的是版本号而不是标题文字
            latest = data.get("tag_name", "") or data.get("name", "")
            if latest.startswith("v"):
                latest = latest[1:]
            assets = data.get("assets", [])
            print(f"资产列表: {assets}")
            # 优先选择 .exe 或 .zip 文件，否则取第一个
            download_url = ""
            for asset in assets:
                name = asset.get("name", "")
                url = asset.get("browser_download_url", "")
                print(f"资产: {name}, URL: {url}")
                if name.endswith(".exe") or name.endswith(".zip") or name.endswith(".rar"):
                    download_url = url
                    break
            if not download_url and assets:
                download_url = assets[0].get("browser_download_url", "")
            # 如果没有找到资产，使用zipball_url或tarball_url
            if not download_url:
                download_url = data.get("zipball_url", "")
                if not download_url:
                    download_url = data.get("tarball_url", "")
                if not download_url:
                    download_url = data.get("html_url", PROJECT_URL)
            print(f"最终下载链接: {download_url}")
            print(f"[{auth_status}] 最新版本: {latest}, 下载链接: {download_url}")
            return latest, download_url
    except Exception as e:
        print(f"获取版本失败: {e}")
        # 即使失败，也返回当前版本和项目URL，以便用户手动更新
        return CURRENT_VERSION, PROJECT_URL

def download_file(url, dest_path, parent):
    print(f"开始下载文件，URL: {url}")
    print(f"目标路径: {dest_path}")
    # 检查URL是否为文件链接或GitHub API的zipball/tarball链接
    is_file_link = (url.endswith('.exe') or url.endswith('.zip') or url.endswith('.rar'))
    is_github_api_link = ('api.github.com' in url and ('/zipball/' in url or '/tarball/' in url))
    
    if not (is_file_link or is_github_api_link):
        print(f"URL不是直接文件链接，开始处理")
        # 检查是否为GitHub发布页面链接
        if 'github.com' in url and ('/releases/tag/' in url or '/releases/latest' in url):
            print(f"URL是GitHub发布页面链接")
            try:
                import re
                # 从GitHub发布页面提取资产下载链接
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
                print(f"发送请求获取GitHub发布页面")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    print(f"获取到GitHub发布页面，状态码: {resp.status}")
                    content = resp.read().decode()
                    # 保存HTML内容到临时文件以进行调试
                    debug_file = os.path.join(tempfile.gettempdir(), "github_release_page.html")
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"已保存GitHub发布页面到：{debug_file}")
                    
                    # 查找资产下载链接 - 尝试多种模式
                    patterns = [
                        r'href=["\'](/[^"/]+/[^"/]+/releases/download/[^"/]+/[^"\'\s]+\.(?:exe|zip|rar))["\']',
                        r'href=["\'](https://github.com/[^"/]+/[^"/]+/releases/download/[^"/]+/[^"\'\s]+\.(?:exe|zip|rar))["\']',
                        r'browser_download_url[\s:]+["\']([^"\']+\.(?:exe|zip|rar))["\']',
                        r'/releases/download/[^"/]+/[^"\'\s]+\.(?:exe|zip|rar)'
                    ]
                    
                    asset_url = None
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            print(f"使用模式 {pattern} 找到匹配：{matches}")
                            if matches[0].startswith('http'):
                                asset_url = matches[0]
                            elif matches[0].startswith('/'):
                                asset_url = f"https://github.com{matches[0]}"
                            else:
                                # 尝试构建完整URL
                                if '/releases/download/' in matches[0]:
                                    asset_url = f"https://github.com{matches[0]}"
                            if asset_url:
                                break
                    
                    # 提取第一个匹配的链接
                    if asset_url:
                        print(f"从GitHub页面提取到资产链接：{asset_url}")
                        # 重新调用download_file函数下载资产
                        return download_file(asset_url, dest_path, parent)
                    else:
                        print("未找到资产下载链接")
            except Exception as e:
                print(f"提取GitHub资产链接失败：{e}")
                import traceback
                traceback.print_exc()
        
        # 不是文件链接，也不是GitHub发布页面，或者提取失败
        print(f"无法直接下载此链接，将打开浏览器进行手动下载：{url}")
        progress_win = tk.Toplevel(parent)
        progress_win.title("下载提示")
        progress_win.geometry("400x150")
        progress_win.transient(parent)
        progress_win.grab_set()
        tk.Label(progress_win, text="无法直接下载此链接，将打开浏览器进行手动下载。").pack(pady=10)
        tk.Label(progress_win, text=f"链接: {url}").pack(pady=5)
        
        def open_browser():
            webbrowser.open(url)
            progress_win.destroy()
        
        tk.Button(progress_win, text="打开浏览器", command=open_browser).pack(pady=10)
        progress_win.wait_window()
        return False
    
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

    try:
        # 使用 urllib.request 分块下载
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
        messagebox.showerror("下载失败", f"下载更新文件时出错：{e}\n\n请尝试手动下载：{url}", parent=parent)
        webbrowser.open(url)
        return False

def create_backup():
    """创建整个文件夹的备份"""
    import datetime
    import zipfile
    
    # 获取当前目录
    current_exe = sys.argv[0] if getattr(sys, 'frozen', False) else sys.argv[0]
    current_dir = os.path.dirname(current_exe)
    
    # 生成备份文件名：备份+日期+顺序号
    today = datetime.datetime.now().strftime("%Y%m%d")
    backup_dir = os.path.join(current_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # 查找当前日期的备份文件，确定顺序号
    backup_pattern = f"备份{today}*"
    import glob
    existing_backups = glob.glob(os.path.join(backup_dir, backup_pattern))
    sequence = len(existing_backups) + 1
    
    backup_filename = f"备份{today}_{sequence:02d}.zip"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    print(f"创建备份：{backup_path}")
    
    # 打包整个目录
    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(current_dir):
                # 跳过备份目录和临时文件
                if "backups" in root or "__pycache__" in root:
                    continue
                
                for file in files:
                    # 跳过大型文件或临时文件
                    file_path = os.path.join(root, file)
                    if os.path.getsize(file_path) > 100 * 1024 * 1024:  # 跳过大于100MB的文件
                        print(f"跳过大型文件：{file_path}")
                        continue
                    
                    # 计算相对路径
                    arcname = os.path.relpath(file_path, current_dir)
                    zipf.write(file_path, arcname)
        
        print(f"备份创建成功：{backup_path}")
        
        # 清理30天前的备份
        cleanup_old_backups(backup_dir)
        
        return backup_path
    except Exception as e:
        print(f"备份创建失败：{e}")
        return None

def cleanup_old_backups(backup_dir):
    """清理30天前的备份"""
    import datetime
    
    today = datetime.datetime.now()
    thirty_days_ago = today - datetime.timedelta(days=30)
    
    for file in os.listdir(backup_dir):
        if file.endswith('.zip') and file.startswith('备份'):
            file_path = os.path.join(backup_dir, file)
            try:
                # 提取日期部分：备份20230101_01.zip -> 20230101
                date_str = file[2:10]  # 跳过"备份"，取8位日期
                backup_date = datetime.datetime.strptime(date_str, "%Y%m%d")
                
                if backup_date < thirty_days_ago:
                    os.remove(file_path)
                    print(f"已删除过期备份：{file}")
            except Exception as e:
                print(f"清理备份失败：{e}")

def apply_update(download_path, parent):
    """解压或复制文件，并启动更新脚本"""
    current_exe = sys.argv[0] if getattr(sys, 'frozen', False) else sys.argv[0]
    current_dir = os.path.dirname(current_exe)
    
    print(f"开始应用更新，当前文件：{current_exe}")
    print(f"下载路径：{download_path}")
    
    # 检查文件是否存在
    if not os.path.exists(download_path):
        messagebox.showerror("文件不存在", f"更新文件不存在：{download_path}", parent=parent)
        return False
    
    # 创建整个文件夹的备份
    backup_path = create_backup()
    if backup_path:
        print(f"备份已创建：{backup_path}")
    else:
        print("备份创建失败，但继续更新")

    # 判断下载的是压缩包还是单文件
    if download_path.endswith('.zip'):
        # 解压到临时目录
        extract_dir = tempfile.mkdtemp()
        print(f"解压到临时目录：{extract_dir}")
        try:
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            # 查找新文件
            new_exe = None
            # 首先查找与当前文件同名的文件
            current_exe_name = os.path.basename(current_exe)
            print(f"当前文件名：{current_exe_name}")
            for root, dirs, files in os.walk(extract_dir):
                print(f"在目录 {root} 中查找文件：{files}")
                for f in files:
                    if f == current_exe_name:
                        new_exe = os.path.join(root, f)
                        print(f"找到与当前文件同名的文件：{new_exe}")
                        break
                    elif f.endswith('.exe') or f.endswith('.pyw') or f == 'main.py':
                        new_exe = os.path.join(root, f)
                        print(f"找到目标文件：{new_exe}")
                        break
                if new_exe:
                    break
            if not new_exe:
                # 尝试查找任何Python文件
                for root, dirs, files in os.walk(extract_dir):
                    for f in files:
                        if f.endswith('.py'):
                            new_exe = os.path.join(root, f)
                            print(f"找到Python文件：{new_exe}")
                            break
                    if new_exe:
                        break
            if not new_exe:
                raise Exception("压缩包中未找到可执行文件或Python文件")
            # 检查新文件大小
            new_exe_size = os.path.getsize(new_exe)
            print(f"新文件大小：{new_exe_size} bytes")
        except Exception as e:
            print(f"解压失败：{e}")
            messagebox.showerror("解压失败", f"解压更新包失败：{e}", parent=parent)
            return False
    else:
        # 直接下载的可执行文件
        new_exe = download_path
        extract_dir = None
        # 检查新文件大小
        new_exe_size = os.path.getsize(new_exe)
        print(f"新文件大小：{new_exe_size} bytes")

    # 备份旧文件
    backup_path = current_exe + ".backup"
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        shutil.copy2(current_exe, backup_path)
        print(f"已备份旧文件到：{backup_path}")
        # 检查备份文件大小
        backup_size = os.path.getsize(backup_path)
        print(f"备份文件大小：{backup_size} bytes")
    except Exception as e:
        print(f"备份失败：{e}")
        messagebox.showwarning("备份警告", f"备份旧版本失败：{e}，更新可能无法继续", parent=parent)

    # 创建更新脚本（批处理）
    script_path = os.path.join(tempfile.gettempdir(), "update_script.bat")
    try:
        with open(script_path, "w", encoding='utf-8') as f:
            f.write(f"""
@echo off
echo 正在更新程序...
echo 当前文件：{current_exe}
echo 新文件：{new_exe}
timeout /t 2 /nobreak >nul
taskkill /f /im "{os.path.basename(current_exe)}" 2>nul
del /f /q "{current_exe}" 2>nul
echo 复制新文件...
copy /y "{new_exe}" "{current_exe}"
if %errorlevel% equ 0 (
    echo 更新成功！
    start "" "{current_exe}"
) else (
    echo 更新失败，尝试恢复备份...
    copy /y "{backup_path}" "{current_exe}"
    start "" "{current_exe}"
)
del "%~f0"
""")
        print(f"已创建更新脚本：{script_path}")
    except Exception as e:
        print(f"脚本创建失败：{e}")
        messagebox.showerror("脚本创建失败", f"创建更新脚本失败：{e}", parent=parent)
        return False

    # 执行更新脚本并退出
    try:
        subprocess.Popen([script_path], shell=True)
        print("更新脚本已启动")
        # 关闭当前程序
        parent.quit()
        sys.exit(0)
    except Exception as e:
        print(f"执行失败：{e}")
        messagebox.showerror("执行失败", f"执行更新脚本失败：{e}", parent=parent)
        return False

def auto_update(parent, download_url):
    """自动下载并更新"""
    # 检查下载URL是否有效
    if not download_url:
        messagebox.showerror("更新失败", "下载链接无效，无法进行自动更新。", parent=parent)
        webbrowser.open(PROJECT_URL)
        return

    # 下载到临时文件
    temp_dir = tempfile.gettempdir()
    file_name = download_url.split('/')[-1] or "update.zip"
    # 如果是GitHub的zipball或tarball链接，添加.zip扩展名
    if 'api.github.com' in download_url and ('/zipball/' in download_url or '/tarball/' in download_url):
        if not file_name.endswith('.zip'):
            file_name += '.zip'
    dest_path = os.path.join(temp_dir, file_name)

    print(f"开始下载更新到：{dest_path}")
    if not download_file(download_url, dest_path, parent):
        print("下载失败，已打开浏览器进行手动下载")
        return

    # 应用更新
    print("下载完成，开始应用更新")
    apply_update(dest_path, parent)

# 以下是原有的 check_for_updates 函数，修改为调用 auto_update
def get_latest_version():
    """获取最新版本号"""
    latest, _ = fetch_latest_version()
    return latest

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