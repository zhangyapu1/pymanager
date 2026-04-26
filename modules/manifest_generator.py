"""清单生成器 - 扫描项目文件并生成 manifest.json，用于更新时清理废弃文件。"""
import os
import json
import sys

PROTECTED_DIRS = {
    "data", "config", "logs", "backups",
    "__pycache__", ".git", ".idea", ".vscode",
    ".pytest_cache", "node_modules",
}

PROTECTED_FILES = {
    "manifest.json", "settings.json", "groups_meta.json",
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
        output_path = os.path.join(base_dir, "manifest.json")
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
