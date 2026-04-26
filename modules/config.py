"""
全局配置 - 定义版本号、数据目录、配置目录等基础路径常量，并在启动时自动创建。

常量：
    CURRENT_VERSION：
        当前版本号，所有模块统一引用此值

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
from pathlib import Path

CURRENT_VERSION = "1.8.3"

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
