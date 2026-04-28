"""
GitHub API 通信 - 版本查询、文件下载、Release 发布。

常量：
    PROJECT_URL       - 项目主页
    REPO_OWNER        - GitHub 仓库所有者
    REPO_NAME         - GitHub 仓库名
    RELEASE_API_URL   - GitHub Releases API 地址
    DOWNLOAD_TIMEOUT  - 下载超时时间 60 秒

核心函数：
    fetch_latest_version(parent, output_callback, ui_callback)：
        获取最新版本信息
        - 优先使用 WebDAV（坚果云）
        - 其次使用 Cloudflare Workers
        - 最后回退到 GitHub

    download_file(url, dest_path, ...)：
        下载更新文件
        - 支持进度回调
        - SSL 错误时自动降级验证
        - WebDAV 下载保护（只读）
        - 非标准链接引导浏览器手动下载

    create_github_release(version, changelog, output_callback)：
        创建 GitHub Release
        - 使用 GitHub API 发布新版本
        - 自动设置 tag_name 和 target_commitish

异常类：
    RateLimitError - GitHub API 速率限制异常

依赖：modules.token_crypto, base64
"""
import os
import logging
import urllib.request
import urllib.error
import json
import ssl
import webbrowser
import base64

from .config import CURRENT_VERSION

logger = logging.getLogger(__name__)

if not logger.handlers:
    _log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(_log_dir, exist_ok=True)
    _handler = logging.FileHandler(os.path.join(_log_dir, 'updater_log.txt'), encoding='utf-8')
    _handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

PROJECT_URL = "https://github.com/zhangyapu1/pymanager"
REPO_OWNER = "zhangyapu1"
REPO_NAME = "pymanager"
RELEASE_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
DOWNLOAD_TIMEOUT = 60

# WebDAV 更新配置（坚果云）- 优先使用
WEBDAV_CONFIG_KEY = "webdav_update"
USE_WEBDAV_FOR_UPDATES = True
WEBDAV_URL = "https://dav.jianguoyun.com/dav/pymanager/"

from modules.token_crypto import get_api_token, save_api_token, get_default_token


def _output(callback, msg):
    logger.info(msg)
    if callback:
        try:
            callback(msg)
        except (RuntimeError, OSError):
            pass


def _output_error(callback, msg):
    logger.error(msg)
    if callback:
        try:
            callback(f"[错误] {msg}")
        except (RuntimeError, OSError):
            pass


class RateLimitError(Exception):
    pass


def _get_webdav_credentials():
    """从配置文件或加密硬编码获取 WebDAV 凭据"""
    try:
        import json
        settings_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            webdav_config = settings.get(WEBDAV_CONFIG_KEY, {})
            username = webdav_config.get('username', '')
            password = webdav_config.get('password', '')
            if username and password:
                return username, password
    except Exception:
        pass

    try:
        encoded = "c2xhbmRlci15YXJuLWNpZGVyQGR1Y2suY29tOmFja241NjlqOW42cno5NWc="
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        return username, password
    except Exception:
        return '', ''


def _build_webdav_auth(username, password):
    """构建 WebDAV Basic Auth 认证头"""
    if not username or not password:
        return None
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
    return f"Basic {encoded}"


def fetch_latest_version_webdav(output_callback=None):
    """从 WebDAV 获取最新版本信息"""
    try:
        version_file_url = f"{WEBDAV_URL}version.json"
        _output(output_callback, f"[WebDAV] 检查更新: {version_file_url}")

        headers = {"Accept": "application/json"}

        username, password = _get_webdav_credentials()
        auth = _build_webdav_auth(username, password)
        if auth:
            headers["Authorization"] = auth

        req = urllib.request.Request(version_file_url, headers=headers)

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))

        latest = data.get("version", CURRENT_VERSION)
        download_filename = data.get("downloadUrl", f"pymanager-{latest}.zip")
        download_url = f"{WEBDAV_URL}{download_filename}"

        _output(output_callback, f"[WebDAV] 最新版本: {latest}, 下载链接: {download_url}")
        return latest, download_url

    except Exception as e:
        _output_error(output_callback, f"WebDAV更新检查失败: {e}")
        return None, None


