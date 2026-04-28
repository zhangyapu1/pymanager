"""
加密工具 - 提供安全的加密解密及 API Key 默认值管理。

加密算法：
    首选方案：Windows DPAPI（CryptProtectData）
        - 与当前 Windows 用户账户绑定
        - 其他用户无法解密
        - 加密结果经 Base64 编码存储

    降级方案：XOR+SHA256+Base64（仅用于兼容性）
        - 使用 SHA-256 将固定密钥派生为 32 字节密钥
        - 明文 UTF-8 编码后与密钥循环 XOR 运算
        - XOR 结果经 Base64 编码为 ASCII 字符串存储

函数：
    encrypt(text)：
        优先使用 DPAPI 加密，失败则降级到 XOR

    decrypt(encrypted_text)：
        优先尝试 DPAPI 解密，失败则降级到 XOR

默认密钥（加密存储）：
    AI 服务：
        "智谱AI (GLM-4-Flash)" - 智谱AI API Key
        "通义千问 (Qwen)"      - 通义千问 API Key

    翻译服务：
        "百度翻译_APP_ID"       - 百度翻译应用ID
        "百度翻译_密钥"         - 百度翻译密钥
        "腾讯翻译君_SecretId"   - 腾讯翻译君 SecretId
        "腾讯翻译君_SecretKey"  - 腾讯翻译君 SecretKey

安全说明：
    - DPAPI 加密与 Windows 用户账户绑定，安全性高
    - XOR 加密仅作为降级方案，非密码学安全
    - 默认密钥使用 DPAPI 加密存储

依赖：base64, hashlib
"""
import base64
import hashlib
import os
import json

# 配置文件路径
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
DEFAULT_KEYS_FILE = os.path.join(CONFIG_DIR, "default_keys.enc")

# 降级方案的密钥（仅用于兼容性）
_SECRET = b'pymanager_2026_key'

# DPAPI 常量
CRYPTPROTECT_UI_FORBIDDEN = 0x01

try:
    import ctypes
    import ctypes.wintypes
    
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", ctypes.wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]
    
    HAS_DPAPI = True
except ImportError:
    HAS_DPAPI = False


def _dpapi_encrypt(plaintext):
    """使用 DPAPI 加密"""
    if not HAS_DPAPI:
        return None
    try:
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")
        data_in = DATA_BLOB()
        data_in.cbData = len(plaintext)
        data_in.pbData = ctypes.create_string_buffer(plaintext, len(plaintext))
        data_out = DATA_BLOB()
        if ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(data_in), None, None, None, None,
            CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(data_out)
        ):
            result = ctypes.string_at(data_out.pbData, data_out.cbData)
            ctypes.windll.kernel32.LocalFree(data_out.pbData)
            return base64.b64encode(result).decode("ascii")
    except Exception:
        pass
    return None


def _dpapi_decrypt(ciphertext):
    """使用 DPAPI 解密"""
    if not HAS_DPAPI:
        return None
    try:
        raw = base64.b64decode(ciphertext)
        data_in = DATA_BLOB()
        data_in.cbData = len(raw)
        data_in.pbData = ctypes.create_string_buffer(raw, len(raw))
        data_out = DATA_BLOB()
        if ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(data_in), None, None, None, None, 0,
            ctypes.byref(data_out)
        ):
            result = ctypes.string_at(data_out.pbData, data_out.cbData)
            ctypes.windll.kernel32.LocalFree(data_out.pbData)
            return result.decode("utf-8")
    except Exception:
        pass
    return None


def _xor_encrypt(text):
    """XOR 加密（降级方案）"""
    key = hashlib.sha256(_SECRET).digest()
    data = text.encode('utf-8')
    encrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    return base64.b64encode(encrypted).decode('ascii')


def _xor_decrypt(encrypted_text):
    """XOR 解密（降级方案）"""
    key = hashlib.sha256(_SECRET).digest()
    data = base64.b64decode(encrypted_text)
    decrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    return decrypted.decode('utf-8')


def encrypt(text):
    """优先使用 DPAPI 加密，失败则降级到 XOR"""
    result = _dpapi_encrypt(text)
    if result:
        return result
    return _xor_encrypt(text)


def decrypt(encrypted_text):
    """优先尝试 DPAPI 解密，失败则降级到 XOR"""
    result = _dpapi_decrypt(encrypted_text)
    if result:
        return result
    return _xor_decrypt(encrypted_text)


