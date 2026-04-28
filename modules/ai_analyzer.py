"""
AI 服务模块 - 提供通用的 AI 对话和 GitHub 项目分析功能。

常量：
    AI_PROVIDERS - AI 服务商配置字典
    AI_CONFIG_FILE - AI 配置文件路径

核心函数：
    ai_completion(provider_name, api_key, messages, **kwargs)：
        通用 AI 对话完成函数
        - 支持自定义消息列表和参数
        - 返回 AI 回复内容

    ai_query(provider_name, api_key, repo_info)：
        调用指定 AI 服务分析 GitHub 项目
        - 构建分析提示词（项目名、描述、Star数、语言、标签、许可证）
        - 返回 AI 分析结果文本

    load_ai_config() / save_ai_config(config)：
        加载/保存 AI 配置（加密存储 Key）

    get_local_models(base_url)：
        检测本地服务可用的模型列表

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
from modules.config import CONFIG_DIR, load_app_config, save_app_config
from modules.encrypt_utils import encrypt, decrypt, get_default_key

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
        "url": "http://localhost:8080/v1/chat/completions",
        "model": "DeepSeek-V3.2",
    },
}


def get_local_models(base_url):
    """检测本地服务可用的模型列表"""
    try:
        # 从 base_url 中提取基础地址（去掉 /chat/completions）
        if base_url.endswith("/chat/completions"):
            base_url = base_url.rsplit("/chat/completions", 1)[0]
        models_url = f"{base_url}/models"
        
        req = Request(models_url, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("data", [])
            return [model.get("id") for model in models if model.get("id")]
    except Exception as e:
        log_error(f"检测本地模型失败：{e}")
        return []


def load_ai_config():
    app_config = load_app_config()
    ai_config = app_config["ai"]
    config = {
        "provider": ai_config.get("provider", "通义千问 (Qwen)"),
        "keys": ai_config.get("keys", {}),
        "custom_keys": {},
        "local_model": ai_config.get("local_model", "DeepSeek-V3.2")
    }
    # 解密 custom_keys
    for name, enc_key in config["keys"].items():
        try:
            config["custom_keys"][name] = decrypt(enc_key)
        except Exception:
            pass
    return config


def save_ai_config(config):
    try:
        app_config = load_app_config()
        app_config["ai"]["provider"] = config.get("provider", "通义千问 (Qwen)")
        app_config["ai"]["local_model"] = config.get("local_model", "DeepSeek-V3.2")
        app_config["ai"]["keys"] = {}
        for name, plain_key in config.get("custom_keys", {}).items():
            if plain_key:
                app_config["ai"]["keys"][name] = encrypt(plain_key)
        save_app_config(app_config)
    except Exception as e:
        log_error(f"保存 AI 配置失败：{e}")


def ai_completion(provider_name, api_key, messages, **kwargs):
    """
    通用 AI 对话完成函数
    
    Args:
        provider_name: AI 服务商名称
        api_key: API Key
        messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
        **kwargs: 其他参数，如 max_tokens, temperature 等
    
    Returns:
        str: AI 回复内容
    """
    cfg = AI_PROVIDERS.get(provider_name)
    if not cfg:
        return "未找到 AI 服务商配置"
    if not api_key and provider_name != "本地服务 (127.0.0.1:8080)":
        return "未配置 API Key"

    url = cfg["url"]
    
    # 如果是本地服务，使用配置中保存的模型
    if provider_name == "本地服务 (127.0.0.1:8080)":
        config = load_ai_config()
        model = config.get("local_model", cfg["model"])
    else:
        model = cfg["model"]

    # 构建请求体
    body_dict = {
        "model": model,
        "messages": messages,
        "max_tokens": kwargs.get("max_tokens", 800),
        "temperature": kwargs.get("temperature", 0.7),
        "stream": kwargs.get("stream", False),
    }
    
    # 根据模型添加特定参数
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


def ai_query(provider_name, api_key, repo_info):
    """
    调用指定 AI 服务分析 GitHub 项目
    
    Args:
        provider_name: AI 服务商名称
        api_key: API Key
        repo_info: GitHub 仓库信息字典
    
    Returns:
        str: AI 分析结果文本
    """
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

    messages = [{"role": "user", "content": prompt}]
    return ai_completion(provider_name, api_key, messages, max_tokens=800, temperature=0.7)
