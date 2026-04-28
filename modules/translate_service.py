"""
翻译服务 - 支持 Google、百度、腾讯翻译君三种翻译服务。

常量：
    TRANSLATE_PROVIDERS - 翻译服务商配置字典
    TRANSLATE_CONFIG_FILE - 翻译配置文件路径

核心函数：
    translate_text(text, src, dest)：
        智能分段翻译长文本
        - 按段落拆分，逐段翻译
        - 超长段落按行分块
        - 按配置的服务商顺序尝试，失败自动降级

    translate_chunk(text, src, dest, providers_order)：
        翻译单个文本块
        - 按服务商顺序尝试，首个成功即返回

    load_translate_config() / save_translate_config(config)：
        加载/保存翻译配置（加密存储 Key）

    get_baidu_key() / get_tencent_key()：
        获取百度/腾讯翻译凭证（自定义 Key 优先，否则使用默认 Key）

翻译服务商：
    Google翻译 - 无需 Key，免费接口
    百度翻译   - 需要 APP ID + 密钥
    腾讯翻译君 - 需要 SecretId + SecretKey

依赖：modules.encrypt_utils, modules.token_crypto
"""
import hashlib
import hmac
import json
import os
import re
import time
from urllib.request import urlopen, Request
from urllib.parse import quote, urlencode

from modules.logger import log_error
from modules.config import load_app_config, save_app_config
from modules.encrypt_utils import encrypt, decrypt, get_default_translate_key

USER_AGENT = "pymanager/1.5.0"

TRANSLATE_PROVIDERS = {
    "Google翻译": {"needs_key": False},
    "百度翻译": {"needs_key": True, "fields": ["APP ID", "密钥"], "url": "https://fanyi-api.baidu.com"},
    "腾讯翻译君": {"needs_key": True, "fields": ["SecretId", "SecretKey"], "url": "https://cloud.tencent.com/product/tmt"},
}


def load_translate_config():
    """加载翻译配置（从统一配置中读取 translate 部分）"""
    app_config = load_app_config()
    translate_config = app_config.get("translate", {"provider": "Google翻译", "keys": {}})
    config = {"provider": translate_config.get("provider", "Google翻译"), "keys": {}}
    for name, enc_key in translate_config.get("keys", {}).items():
        try:
            config["keys"][name] = decrypt(enc_key)
        except Exception:
            pass
    return config


def save_translate_config(config):
    """保存翻译配置（保存到统一配置的 translate 部分）"""
    try:
        app_config = load_app_config()
        app_config["translate"]["provider"] = config.get("provider", "Google翻译")
        app_config["translate"]["keys"] = {}
        for name, plain_key in config.get("keys", {}).items():
            if plain_key:
                app_config["translate"]["keys"][name] = encrypt(plain_key)
        save_app_config(app_config)
    except Exception as e:
        log_error(f"保存翻译配置失败：{e}")


def get_baidu_key():
    cfg = load_translate_config()
    custom = cfg.get("keys", {})
    appid = custom.get("百度翻译_APP_ID", "") or get_default_translate_key("百度翻译_APP_ID")
    key = custom.get("百度翻译_密钥", "") or get_default_translate_key("百度翻译_密钥")
    return appid, key


def get_tencent_key():
    cfg = load_translate_config()
    custom = cfg.get("keys", {})
    sid = custom.get("腾讯翻译君_SecretId", "") or get_default_translate_key("腾讯翻译君_SecretId")
    skey = custom.get("腾讯翻译君_SecretKey", "") or get_default_translate_key("腾讯翻译君_SecretKey")
    return sid, skey


def _translate_google(text, src="en", dest="zh"):
    if not text.strip():
        return text
    try:
        dest_code = "zh-CN" if dest == "zh" else dest
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={dest_code}&dt=t&q={quote(text)}"
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            translated = "".join(s[0] for s in result[0] if s[0])
            if translated and translated != text:
                return translated
    except Exception as e:
        log_error(f"Google翻译异常：{e}")
    return text


