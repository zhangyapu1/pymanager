"""
自动更新 - 检查 GitHub Releases 并提示或执行应用更新，支持清单对比清理。

常量：
    CURRENT_VERSION - 当前版本号 "1.6.3"
    PROJECT_URL     - 项目主页 https://github.com/zhangyapu1/pymanager
    REPO_OWNER      - GitHub 仓库所有者
    REPO_NAME       - GitHub 仓库名
    RELEASE_API_URL - GitHub Releases API 地址
    DOWNLOAD_TIMEOUT - 下载超时时间 60 秒
    BACKUP_RETENTION_DAYS - 备份保留天数 30
    MAX_BACKUP_FILE_SIZE  - 备份文件最大大小 100MB

核心函数：
    check_for_updates(parent, ui_callback, show_no_update_msg, output_callback)：
        检查更新入口函数
        - 获取最新版本号和下载链接
        - 比较版本号判断是否需要更新
        - 有更新时弹出对话框让用户选择操作

    fetch_latest_version(parent, output_callback, ui_callback)：
        获取最新版本信息
        - 优先使用用户保存的 Token
        - Token 不足时回退到内置默认 Token
        - 速率限制时提示用户输入自己的 Token

    download_file(url, dest_path, ...)：
        下载更新文件
        - 支持进度回调
        - SSL 错误时自动降级验证
        - 非 .exe/.zip/.rar 链接引导浏览器手动下载

    perform_update(download_url, parent, ...)：
        执行完整更新流程：
        1. 创建备份（限制 100MB）
        2. 下载新版本
        3. 解压并覆盖文件
        4. 对比 manifest.json 清理废弃文件
        5. 提示重启

    create_github_release(version, changelog, output_callback)：
        创建 GitHub Release
        - 使用 GitHub API 发布新版本
        - 自动设置 tag_name 和 target_commitish

辅助函数：
    is_version_greater(v1, v2)    - 版本号比较
    build_auth_headers(parent)    - 构建认证请求头
    fetch_release_data(headers)   - 获取 Release 数据
    parse_latest_version(data)    - 解析最新版本号
    select_download_url(data)     - 选择最佳下载链接
    prompt_for_token(parent, ui)  - 提示用户输入 Token

异常类：
    RateLimitError - GitHub API 速率限制异常

依赖：modules.token_crypto
"""
import os
import sys
import logging
import urllib.request
import urllib.error
import json
import ssl
import webbrowser
import shutil
import tempfile
import subprocess
import zipfile
import datetime
import re
import glob

logger = logging.getLogger(__name__)

if not logger.handlers:
    _log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(_log_dir, exist_ok=True)
    _handler = logging.FileHandler(os.path.join(_log_dir, 'updater_log.txt'), encoding='utf-8')
    _handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

CURRENT_VERSION = "1.6.3"
PROJECT_URL = "https://github.com/zhangyapu1/pymanager"

REPO_OWNER = "zhangyapu1"
REPO_NAME = "pymanager"
RELEASE_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

DOWNLOAD_TIMEOUT = 60
BACKUP_RETENTION_DAYS = 30
MAX_BACKUP_FILE_SIZE = 100 * 1024 * 1024

from modules.token_crypto import get_api_token, save_api_token, get_default_token


def _output(callback, msg):
    logger.info(msg)
    if callback:
        try:
            callback(msg)
        except (RuntimeError, OSError):
            pass


def _output_error(callback, msg):
    logger.error(msg)
    if callback:
        try:
            callback(f"[错误] {msg}")
        except (RuntimeError, OSError):
            pass


def prompt_for_token(parent=None, ui_callback=None):
    if ui_callback:
        token = ui_callback.ask_string(
            "API Token",
            "请输入GitHub Personal Access Token 以提高 API 限额。\n\n"
            "如何获取？\n"
            "1. 访问 https://github.com/settings/tokens\n"
            "2. 生成新令牌，勾选 'repo' 或 'projects' 权限\n"
            "3. 复制并粘贴到此处。\n\n"
            "若跳过，匿名请求每小时限制 60 次。",
            parent=parent
        )
    else:
        return ""
    if token:
        save_api_token(token)
        return token
    return ""


def is_version_greater(v1, v2):
    def normalize_version(v):
        if v.startswith(('v', 'V')):
            v = v[1:]
        parts = []
        for p in v.split('.'):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
        return parts

    try:
        a1 = normalize_version(v1)
        a2 = normalize_version(v2)

        max_len = max(len(a1), len(a2))
        a1 += [0] * (max_len - len(a1))
        a2 += [0] * (max_len - len(a2))

        return a1 > a2
    except (ValueError, TypeError, AttributeError):
        return v1 > v2


