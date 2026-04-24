import os
import sys
import urllib.request
import json
import webbrowser
import shutil
import tempfile
import subprocess
import zipfile
import datetime
import re
import glob
from tkinter import messagebox, simpledialog, ttk
import tkinter as tk

# ================== 配置区域 ==================
CURRENT_VERSION = "1.0.4.1"
PROJECT_URL = "https://github.com/zhangyapu1/pymanager"

REPO_OWNER = "zhangyapu1"
REPO_NAME = "pymanager"
RELEASE_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

# 下载超时（秒）
DOWNLOAD_TIMEOUT = 60
# 备份保留天数
BACKUP_RETENTION_DAYS = 30
# 跳过备份的大文件大小阈值 (100MB)
MAX_BACKUP_FILE_SIZE = 100 * 1024 * 1024
# ===========================================

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
TOKEN_FILE = os.path.join(CONFIG_DIR, "api_token.txt")

def get_api_token():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding='utf-8') as f:
                token = f.read().strip()
                if token:
                    return token
        except Exception:
            pass
    return os.environ.get("GITHUB_TOKEN", "")

def save_api_token(token):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(TOKEN_FILE, "w", encoding='utf-8') as f:
            f.write(token.strip())
    except Exception as e:
        print(f"保存Token失败: {e}")

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
    """
    比较两个版本号字符串。
    返回 True 如果 v1 > v2，否则 False。
    """
    def normalize_version(v):
        # 移除前缀 'v' 或 'V'
        if v.startswith(('v', 'V')):
            v = v[1:]
        parts = []
        for p in v.split('.'):
            try:
                parts.append(int(p))
            except ValueError:
                # 处理非数字部分，例如 '1.0.0-beta'，这里简单处理为0或保留字符串比较的后备
                parts.append(0) 
        return parts

    try:
        a1 = normalize_version(v1)
        a2 = normalize_version(v2)
        
        # 补齐长度
        max_len = max(len(a1), len(a2))
        a1 += [0] * (max_len - len(a1))
        a2 += [0] * (max_len - len(a2))
        
        return a1 > a2
    except Exception:
        # 极端情况下的后备，虽然不准确但防止崩溃
        return v1 > v2

