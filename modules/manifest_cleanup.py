"""
清单清理 - 更新时对比新旧 manifest.json，清理废弃文件和空目录。

核心函数：
    cleanup_obsolete_files(current_dir, new_extract_dir, output_callback)：
        对比新旧 manifest.json 清理废弃文件
        - 强制删除 .trae/、tests/ 目录
        - 强制删除 .gitignore、REQUIREMENTS.md、旧路径 manifest.json
        - 对比新旧清单差异，删除旧版有而新版没有的文件
        - 保护 data/、config/、logs/ 等用户数据目录
        - 循环清理空目录（最多 10 轮）

辅助函数：
    load_manifest(directory)：
        从目录中加载 manifest.json
        - 按优先级查找：modules/ → config/ → 根目录
"""
import os
import json
import shutil
import logging

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


def load_manifest(directory):
    manifest_path = os.path.join(directory, "modules", "manifest.json")
    if not os.path.exists(manifest_path):
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


def cleanup_obsolete_files(current_dir, new_extract_dir, output_callback=None):
    old_manifest = load_manifest(current_dir)
    new_manifest = load_manifest(new_extract_dir)

    force_remove_dirs = {".trae", "tests"}
    force_remove_files = {".gitignore", "REQUIREMENTS.md", "manifest.json", "config/manifest.json"}

    removed = 0
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

    if old_manifest is None or new_manifest is None:
        _output(output_callback, "缺少清单文件，跳过废弃文件清理")
        return

    old_files = set(old_manifest.get("files", []))
    new_files = set(new_manifest.get("files", []))

    obsolete = old_files - new_files

    protected_dirs = {"data", "config", "logs", "backups", "__pycache__", ".git", ".idea", ".vscode"}
    protected_files = {"settings.json", "groups_meta.json"}

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
