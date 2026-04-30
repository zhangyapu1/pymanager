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
from modules.config import load_app_config, save_app_config

CRYPTPROTECT_UI_FORBIDDEN = 0x01

_XOR_KEY = b'pymanager'

# 默认 GitHub Token（XOR+Base64 加密）
# 用户填入自己的 token 后，更新将不再使用此默认值
_DEFAULT_TOKEN_ENC = "FxEdPj4lIQMfAwEFNAMmAggBSDMfIx8nLzMFFgs8MVksMlQ5QBEYLw=="


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
    try:
        app_config = load_app_config()
        # 优先使用用户自己保存的 token（encrypted_token）
        encrypted_token = app_config["github"].get("encrypted_token", "").strip()
        if encrypted_token:
            try:
                return _decrypt(encrypted_token)
            except Exception:
                pass
        
        # 其次检查配置文件中的明文 token（旧版兼容）
        plain_token = app_config["github"].get("token", "").strip()
        if plain_token:
            return plain_token
        
        # 最后使用硬编码的默认加密 token
        if _DEFAULT_TOKEN_ENC:
            return _xor_decode(_DEFAULT_TOKEN_ENC)
    except Exception as e:
        log_error(f"获取默认Token失败: {e}")
    return ""


def get_api_token():
    try:
        app_config = load_app_config()
        encrypted = app_config["github"].get("encrypted_token", "").strip()
        if encrypted:
            return _decrypt(encrypted)
    except (OSError, ValueError, UnicodeDecodeError):
        pass
    return ""


def save_api_token(token):
    try:
        app_config = load_app_config()
        encrypted = _encrypt(token.strip())
        app_config["github"]["encrypted_token"] = encrypted
        save_app_config(app_config)
    except (OSError, ValueError) as e:
        log_error(f"保存Token失败: {e}")


def delete_api_token():
    try:
        app_config = load_app_config()
        app_config["github"]["encrypted_token"] = ""
        save_app_config(app_config)
    except Exception as e:
        log_error(f"删除Token失败: {e}")


def delete_token_ui(ctx):
    if not get_api_token():
        ctx.append_output("[提示] 当前没有保存的 Token。")
        ctx.ui.show_info("提示", "当前没有保存的 Token。")
        return
    if ctx.ui.ask_yes_no("确认删除", "确定要删除已保存的 GitHub API Token 吗？"):
        delete_api_token()
        ctx.append_output("已删除保存的 Token")
        ctx.set_status("已删除保存的 Token")


