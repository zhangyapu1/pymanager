import os
import json
import pytest
from modules.settings_manager import (
    load_json, save_json, load_settings, save_settings,
    load_groups_meta, save_groups_meta, ensure_config_dir
)


def test_save_and_load_json(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.settings_manager.CONFIG_DIR", str(tmp_path))
    data = {"key": "value", "number": 42}
    assert save_json("test.json", data) is True
    result = load_json("test.json")
    assert result == data


def test_load_json_nonexistent(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.settings_manager.CONFIG_DIR", str(tmp_path))
    result = load_json("nonexistent.json")
    assert result == {}


def test_load_json_default(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.settings_manager.CONFIG_DIR", str(tmp_path))
    result = load_json("nonexistent.json", default={"a": 1})
    assert result == {"a": 1}


def test_load_json_corrupted(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.settings_manager.CONFIG_DIR", str(tmp_path))
    corrupted = tmp_path / "bad.json"
    corrupted.write_text("{invalid json", encoding="utf-8")
    result = load_json("bad.json")
    assert result == {}


def test_save_and_load_settings(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.settings_manager.CONFIG_DIR", str(tmp_path))
    settings = {
        "window": {"width": 1024, "height": 768, "x": 100, "y": 200},
        "log": {"retain_days": 14, "max_file_size_mb": 2}
    }
    assert save_settings(settings) is True
    result = load_settings()
    assert result["window"]["width"] == 1024
    assert result["window"]["height"] == 768
    assert result["window"]["x"] == 100
    assert result["window"]["y"] == 200
    assert result["log"]["retain_days"] == 14
    assert result["log"]["max_file_size_mb"] == 2


def test_load_settings_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.settings_manager.CONFIG_DIR", str(tmp_path))
    result = load_settings()
    assert result["window"]["width"] == 950
    assert result["window"]["height"] == 600
    assert result["log"]["retain_days"] == 7
    assert result["log"]["max_file_size_mb"] == 1


def test_load_settings_partial(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.settings_manager.CONFIG_DIR", str(tmp_path))
    partial = {"window": {"width": 1200}}
    save_json("settings.json", partial)
    result = load_settings()
    assert result["window"]["width"] == 1200
    assert result["window"]["height"] == 600
    assert result["log"]["retain_days"] == 7


def test_save_and_load_groups_meta(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.settings_manager.CONFIG_DIR", str(tmp_path))
    meta = {
        "默认分组": {"order": 0},
        "系统工具": {"order": 1}
    }
    assert save_groups_meta(meta) is True
    result = load_groups_meta()
    assert result == meta


def test_load_groups_meta_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.settings_manager.CONFIG_DIR", str(tmp_path))
    result = load_groups_meta()
    assert result == {}


def test_ensure_config_dir(tmp_path, monkeypatch):
    new_dir = str(tmp_path / "new_config")
    monkeypatch.setattr("modules.settings_manager.CONFIG_DIR", new_dir)
    ensure_config_dir()
    assert os.path.isdir(new_dir)
