import pytest
from modules.encrypt_utils import encrypt, decrypt, get_default_key


def test_encrypt_decrypt_roundtrip():
    original = "hello world 测试中文"
    encrypted = encrypt(original)
    decrypted = decrypt(encrypted)
    assert decrypted == original


def test_encrypt_produces_different_output():
    original = "test data"
    encrypted = encrypt(original)
    assert encrypted != original


def test_encrypt_empty_string():
    original = ""
    encrypted = encrypt(original)
    decrypted = decrypt(encrypted)
    assert decrypted == original


def test_encrypt_long_text():
    original = "A" * 10000
    encrypted = encrypt(original)
    decrypted = decrypt(encrypted)
    assert decrypted == original


def test_encrypt_special_chars():
    original = "!@#$%^&*()_+-=[]{}|;':\",./<>?\n\t\r"
    encrypted = encrypt(original)
    decrypted = decrypt(encrypted)
    assert decrypted == original


def test_decrypt_invalid_base64():
    with pytest.raises(Exception):
        decrypt("not_valid_base64!!!")


def test_get_default_key_zhipu():
    key = get_default_key("智谱AI (GLM-4-Flash)")
    assert key != ""
    assert len(key) > 10


def test_get_default_key_qwen():
    key = get_default_key("通义千问 (Qwen)")
    assert key != ""
    assert len(key) > 10


def test_get_default_key_unknown():
    key = get_default_key("Unknown Provider")
    assert key == ""


def test_multiple_roundtrips():
    for text in ["abc", "123", "中文测试", "emoji 🎉", "  spaces  "]:
        assert decrypt(encrypt(text)) == text
