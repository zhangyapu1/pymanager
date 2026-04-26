"""
清单生成器 - 扫描项目文件并生成 manifest.json，用于更新时对比清理废弃文件。

工作原理：
    1. 扫描项目目录下所有文件，生成相对路径列表
    2. 排除受保护目录和文件（data/、config/、用户配置等）
    3. 从 updater.py 读取当前版本号
    4. 输出 JSON 格式的清单文件到 config/manifest.json

常量：
    PROTECTED_DIRS - 受保护目录集合，扫描时跳过
        data, config, logs, backups, __pycache__, .git, .idea, .vscode,
        .pytest_cache, node_modules, .trae, tests

    PROTECTED_FILES - 受保护文件集合，不纳入清单
        manifest.json, settings.json, groups_meta.json,
        .gitignore, REQUIREMENTS.md

    SKIP_EXTENSIONS - 跳过的文件扩展名
        .pyc, .pyo, .log, .tmp

函数：
    should_skip(rel_path)：
        判断文件是否应跳过（受保护目录/文件/扩展名）

    generate_manifest(base_dir=None)：
        生成清单字典 {"version": "x.x.x", "files": [...]}
        base_dir 默认为项目根目录

    write_manifest(base_dir=None, output_path=None)：
        生成并写入 config/manifest.json 文件
        返回输出文件路径

    _read_version(base_dir)：
        从 modules/updater.py 读取 CURRENT_VERSION 值

命令行用法：
    python -m modules.manifest_generator [base_dir]

更新流程中的使用：
    1. 发布新版本前运行生成 config/manifest.json
    2. 更新时下载新版本清单
    3. 对比本地清单与新清单，删除新版本中不存在的文件

依赖：json, os
"""
import os
import json
import sys

PROTECTED_DIRS = {
    "data", "config", "logs", "backups",
    "__pycache__", ".git", ".idea", ".vscode",
    ".pytest_cache", "node_modules",
    ".trae", "tests",
}

PROTECTED_FILES = {
    "manifest.json", "settings.json", "groups_meta.json",
    ".gitignore", "REQUIREMENTS.md",
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".log", ".tmp",
}


def should_skip(rel_path):
    parts = rel_path.replace("\\", "/").split("/")
    for p in parts:
        if p in PROTECTED_DIRS:
            return True
    name = os.path.basename(rel_path)
    if name in PROTECTED_FILES:
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
    updater_path = os.path.join(base_dir, "modules", "updater.py")
    if not os.path.exists(updater_path):
        return "unknown"
    try:
        with open(updater_path, "r", encoding="utf-8") as f:
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