def download_file_webdav(url, dest_path, username="", password="", output_callback=None, progress_callback=None):
    """从 WebDAV 下载文件（只读操作，禁止上传）"""
    allowed_prefix = WEBDAV_URL.rstrip('/')
    if not url.startswith(allowed_prefix):
        _output_error(output_callback, f"WebDAV 安全拒绝：不允许多级目录访问")
        return False

    try:
        _output(output_callback, f"[WebDAV] 开始下载: {url}")

        headers = {}
        if not username or not password:
            username, password = _get_webdav_credentials()
        auth = _build_webdav_auth(username, password)
        if auth:
            headers["Authorization"] = auth

        req = urllib.request.Request(url, headers=headers)

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT, context=ctx) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded_size = 0
            chunk_size = 1024 * 1024

            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    if progress_callback and total_size > 0:
                        progress = int((downloaded_size / total_size) * 100)
                        progress_callback(progress)

        _output(output_callback, f"[WebDAV] 下载完成: {dest_path}")
        return True

    except Exception as e:
        _output_error(output_callback, f"WebDAV下载失败: {e}")
        return False


def webdav_upload_file(local_path, remote_name, output_callback=None):
    """WebDAV 上传文件（此功能已禁用，禁止通过程序上传）"""
    _output_error(output_callback, "WebDAV 上传功能已禁用，不允许通过程序上传文件")
    return False


def prompt_for_token(parent=None, ui_callback=None):
    if ui_callback:
        token = ui_callback.ask_string(
            "API Token",
            "请输入GitHub Personal Access Token 以提高 API 限额。\n\n"
            "如何获取？\n"
            "1. 访问 https://github.com/settings/tokens\n"
            "2. 生成新令牌，勾选 'repo' 或 'projects' 权限\n"
            "3. 复制并粘贴到此处。\n\n"
            "若跳过，匿名请求每小时限制 60 次。",
            parent=parent
        )
    else:
        return ""
    if token:
        save_api_token(token)
        return token
    return ""


def is_version_greater(v1, v2):
    def normalize_version(v):
        if v.startswith(('v', 'V')):
            v = v[1:]
        parts = []
        for p in v.split('.'):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
        return parts

    try:
        a1 = normalize_version(v1)
        a2 = normalize_version(v2)

        max_len = max(len(a1), len(a2))
        a1 += [0] * (max_len - len(a1))
        a2 += [0] * (max_len - len(a2))

        return a1 > a2
    except (ValueError, TypeError, AttributeError):
        return v1 > v2


def build_auth_headers(parent=None):
    headers = {"User-Agent": f"ScriptManager/{CURRENT_VERSION}"}
    token = get_api_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
        return headers, "用户Token"
    default_token = get_default_token()
    if default_token:
        headers["Authorization"] = f"Bearer {default_token}"
        return headers, "内置Token"
    return headers, "未认证"


def fetch_release_data(headers):
    api_url = RELEASE_API_URL
    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}")
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise RateLimitError("API 速率限制已达上限")
        raise
    except ssl.SSLError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}")
            return json.loads(resp.read().decode('utf-8'))


def parse_latest_version(data):
    latest = data.get("tag_name", "") or data.get("name", "")
    if latest.startswith("v"):
        latest = latest[1:]
    return latest


def select_download_url(data):
    assets = data.get("assets", [])
    preferred_exts = ('.exe', '.zip', '.rar')

    for asset in assets:
        name = asset.get("name", "")
        url = asset.get("browser_download_url", "")
        if any(name.endswith(ext) for ext in preferred_exts):
            logger.debug(f"选择首选资产: {name}")
            return url, name

    if assets:
        first_asset = assets[0]
        logger.debug(f"选择第一个资产: {first_asset.get('name', '')}")
        return first_asset.get("browser_download_url", ""), first_asset.get("name", "")

    download_url = data.get("zipball_url", "")
    if download_url:
        logger.debug("使用 zipball_url")
        return download_url, "源码包(zip)"

    download_url = data.get("tarball_url", "")
    if download_url:
        logger.debug("使用 tarball_url")
        return download_url, "源码包(tar)"

    logger.debug("使用 html_url 作为兜底")
    return data.get("html_url", PROJECT_URL), "项目主页"


