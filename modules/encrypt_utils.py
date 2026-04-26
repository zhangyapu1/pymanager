"""
加密工具 - 提供 XOR+SHA256+Base64 加密解密及 API Key 默认值管理。

加密算法：
    1. 使用 SHA-256 将固定密钥 _SECRET 派生为 32 字节密钥
    2. 明文 UTF-8 编码后与密钥循环 XOR 运算
    3. XOR 结果经 Base64 编码为 ASCII 字符串存储

函数：
    encrypt(text)：
        明文 → UTF-8 → XOR(SHA256密钥) → Base64 → ASCII 字符串

    decrypt(encrypted_text)：
        ASCII 字符串 → Base64解码 → XOR(SHA256密钥) → UTF-8 → 明文

默认密钥（加密存储）：
    AI 服务：
        "智谱AI (GLM-4-Flash)" - 智谱AI API Key
        "通义千问 (Qwen)"      - 通义千问 API Key

    翻译服务：
        "百度翻译_APP_ID"       - 百度翻译应用ID
        "百度翻译_密钥"         - 百度翻译密钥
        "腾讯翻译君_SecretId"   - 腾讯翻译君 SecretId
        "腾讯翻译君_SecretKey"  - 腾讯翻译君 SecretKey

    get_default_key(provider_name)：
        获取 AI 服务的默认解密后 API Key

    get_default_translate_key(key_name)：
        获取翻译服务的默认解密后密钥

安全说明：
    - XOR 加密为混淆级别保护，非密码学安全
    - 密钥硬编码在源码中，仅防止明文泄露
    - 生产环境建议使用系统密钥库（如 Windows DPAPI）

依赖：base64, hashlib
"""
import base64
import hashlib


_SECRET = b'pymanager_2026_key'


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


DEFAULT_KEYS = {
    "智谱AI (GLM-4-Flash)": "fxR3sbgey/AAwbm2QkrN5QXNastrEXBejuuECTuq3HlibHvxuX2atSqFieQaS82rfg==",
    "通义千问 (Qwen)": "P0k8s7sTnqdVley1QEib5l2ZOJlrRiAOjO2JW2uljykuFiQ=",
}

DEFAULT_TRANSLATE_KEYS = {
    "百度翻译_APP_ID": "fhIjtb0fmvBRwO7iRkyd5g8=",
    "百度翻译_密钥": "BVhLxP1I7PMNpJ3gFTvpow3VMrY=",
    "腾讯翻译君_SecretId": "DWlYx9lanPAUqKaRMQzmhGvnLrEPIA0unpDYUT7p3DILcly0",
    "腾讯翻译君_SecretKey": "LxRB1NwcybFWx6mCAk2epVvvPYwVEjdVqe3UeAvLsQU=",
}


def get_default_key(provider_name):
    enc = DEFAULT_KEYS.get(provider_name)
    if enc:
        try:
            return decrypt(enc)
        except Exception:
            return ""
    return ""


def get_default_translate_key(key_name):
    enc = DEFAULT_TRANSLATE_KEYS.get(key_name)
    if enc:
        try:
            return decrypt(enc)
        except Exception:
            return ""
    return ""
