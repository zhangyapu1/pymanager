import pytest
from modules.updater import is_version_greater


def test_greater_patch():
    assert is_version_greater("1.2.1", "1.2.0") is True


def test_greater_minor():
    assert is_version_greater("1.3.0", "1.2.9") is True


def test_greater_major():
    assert is_version_greater("2.0.0", "1.9.9") is True


def test_equal():
    assert is_version_greater("1.2.0", "1.2.0") is False


def test_less():
    assert is_version_greater("1.1.9", "1.2.0") is False


def test_different_length():
    assert is_version_greater("1.2", "1.1.9") is True


def test_with_v_prefix():
    assert is_version_greater("v1.3.0", "v1.2.0") is True


def test_mixed_prefix():
    assert is_version_greater("1.3.0", "v1.2.0") is True
