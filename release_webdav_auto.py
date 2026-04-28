#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动发布新版本到 WebDAV（非交互式版本）
使用方式：
    python release_webdav_auto.py [version] [changelog_file]
示例：
    python release_webdav_auto.py
    python release_webdav_auto.py 1.9.0
    python release_webdav_auto.py 1.9.0 changelog.txt
"""

import os
import sys
import json
import zipfile
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from modules.config import CURRENT_VERSION, PROTECTED_DIRS, PROTECTED_FILES
from modules.github_api import (
    WEBDAV_URL,
    webdav_upload_file,
    _output,
    _output_error
)


def print_info(msg):
    print(f"[INFO] {msg}")


def print_error(msg):
    print(f"[ERROR] {msg}")


def read_changelog_from_file(filepath):
    """从文件读取更新内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print_error(f"无法读取更新内容文件 {filepath}: {e}")
        return ""


def get_file_list_from_manifest():
    """从 manifest.json 获取文件列表"""
    manifest_path = BASE_DIR / "modules" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json 不存在: {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    return manifest.get("files", [])


def build_release_zip(version):
    """构建发布 ZIP 包"""
    zip_filename = f"pymanager-{version}.zip"
    zip_path = BASE_DIR / zip_filename

    print_info(f"构建发布包: {version}")

    if zip_path.exists():
        print_info("删除旧的 ZIP 文件...")
        zip_path.unlink()

    # 从 manifest 获取文件列表
    file_list = get_file_list_from_manifest()
    print_info(f"文件数: {len(file_list)}")

    # 创建 ZIP 包
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel_path in file_list:
            # 额外排除 .zip 文件
            if rel_path.endswith('.zip'):
                continue
            full_path = BASE_DIR / rel_path
            if not full_path.exists():
                print_info(f"[警告] 文件不存在: {rel_path}")
                continue
            zf.write(full_path, rel_path)
            print(f"  + {rel_path}")

    file_size = zip_path.stat().st_size
    print_info(f"ZIP 文件大小: {file_size / (1024*1024):.2f} MB")
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


def upload_to_webdav(local_path, remote_name):
    """上传文件到 WebDAV"""
    print_info(f"上传 {remote_name}...")
    success = webdav_upload_file(local_path, remote_name, output_callback=print)
    return success


def main():
    print("="*60)
    print("  pymanager 自动发布工具")
    print("="*60)

    version = CURRENT_VERSION
    changelog = ""

    # 解析命令行参数
    if len(sys.argv) >= 2:
        version = sys.argv[1]
        print_info(f"使用指定版本: {version}")
    else:
        print_info(f"当前版本: {version}")

    if len(sys.argv) >= 3:
        changelog_file = sys.argv[2]
        changelog = read_changelog_from_file(changelog_file)
        if changelog:
            print_info(f"已读取更新内容 ({len(changelog)} 字符)")

    try:
        # 步骤0: 更新 manifest.json
        print()
        print_info("更新 manifest.json...")
        from modules.manifest_generator import write_manifest
        write_manifest()

        # 步骤1: 构建 ZIP 包
        print()
        zip_path = build_release_zip(version)
        zip_filename = os.path.basename(zip_path)

        # 步骤2: 创建 version.json
        print()
        version_json_path = create_version_json(version, zip_filename, changelog)

        # 步骤3: 上传到 WebDAV
        print()
        print_info(f"WebDAV URL: {WEBDAV_URL}")

        # 上传 version.json
        print()
        if not upload_to_webdav(version_json_path, "version.json"):
            print_error("上传 version.json 失败")
            return 1

        # 上传 ZIP 包
        print()
        if not upload_to_webdav(zip_path, zip_filename):
            print_error("上传 ZIP 包失败")
            return 1

        # 完成
        print()
        print("="*60)
        print("  发布成功!")
        print("="*60)
        print_info(f"版本: {version}")
        print_info(f"ZIP 文件: {zip_path}")
        print_info(f"WebDAV: {WEBDAV_URL}")
        print_info("\n用户可以通过'检查更新'功能获取新版本")

        return 0

    except Exception as e:
        print_error(f"发布失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
