import pytest
from modules.dependencies import DependencyChecker


def test_is_stdlib_module_os():
    assert DependencyChecker.is_stdlib_module("os") is True


def test_is_stdlib_module_sys():
    assert DependencyChecker.is_stdlib_module("sys") is True


def test_is_stdlib_module_json():
    assert DependencyChecker.is_stdlib_module("json") is True


def test_is_stdlib_module_collections():
    assert DependencyChecker.is_stdlib_module("collections") is True


def test_is_stdlib_module_threading():
    assert DependencyChecker.is_stdlib_module("threading") is True


def test_is_stdlib_module_pandas():
    assert DependencyChecker.is_stdlib_module("pandas") is False


def test_is_stdlib_module_numpy():
    assert DependencyChecker.is_stdlib_module("numpy") is False


def test_is_stdlib_module_requests():
    assert DependencyChecker.is_stdlib_module("requests") is False


def test_is_stdlib_module_nonexistent():
    assert DependencyChecker.is_stdlib_module("xyz_nonexistent_pkg_12345") is False


def test_extract_imports_from_script(tmp_path):
    script = tmp_path / "test.py"
    script.write_text("import os\nimport json\nimport pandas\n", encoding="utf-8")
    result = DependencyChecker.extract_imports_from_script(str(script))
    assert "os" in result
    assert "json" in result
    assert "pandas" in result


def test_extract_imports_from_script_from_import(tmp_path):
    script = tmp_path / "test.py"
    script.write_text("from collections import OrderedDict\nfrom os.path import join\n", encoding="utf-8")
    result = DependencyChecker.extract_imports_from_script(str(script))
    assert "collections" in result
    assert "os" in result


def test_extract_imports_from_script_nonexistent():
    result = DependencyChecker.extract_imports_from_script("/nonexistent/script.py")
    assert result == set()


def test_extract_imports_from_script_empty(tmp_path):
    script = tmp_path / "empty.py"
    script.write_text("", encoding="utf-8")
    result = DependencyChecker.extract_imports_from_script(str(script))
    assert result == set()
