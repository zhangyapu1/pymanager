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
