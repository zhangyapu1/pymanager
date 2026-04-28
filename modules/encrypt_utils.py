"""
加密工具 - 提供安全的加密解密及 API Key 管理。

加密算法：
    Windows DPAPI（CryptProtectData）
        - 与当前 Windows 用户账户绑定
        - 其他用户无法解密
        - 加密结果经 Base64 编码存储

函数：
    encrypt(text)：
        使用 DPAPI 加密文本

    decrypt(encrypted_text)：
        使用 DPAPI 解密文本

安全说明：
    - DPAPI 加密与 Windows 用户账户绑定，安全性高
    - 用户必须在配置文件中设置自己的 API Key
    - 不再提供硬编码的默认密钥

依赖：base64
"""
import base64
import os

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


def encrypt(text):
    """使用 DPAPI 加密文本"""
    if not HAS_DPAPI:
        raise NotImplementedError("DPAPI 不可用，无法加密")
    plaintext = text.encode("utf-8") if isinstance(text, str) else text
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
    raise OSError("CryptProtectData failed")


def decrypt(encrypted_text):
    """使用 DPAPI 解密文本"""
    if not HAS_DPAPI:
        raise NotImplementedError("DPAPI 不可用，无法解密")
    raw = base64.b64decode(encrypted_text)
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
    raise OSError("CryptUnprotectData failed")


def _load_default_keys():
    """加载默认密钥配置（已移除所有硬编码密钥）"""
    # 用户必须在配置文件中设置自己的 API Key
    default_keys_enc = {}
    default_translate_keys_enc = {}
    
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