def fetch_latest_version(parent=None):
    token = get_api_token()
    if not token and parent:
        token = prompt_for_token(parent)

    headers = {"User-Agent": f"ScriptManager/{CURRENT_VERSION}"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        # 日志脱敏
        log_headers = {k: ("***" if k == "Authorization" else v) for k, v in headers.items()}
        auth_status = "已认证"
    else:
        log_headers = headers
        auth_status = "未认证"

    try:
        print(f"请求URL: {RELEASE_API_URL}")
        print(f"请求头: {log_headers}")
        req = urllib.request.Request(RELEASE_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"响应状态码: {resp.status}")
            data = json.loads(resp.read().decode('utf-8'))
            
            # 优先使用tag_name，确保获取到的是版本号而不是标题文字
            latest = data.get("tag_name", "") or data.get("name", "")
            if latest.startswith("v"):
                latest = latest[1:]
            
            assets = data.get("assets", [])
            
            # 优先选择 .exe 或 .zip 文件，否则取第一个
            download_url = ""
            selected_asset_name = ""
            
            # 定义优先级扩展名
            preferred_exts = ('.exe', '.zip', '.rar')
            
            for asset in assets:
                name = asset.get("name", "")
                url = asset.get("browser_download_url", "")
                
                # 优先匹配首选扩展名
                if any(name.endswith(ext) for ext in preferred_exts):
                    download_url = url
                    selected_asset_name = name
                    break
            
            # 如果没有找到首选扩展名，但有资产，取第一个
            if not download_url and assets:
                first_asset = assets[0]
                download_url = first_asset.get("browser_download_url", "")
                selected_asset_name = first_asset.get("name", "")

            # 如果仍然没有找到资产（例如只有源码包），使用zipball_url
            if not download_url:
                download_url = data.get("zipball_url", "")
                if not download_url:
                    download_url = data.get("tarball_url", "")
                
            # 最后的兜底
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
    
    # 检查URL是否为直接文件链接
    # 注意：GitHub API 的 zipball/tarball 链接也是直接可下载的，不需要解析HTML
    is_direct_download = (
        url.endswith('.exe') or 
        url.endswith('.zip') or 
        url.endswith('.rar') or 
        'api.github.com' in url
    )
    
    if not is_direct_download:
        # 如果不是直接链接，也不是API链接，尝试判断是否是GitHub Release页面
        # 但为了稳定性，不建议在此处进行复杂的HTML解析，因为fetch_latest_version应该已经提供了直接链接
        # 如果到这里，说明链接格式未知，直接引导用户手动下载
        print(f"URL不是标准的直接下载链接，引导手动下载: {url}")
        progress_win = tk.Toplevel(parent)
        progress_win.title("下载提示")
        progress_win.geometry("400x150")
        progress_win.transient(parent)
        progress_win.grab_set()
        tk.Label(progress_win, text="无法直接自动下载此链接。").pack(pady=10)
        tk.Label(progress_win, text=f"请在浏览器中打开以下链接手动下载：").pack(pady=5)
        tk.Label(progress_win, text=url, wraplength=350).pack(pady=5)
        
        def open_browser():
            webbrowser.open(url)
            progress_win.destroy()
        
        tk.Button(progress_win, text="打开浏览器", command=open_browser).pack(pady=10)
        # 提供一个“我已下载”的按钮可能更好，但当前逻辑是返回False表示自动下载失败
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
                    else:
                        status_label.config(text=f"下载中... ({downloaded} bytes)")
                    
                    # 保持UI响应
                    progress_win.update_idletasks()
        
        progress_win.destroy()
        print(f"下载完成: {dest_path}")
        return True
    except Exception as e:
        if progress_win.winfo_exists():
            progress_win.destroy()
        messagebox.showerror("下载失败", f"下载更新文件时出错：{e}\n\n请尝试手动下载：{url}", parent=parent)
        webbrowser.open(url)
        return False

def create_backup():
    """创建整个文件夹的备份"""
    # 获取当前目录
    current_exe = sys.argv[0]
    current_dir = os.path.dirname(current_exe)
    
    # 生成备份文件名：备份+日期+顺序号
    today = datetime.datetime.now().strftime("%Y%m%d")
    backup_dir = os.path.join(current_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # 查找当前日期的备份文件，确定顺序号
    backup_pattern = f"备份{today}*"
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
                rel_root = os.path.relpath(root, current_dir)
                if "backups" in rel_root.split(os.sep) or "__pycache__" in rel_root.split(os.sep):
                    continue
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # 跳过大型文件或临时文件
                        if os.path.getsize(file_path) > MAX_BACKUP_FILE_SIZE:
                            print(f"跳过大型文件：{file_path}")
                            continue
                        
                        # 计算相对路径
                        arcname = os.path.relpath(file_path, current_dir)
                        zipf.write(file_path, arcname)
                    except PermissionError:
                        print(f"跳过权限不足文件：{file_path}")
                    except Exception as e:
                        print(f"跳过处理失败文件 {file_path}: {e}")
        
        print(f"备份创建成功：{backup_path}")
        
        # 清理旧备份
        cleanup_old_backups(backup_dir)
        
        return backup_path
    except Exception as e:
        print(f"备份创建失败：{e}")
        import traceback
        traceback.print_exc()
        return None

def cleanup_old_backups(backup_dir):
    """清理30天前的备份"""
    today = datetime.datetime.now()
    cutoff_date = today - datetime.timedelta(days=BACKUP_RETENTION_DAYS)
    
    if not os.path.exists(backup_dir):
        return

    for file in os.listdir(backup_dir):
        if file.endswith('.zip') and file.startswith('备份'):
            file_path = os.path.join(backup_dir, file)
            try:
                # 提取日期部分：备份20230101_01.zip -> 20230101
                # 确保文件名格式符合预期
                if len(file) < 12: 
                    continue
                date_str = file[2:10] 
                backup_date = datetime.datetime.strptime(date_str, "%Y%m%d")
                
                if backup_date < cutoff_date:
                    os.remove(file_path)
                    print(f"已删除过期备份：{file}")
            except Exception as e:
                print(f"清理备份失败 {file}: {e}")

def apply_update(download_path, parent):
    """解压或复制文件，并启动更新脚本"""
    current_exe = sys.argv[0]
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

    new_exe = None
    extract_dir = None
    temp_files_to_clean = []

    try:
        # 判断下载的是压缩包还是单文件
        if download_path.endswith('.zip'):
            # 解压到临时目录
            extract_dir = tempfile.mkdtemp()
            temp_files_to_clean.append(extract_dir)
            print(f"解压到临时目录：{extract_dir}")
            
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                # 安全检查：防止路径遍历攻击 (虽然extractall在现代Python中有一定保护，但显式检查更好)
                for member in zip_ref.infolist():
                    if member.filename.startswith('/') or '..' in member.filename:
                        raise Exception(f"Unsafe zip path: {member.filename}")
                zip_ref.extractall(extract_dir)
            
            # 查找新文件
            current_exe_name = os.path.basename(current_exe)
            found_file = None
            
            # 策略1: 查找与当前执行文件同名的文件
            for root, _, files in os.walk(extract_dir):
                for f in files:
                    if f == current_exe_name:
                        found_file = os.path.join(root, f)
                        break
                if found_file:
                    break
            
            # 策略2: 如果没有同名文件，查找常见的入口文件
            if not found_file:
                common_names = ['main.py', 'app.py', 'start.py']
                # 如果是exe环境，可能还是找exe
                if getattr(sys, 'frozen', False):
                     common_names = [f for f in os.listdir(extract_dir) if f.endswith('.exe')]
                     # 如果根目录有exe，优先取
                     for f in common_names:
                         p = os.path.join(extract_dir, f)
                         if os.path.isfile(p):
                             found_file = p
                             break
                else:
                    for root, _, files in os.walk(extract_dir):
                        for f in files:
                            if f in common_names or f.endswith('.pyw'):
                                found_file = os.path.join(root, f)
                                break
                        if found_file:
                            break

            if not found_file:
                 # 策略3: 任意py或exe
                 for root, _, files in os.walk(extract_dir):
                    for f in files:
                        if f.endswith('.py') or f.endswith('.exe'):
                            found_file = os.path.join(root, f)
                            break
                    if found_file:
                        break

            if not found_file:
                raise Exception("压缩包中未找到可执行文件或Python文件")
            
            new_exe = found_file
            print(f"找到目标更新文件：{new_exe}")
            
        else:
            # 直接下载的可执行文件
            new_exe = download_path
        
        if not new_exe or not os.path.exists(new_exe):
            raise Exception("未能定位到新版本的执行文件")

        # 备份旧文件 (单个文件备份，用于快速回滚)
        single_backup_path = current_exe + ".backup"
        try:
            if os.path.exists(single_backup_path):
                os.remove(single_backup_path)
            shutil.copy2(current_exe, single_backup_path)
            print(f"已备份旧文件到：{single_backup_path}")
        except Exception as e:
            print(f"单文件备份失败：{e}")
            # 继续，因为已经有文件夹备份了

        # 创建更新脚本（批处理）
        # 注意：仅支持 Windows
        if sys.platform != 'win32':
            messagebox.showerror("不支持的平台", "自动更新仅支持 Windows 系统。请手动替换文件。", parent=parent)
            return False

        script_path = os.path.join(tempfile.gettempdir(), "update_script.bat")
        temp_files_to_clean.append(script_path)
        
        # 确保路径被双引号包裹，防止空格或特殊字符问题
        safe_current_exe = f'"{current_exe}"'
        safe_new_exe = f'"{new_exe}"'
        safe_single_backup = f'"{single_backup_path}"'
        exe_basename = os.path.basename(current_exe)

        bat_content = f"""@echo off
chcp 65001 >nul
echo 正在更新程序...
timeout /t 2 /nobreak >nul

:: 尝试关闭当前进程
taskkill /f /im "{exe_basename}" 2>nul

:: 等待进程完全退出
timeout /t 1 /nobreak >nul

:: 复制新文件
copy /y {safe_new_exe} {safe_current_exe}
if %errorlevel% equ 0 (
    echo 更新成功！
    start "" {safe_current_exe}
) else (
    echo 更新失败，尝试恢复备份...
    if exist {safe_single_backup} (
        copy /y {safe_single_backup} {safe_current_exe}
        start "" {safe_current_exe}
    ) else (
        echo 严重错误：更新失败且无备份。
        pause
    )
)

:: 清理脚本自身
del "%~f0"
"""
        with open(script_path, "w", encoding='gbk') as f: # Windows batch 通常使用 gbk 或 ansi，utf-8 有时会有 BOM 问题
            f.write(bat_content)
        
        print(f"已创建更新脚本：{script_path}")

        # 执行更新脚本并退出
        # DETACHED_PROCESS 使得子进程独立于父进程运行
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        
        subprocess.Popen(
            [script_path], 
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            shell=True
        )
        
        print("更新脚本已启动，当前程序即将退出")
        
        # 关闭当前程序
        if parent:
            parent.quit()
        sys.exit(0)

    except Exception as e:
        print(f"应用更新过程中发生错误：{e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("更新失败", f"应用更新时出错：{e}", parent=parent)
        return False
    finally:
        # 注意：由于我们调用了 sys.exit(0)，finally 块在正常更新流程中可能不会执行清理
        # 但在异常情况下，我们可以尝试清理临时解压目录
        # 然而，如果更新成功，新进程会接管，旧进程退出，临时目录可能需要手动清理或由系统清理
        # 这里不做强制清理，以免干扰正在进行的复制操作（如果是在异步场景下）
        pass

def auto_update(parent, download_url):
    """自动下载并更新"""
    if not download_url:
        messagebox.showerror("更新失败", "下载链接无效，无法进行自动更新。", parent=parent)
        webbrowser.open(PROJECT_URL)
        return

    temp_dir = tempfile.gettempdir()
    file_name = download_url.split('/')[-1] or "update.zip"
    
    # 清理文件名中的查询参数
    if '?' in file_name:
        file_name = file_name.split('?')[0]

    # 如果是GitHub的zipball或tarball链接，确保有正确的扩展名
    if 'api.github.com' in download_url:
        if '/zipball/' in download_url:
            if not file_name.endswith('.zip'):
                file_name += '.zip'
        elif '/tarball/' in download_url:
             if not file_name.endswith('.tar.gz'):
                 file_name += '.tar.gz' # 注意：当前代码主要处理zip/exe，tar.gz支持有限

    dest_path = os.path.join(temp_dir, file_name)

    print(f"开始下载更新到：{dest_path}")
    if not download_file(download_url, dest_path, parent):
        print("下载失败，已打开浏览器进行手动下载")
        return

    # 应用更新
    print("下载完成，开始应用更新")
    apply_update(dest_path, parent)

def get_latest_version():
    """获取最新版本号"""
    latest, _ = fetch_latest_version()
    return latest

def check_for_updates(parent_root=None, show_no_update_msg=True):
    latest, download_url = fetch_latest_version(parent_root)
    
    if not latest:
        if show_no_update_msg:
            messagebox.showerror("检查更新失败", "无法获取最新版本信息，请检查网络。", parent=parent_root)
        return False
        
    try:
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
    except Exception as e:
        print(f"版本比较出错: {e}")
        if show_no_update_msg:
            messagebox.showerror("错误", f"版本检查出错: {e}", parent=parent_root)
        return False