"""
加密工具 - 提供 XOR+SHA256+Base64 加密解密及 API Key 管理。

加密算法：
    1. 使用 SHA-256 将固定密钥 _SECRET 派生为 32 字节密钥
    2. 明文 UTF-8 编码后与密钥循环 XOR 运算
    3. XOR 结果经 Base64 编码为 ASCII 字符串存储

函数：
    encrypt(text)：
        明文 → UTF-8 → XOR(SHA256密钥) → Base64 → ASCII 字符串

    decrypt(encrypted_text)：
        ASCII 字符串 → Base64解码 → XOR(SHA256密钥) → UTF-8 → 明文

配置文件：
    config/api_keys.json - 存储 GitHub token 和 AI API keys

默认密钥（加密存储）：
    翻译服务：
        "百度翻译_APP_ID"       - 百度翻译应用ID
        "百度翻译_密钥"         - 百度翻译密钥
        "腾讯翻译君_SecretId"   - 腾讯翻译君 SecretId
        "腾讯翻译君_SecretKey"  - 腾讯翻译君 SecretKey

    get_default_translate_key(key_name)：
        获取翻译服务的默认解密后密钥

安全说明：
    - XOR 加密为混淆级别保护，非密码学安全
    - AI 和 GitHub keys 已移至配置文件，仅翻译 keys 硬编码
    - 生产环境建议使用系统密钥库（如 Windows DPAPI）

依赖：base64, hashlib, json
"""
import base64
import hashlib
import os
import json


_SECRET = b'pymanager_2026_key'

_API_KEYS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "api_keys.json")

DEFAULT_TRANSLATE_KEYS = {
    "百度翻译_APP_ID": "fhIjtb0fmvBRwO7iRkyd5g8=",
    "百度翻译_密钥": "BVhLxP1I7PMNpJ3gFTvpow3VMrY=",
    "腾讯翻译君_SecretId": "DWlYx9lanPAUqKaRMQzmhGvnLrEPIA0unpDYUT7p3DILcly0",
    "腾讯翻译君_SecretKey": "LxRB1NwcybFWx6mCAk2epVvvPYwVEjdVqe3UeAvLsQU=",
}


def encrypt(text):
    key = hashlib.sha256(_SECRET).digest()
    data = text.encode('utf-8')
    encrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    return base64.b64encode(encrypted).decode('ascii')


def decrypt(encrypted_text):
    key = hashlib.sha256(_SECRET).digest()
    data = base64.b64decode(encrypted_text)
    decrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    return decrypted.decode('utf-8')


def get_default_key(provider_name):
    keys = _load_ai_keys_from_config()
    return keys.get(provider_name, "")


def _load_ai_keys_from_config():
    try:
        if os.path.exists(_API_KEYS_FILE):
            with open(_API_KEYS_FILE, 'r', encoding='utf-8') as f:
                keys = json.load(f)
            ai_keys = keys.get("ai", {})
            result = {}
            for provider, key in ai_keys.items():
                if key and key.strip():
                    result[provider] = key.strip()
            return result
    except Exception:
        pass
    return {}


def get_default_translate_key(key_name):
    enc = DEFAULT_TRANSLATE_KEYS.get(key_name)
    if enc:
        try:
            return decrypt(enc)
        except Exception:
            return ""
    return ""


def save_api_keys_to_config(github_token=None, ai_keys=None):
    try:
        os.makedirs(os.path.dirname(_API_KEYS_FILE), exist_ok=True)
        data = {}
        if os.path.exists(_API_KEYS_FILE):
            try:
                with open(_API_KEYS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                pass
        if github_token is not None:
            if "github" not in data:
                data["github"] = {}
            data["github"]["token"] = github_token
        if ai_keys is not None:
            if "ai" not in data:
                data["ai"] = {}
            data["ai"].update(ai_keys)
        with open(_API_KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load_api_keys_from_config():
    try:
        if os.path.exists(_API_KEYS_FILE):
            with open(_API_KEYS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}
