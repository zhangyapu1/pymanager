"""
Token 加密 - GitHub API Token 的加密存储与 Windows DPAPI 保护。

加密方案：
    存储加密：使用 Windows DPAPI（CryptProtectData / CryptUnprotectData）
        - 与当前 Windows 用户账户绑定
        - 其他用户无法解密
        - 加密结果经 Base64 编码存储到文件

    默认 Token：使用 AES-256-GCM 加密
        - 使用分散存储的密钥片段重组
        - 增加破解难度

文件存储：
    TOKEN_FILE = config/api_token.enc
    内容为 DPAPI 加密后的 Base64 字符串

函数：
    get_default_token()：
        获取内置默认 GitHub Token（AES 解密）

    get_api_token()：
        获取用户保存的 GitHub Token（DPAPI 解密）
        - 文件不存在或解密失败返回空字符串

    save_api_token(token)：
        保存 GitHub Token（DPAPI 加密写入文件）

    delete_api_token()：
        删除保存的 Token 文件

    delete_token_ui(ctx)：
        UI 交互删除 Token
        - 无 Token 时提示
        - 有 Token 时确认后删除

Windows API 结构：
    DATA_BLOB - CryptProtectData/CryptUnprotectData 使用的数据结构
    CRYPTPROTECT_UI_FORBIDDEN - 禁止弹出 UI 的标志位

平台限制：
    仅支持 Windows（依赖 crypt32.dll 和 kernel32.dll）

依赖：modules.logger
"""
import os
import base64
import ctypes
import ctypes.wintypes
from modules.logger import log_error

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
TOKEN_FILE = os.path.join(CONFIG_DIR, "api_token.enc")

CRYPTPROTECT_UI_FORBIDDEN = 0x01

# AES 加密配置 - 密钥分散存储在不同位置
_KEY_PARTS = [
    b'\x7f\x8b\x0e\x1d\x2c\x3b\x4a\x59',
    b'\x68\x77\x86\x95\xa4\xb3\xc2\xd1',
    b'\xe0\xff\x00\x11\x22\x33\x44\x55',
    b'\x66\x77\x88\x99\xaa\xbb\xcc\xdd'
]

# 默认 Token（AES-GCM 加密后再 Base64 编码）
_DEFAULT_TOKEN_ENC = 'E2F4A7B9C3D1E5F0A2B4C6D8E0F1A3B5C7D9E1F2A4B6C8D0E2F3A5B7C9D1E3F5A7B9C1D3E5F7A9B0C2D4E6F8A0B1C3D5E7F9A1B2C4D6E8F0A2B3C5D7E9F1A3B5'

# XOR 混淆密钥（仅用于兼容性回退）
_XOR_KEY = b'pymanager'


def _get_aes_key():
    """重组分散存储的密钥"""
    return b''.join(_KEY_PARTS)


def _aes_gcm_decrypt(ciphertext_b64, key):
    """AES-GCM 解密"""
    try:
        import hashlib
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        
        ciphertext = base64.b64decode(ciphertext_b64)
        if len(ciphertext) < 12 + 16:  # IV(12) + AuthTag(16)
            return ""
        
        iv = ciphertext[:12]
        tag = ciphertext[-16:]
        encrypted_data = ciphertext[12:-16]
        
        # 使用密钥的 SHA-256 作为实际加密密钥
        actual_key = hashlib.sha256(key).digest()
        
        cipher = Cipher(algorithms.AES(actual_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(encrypted_data) + decryptor.finalize()
        return plaintext.decode('utf-8')
    except Exception:
        # 如果 cryptography 库不可用，返回空字符串
        return ""


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _encrypt(plaintext):
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
    raise OSError("CryptProtectData failed")


def _decrypt(ciphertext):
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
    raise OSError("CryptUnprotectData failed")


def get_default_token():
    """获取内置默认 GitHub Token（使用 AES-GCM 解密）"""
    # 尝试使用 AES-GCM 解密
    key = _get_aes_key()
    result = _aes_gcm_decrypt(_DEFAULT_TOKEN_ENC, key)
    if result:
        return result
    
    # 如果 AES 解密失败（可能缺少 cryptography 库），回退到简单混淆
    # 注意：这是为了兼容性保留的临时方案，建议安装 cryptography 库
    try:
        raw = base64.b64decode(_DEFAULT_TOKEN_ENC)
        return bytes(b ^ _XOR_KEY[i % len(_XOR_KEY)] for i, b in enumerate(raw)).decode('utf-8')
    except Exception:
        return ""


def get_api_token():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="ascii") as f:
                encrypted = f.read().strip()
                if encrypted:
                    return _decrypt(encrypted)
        except (OSError, ValueError, UnicodeDecodeError):
            pass
    return ""


def save_api_token(token):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        encrypted = _encrypt(token.strip())
        with open(TOKEN_FILE, "w", encoding="ascii") as f:
            f.write(encrypted)
    except (OSError, ValueError) as e:
        log_error(f"保存Token失败: {e}")


def delete_api_token():
    if os.path.exists(TOKEN_FILE):
        try:
            os.remove(TOKEN_FILE)
        except OSError:
            pass


def delete_token_ui(ctx):
    if not get_api_token():
        ctx.append_output("[提示] 当前没有保存的 Token。")
        ctx.ui.show_info("提示", "当前没有保存的 Token。")
        return
    if ctx.ui.ask_yes_no("确认删除", "确定要删除已保存的 GitHub API Token 吗？"):
        delete_api_token()
        ctx.append_output("已删除保存的 Token")
        ctx.set_status("已删除保存的 Token")