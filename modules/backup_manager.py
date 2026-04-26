"""
备份管理 - 更新前创建项目备份，自动清理过期备份。

常量：
    BACKUP_RETENTION_DAYS - 备份保留天数 30
    MAX_BACKUP_FILE_SIZE  - 备份文件最大大小 100MB

核心函数：
    create_backup(output_callback)：
        创建项目目录的 zip 备份
        - 排除 backups/ 和 __pycache__/ 目录
        - 跳过超过 100MB 的大文件
        - 跳过权限不足的文件
        - 同一天多次备份自动编号
        - 创建后自动清理过期备份

    cleanup_old_backups(backup_dir, output_callback)：
        清理超过保留天数的备份文件
"""
import os
import sys
import logging
import zipfile
import datetime
import glob

logger = logging.getLogger(__name__)

BACKUP_RETENTION_DAYS = 30
MAX_BACKUP_FILE_SIZE = 100 * 1024 * 1024


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
