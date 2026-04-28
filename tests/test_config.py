"""
config.py 单元测试
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config import (
    CURRENT_VERSION,
    BASE_DIR,
    DATA_DIR,
    CONFIG_DIR,
    PROTECTED_DIRS,
    PROTECTED_FILES,
    SKIP_EXTENSIONS,
    FORCE_REMOVE_DIRS,
    FORCE_REMOVE_FILES,
)


class TestConfigConstants:
    def test_version_format(self):
        """测试版本号格式"""
        assert isinstance(CURRENT_VERSION, str)
        parts = CURRENT_VERSION.split('.')
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit(), f"版本号部分 {part} 应为数字"

    def test_version_is_reasonable(self):
        """测试版本号是否合理"""
        major, minor, patch = CURRENT_VERSION.split('.')
        assert int(major) >= 1, "主版本号应 >= 1"
        assert 0 <= int(minor) < 100, "次版本号应在 0-99 之间"
        assert 0 <= int(patch) < 100, "补丁版本号应在 0-99 之间"

    def test_base_dir_exists(self):
        """测试 BASE_DIR 是否存在"""
        assert os.path.exists(BASE_DIR), f"BASE_DIR {BASE_DIR} 不存在"

    def test_data_dir_under_base(self):
        """测试 DATA_DIR 是否在 BASE_DIR 下"""
        assert str(DATA_DIR).startswith(str(BASE_DIR)), "DATA_DIR 应在 BASE_DIR 下"

    def test_config_dir_under_base(self):
        """测试 CONFIG_DIR 是否在 BASE_DIR 下"""
        assert str(CONFIG_DIR).startswith(str(BASE_DIR)), "CONFIG_DIR 应在 BASE_DIR 下"

    def test_protected_dirs_contains_standard(self):
        """测试 PROTECTED_DIRS 是否包含标准目录"""
        expected = {"data", "config", "logs", "__pycache__", ".git"}
        for d in expected:
            assert d in PROTECTED_DIRS, f"PROTECTED_DIRS 应包含 {d}"

    def test_protected_files_contains_standard(self):
        """测试 PROTECTED_FILES 是否包含标准文件"""
        expected = {".gitignore", "settings.json", "groups_meta.json"}
        for f in expected:
            assert f in PROTECTED_FILES, f"PROTECTED_FILES 应包含 {f}"

    def test_skip_extensions_format(self):
        """测试 SKIP_EXTENSIONS 格式"""
        for ext in SKIP_EXTENSIONS:
            assert ext.startswith('.'), f"扩展名 {ext} 应以 . 开头"

    def test_force_remove_dirs(self):
        """测试 FORCE_REMOVE_DIRS 非空"""
        assert len(FORCE_REMOVE_DIRS) > 0, "FORCE_REMOVE_DIRS 不应为空"

    def test_force_remove_files(self):
        """测试 FORCE_REMOVE_FILES 非空"""
        assert len(FORCE_REMOVE_FILES) > 0, "FORCE_REMOVE_FILES 不应为空"


class TestConfigInitialization:
    def test_data_dir_creatable(self):
        """测试 DATA_DIR 可以被创建（如果不存在）"""
        data_dir = Path(DATA_DIR)
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
        assert data_dir.exists()

    def test_config_dir_creatable(self):
        """测试 CONFIG_DIR 可以被创建（如果不存在）"""
        config_dir = Path(CONFIG_DIR)
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
        assert config_dir.exists()
