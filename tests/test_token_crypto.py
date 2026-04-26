import os
import pytest
from modules.token_crypto import _xor_decode, get_default_token, delete_api_token


def test_xor_decode_default_token():
    token = get_default_token()
    assert token != ""
    assert len(token) > 10
    assert token.startswith("ghp_") or len(token) > 20


def test_xor_decode_roundtrip():
    from modules.token_crypto import _XOR_KEY
    import base64
    original = "test_token_123"
    encoded = base64.b64encode(
        bytes(b ^ _XOR_KEY[i % len(_XOR_KEY)] for i, b in enumerate(original.encode('utf-8')))
    ).decode('ascii')
    decoded = _xor_decode(encoded)
    assert decoded == original


def test_delete_api_token_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.token_crypto.TOKEN_FILE", str(tmp_path / "nonexistent.enc"))
    delete_api_token()
    assert not os.path.exists(str(tmp_path / "nonexistent.enc"))


def test_get_api_token_no_file(tmp_path, monkeypatch):
    from modules.token_crypto import get_api_token
    monkeypatch.setattr("modules.token_crypto.TOKEN_FILE", str(tmp_path / "nonexistent.enc"))
    result = get_api_token()
    assert result == ""