def fetch_latest_version(parent=None, output_callback=None, ui_callback=None):
    # 优先使用 WebDAV（适用于国内用户）
    if USE_WEBDAV_FOR_UPDATES:
        latest, download_url = fetch_latest_version_webdav(output_callback)
        if latest and download_url:
            return latest, download_url
        _output(output_callback, "[WebDAV] 回退到 GitHub")

    # 回退到 GitHub
    try:
        headers = {"Accept": "application/json"}
        data = fetch_release_data(headers)
        latest = parse_latest_version(data)
        download_url, asset_name = select_download_url(data)

        _output(output_callback, f"[GitHub] 最新版本: {latest}, 下载链接: {download_url}")
        return latest, download_url
    except RateLimitError:
        _output_error(output_callback, "API 速率限制已达上限")
        if ui_callback:
            ui_callback.show_warning("API 限制", "API请求次数已达上限，请稍后再试。", parent=parent)
        return CURRENT_VERSION, PROJECT_URL
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        _output_error(output_callback, f"获取版本失败: {e}")
        return CURRENT_VERSION, PROJECT_URL


def download_file(url, dest_path, parent=None, output_callback=None, ui_callback=None, progress_callback=None):
    _output(output_callback, f"开始下载文件，URL: {url}")
    _output(output_callback, f"目标路径: {dest_path}")

    # 检查是否为 WebDAV 链接且已配置凭据
    if WEBDAV_URL and url.startswith(WEBDAV_URL):
        username, password = _get_webdav_credentials()
        if username and password:
            _output(output_callback, "[WebDAV] 使用 WebDAV 下载")
            return download_file_webdav(url, dest_path, username, password, output_callback=output_callback, progress_callback=progress_callback)
        else:
            _output_error(output_callback, "WebDAV 未配置用户名或密码，请在设置中配置")
            return False

    is_direct_download = (
        url.endswith('.exe') or
        url.endswith('.zip') or
        url.endswith('.rar') or
        'api.github.com' in url
    )

    if not is_direct_download:
        _output(output_callback, f"URL不是标准的直接下载链接，引导手动下载: {url}")
        if ui_callback:
            ui_callback.show_info("下载提示", f"无法直接自动下载此链接。\n请在浏览器中手动下载：\n{url}")
        webbrowser.open(url)
        return False

    try:
        headers = {"User-Agent": "ScriptManager"}

        req = urllib.request.Request(url, headers=headers)
        try:
            opener = urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT)
        except ssl.SSLError:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            opener = urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT, context=ctx)
        with opener as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            with open(dest_path, 'wb') as out_file:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = int(downloaded * 100 / total_size)
                        if progress_callback:
                            progress_callback(percent, f"下载中... {percent}%")
                    else:
                        if progress_callback:
                            progress_callback(-1, f"下载中... ({downloaded} bytes)")

        _output(output_callback, f"下载完成: {dest_path}")
        return True
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        msg = f"下载更新文件时出错：{e}\n\n请尝试手动下载：{url}"
        _output_error(output_callback, msg)
        if ui_callback:
            ui_callback.show_error("下载失败", msg, parent=parent)
        webbrowser.open(url)
        return False


def get_latest_version():
    latest, _ = fetch_latest_version()
    return latest


def create_github_release(version, changelog, output_callback=None):
    token = get_api_token()
    if not token:
        default = get_default_token()
        if default:
            token = default
    if not token:
        _output_error(output_callback, "没有可用的 GitHub Token，无法发布 Release")
        return False

    tag_name = f"v{version}"
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"

    body = {
        "tag_name": tag_name,
        "target_commitish": "main",
        "name": tag_name,
        "body": changelog,
        "draft": False,
        "prerelease": False,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": f"ScriptManager/{CURRENT_VERSION}",
        "Content-Type": "application/json",
    }

    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except ssl.SSLError:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                result = json.loads(resp.read().decode("utf-8"))

        html_url = result.get("html_url", "")
        _output(output_callback, f"Release 发布成功: {html_url}")

        return True

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            pass
        _output_error(output_callback, f"发布 Release 失败 (HTTP {e.code}): {error_body}")
        return False
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        _output_error(output_callback, f"发布 Release 失败: {e}")
        return False
