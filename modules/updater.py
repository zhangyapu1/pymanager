"""
自动更新 - 检查 GitHub Releases 并提示或执行应用更新。

核心函数：
    check_for_updates(parent_root, show_no_update_msg, output_callback, ui_callback)：
        检查更新入口函数
        - 获取最新版本号和下载链接
        - 比较版本号判断是否需要更新
        - 有更新时弹出对话框让用户选择操作

    auto_update(parent, download_url, output_callback, ui_callback)：
        执行自动更新流程（下载 + 应用）

    show_version_info(ctx)：
        启动时异步检查版本并显示状态信息

    apply_update(download_path, parent, output_callback, ui_callback)：
        执行完整更新流程：
        1. 创建备份（限制 100MB）
        2. 下载新版本
        3. 解压并覆盖文件
        4. 对比 manifest.json 清理废弃文件
        5. 提示重启

依赖：modules.github_api, modules.backup_manager, modules.manifest_cleanup
"""
import os
import sys
import logging
import shutil
import tempfile
import subprocess
import zipfile

from modules.config import CURRENT_VERSION, PROTECTED_FILES
from modules.github_api import (
    PROJECT_URL,
    is_version_greater,
    fetch_latest_version,
    download_file,
    get_latest_version,
    create_github_release,
    RateLimitError,
)
from modules.backup_manager import create_backup
from modules.manifest_cleanup import cleanup_obsolete_files

logger = logging.getLogger(__name__)


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

            extract_root = extract_dir
            top_items = os.listdir(extract_dir)
            if len(top_items) == 1 and os.path.isdir(os.path.join(extract_dir, top_items[0])):
                extract_root = os.path.join(extract_dir, top_items[0])
                _output(output_callback, f"检测到单目录压缩包，使用子目录：{top_items[0]}")

            cleanup_obsolete_files(current_dir, extract_root, output_callback)

            for item in os.listdir(extract_root):
                if item in PROTECTED_FILES:
                    continue

                src = os.path.join(extract_root, item)
                dst = os.path.join(current_dir, item)

                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    if os.path.exists(dst):
                        try:
                            os.remove(dst)
                        except PermissionError:
                            for i in range(5):
                                try:
                                    os.remove(dst)
                                    break
                                except PermissionError:
                                    import time
                                    time.sleep(0.5)
                    shutil.copy2(src, dst)

            try:
                shutil.rmtree(extract_dir)
            except OSError:
                pass

            _output(output_callback, "文件覆盖完成，准备重启...")

        elif download_path.endswith('.exe'):
            shutil.copy2(current_exe, single_backup_path)
            shutil.copy2(download_path, current_exe)
            _output(output_callback, "EXE 文件已替换，准备重启...")

        else:
            _output_error(output_callback, f"不支持的更新文件格式：{download_path}")
            return False

        script_path = os.path.join(tempfile.gettempdir(), "pymanager_update.bat")
        safe_current_exe = current_exe.replace('/', '\\')
        safe_single_backup = single_backup_path.replace('/', '\\')

        bat_content = f"""@echo off
setlocal
echo 正在更新 PyManager...
timeout /t 2 /nobreak >nul

taskkill /f /im "{os.path.basename(current_exe)}" >nul 2>&1
timeout /t 1 /nobreak >nul

if exist {safe_current_exe} (
    echo 更新成功，正在启动...
    if exist {safe_single_backup} del {safe_single_backup} >nul 2>&1
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


def check_for_updates(parent_root=None, show_no_update_msg=True, output_callback=None, ui_callback=None):
    latest, download_url, changelog, release_date = fetch_latest_version(parent_root, output_callback, ui_callback=ui_callback)

    if not latest:
        if show_no_update_msg:
            msg = "无法获取最新版本信息，请检查网络。"
            _output_error(output_callback, msg)
            if ui_callback:
                ui_callback.show_error("检查更新失败", msg, parent=parent_root)
        return False

    try:
        if is_version_greater(latest, CURRENT_VERSION):
            # 构建更新信息
            msg = f"发现新版本 v{latest}（当前版本 v{CURRENT_VERSION}）"
            if release_date:
                msg += f"\n发布日期：{release_date}"
            msg += "\n\n点击「立即更新」开始自动更新，或点击「稍后再说」。"

            _output(output_callback, f"发现新版本 v{latest}")

            confirmed = False
            if ui_callback:
                confirmed = ui_callback.show_update_dialog("软件更新", msg, changelog, parent=parent_root)

            if confirmed:
                auto_update(parent_root, download_url, output_callback, ui_callback=ui_callback)
            else:
                import webbrowser
                webbrowser.open(download_url)
            return True
        else:
            if show_no_update_msg:
                msg = f"当前已是最新版本 v{CURRENT_VERSION}\n\n是否重新安装当前版本？"
                _output(output_callback, f"当前已是最新版本 v{CURRENT_VERSION}")
                confirmed = False
                if ui_callback:
                    confirmed = ui_callback.ask_yes_no("检查更新", msg, parent=parent_root)
                if confirmed:
                    auto_update(parent_root, download_url, output_callback, ui_callback=ui_callback)
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
