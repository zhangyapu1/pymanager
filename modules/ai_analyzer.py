"""
AI 分析 - 使用智谱AI、通义千问、DeepSeek 分析 GitHub 项目。

常量：
    AI_PROVIDERS - AI 服务商配置字典
    AI_CONFIG_FILE - AI 配置文件路径

核心函数：
    ai_query(provider_name, api_key, repo_info)：
        调用指定 AI 服务分析 GitHub 项目
        - 构建分析提示词（项目名、描述、Star数、语言、标签、许可证）
        - 返回 AI 分析结果文本

    load_ai_config() / save_ai_config(config)：
        加载/保存 AI 配置（加密存储 Key）

AI 服务商：
    通义千问 (Qwen)     - dashscope API
    智谱AI (GLM-4-Flash) - bigmodel API
    DeepSeek            - deepseek API
    本地服务 (127.0.0.1:8080) - 本地部署的 OpenAI 兼容接口

依赖：modules.encrypt_utils
"""
import json
import os
from urllib.request import urlopen, Request

from modules.logger import log_error
from modules.config import CONFIG_DIR
from modules.encrypt_utils import encrypt, decrypt, get_default_key

AI_CONFIG_FILE = os.path.join(CONFIG_DIR, "ai_config.json")

AI_PROVIDERS = {
    "通义千问 (Qwen)": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-turbo",
    },
    "智谱AI (GLM-4-Flash)": {
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-4-flash",
    },
    "DeepSeek": {
        "url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
    },
    "本地服务 (127.0.0.1:8080)": {
        "url": "http://127.0.0.1:8080/v1/chat/completions",
        "model": "local-model",
    },
}


def load_ai_config():
    config = {"provider": "通义千问 (Qwen)", "keys": {}, "custom_keys": {}}
    if os.path.exists(AI_CONFIG_FILE):
        try:
            with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                saved_provider = saved.get("provider", config["provider"])
                if saved_provider in AI_PROVIDERS:
                    config["provider"] = saved_provider
                for name, enc_key in saved.get("keys", {}).items():
                    try:
                        config["custom_keys"][name] = decrypt(enc_key)
                    except Exception:
                        pass
        except Exception:
            pass
    return config


def save_ai_config(config):
    try:
        to_save = {"provider": config.get("provider", "通义千问 (Qwen)"), "keys": {}}
        for name, plain_key in config.get("custom_keys", {}).items():
            if plain_key:
                to_save["keys"][name] = encrypt(plain_key)
        with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(f"保存 AI 配置失败：{e}")


def ai_query(provider_name, api_key, repo_info):
    cfg = AI_PROVIDERS.get(provider_name)
    if not cfg:
        return "未找到 AI 服务商配置"
    if not api_key and provider_name != "本地服务 (127.0.0.1:8080)":
        return "未配置 API Key，请在右侧设置"

    url = cfg["url"]
    model = cfg["model"]

    name = repo_info.get("full_name", "")
    desc = repo_info.get("description", "") or "无描述"
    stars = repo_info.get("stargazers_count", 0)
    lang = repo_info.get("language", "")
    topics = ", ".join(repo_info.get("topics", [])) or "无"
    license_info = (repo_info.get("license") or {}).get("name", "未知")

    prompt = (
        f"请用简体中文分析以下 GitHub 项目，给出简洁有用的信息：\n\n"
        f"项目：{name}\n"
        f"描述：{desc}\n"
        f"Star 数：{stars}\n"
        f"语言：{lang}\n"
        f"标签：{topics}\n"
        f"许可证：{license_info}\n\n"
        f"请从以下方面分析：\n"
        f"1. 项目简介（一句话概括）\n"
        f"2. 主要功能和用途\n"
        f"3. 适合什么类型的用户\n"
        f"4. 项目质量评估（基于 Star 数和描述）\n"
        f"5. 使用建议和注意事项"
    )

    body_dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.7,
        "stream": False,
    }
    if "deepseek" in model.lower():
        body_dict["reasoning_effort"] = "none"
    elif "qwen" in model.lower():
        body_dict["enable_thinking"] = False
    elif "glm" in model.lower():
        body_dict["do_sample"] = True

    body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = Request(url, data=body, headers=headers)

    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
