import pytest
from modules.utils import extract_docstring


@pytest.fixture
def write_tmp_py(tmp_path):
    def _write(content):
        f = tmp_path / "test_script.py"
        f.write_text(content, encoding="utf-8")
        return str(f)
    return _write


def test_triple_quote_docstring(write_tmp_py):
    path = write_tmp_py('"""这是文档字符串"""\nprint("hello")\n')
    assert extract_docstring(path) == "这是文档字符串"


def test_single_quote_docstring(write_tmp_py):
    path = write_tmp_py("'''这是文档字符串'''\nprint('hello')\n")
    assert extract_docstring(path) == "这是文档字符串"


def test_multiline_docstring(write_tmp_py):
    path = write_tmp_py('"""第一行\n第二行\n第三行"""\nprint("hello")\n')
    result = extract_docstring(path)
    assert "第一行" in result
    assert "第二行" in result
    assert "第三行" in result


def test_hash_comments_only(write_tmp_py):
    path = write_tmp_py("# 这是注释\n# 第二行注释\nprint('hello')\n")
    result = extract_docstring(path)
    assert "这是注释" in result
    assert "第二行注释" in result


def test_hash_comments_before_code(write_tmp_py):
    path = write_tmp_py("# 文件头注释\nimport os\n")
    result = extract_docstring(path)
    assert result == "文件头注释"


def test_no_docstring(write_tmp_py):
    path = write_tmp_py('import os\nprint("hello")\n')
    assert extract_docstring(path) is None


def test_file_not_exists():
    assert extract_docstring("/nonexistent/file.py") is None


def test_empty_file(write_tmp_py):
    path = write_tmp_py("")
    assert extract_docstring(path) is None


def test_only_hash_comments_no_code(write_tmp_py):
    path = write_tmp_py("# 注释1\n# 注释2\n")
    result = extract_docstring(path)
    assert "注释1" in result
    assert "注释2" in result


def test_chinese_docstring(write_tmp_py):
    path = write_tmp_py('"""中文文档字符串测试"""\nprint("hello")\n')
    assert extract_docstring(path) == "中文文档字符串测试"
