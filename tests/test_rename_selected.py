import os
import pytest
from modules.rename_selected import _sanitize_filename, _generate_unique_path


def test_sanitize_filename_normal():
    assert _sanitize_filename("hello.py") == "hello.py"


def test_sanitize_filename_illegal_chars():
    result = _sanitize_filename('file<>:"/\\|?*.py')
    for ch in '<>:"/\\|?*':
        assert ch not in result


def test_sanitize_filename_dots():
    result = _sanitize_filename("...test...")
    assert not result.startswith('.')
    assert not result.endswith('.')


def test_sanitize_filename_empty():
    result = _sanitize_filename("")
    assert result == "unnamed"


def test_sanitize_filename_only_dots():
    result = _sanitize_filename("...")
    assert result == "unnamed"


def test_sanitize_filename_chinese():
    result = _sanitize_filename("中文脚本.py")
    assert result == "中文脚本.py"


def test_generate_unique_path_no_conflict(tmp_path):
    original = str(tmp_path / "script.py")
    result = _generate_unique_path(str(tmp_path), "script", ".py", original)
    assert result == os.path.join(str(tmp_path), "script.py")


def test_generate_unique_path_one_conflict(tmp_path):
    original = str(tmp_path / "script.py")
    (tmp_path / "other.py").write_text("existing")
    (tmp_path / "script.py").write_text("existing")
    result = _generate_unique_path(str(tmp_path), "new_script", ".py", original)
    assert result == os.path.join(str(tmp_path), "new_script.py")


def test_generate_unique_path_same_as_original(tmp_path):
    original = str(tmp_path / "script.py")
    (tmp_path / "script.py").write_text("existing")
    result = _generate_unique_path(str(tmp_path), "script", ".py", original)
    assert os.path.realpath(result) == os.path.realpath(original) or result.endswith("script_1.py")
