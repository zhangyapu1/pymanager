"""
Token 加密 - GitHub API Token 的加密存储与 Windows DPAPI 保护。

加密方案：
    存储加密：使用 Windows DPAPI（CryptProtectData / CryptUnprotectData）
        - 与当前 Windows 用户账户绑定
        - 其他用户无法解密
        - 加密结果经 Base64 编码存储到文件

    默认 Token：使用简单 XOR 混淆
        - _DEFAULT_TOKEN_ENC 为 XOR+Base64 编码的默认 Token
        - 仅用于内置默认 Token 的混淆存储

文件存储：
    TOKEN_FILE = config/api_token.enc
    内容为 DPAPI 加密后的 Base64 字符串

函数：
    get_default_token()：
        获取内置默认 GitHub Token（XOR 解码）

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

_XOR_KEY = b'pymanager'
_DEFAULT_TOKEN_ENC = 'FxEdPh0kAwojQwoIOCdUMREcSAoZNwgjL1EqETAsKAgFH1FFFxUiMA=='


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _xor_decode(encoded):
    raw = base64.b64decode(encoded)
    return bytes(b ^ _XOR_KEY[i % len(_XOR_KEY)] for i, b in enumerate(raw)).decode('utf-8')


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
    return _xor_decode(_DEFAULT_TOKEN_ENC)


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
