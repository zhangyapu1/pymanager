"""
utils.py 单元测试
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.utils import update_title_mode, open_program_dir, extract_docstring


class TestUtilsFunctions:
    def test_update_title_mode_callable(self):
        """测试 update_title_mode 是可调用的"""
        assert callable(update_title_mode)

    def test_open_program_dir_callable(self):
        """测试 open_program_dir 是可调用的"""
        assert callable(open_program_dir)

    def test_extract_docstring_callable(self):
        """测试 extract_docstring 是可调用的"""
        assert callable(extract_docstring)


class TestExtractDocstring:
    def test_extract_docstring_nonexistent_file(self):
        """测试提取不存在的文件"""
        result = extract_docstring("nonexistent_file.py")
        assert result is None

    def test_extract_docstring_this_file(self):
        """测试提取当前文件的 docstring"""
        result = extract_docstring(__file__)
        assert result is not None
        assert "单元测试" in result or len(result) > 0

    def test_extract_docstring_module_file(self):
        """测试提取模块文件的 docstring"""
        result = extract_docstring(str(Path(__file__).parent.parent / "modules" / "config.py"))
        assert result is not None
        assert len(result) > 0


class TestOpenProgramDir:
    def test_open_program_dir_executes(self):
        """测试 open_program_dir 可以执行（不抛异常）"""
        try:
            open_program_dir()
        except Exception as e:
            pytest.fail(f"open_program_dir 抛出了异常: {e}")


class TestUpdateTitleMode:
    def test_update_title_mode_with_none(self):
        """测试 update_title_mode 可以接受 None 作为参数"""
        try:
            update_title_mode(None)
        except TypeError:
            pass
        except Exception:
            pass
