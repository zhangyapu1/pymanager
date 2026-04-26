"""加密工具 - 提供 XOR+Base64 加密解密及 API Key 默认值管理。"""
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