def _translate_baidu(text, src="en", dest="zh"):
    if not text.strip():
        return text
    try:
        appid, key = get_baidu_key()
        if not appid or not key:
            return text
        if len(text.encode("utf-8")) > 5800:
            lines = text.split("\n")
            parts = []
            chunk = []
            chunk_len = 0
            for line in lines:
                line_len = len(line.encode("utf-8")) + 1
                if chunk_len + line_len > 5800 and chunk:
                    parts.append("\n".join(chunk))
                    chunk = []
                    chunk_len = 0
                chunk.append(line)
                chunk_len += line_len
            if chunk:
                parts.append("\n".join(chunk))
            translated_parts = []
            for part in parts:
                translated_parts.append(_translate_baidu(part, src, dest))
            return "\n".join(translated_parts)
        salt = str(int(time.time() * 1000))
        sign_str = appid + text + salt + key
        sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest()
        params = urlencode({
            "q": text,
            "from": src,
            "to": dest,
            "appid": appid,
            "salt": salt,
            "sign": sign,
        })
        url = f"https://fanyi-api.baidu.com/api/trans/vip/translate?{params}"
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "error_code" in data:
                log_error(f"百度翻译错误：{data.get('error_code')} - {data.get('error_msg', '')}")
                return text
            trans_result = data.get("trans_result", [])
            if trans_result:
                translated = "\n".join(item.get("dst", "") for item in trans_result)
                if translated and translated != text:
                    return translated
    except Exception as e:
        log_error(f"百度翻译异常：{e}")
    return text


def _translate_tencent(text, src="en", dest="zh"):
    if not text.strip():
        return text
    try:
        secret_id, secret_key = get_tencent_key()
        if not secret_id or not secret_key:
            return text
        service = "tmt"
        host = "tmt.tencentcloudapi.com"
        action = "TextTranslate"
        version = "2018-03-21"
        region = "ap-beijing"
        timestamp = int(time.time())
        date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))

        credential_scope = f"{date}/{service}/tc3_request"
        payload = json.dumps({
            "SourceText": text,
            "Source": src,
            "Target": dest,
            "ProjectId": 0,
        }, ensure_ascii=False)
        hashed_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        http_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        canonical_headers = f"content-type:application/json; charset=utf-8\nhost:{host}\nx-tc-action:{action.lower()}\n"
        signed_headers = "content-type;host;x-tc-action"
        canonical_request = f"{http_method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{hashed_payload}"

        algorithm = "TC3-HMAC-SHA256"
        hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical}"

        def _hmac_sha256(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = _hmac_sha256(("TC3" + secret_key).encode("utf-8"), date)
        secret_service = _hmac_sha256(secret_date, service)
        secret_signing = _hmac_sha256(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        headers = {
            "Authorization": f"{algorithm} Credential={secret_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}",
            "Content-Type": "application/json; charset=utf-8",
            "Host": host,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": version,
            "X-TC-Region": region,
        }
        req = Request(f"https://{host}", data=payload.encode("utf-8"), headers=headers)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = data.get("Response", {}).get("TargetText", "")
            if translated and translated != text:
                return translated
    except Exception as e:
        log_error(f"腾讯翻译异常：{e}")
    return text


def translate_chunk(text, src="en", dest="zh", providers_order=None):
    if not text.strip():
        return text
    if providers_order is None:
        providers_order = list(TRANSLATE_PROVIDERS.keys())

    translate_funcs = {
        "Google翻译": _translate_google,
        "百度翻译": _translate_baidu,
        "腾讯翻译君": _translate_tencent,
    }

    for p in providers_order:
        func = translate_funcs.get(p)
        if func:
            result = func(text, src, dest)
            if result and result != text:
                return result
    return text


def translate_text(text, src="en", dest="zh"):
    if not text.strip():
        return text
    cfg = load_translate_config()
    provider = cfg.get("provider", "Google翻译")
    providers_order = [provider]
    for p in TRANSLATE_PROVIDERS:
        if p not in providers_order:
            providers_order.append(p)

    segments = re.split(r'(\n{2,})', text)
    result_parts = []
    for seg in segments:
        if re.match(r'^\s*$', seg):
            result_parts.append(seg)
            continue
        if len(seg) > 480:
            lines = seg.split('\n')
            chunk = []
            for line in lines:
                chunk.append(line)
                chunk_text = '\n'.join(chunk)
                if len(chunk_text) > 450:
                    result_parts.append(translate_chunk(chunk_text, src, dest, providers_order))
                    chunk = []
            if chunk:
                result_parts.append(translate_chunk('\n'.join(chunk), src, dest, providers_order))
        else:
            result_parts.append(translate_chunk(seg, src, dest, providers_order))
    return ''.join(result_parts)
