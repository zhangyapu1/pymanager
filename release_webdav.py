#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布新版本到 WebDAV
使用方式：
    python release_webdav.py
"""

import os
import sys
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from modules.config import CURRENT_VERSION, PROTECTED_DIRS, PROTECTED_FILES, CONFIG_DIR
from modules.github_api import (
    WEBDAV_URL,
    webdav_upload_file,
    _output,
    _output_error
)


def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


def print_info(msg):
    print(f"[INFO] {msg}")


def print_error(msg):
    print(f"[ERROR] {msg}")


def ask_yes_no(question, default="y"):
    valid = {"y": True, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "y":
        prompt = " [Y/n] "
    elif default == "n":
        prompt = " [y/N] "
    else:
        raise ValueError(f"无效的默认值: {default}")

    while True:
        choice = input(question + prompt).lower()
        if default is not None and choice == "":
            return valid[default]
        if choice in valid:
            return valid[choice]
        print("请输入 'y' 或 'n'。")


def should_exclude(path):
    """检查路径是否应该排除"""
    path_str = str(path)
    parts = path_str.split(os.sep)

    # 检查受保护的目录
    for dir_name in PROTECTED_DIRS:
        if dir_name in parts:
            return True

    # 检查受保护的文件
    for file_name in PROTECTED_FILES:
        if path.name == file_name:
            return True

    # 检查扩展名
    for ext in ['.pyc', '.pyo', '.log', '.tmp']:
        if path_str.endswith(ext):
            return True

    return False


def build_release_zip(version):
    """构建发布 ZIP 包"""
    zip_filename = f"pymanager-{version}.zip"
    zip_path = BASE_DIR / zip_filename

    print_header("构建发布包")
    print_info(f"版本: {version}")
    print_info(f"文件: {zip_path}")

    if zip_path.exists():
        print_info("删除旧的 ZIP 文件...")
        zip_path.unlink()

    # 创建 ZIP 包
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(BASE_DIR):
            # 移除受保护的目录（避免继续遍历）
            dirs[:] = [d for d in dirs if d not in PROTECTED_DIRS]

            for file_name in files:
                file_path = Path(root) / file_name
                if should_exclude(file_path):
                    continue

                # 计算在 ZIP 中的相对路径
                arcname = str(file_path.relative_to(BASE_DIR))
                zf.write(file_path, arcname)
                print(f"  + {arcname}")

    file_size = zip_path.stat().st_size
    print_info(f"\nZIP 文件大小: {file_size / (1024*1024):.2f} MB")
    return str(zip_path)


def create_version_json(version, zip_filename, changelog=""):
    """创建 version.json 文件"""
    version_data = {
        "version": version,
        "downloadUrl": zip_filename,
        "releaseDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "changelog": changelog
    }

    json_path = BASE_DIR / "version.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, ensure_ascii=False, indent=2)

    print_info(f"创建版本文件: {json_path}")
    return str(json_path)


def ask_for_changelog():
    """询问用户更新内容"""
    print_header("更新内容")
    print("请输入本次更新的内容（多行输入，输入空行结束）：")
    print("例如：")
    print("  • 新增功能A")
    print("  • 修复问题B")
    print("  • 优化性能C")
    print()

    lines = []
    while True:
        try:
            line = input()
            if line == "":
                break
            lines.append(line)
        except EOFError:
            break

    changelog = "\n".join(lines).strip()
    if changelog:
        print_info(f"更新内容已录入 ({len(changelog)} 字符)")
    else:
        print_info("未输入更新内容")
    return changelog


def upload_to_webdav(local_path, remote_name):
    """上传文件到 WebDAV"""
    print_header(f"上传 {remote_name}")
    success = webdav_upload_file(local_path, remote_name, output_callback=print)
    return success


def main():
    print_header("pymanager 发布工具")

    current_version = CURRENT_VERSION
    print_info(f"当前版本: {current_version}")

    # 询问版本号
    new_version = input(f"请输入新版本号 (默认: {current_version}): ").strip()
    if not new_version:
        new_version = current_version

    # 询问更新内容
    changelog = ask_for_changelog()

    # 确认发布
    if not ask_yes_no(f"确认发布版本 {new_version}?", default="y"):
        print_info("发布已取消")
        return

    try:
        # 步骤1: 构建 ZIP 包
        zip_path = build_release_zip(new_version)
        zip_filename = os.path.basename(zip_path)

        # 步骤2: 创建 version.json
        version_json_path = create_version_json(new_version, zip_filename, changelog)

        # 步骤3: 上传到 WebDAV
        print_header("上传到 WebDAV")
        print_info(f"WebDAV URL: {WEBDAV_URL}")

        # 上传 version.json
        print_info("\n上传 version.json...")
        if not upload_to_webdav(version_json_path, "version.json"):
            print_error("上传 version.json 失败")
            return

        # 上传 ZIP 包
        print_info("\n上传 ZIP 包...")
        if not upload_to_webdav(zip_path, zip_filename):
            print_error("上传 ZIP 包失败")
            return

        # 完成
        print_header("发布成功!")
        print_info(f"版本: {new_version}")
        print_info(f"ZIP 文件: {zip_path}")
        print_info(f"WebDAV: {WEBDAV_URL}")
        print_info("\n用户可以通过'检查更新'功能获取新版本")

    except KeyboardInterrupt:
        print_info("\n发布已取消")
    except Exception as e:
        print_error(f"发布失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
