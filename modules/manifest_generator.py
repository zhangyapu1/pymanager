"""
清单生成器 - 扫描项目文件并生成 manifest.json，用于更新时对比清理废弃文件。

工作原理：
    1. 扫描项目目录下所有文件，生成相对路径列表
    2. 排除受保护目录和文件（规则统一在 config.py 中定义）
    3. 从 config.py 读取当前版本号
    4. 输出 JSON 格式的清单文件到 modules/manifest.json

函数：
    should_skip(rel_path)：
        判断文件是否应跳过（受保护目录/文件/扩展名）

    generate_manifest(base_dir=None)：
        生成清单字典 {"version": "x.x.x", "files": [...]}
        base_dir 默认为项目根目录

    write_manifest(base_dir=None, output_path=None)：
        生成并写入 modules/manifest.json 文件
        返回输出文件路径

    _read_version(base_dir)：
        从 modules/config.py 读取 CURRENT_VERSION 值

命令行用法：
    python -m modules.manifest_generator [base_dir]

依赖：json, os, modules.config
"""
import os
import json
import sys

if __name__ == "__main__":
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)

from modules.config import (
    PROTECTED_DIRS, PROTECTED_FILES, ROOT_PROTECTED_FILES, SKIP_EXTENSIONS,
)


def should_skip(rel_path):
    parts = rel_path.replace("\\", "/").split("/")
    for p in parts:
        if p in PROTECTED_DIRS:
            return True
    name = os.path.basename(rel_path)
    if name in PROTECTED_FILES:
        return True
    if name in ROOT_PROTECTED_FILES and len(parts) == 1:
        return True
    _, ext = os.path.splitext(name)
    if ext.lower() in SKIP_EXTENSIONS:
        return True
    return False


def generate_manifest(base_dir=None):
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        parent = os.path.dirname(base_dir)
        if os.path.basename(base_dir) == "modules":
            base_dir = parent

    files = []
    for root, dirs, filenames in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in PROTECTED_DIRS]
        for f in filenames:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, base_dir).replace("\\", "/")
            if should_skip(rel):
                continue
            files.append(rel)

    files.sort()

    manifest = {
        "version": _read_version(base_dir),
        "files": files,
    }
    return manifest


def _read_version(base_dir):
    filepath = os.path.join(base_dir, "modules", "config.py")
    if not os.path.exists(filepath):
        return "unknown"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("CURRENT_VERSION"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return "unknown"


def write_manifest(base_dir=None, output_path=None):
    manifest = generate_manifest(base_dir)
    if output_path is None:
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            parent = os.path.dirname(base_dir)
            if os.path.basename(base_dir) == "modules":
                base_dir = parent
        modules_dir = os.path.join(base_dir, "modules")
        os.makedirs(modules_dir, exist_ok=True)
        output_path = os.path.join(modules_dir, "manifest.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return output_path


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else None
    path = write_manifest(base)
    m = generate_manifest(base)
    print(f"清单已生成: {path}")
    print(f"版本: {m['version']}")
    print(f"文件数: {len(m['files'])}")
