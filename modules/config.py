"""
全局配置 - 定义版本号、数据目录、配置目录等基础路径常量，并在启动时自动创建。

常量：
    CURRENT_VERSION：
        当前版本号，所有模块统一引用此值

    PROTECTED_DIRS：
        发布排除目录集合，扫描/复制/清理时跳过
        data, config, logs, backups, __pycache__, .git, .idea, .vscode,
        .pytest_cache, node_modules, .trae, tests

    PROTECTED_FILES：
        发布排除文件集合，不纳入清单、不复制到用户目录
        settings.json, groups_meta.json, .gitignore, REQUIREMENTS.md

    FORCE_REMOVE_DIRS：
        更新时强制删除的目录
        .trae, tests

    FORCE_REMOVE_FILES：
        更新时强制删除的文件
        .gitignore, REQUIREMENTS.md, manifest.json, config/manifest.json

    SKIP_EXTENSIONS：
        跳过的文件扩展名
        .pyc, .pyo, .log, .tmp

    BASE_DIR：
        项目根目录。打包运行时取可执行文件所在目录，
        开发运行时取 modules 的父目录

    DATA_DIR：
        脚本数据目录，路径为 BASE_DIR/data/
        用于存放用户脚本文件，按分组组织子目录

    CONFIG_DIR：
        配置目录，路径为 BASE_DIR/config/
        用于存放 settings.json、groups_meta.json 等配置文件

    DATA_DIR_NAME  - 数据目录名 "data"
    CONFIG_DIR_NAME- 配置目录名 "config"
    DEFAULT_GROUP  - 默认分组名 "默认分组"

初始化行为：
    模块加载时自动创建 DATA_DIR 和 CONFIG_DIR（如不存在）
    创建失败时抛出 OSError

依赖：pathlib
"""
import os
import sys
import json
from pathlib import Path

CURRENT_VERSION = "1.9.1"

PROTECTED_DIRS = {
    "data", "config", "logs", "backups",
    "__pycache__", ".git", ".idea", ".vscode",
    ".pytest_cache", "node_modules",
    ".trae", "tests",
}

PROTECTED_FILES = {
    "settings.json", "groups_meta.json",
    ".gitignore", "REQUIREMENTS.md",
    "release.py", "release_auto.py",
    "version.json", "changelog.txt",
}

FORCE_REMOVE_DIRS = {
    ".trae", "tests",
}

FORCE_REMOVE_FILES = {
    ".gitignore", "REQUIREMENTS.md",
    "manifest.json", "config/manifest.json",
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".log", ".tmp",
}

ROOT_PROTECTED_FILES = {
    "manifest.json",
}

# 脚本市场配置
SCRIPT_MARKET_CONFIG = {
    # 搜索配置
    "search": {
        "per_page": 30,
        "max_pages": 1,
        "timeout": 30,
        "sort": "stars",
        "order": "desc",
    },
    # 下载配置
    "download": {
        "timeout": 60,
        "chunk_size": 1024 * 1024,  # 1MB
        "max_retries": 3,
    },
    # 预览配置
    "preview": {
        "max_readme_size": 1024 * 1024,  # 1MB
        "max_translate_size": 5000,  # 5KB
    },
    # 缓存配置
    "cache": {
        "enabled": True,
        "max_history": 50,
        "expiry_days": 7,
    },
    # 本地服务配置
    "local_service": {
        "url": "http://localhost:8080/v1/chat/completions",
        "default_model": "DeepSeek-V3.2",
        "timeout": 30,
    },
}

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return str(Path(sys.executable).parent)
    current_file = Path(__file__).resolve().parent
    base_dir = current_file.parent
    return str(base_dir)

DATA_DIR_NAME = "data"
CONFIG_DIR_NAME = "config"
DEFAULT_GROUP = "默认分组"

BASE_DIR = get_base_dir()
DATA_DIR = str(Path(BASE_DIR) / DATA_DIR_NAME)
CONFIG_DIR = str(Path(BASE_DIR) / CONFIG_DIR_NAME)

try:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
except OSError as e:
    raise e

try:
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
except OSError as e:
    raise e

# 统一配置文件
APP_CONFIG_FILE = str(Path(CONFIG_DIR) / "app_config.json")
DEFAULT_APP_CONFIG = {
    # ==================== GitHub 相关配置 ====================
    "github": {
        # GitHub Personal Access Token（明文存储，用于提高 API 访问额度
        # 获取方式：https://github.com/settings/tokens → Generate new token
        # 权限建议：repo（读取权限）
        "token": "",
        
        # GitHub Token 的加密版本（使用 Windows DPAPI 加密，仅当前用户可解密）
        "encrypted_token": ""
    },
    
    # ==================== AI 服务相关配置 ====================
    "ai": {
        # 当前使用的 AI 服务提供商
        # 可选值："通义千问 (Qwen)"、"智谱AI (GLM-4-Flash)"、"DeepSeek"、"本地服务 (127.0.0.1:8080)"
        "provider": "通义千问 (Qwen)",
        
        # AI 服务的 API Key（加密存储）
        # 格式：{"服务商名称": "加密后的 API Key"}
        "keys": {},
        
        # 本地服务使用的模型名称（仅对"本地服务"时有效）
        # 例如："DeepSeek-V3.2"、"Qwen3.5-Plus"
        "local_model": "DeepSeek-V3.2"
    },
    
    # ==================== 窗口相关配置 ====================
    "window": {
        # 窗口宽度（像素）
        "width": 950,
        
        # 窗口高度（像素）
        "height": 600,
        
        # 窗口左上角 X 坐标（像素），None 表示居中
        "x": None,
        
        # 窗口左上角 Y 坐标（像素），None 表示居中
        "y": None
    },
    
    # ==================== 日志相关配置 ====================
    "log": {
        # 日志保留天数（超过此天数的日志文件会被自动清理
        "retain_days": 7,
        
        # 单个日志文件最大大小（MB），超过会自动截断
        "max_file_size_mb": 1
    },
    
    # ==================== 收藏夹相关配置 ====================
    "favorites": [],
    
    # ==================== 脚本图标相关配置 ====================
    "script_icons": {},
    
    # ==================== 最近运行相关配置 ====================
    "recent_runs": {},
    
    # ==================== 分组元数据相关配置 ====================
    "groups_meta": {},
    
    # ==================== 翻译服务相关配置 ====================
    "translate": {
        # 当前使用的翻译服务商
        # 可选值："Google翻译"、"百度翻译"、"腾讯翻译君"
        "provider": "Google翻译",
        
        # 翻译服务的 API Key（加密存储）
        # 格式：{"密钥名称": "加密后的密钥"}
        "keys": {}
    }
}

def load_app_config():
    """加载统一配置文件"""
    config = _deep_copy_dict(DEFAULT_APP_CONFIG)
    try:
        if Path(APP_CONFIG_FILE).exists():
            with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # 深度合并配置
            _deep_merge_dict(config, loaded)
    except Exception:
        pass
    return config

def save_app_config(config):
    """保存统一配置文件"""
    try:
        with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def _deep_copy_dict(src):
    """深度复制字典"""
    if not isinstance(src, dict):
        return src
    result = {}
    for k, v in src.items():
        if isinstance(v, dict):
            result[k] = _deep_copy_dict(v)
        elif isinstance(v, list):
            result[k] = v.copy()
        else:
            result[k] = v
    return result

def _deep_merge_dict(target, source):
    """深度合并字典，target 会被修改"""
    for k, v in source.items():
        if k in target and isinstance(target[k], dict) and isinstance(v, dict):
            _deep_merge_dict(target[k], v)
        else:
            target[k] = v