def build_auth_headers(parent=None):
    headers = {"User-Agent": f"ScriptManager/{CURRENT_VERSION}"}
    token = get_api_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
        return headers, "用户Token"
    default_token = get_default_token()
    if default_token:
        headers["Authorization"] = f"Bearer {default_token}"
        return headers, "内置Token"
    return headers, "未认证"


class RateLimitError(Exception):
    pass


def fetch_release_data(headers):
    req = urllib.request.Request(RELEASE_API_URL, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}")
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise RateLimitError("GitHub API 速率限制已达上限")
        raise
    except ssl.SSLError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}")
            return json.loads(resp.read().decode('utf-8'))


def parse_latest_version(data):
    latest = data.get("tag_name", "") or data.get("name", "")
    if latest.startswith("v"):
        latest = latest[1:]
    return latest


def select_download_url(data):
    assets = data.get("assets", [])
    preferred_exts = ('.exe', '.zip', '.rar')

    for asset in assets:
        name = asset.get("name", "")
        url = asset.get("browser_download_url", "")
        if any(name.endswith(ext) for ext in preferred_exts):
            logger.debug(f"选择首选资产: {name}")
            return url, name

    if assets:
        first_asset = assets[0]
        logger.debug(f"选择第一个资产: {first_asset.get('name', '')}")
        return first_asset.get("browser_download_url", ""), first_asset.get("name", "")

    download_url = data.get("zipball_url", "")
    if download_url:
        logger.debug("使用 zipball_url")
        return download_url, "源码包(zip)"

    download_url = data.get("tarball_url", "")
    if download_url:
        logger.debug("使用 tarball_url")
        return download_url, "源码包(tar)"

    logger.debug("使用 html_url 作为兜底")
    return data.get("html_url", PROJECT_URL), "项目主页"


def fetch_latest_version(parent=None, output_callback=None, ui_callback=None):
    try:
        headers, auth_status = build_auth_headers(parent)
        data = fetch_release_data(headers)
        latest = parse_latest_version(data)
        download_url, asset_name = select_download_url(data)

        _output(output_callback, f"[{auth_status}] 最新版本: {latest}, 下载链接: {download_url}")
        return latest, download_url
    except RateLimitError:
        if parent and not get_api_token():
            token = prompt_for_token(parent, ui_callback=ui_callback)
            if token:
                headers, auth_status = build_auth_headers(parent)
                try:
                    data = fetch_release_data(headers)
                    latest = parse_latest_version(data)
                    download_url, asset_name = select_download_url(data)
                    _output(output_callback, f"[{auth_status}] 最新版本: {latest}, 下载链接: {download_url}")
                    return latest, download_url
                except RateLimitError:
                    _output_error(output_callback, "用户Token也已达速率限制")
                    if ui_callback:
                        ui_callback.show_warning("API 限制", "当前Token的API请求次数已达上限，请稍后再试。", parent=parent)
                    return CURRENT_VERSION, PROJECT_URL
        _output_error(output_callback, "GitHub API 速率限制已达上限")
        if ui_callback:
            ui_callback.show_warning("API 限制", "内置Token的API请求次数已达上限。\n请输入您自己的GitHub Token以提高限额。", parent=parent)
        return CURRENT_VERSION, PROJECT_URL
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        _output_error(output_callback, f"获取版本失败: {e}")
        return CURRENT_VERSION, PROJECT_URL


def download_file(url, dest_path, parent=None, output_callback=None, ui_callback=None, progress_callback=None):
    _output(output_callback, f"开始下载文件，URL: {url}")
    _output(output_callback, f"目标路径: {dest_path}")

    is_direct_download = (
        url.endswith('.exe') or
        url.endswith('.zip') or
        url.endswith('.rar') or
        'api.github.com' in url
    )

    if not is_direct_download:
        _output(output_callback, f"URL不是标准的直接下载链接，引导手动下载: {url}")
        if ui_callback:
            ui_callback.show_info("下载提示", f"无法直接自动下载此链接。\n请在浏览器中手动下载：\n{url}")
        webbrowser.open(url)
        return False

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ScriptManager"})
        try:
            opener = urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT)
        except ssl.SSLError:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            opener = urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT, context=ctx)
        with opener as response:
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
                        if progress_callback:
                            progress_callback(percent, f"下载中... {percent}%")
                    else:
                        if progress_callback:
                            progress_callback(-1, f"下载中... ({downloaded} bytes)")

        _output(output_callback, f"下载完成: {dest_path}")
        return True
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        msg = f"下载更新文件时出错：{e}\n\n请尝试手动下载：{url}"
        _output_error(output_callback, msg)
        if ui_callback:
            ui_callback.show_error("下载失败", msg, parent=parent)
        webbrowser.open(url)
        return False


