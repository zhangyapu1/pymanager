import os
import pytest
from modules.script_manager import resolve_path, get_unique_path


def test_resolve_path_relative():
    result = resolve_path("/data", "script.py")
    assert result == os.path.join("/data", "script.py")


def test_resolve_path_relative_with_subdir():
    result = resolve_path("/data", "group/script.py")
    expected = os.path.normpath(os.path.join("/data", "group", "script.py"))
    assert os.path.normpath(result) == expected


def test_resolve_path_absolute():
    result = resolve_path("/data", "/absolute/path/script.py")
    assert result == "/absolute/path/script.py"


def test_resolve_path_absolute_windows():
    result = resolve_path("C:\\data", "D:\\other\\script.py")
    assert result == "D:\\other\\script.py"


def test_get_unique_path_no_conflict(tmp_path):
    result = get_unique_path(str(tmp_path), "script.py")
    assert result == os.path.join(str(tmp_path), "script.py")


def test_get_unique_path_one_conflict(tmp_path):
    (tmp_path / "script.py").write_text("existing")
    result = get_unique_path(str(tmp_path), "script.py")
    assert result == os.path.join(str(tmp_path), "script_1.py")


def test_get_unique_path_multiple_conflicts(tmp_path):
    (tmp_path / "script.py").write_text("existing")
    (tmp_path / "script_1.py").write_text("existing")
    result = get_unique_path(str(tmp_path), "script.py")
    assert result == os.path.join(str(tmp_path), "script_2.py")


def test_get_unique_path_different_name(tmp_path):
    (tmp_path / "other.py").write_text("existing")
    result = get_unique_path(str(tmp_path), "script.py")
    assert result == os.path.join(str(tmp_path), "script.py")
