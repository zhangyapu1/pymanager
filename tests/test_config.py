import os
import pytest
from modules.config import get_base_dir, DATA_DIR, CONFIG_DIR, DEFAULT_GROUP


def test_get_base_dir():
    base = get_base_dir()
    assert os.path.isdir(base)


def test_data_dir_exists():
    assert os.path.isdir(DATA_DIR)


def test_config_dir_exists():
    assert os.path.isdir(CONFIG_DIR)


def test_default_group():
    assert DEFAULT_GROUP == "默认分组"


def test_data_dir_is_subdir():
    assert DATA_DIR.endswith("data") or "data" in DATA_DIR


def test_config_dir_is_subdir():
    assert CONFIG_DIR.endswith("config") or "config" in CONFIG_DIR