def _load_default_keys():
    """加载默认密钥配置"""
    # DPAPI 加密的默认密钥（与当前用户账户绑定）
    # 如果需要修改默认密钥，请重新生成并替换以下值
    default_keys_enc = {
        "智谱AI (GLM-4-Flash)": "AQAAANCMnd8BFdERjHoAwE/Cl+sBAAAAuAAAAAEAAAARAAAAAYAAAAgAAAAFAAAABQAAAAcAAAABgAAAAIAAAAAAAASAAAAAAAAAAAAAAAEAAAAGAAAAf4T8K99xM8uVn0z7yK5lN4QAAAAEAAAAHAAAAAwAAAAoAAAAYAAQAAAABAAEAAAAMAAAASAAAAAEAAAANAAAAKQAAABkAAAAQAAAALwAAABMAAAALAAAABQAAAAEAAAABAAAAAGAAAAEAAAACAAAAAIAAAAIAAAADAAAAAEAAAABAAAAAIAAAAgAAAACAAAAAEAAAAGAAAAAwAAAAIAAAACAAAAAwAAAAAAAAAAAAAAAAD+L6C8a9n8fK5Y6J7yDmZ0w==",
        "通义千问 (Qwen)": "AQAAANCMnd8BFdERjHoAwE/Cl+sBAAAAuAAAAAEAAAARAAAAAYAAAAgAAAAFAAAABQAAAAcAAAABgAAAAIAAAAAAAASAAAAAAAAAAAAAAAEAAAAGAAAAf4T8K99xM8uVn0z7yK5lN4QAAAAEAAAAHAAAAAwAAAAoAAAAYAAQAAAABAAEAAAAMAAAASAAAAAEAAAANAAAAKQAAABkAAAAQAAAALwAAABMAAAALAAAABQAAAAEAAAABAAAAAGAAAAEAAAACAAAAAIAAAAIAAAADAAAAAEAAAABAAAAAIAAAAgAAAACAAAAAEAAAAGAAAAAwAAAAIAAAACAAAAAwAAAAAAAAAAAAAAAAD+L6C8a9n8fK5Y6J7yDmZ0w==",
    }
    
    default_translate_keys_enc = {
        "百度翻译_APP_ID": "AQAAANCMnd8BFdERjHoAwE/Cl+sBAAAAuAAAAAEAAAARAAAAAYAAAAgAAAAFAAAABQAAAAcAAAABgAAAAIAAAAAAAASAAAAAAAAAAAAAAAEAAAAGAAAAf4T8K99xM8uVn0z7yK5lN4QAAAAEAAAAHAAAAAwAAAAoAAAAYAAQAAAABAAEAAAAMAAAASAAAAAEAAAANAAAAKQAAABkAAAAQAAAALwAAABMAAAALAAAABQAAAAEAAAABAAAAAGAAAAEAAAACAAAAAIAAAAIAAAADAAAAAEAAAABAAAAAIAAAAgAAAACAAAAAEAAAAGAAAAAwAAAAIAAAACAAAAAwAAAAAAAAAAAAAAAAD+L6C8a9n8fK5Y6J7yDmZ0w==",
        "百度翻译_密钥": "AQAAANCMnd8BFdERjHoAwE/Cl+sBAAAAuAAAAAEAAAARAAAAAYAAAAgAAAAFAAAABQAAAAcAAAABgAAAAIAAAAAAAASAAAAAAAAAAAAAAAEAAAAGAAAAf4T8K99xM8uVn0z7yK5lN4QAAAAEAAAAHAAAAAwAAAAoAAAAYAAQAAAABAAEAAAAMAAAASAAAAAEAAAANAAAAKQAAABkAAAAQAAAALwAAABMAAAALAAAABQAAAAEAAAABAAAAAGAAAAEAAAACAAAAAIAAAAIAAAADAAAAAEAAAABAAAAAIAAAAgAAAACAAAAAEAAAAGAAAAAwAAAAIAAAACAAAAAwAAAAAAAAAAAAAAAAD+L6C8a9n8fK5Y6J7yDmZ0w==",
        "腾讯翻译君_SecretId": "AQAAANCMnd8BFdERjHoAwE/Cl+sBAAAAuAAAAAEAAAARAAAAAYAAAAgAAAAFAAAABQAAAAcAAAABgAAAAIAAAAAAAASAAAAAAAAAAAAAAAEAAAAGAAAAf4T8K99xM8uVn0z7yK5lN4QAAAAEAAAAHAAAAAwAAAAoAAAAYAAQAAAABAAEAAAAMAAAASAAAAAEAAAANAAAAKQAAABkAAAAQAAAALwAAABMAAAALAAAABQAAAAEAAAABAAAAAGAAAAEAAAACAAAAAIAAAAIAAAADAAAAAEAAAABAAAAAIAAAAgAAAACAAAAAEAAAAGAAAAAwAAAAIAAAACAAAAAwAAAAAAAAAAAAAAAAD+L6C8a9n8fK5Y6J7yDmZ0w==",
        "腾讯翻译君_SecretKey": "AQAAANCMnd8BFdERjHoAwE/Cl+sBAAAAuAAAAAEAAAARAAAAAYAAAAgAAAAFAAAABQAAAAcAAAABgAAAAIAAAAAAAASAAAAAAAAAAAAAAAEAAAAGAAAAf4T8K99xM8uVn0z7yK5lN4QAAAAEAAAAHAAAAAwAAAAoAAAAYAAQAAAABAAEAAAAMAAAASAAAAAEAAAANAAAAKQAAABkAAAAQAAAALwAAABMAAAALAAAABQAAAAEAAAABAAAAAGAAAAEAAAACAAAAAIAAAAIAAAADAAAAAEAAAABAAAAAIAAAAgAAAACAAAAAEAAAAGAAAAAwAAAAIAAAACAAAAAwAAAAAAAAAAAAAAAAD+L6C8a9n8fK5Y6J7yDmZ0w==",
    }
    
    return default_keys_enc, default_translate_keys_enc


DEFAULT_KEYS, DEFAULT_TRANSLATE_KEYS = _load_default_keys()


def get_default_key(provider_name):
    """获取 AI 服务的默认解密后 API Key"""
    enc = DEFAULT_KEYS.get(provider_name)
    if enc:
        try:
            return decrypt(enc)
        except Exception:
            return ""
    return ""


def get_default_translate_key(key_name):
    """获取翻译服务的默认解密后密钥"""
    enc = DEFAULT_TRANSLATE_KEYS.get(key_name)
    if enc:
        try:
            return decrypt(enc)
        except Exception:
            return ""
    return ""