"""
GitHub 仓库 API - 搜索仓库、获取文件列表、下载文件内容。

常量：
    GITHUB_API - GitHub API 基础 URL
    USER_AGENT - 请求 User-Agent
    PER_PAGE   - 每页结果数 30

核心函数：
    search_repos(keyword, page)：
        搜索 GitHub Python 仓库，按 Star 排序

    get_repo_contents(owner, repo, path)：
        获取仓库指定路径下的文件/文件夹列表

    get_raw_file(download_url)：
        下载文件原始内容（文本）

    get_repo_readme(owner, repo)：
        获取仓库 README 内容（自动 base64 解码）

    is_english(text)：
        判断文本是否主要为英文（拉丁字母占比 > 85%）

依赖：modules.token_crypto
"""
import base64
import json
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import HTTPError

from modules.token_crypto import get_api_token, get_default_token as get_github_default_token, delete_api_token

GITHUB_API = "https://api.github.com"
USER_AGENT = "pymanager/1.5.0"
PER_PAGE = 30


def _get_github_headers(use_token=True):
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github.v3+json"}
    if use_token:
        token = get_api_token()
        if not token:
            token = get_github_default_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


def _request(url, use_token=True):
    req = Request(url, headers=_get_github_headers(use_token))
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        if e.code == 401 and use_token:
            # Token 无效，删除保存的用户 Token（如果有），然后尝试匿名请求
            delete_api_token()
            return _request(url, use_token=False)
        raise


def _request_raw(url, use_token=True):
    headers = {"User-Agent": USER_AGENT}
    if use_token:
        token = get_api_token()
        if not token:
            token = get_github_default_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except HTTPError as e:
        if e.code == 401 and use_token:
            # Token 无效，删除保存的用户 Token（如果有），然后尝试匿名请求
            delete_api_token()
            return _request_raw(url, use_token=False)
        raise


def search_repos(keyword, page=1):
    url = f"{GITHUB_API}/search/repositories?q={quote(keyword)}+language:python&sort=stars&order=desc&per_page={PER_PAGE}&page={page}"
    return _request(url)


def get_repo_contents(owner, repo, path=""):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    return _request(url)


def get_raw_file(download_url):
    return _request_raw(download_url)


def get_repo_readme(owner, repo):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/readme"
    data = _request(url)
    content_b64 = data.get("content", "")
    encoding = data.get("encoding", "base64")
    if encoding == "base64":
        return base64.b64decode(content_b64).decode("utf-8", errors="replace")
    return content_b64


def is_english(text):
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    total = sum(1 for c in text if c.isalpha())
    if total == 0:
        return False
    return latin / total > 0.85
