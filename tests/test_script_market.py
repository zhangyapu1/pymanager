import os
import json
import pytest
from modules.script_market import (
    _load_translate_config, _save_translate_config,
    _is_english, _render_markdown, TRANSLATE_PROVIDERS,
    _load_ai_config, _save_ai_config, AI_PROVIDERS,
)


def test_translate_providers_structure():
    assert "Google翻译" in TRANSLATE_PROVIDERS
    assert "百度翻译" in TRANSLATE_PROVIDERS
    assert "腾讯翻译君" in TRANSLATE_PROVIDERS
    assert TRANSLATE_PROVIDERS["Google翻译"]["needs_key"] is False
    assert TRANSLATE_PROVIDERS["百度翻译"]["needs_key"] is True
    assert TRANSLATE_PROVIDERS["腾讯翻译君"]["needs_key"] is True


def test_load_translate_config_default(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.script_market.TRANSLATE_CONFIG_FILE", str(tmp_path / "t.json"))
    config = _load_translate_config()
    assert config["provider"] == "Google翻译"
    assert config["keys"] == {}


def test_save_and_load_translate_config(tmp_path, monkeypatch):
    path = str(tmp_path / "t.json")
    monkeypatch.setattr("modules.script_market.TRANSLATE_CONFIG_FILE", path)
    config = {"provider": "百度翻译", "keys": {"百度翻译_APP_ID": "testid", "百度翻译_密钥": "testkey"}}
    _save_translate_config(config)
    loaded = _load_translate_config()
    assert loaded["provider"] == "百度翻译"
    assert loaded["keys"]["百度翻译_APP_ID"] == "testid"
    assert loaded["keys"]["百度翻译_密钥"] == "testkey"


def test_load_translate_config_invalid_provider(tmp_path, monkeypatch):
    path = str(tmp_path / "t.json")
    monkeypatch.setattr("modules.script_market.TRANSLATE_CONFIG_FILE", path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"provider": "不存在的翻译", "keys": {}}, f)
    config = _load_translate_config()
    assert config["provider"] == "Google翻译"


def test_ai_providers_default():
    assert "通义千问 (Qwen)" in AI_PROVIDERS
    assert "智谱AI (GLM-4-Flash)" in AI_PROVIDERS
    assert "DeepSeek" in AI_PROVIDERS


def test_load_ai_config_default(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.script_market.AI_CONFIG_FILE", str(tmp_path / "ai.json"))
    config = _load_ai_config()
    assert config["provider"] == "通义千问 (Qwen)"


def test_save_and_load_ai_config(tmp_path, monkeypatch):
    path = str(tmp_path / "ai.json")
    monkeypatch.setattr("modules.script_market.AI_CONFIG_FILE", path)
    config = {"provider": "DeepSeek", "keys": {}, "custom_keys": {"DeepSeek": "sk-test123"}}
    _save_ai_config(config)
    loaded = _load_ai_config()
    assert loaded["provider"] == "DeepSeek"
    assert loaded["custom_keys"]["DeepSeek"] == "sk-test123"


def test_load_ai_config_invalid_provider(tmp_path, monkeypatch):
    path = str(tmp_path / "ai.json")
    monkeypatch.setattr("modules.script_market.AI_CONFIG_FILE", path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"provider": "不存在的AI", "keys": {}}, f)
    config = _load_ai_config()
    assert config["provider"] == "通义千问 (Qwen)"


def test_is_english_pure_english():
    assert _is_english("Hello World") is True


def test_is_english_pure_chinese():
    assert _is_english("你好世界") is False


def test_is_english_mixed():
    assert _is_english("Hello 你好") is False


def test_is_english_empty():
    assert _is_english("") is False


def test_is_english_code():
    assert _is_english("import os\nfrom sys import path") is True


def test_render_markdown_headings():
    result = _render_markdown("# Title\n## Subtitle\n### Section")
    assert "Title" in result
    assert "Subtitle" in result
    assert "Section" in result
    assert "══" in result
    assert "──" in result


def test_render_markdown_links():
    result = _render_markdown("[Click here](https://example.com)")
    assert "Click here" in result
    assert "https://example.com" in result


def test_render_markdown_images():
    result = _render_markdown("![Alt text](https://example.com/img.png)")
    assert "Alt text" in result


def test_render_markdown_list():
    result = _render_markdown("- item1\n- item2\n- item3")
    assert "item1" in result
    assert "item2" in result
    assert "item3" in result


def test_render_markdown_bold_italic():
    result = _render_markdown("**bold** and *italic*")
    assert "bold" in result
    assert "italic" in result
    assert "**" not in result
    assert "*" not in result or "italic" in result


def test_render_markdown_code():
    result = _render_markdown("`code here`")
    assert "code here" in result
    assert "`" not in result


def test_render_markdown_html_h1():
    result = _render_markdown('<h1 align="center">Title</h1>')
    assert "Title" in result
    assert "<h1" not in result


def test_render_markdown_html_links():
    result = _render_markdown('<a href="https://example.com">Link</a>')
    assert "Link" in result
    assert "https://example.com" in result
    assert "<a" not in result


def test_render_markdown_html_images():
    result = _render_markdown('<img alt="Logo" src="logo.png">')
    assert "Logo" in result
    assert "<img" not in result


def test_render_markdown_html_div():
    result = _render_markdown('<div align="center">Content</div>')
    assert "Content" in result
    assert "<div" not in result


def test_render_markdown_html_entities():
    result = _render_markdown("&amp; &lt; &gt; &nbsp;")
    assert "&" in result
    assert "<" in result
    assert ">" in result
    assert "&amp;" not in result


def test_render_markdown_blockquote():
    result = _render_markdown("> This is a quote")
    assert "This is a quote" in result


def test_render_markdown_horizontal_rule():
    result = _render_markdown("---")
    assert "──" in result


def test_render_markdown_empty():
    result = _render_markdown("")
    assert result == ""


def test_render_markdown_plain_text():
    result = _render_markdown("Just plain text")
    assert "Just plain text" in result


def test_render_markdown_numbered_list():
    result = _render_markdown("1. first\n2. second\n3. third")
    assert "first" in result
    assert "second" in result
    assert "third" in result


def test_render_markdown_code_block():
    result = _render_markdown("```python\nprint('hello')\n```")
    assert "print" in result
    assert "```" not in result