def show_token_config_dialog(parent):
    """显示 Token/API 配置对话框"""
    import tkinter as tk
    import webbrowser
    from tkinter import ttk, messagebox
    from modules.config import load_app_config, save_app_config
    from modules.encrypt_utils import encrypt, decrypt

    app_config = load_app_config()

    dialog = tk.Toplevel(parent)
    dialog.title("Token/API 配置")
    dialog.geometry("550x750")

    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() - 550) // 2
    y = (dialog.winfo_screenheight() - 750) // 2
    dialog.geometry(f"550x750+{x}+{y}")

    dialog.resizable(True, True)
    dialog.transient(parent)
    dialog.grab_set()

    notebook = ttk.Notebook(dialog)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    content = {}
    for name in ["GitHub", "AI服务", "翻译服务"]:
        frame = ttk.Frame(notebook, padding=15)
        notebook.add(frame, text=name)
        content[name] = frame

    entries = {}

    def _get_decrypted_key_local(section, key_name):
        try:
            keys = app_config.get(section, {}).get("keys", {})
            enc_key = keys.get(key_name, "")
            if enc_key:
                return decrypt(enc_key)
        except Exception as e:
            log_error(f"解密密钥失败 [{section}.{key_name}]: {e}")
        return ""

    def _set_encrypted_key_local(section, key_name, value):
        if key_name not in app_config[section]["keys"]:
            app_config[section]["keys"][key_name] = ""
        if value:
            app_config[section]["keys"][key_name] = encrypt(value)
        else:
            app_config[section]["keys"][key_name] = ""

    def create_section_header(parent, text, row):
        ttk.Label(parent, text=text, font=("", 11, "bold")).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))

    def create_labeled_entry(parent, label_text, row, width=40):
        label = ttk.Label(parent, text=label_text, font=("微软雅黑", 9))
        label.grid(row=row, column=0, sticky=tk.W, pady=3)
        entry = ttk.Entry(parent, width=width)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=3, padx=(10, 0))
        return entry

    def create_help_text(parent, text, row):
        help_label = tk.Label(parent, text=text, font=("微软雅黑", 8), fg="#666666", wraplength=500, justify=tk.LEFT)
        help_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 8), padx=(0, 0))

    def create_clickable_link(parent, text, url, row):
        link_label = tk.Label(parent, text=text, font=("微软雅黑", 9, "underline"), fg="#0066cc", cursor="hand2")
        link_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 8), padx=(0, 0))
        link_label.bind("<Button-1>", lambda e: webbrowser.open(url))
        return link_label

    def create_labeled_combobox(parent, label_text, row, values, width=40):
        label = ttk.Label(parent, text=label_text, font=("微软雅黑", 9))
        label.grid(row=row, column=0, sticky=tk.W, pady=3)
        combo = ttk.Combobox(parent, values=values, width=width, state="readonly")
        combo.grid(row=row, column=1, sticky=tk.EW, pady=3, padx=(10, 0))
        return combo

    def create_help_line(parent, text, row):
        help_label = tk.Label(parent, text=text, font=("微软雅黑", 8), fg="#666666", wraplength=500, justify=tk.LEFT)
        help_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 3), padx=(0, 0))

    # ========== GitHub Tab ==========
    f = content["GitHub"]
    f.columnconfigure(1, weight=1)

    create_section_header(f, "📦 GitHub Personal Access Token", 0)
    create_help_text(f, "用途：用于提高 GitHub API 访问额度。匿名请求每小时限制60次，有Token可更高。", 1)

    entries["github_token"] = create_labeled_entry(f, "Token:", 2)
    entries["github_token"].insert(0, app_config["github"].get("token", ""))

    create_help_text(f, "获取方式：", 3)
    create_clickable_link(f, "👉 点击此处打开 GitHub Tokens 页面", "https://github.com/settings/tokens", 4)
    create_help_line(f, "1. 点击 'Generate new token (classic)'", 5)
    create_help_line(f, "2. 勾选 'repo' 权限（用于读取仓库信息）", 6)
    create_help_line(f, "3. 生成后将 Token 粘贴到此处", 7)

    # ========== AI服务 Tab ==========
    f = content["AI服务"]
    f.columnconfigure(1, weight=1)

    create_section_header(f, "🤖 AI 服务 API Keys（已加密存储）", 0)
    create_help_text(f, "用途：用于AI分析和翻译GitHub项目信息、脚本内容等。", 1)

    create_section_header(f, "当前服务商选择", 2)
    ai_providers = ["通义千问 (Qwen)", "智谱AI (GLM-4-Flash)", "DeepSeek", "本地服务 (127.0.0.1:8080)"]
    entries["ai_provider"] = create_labeled_combobox(f, "当前服务商:", 3, ai_providers)
    entries["ai_provider"].set(app_config["ai"].get("provider", "通义千问 (Qwen)"))

    create_section_header(f, "API Keys 配置", 4)

    entries["ai_qwen"] = create_labeled_entry(f, "通义千问 Key:", 5)
    entries["ai_qwen"].insert(0, _get_decrypted_key_local("ai", "通义千问 (Qwen)"))
    create_help_line(f, "获取：", 6)
    create_clickable_link(f, "👉 点击此处打开阿里云百炼控制台", "https://dashscope.console.aliyun.com/", 7)

    entries["ai_zhipu"] = create_labeled_entry(f, "智谱AI Key:", 8)
    entries["ai_zhipu"].insert(0, _get_decrypted_key_local("ai", "智谱AI (GLM-4-Flash)"))
    create_help_line(f, "获取：", 9)
    create_clickable_link(f, "👉 点击此处打开智谱AI开放平台", "https://open.bigmodel.cn/", 10)

    entries["ai_deepseek"] = create_labeled_entry(f, "DeepSeek Key:", 11)
    entries["ai_deepseek"].insert(0, _get_decrypted_key_local("ai", "DeepSeek"))
    create_help_line(f, "获取：", 12)
    create_clickable_link(f, "👉 点击此处打开 DeepSeek 平台", "https://platform.deepseek.com/", 13)

    entries["ai_local"] = create_labeled_entry(f, "本地服务 Key:", 14)
    entries["ai_local"].insert(0, _get_decrypted_key_local("ai", "本地服务 (127.0.0.1:8080)"))

    create_section_header(f, "本地服务配置", 15)
    entries["ai_local_model"] = create_labeled_entry(f, "本地模型名称:", 16)
    entries["ai_local_model"].insert(0, app_config["ai"].get("local_model", ""))
    create_help_text(f, "例如：DeepSeek-V3.2, Qwen3.5-Plus 等。需本地服务已启动并监听 127.0.0.1:8080", 17)

    # ========== 翻译服务 Tab ==========
    f = content["翻译服务"]
    f.columnconfigure(1, weight=1)

    create_section_header(f, "🌐 翻译服务 API Keys（已加密存储）", 0)
    create_help_text(f, "用途：用于翻译脚本内容和README等文本。提示：Google翻译无需Key，百度和腾讯翻译需要申请API。", 1)

    create_section_header(f, "当前服务商选择", 2)
    trans_providers = ["Google翻译", "百度翻译", "腾讯翻译君"]
    entries["trans_provider"] = create_labeled_combobox(f, "当前服务商:", 3, trans_providers)
    entries["trans_provider"].set(app_config["translate"].get("provider", "Google翻译"))

    create_section_header(f, "百度翻译配置", 4)
    create_help_text(f, "用途：中文翻译引擎，适合技术文档翻译。", 5)
    create_help_line(f, "获取：", 6)
    create_clickable_link(f, "👉 点击此处打开百度翻译开放平台", "https://fanyi-api.baidu.com/", 7)

    entries["baidu_appid"] = create_labeled_entry(f, "APP ID:", 8)
    entries["baidu_appid"].insert(0, _get_decrypted_key_local("translate", "百度翻译_APP_ID"))

    entries["baidu_key"] = create_labeled_entry(f, "密钥:", 9)
    entries["baidu_key"].insert(0, _get_decrypted_key_local("translate", "百度翻译_密钥"))

    create_section_header(f, "腾讯翻译君配置", 10)
    create_help_text(f, "用途：腾讯云机器翻译服务，准确性较高。", 11)
    create_help_line(f, "获取：", 12)
    create_clickable_link(f, "👉 点击此处打开腾讯云机器翻译", "https://cloud.tencent.com/product/tmt", 13)

    entries["tencent_sid"] = create_labeled_entry(f, "SecretId:", 14)
    entries["tencent_sid"].insert(0, _get_decrypted_key_local("translate", "腾讯翻译君_SecretId"))

    entries["tencent_skey"] = create_labeled_entry(f, "SecretKey:", 15)
    entries["tencent_skey"].insert(0, _get_decrypted_key_local("translate", "腾讯翻译君_SecretKey"))

    # ========== Buttons ==========
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

    def on_save():
        try:
            app_config["github"]["token"] = entries["github_token"].get().strip()

            app_config["ai"]["provider"] = entries["ai_provider"].get()
            app_config["ai"]["local_model"] = entries["ai_local_model"].get().strip()

            _set_encrypted_key_local("ai", "通义千问 (Qwen)", entries["ai_qwen"].get().strip())
            _set_encrypted_key_local("ai", "智谱AI (GLM-4-Flash)", entries["ai_zhipu"].get().strip())
            _set_encrypted_key_local("ai", "DeepSeek", entries["ai_deepseek"].get().strip())
            _set_encrypted_key_local("ai", "本地服务 (127.0.0.1:8080)", entries["ai_local"].get().strip())

            app_config["translate"]["provider"] = entries["trans_provider"].get()
            _set_encrypted_key_local("translate", "百度翻译_APP_ID", entries["baidu_appid"].get().strip())
            _set_encrypted_key_local("translate", "百度翻译_密钥", entries["baidu_key"].get().strip())
            _set_encrypted_key_local("translate", "腾讯翻译君_SecretId", entries["tencent_sid"].get().strip())
            _set_encrypted_key_local("translate", "腾讯翻译君_SecretKey", entries["tencent_skey"].get().strip())

            save_app_config(app_config)
            messagebox.showinfo("成功", "配置已保存！", parent=dialog)
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{e}", parent=dialog)

    def on_cancel():
        dialog.destroy()

    ttk.Button(btn_frame, text="取消", command=on_cancel).pack(side=tk.RIGHT, padx=5)
    ttk.Button(btn_frame, text="保存", command=on_save, style="Accent.TButton").pack(side=tk.RIGHT, padx=5)


def _get_decrypted_key(app_config, section, key_name):
    """获取解密后的 key"""
    try:
        keys = app_config.get(section, {}).get("keys", {})
        enc_key = keys.get(key_name, "")
        if enc_key:
            return decrypt(enc_key)
    except Exception as e:
        log_error(f"解密密钥失败 [{section}.{key_name}]: {e}")
    return ""


def _set_encrypted_key(app_config, section, key_name, value):
    """设置加密的 key"""
    if key_name not in app_config[section]["keys"]:
        app_config[section]["keys"][key_name] = ""
    if value:
        app_config[section]["keys"][key_name] = encrypt(value)
    else:
        app_config[section]["keys"][key_name] = ""