def create_backup(output_callback=None):
    current_exe = sys.argv[0]
    current_dir = os.path.dirname(current_exe)

    today = datetime.datetime.now().strftime("%Y%m%d")
    backup_dir = os.path.join(current_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    backup_pattern = f"备份{today}*"
    existing_backups = glob.glob(os.path.join(backup_dir, backup_pattern))
    sequence = len(existing_backups) + 1

    backup_filename = f"备份{today}_{sequence:02d}.zip"
    backup_path = os.path.join(backup_dir, backup_filename)

    _output(output_callback, f"创建备份：{backup_path}")

    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(current_dir):
                rel_root = os.path.relpath(root, current_dir)
                if "backups" in rel_root.split(os.sep) or "__pycache__" in rel_root.split(os.sep):
                    continue

                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getsize(file_path) > MAX_BACKUP_FILE_SIZE:
                            logger.debug(f"跳过大型文件：{file_path}")
                            continue

                        arcname = os.path.relpath(file_path, current_dir)
                        zipf.write(file_path, arcname)
                    except PermissionError:
                        logger.debug(f"跳过权限不足文件：{file_path}")
                    except OSError as e:
                        logger.debug(f"跳过处理失败文件 {file_path}: {e}")

        _output(output_callback, f"备份创建成功：{backup_path}")

        cleanup_old_backups(backup_dir, output_callback)

        return backup_path
    except (OSError, zipfile.BadZipFile) as e:
        _output_error(output_callback, f"备份创建失败：{e}")
        return None


def cleanup_old_backups(backup_dir, output_callback=None):
    today = datetime.datetime.now()
    cutoff_date = today - datetime.timedelta(days=BACKUP_RETENTION_DAYS)

    if not os.path.exists(backup_dir):
        return

    for file in os.listdir(backup_dir):
        if file.endswith('.zip') and file.startswith('备份'):
            file_path = os.path.join(backup_dir, file)
            try:
                if len(file) < 12:
                    continue
                date_str = file[2:10]
                backup_date = datetime.datetime.strptime(date_str, "%Y%m%d")

                if backup_date < cutoff_date:
                    os.remove(file_path)
                    _output(output_callback, f"已删除过期备份：{file}")
            except (ValueError, OSError) as e:
                logger.debug(f"清理备份失败 {file}: {e}")


def _load_manifest(directory):
    manifest_path = os.path.join(directory, "config", "manifest.json")
    if not os.path.exists(manifest_path):
        manifest_path = os.path.join(directory, "manifest.json")
    if not os.path.exists(manifest_path):
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.debug(f"读取清单失败: {e}")
        return None


def _cleanup_obsolete_files(current_dir, new_extract_dir, output_callback=None):
    old_manifest = _load_manifest(current_dir)
    new_manifest = _load_manifest(new_extract_dir)

    if old_manifest is None or new_manifest is None:
        _output(output_callback, "缺少清单文件，跳过废弃文件清理")
        return

    old_files = set(old_manifest.get("files", []))
    new_files = set(new_manifest.get("files", []))

    obsolete = old_files - new_files

    protected_dirs = {"data", "config", "logs", "backups", "__pycache__", ".git", ".idea", ".vscode"}
    protected_files = {"settings.json", "groups_meta.json"}

    force_remove_dirs = {".trae", "tests"}
    force_remove_files = {".gitignore", "REQUIREMENTS.md", "manifest.json"}

    removed = 0
    for rel_path in sorted(obsolete):
        parts = rel_path.replace("\\", "/").split("/")
        if any(p in protected_dirs for p in parts):
            continue
        if os.path.basename(rel_path) in protected_files:
            continue

        abs_path = os.path.join(current_dir, rel_path.replace("/", os.sep))
        if os.path.isfile(abs_path):
            try:
                os.remove(abs_path)
                removed += 1
                _output(output_callback, f"已删除废弃文件: {rel_path}")
            except OSError as e:
                logger.debug(f"删除失败 {rel_path}: {e}")

    for fname in force_remove_files:
        abs_path = os.path.join(current_dir, fname)
        if os.path.isfile(abs_path):
            try:
                os.remove(abs_path)
                removed += 1
                _output(output_callback, f"已删除废弃文件: {fname}")
            except OSError as e:
                logger.debug(f"删除失败 {fname}: {e}")

    for dname in force_remove_dirs:
        abs_path = os.path.join(current_dir, dname)
        if os.path.isdir(abs_path):
            try:
                shutil.rmtree(abs_path)
                _output(output_callback, f"已删除废弃目录: {dname}")
            except OSError as e:
                logger.debug(f"删除目录失败 {dname}: {e}")

    empty_dirs = []
    for root, dirs, files in os.walk(current_dir, topdown=False):
        skip = False
        rel = os.path.relpath(root, current_dir).replace("\\", "/")
        if rel == ".":
            continue
        for p in rel.split("/"):
            if p in protected_dirs:
                skip = True
                break
        if skip:
            continue
        if not dirs and not files:
            empty_dirs.append(root)

    removed_dirs = 0
    for d in empty_dirs:
        try:
            os.rmdir(d)
            removed_dirs += 1
            _output(output_callback, f"已删除空目录: {os.path.relpath(d, current_dir)}")
        except OSError:
            pass

    for _ in range(10):
        found_parent = False
        for root, dirs, files in os.walk(current_dir, topdown=False):
            skip = False
            rel = os.path.relpath(root, current_dir).replace("\\", "/")
            if rel == ".":
                continue
            for p in rel.split("/"):
                if p in protected_dirs:
                    skip = True
                    break
            if skip:
                continue
            if not dirs and not files:
                try:
                    os.rmdir(root)
                    removed_dirs += 1
                    _output(output_callback, f"已删除空目录: {os.path.relpath(root, current_dir)}")
                    found_parent = True
                except OSError:
                    pass
        if not found_parent:
            break

    if removed > 0:
        _output(output_callback, f"共清理 {removed} 个废弃文件")
    if removed_dirs > 0:
        _output(output_callback, f"共清理 {removed_dirs} 个空目录")
    if removed == 0 and removed_dirs == 0:
        _output(output_callback, "无需清理废弃文件")


def apply_update(download_path, parent=None, output_callback=None, ui_callback=None):
    current_exe = os.path.abspath(sys.argv[0])
    current_dir = os.path.dirname(current_exe)

    _output(output_callback, f"开始应用更新，当前文件：{current_exe}")
    _output(output_callback, f"项目目录：{current_dir}")
    _output(output_callback, f"下载路径：{download_path}")

    if not os.path.exists(download_path):
        msg = f"更新文件不存在：{download_path}"
        _output_error(output_callback, msg)
        if ui_callback:
            ui_callback.show_error("文件不存在", msg, parent=parent)
        return False

    backup_path = create_backup(output_callback)
    if backup_path:
        _output(output_callback, f"备份已创建：{backup_path}")
    else:
        _output(output_callback, "备份创建失败，但继续更新")

    single_backup_path = current_exe + ".backup"

    try:
        if download_path.endswith('.zip'):
            extract_dir = tempfile.mkdtemp()
            _output(output_callback, f"解压到临时目录：{extract_dir}")

            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    if member.filename.startswith('/') or '..' in member.filename:
                        raise ValueError(f"Unsafe zip path: {member.filename}")
                zip_ref.extractall(extract_dir)

            entries = os.listdir(extract_dir)
            if len(entries) == 1 and os.path.isdir(os.path.join(extract_dir, entries[0])):
                extract_dir = os.path.join(extract_dir, entries[0])
                _output(output_callback, f"检测到 zipball 子目录，切换到：{extract_dir}")

            skip_dirs = {'backups', '__pycache__', '.git', '.config'}
            copied = 0
            for root, dirs, files in os.walk(extract_dir):
                dirs[:] = [d for d in dirs if d not in skip_dirs]

                rel_root = os.path.relpath(root, extract_dir)
                if rel_root == '.':
                    dest_root = current_dir
                else:
                    dest_root = os.path.join(current_dir, rel_root)

                os.makedirs(dest_root, exist_ok=True)

                for f in files:
                    src_file = os.path.join(root, f)
                    dst_file = os.path.join(dest_root, f)
                    try:
                        shutil.copy2(src_file, dst_file)
                        copied += 1
                        logger.debug(f"已复制: {os.path.relpath(dst_file, current_dir)}")
                    except PermissionError:
                        logger.debug(f"跳过权限不足: {dst_file}")
                    except OSError as e:
                        logger.debug(f"复制失败 {dst_file}: {e}")

            _output(output_callback, f"共复制 {copied} 个文件")

            _cleanup_obsolete_files(current_dir, extract_dir, output_callback)

            current_exe_name = os.path.basename(current_exe)
            current_pid = os.getpid()
            script_path = os.path.join(tempfile.gettempdir(), "update_script.bat")
            safe_current_exe = f'"{current_exe}"'

            bat_content = f"""@echo off
chcp 65001 >nul
echo 更新完成，正在关闭旧进程...
taskkill /f /pid {current_pid} 2>nul
taskkill /f /im "{current_exe_name}" 2>nul
timeout /t 2 /nobreak >nul

echo 正在重启程序...
start "" {safe_current_exe}
del "%~f0"
"""
            with open(script_path, "w", encoding='gbk') as f:
                f.write(bat_content)

            _output(output_callback, f"已创建重启脚本：{script_path}")

            CREATE_NEW_PROCESS_GROUP = 0x00000200
            DETACHED_PROCESS = 0x00000008

            subprocess.Popen(
                [script_path],
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                shell=True
            )

            _output(output_callback, "重启脚本已启动，当前程序即将退出")

            if parent and hasattr(parent, 'quit'):
                parent.quit()
            sys.exit(0)

        else:
            new_exe = download_path

            try:
                if os.path.exists(single_backup_path):
                    os.remove(single_backup_path)
                shutil.copy2(current_exe, single_backup_path)
                _output(output_callback, f"已备份旧文件到：{single_backup_path}")
            except OSError as e:
                _output(output_callback, f"单文件备份失败：{e}")

            if sys.platform != 'win32':
                msg = "自动更新仅支持 Windows 系统。请手动替换文件。"
                _output_error(output_callback, msg)
                if ui_callback:
                    ui_callback.show_error("不支持的平台", msg, parent=parent)
                return False

            script_path = os.path.join(tempfile.gettempdir(), "update_script.bat")

            safe_current_exe = f'"{current_exe}"'
            safe_new_exe = f'"{new_exe}"'
            safe_single_backup = f'"{single_backup_path}"'
            exe_basename = os.path.basename(current_exe)
            current_pid = os.getpid()

            bat_content = f"""@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo 正在更新程序...
timeout /t 2 /nobreak >nul

taskkill /f /pid {current_pid} 2>nul
taskkill /f /im "{exe_basename}" 2>nul
timeout /t 2 /nobreak >nul

set COPY_OK=0
for /L %%i in (1,1,5) do (
    if !COPY_OK! equ 0 (
        copy /y {safe_new_exe} {safe_current_exe} >nul 2>&1
        if !errorlevel! equ 0 (
            set COPY_OK=1
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)

if !COPY_OK! equ 1 (
    echo 更新成功！
    start "" {safe_current_exe}
) else (
    echo 更新失败，尝试恢复备份...
    if exist {safe_single_backup} (
        copy /y {safe_single_backup} {safe_current_exe} >nul 2>&1
        start "" {safe_current_exe}
    ) else (
        echo 严重错误：更新失败且无备份。
        pause
    )
)

endlocal
del "%~f0"
"""
            with open(script_path, "w", encoding='gbk') as f:
                f.write(bat_content)

            _output(output_callback, f"已创建更新脚本：{script_path}")

            CREATE_NEW_PROCESS_GROUP = 0x00000200
            DETACHED_PROCESS = 0x00000008

            subprocess.Popen(
                [script_path],
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                shell=True
            )

            _output(output_callback, "更新脚本已启动，当前程序即将退出")

            if parent and hasattr(parent, 'quit'):
                parent.quit()
            sys.exit(0)

    except (OSError, zipfile.BadZipFile, subprocess.SubprocessError) as e:
        _output_error(output_callback, f"应用更新过程中发生错误：{e}")
        if ui_callback:
            ui_callback.show_error("更新失败", f"应用更新时出错：{e}", parent=parent)
        return False


def auto_update(parent=None, download_url=None, output_callback=None, ui_callback=None):
    if not download_url:
        msg = "下载链接无效，无法进行自动更新。"
        _output_error(output_callback, msg)
        if ui_callback:
            ui_callback.show_error("更新失败", msg, parent=parent)
        return

    temp_dir = tempfile.mkdtemp()
    file_name = os.path.basename(download_url).split('?')[0]
    if not file_name:
        file_name = "update_download"

    if 'api.github.com' in download_url:
        if '/zipball/' in download_url:
            if not file_name.endswith('.zip'):
                file_name += '.zip'
        elif '/tarball/' in download_url:
            if not file_name.endswith('.tar.gz'):
                file_name += '.tar.gz'

    dest_path = os.path.join(temp_dir, file_name)

    _output(output_callback, f"开始下载更新到：{dest_path}")

    def progress_callback(percent, status_text):
        _output(output_callback, status_text)

    if not download_file(download_url, dest_path, parent, output_callback, ui_callback=ui_callback, progress_callback=progress_callback):
        _output(output_callback, "下载失败，已打开浏览器进行手动下载")
        return

    _output(output_callback, "下载完成，开始应用更新")
    apply_update(dest_path, parent, output_callback, ui_callback=ui_callback)


def get_latest_version():
    latest, _ = fetch_latest_version()
    return latest


def check_for_updates(parent_root=None, show_no_update_msg=True, output_callback=None, ui_callback=None):
    latest, download_url = fetch_latest_version(parent_root, output_callback, ui_callback=ui_callback)

    if not latest:
        if show_no_update_msg:
            msg = "无法获取最新版本信息，请检查网络。"
            _output_error(output_callback, msg)
            if ui_callback:
                ui_callback.show_error("检查更新失败", msg, parent=parent_root)
        return False

    try:
        if is_version_greater(latest, CURRENT_VERSION):
            msg = f"发现新版本 v{latest}（当前版本 v{CURRENT_VERSION}）\n\n是否自动更新？"
            _output(output_callback, msg.replace('\n', ' '))
            confirmed = False
            if ui_callback:
                confirmed = ui_callback.ask_yes_no("软件更新", msg, parent=parent_root)
            if confirmed:
                auto_update(parent_root, download_url, output_callback, ui_callback=ui_callback)
            else:
                webbrowser.open(download_url)
            return True
        else:
            if show_no_update_msg:
                msg = f"当前已是最新版本 v{CURRENT_VERSION}"
                _output(output_callback, msg)
                if ui_callback:
                    ui_callback.show_info("检查更新", msg, parent=parent_root)
            return False
    except (ValueError, TypeError) as e:
        _output_error(output_callback, f"版本比较出错: {e}")
        if show_no_update_msg and ui_callback:
            ui_callback.show_error("错误", f"版本检查出错: {e}", parent=parent_root)
        return False


def show_version_info(ctx):
    import threading
    from modules.logger import log_error

    def check_version_thread():
        try:
            latest_version = get_latest_version()
            if latest_version:
                status = "最新版本" if CURRENT_VERSION == latest_version else "有新版本"
                msg = f"当前版本：{CURRENT_VERSION} | 最新版本：{latest_version} | {status}"
            else:
                msg = f"当前版本：{CURRENT_VERSION} | 检查更新失败"
        except (OSError, ValueError) as e:
            log_error(f"版本检查异常: {e}")
            msg = f"当前版本：1.0.0 | 检查更新失败"
        ctx.schedule_callback(lambda: ctx.set_version_info(msg))

    thread = threading.Thread(target=check_version_thread)
    thread.daemon = True
    thread.start()


def create_github_release(version, changelog, output_callback=None):
    token = get_api_token()
    if not token:
        default = get_default_token()
        if default:
            token = default
    if not token:
        _output_error(output_callback, "没有可用的 GitHub Token，无法发布 Release")
        return False

    tag_name = f"v{version}"
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"

    body = {
        "tag_name": tag_name,
        "target_commitish": "main",
        "name": tag_name,
        "body": changelog,
        "draft": False,
        "prerelease": False,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": f"ScriptManager/{CURRENT_VERSION}",
        "Content-Type": "application/json",
    }

    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except ssl.SSLError:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                result = json.loads(resp.read().decode("utf-8"))

        html_url = result.get("html_url", "")
        _output(output_callback, f"Release 发布成功: {html_url}")
        return True

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            pass
        _output_error(output_callback, f"发布 Release 失败 (HTTP {e.code}): {error_body}")
        return False
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        _output_error(output_callback, f"发布 Release 失败: {e}")
        return False
