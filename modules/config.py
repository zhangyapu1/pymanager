"""全局配置 - 定义数据目录、配置目录等基础路径常量。"""
import os
import sys
from pathlib import Path

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
