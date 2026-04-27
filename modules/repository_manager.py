"""
仓库管理器 - 封装 GitHub 仓库搜索和内容加载功能。

核心函数：
    search_github_repos(query, **kwargs)：
        搜索 GitHub 仓库
        - 支持分页、排序等参数
        - 返回仓库列表

    get_repository_contents(owner, repo, path)：
        获取仓库文件列表
        - 支持递归获取子目录
        - 返回文件和目录列表

    get_repository_readme(owner, repo)：
        获取仓库 README 内容
        - 自动检测 README 文件
        - 返回 README 内容

    get_file_content(url)：
        获取文件原始内容
        - 支持各种文件类型
        - 返回文件内容字符串

依赖：modules.github_repo
"""
from modules.github_repo import (
    search_repos,
    get_repo_contents,
    get_raw_file,
    get_repo_readme,
    is_english,
)
from modules.config import SCRIPT_MARKET_CONFIG


def search_github_repos(query, **kwargs):
    """
    搜索 GitHub 仓库
    
    Args:
        query: 搜索关键词
        **kwargs: 额外参数
            page: 页码
    
    Returns:
        dict: 仓库搜索结果
    """
    page = kwargs.get("page", 1)
    return search_repos(keyword=query, page=page)


def get_repository_contents(owner, repo, path=""):
    """
    获取仓库文件列表
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        path: 路径（可选）
    
    Returns:
        list: 文件和目录列表
    """
    return get_repo_contents(owner, repo, path)


def get_repository_readme(owner, repo):
    """
    获取仓库 README 内容
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
    
    Returns:
        str: README 内容
    """
    return get_repo_readme(owner, repo)


def get_file_content(url):
    """
    获取文件原始内容
    
    Args:
        url: 文件 URL
    
    Returns:
        str: 文件内容
    """
    return get_raw_file(url)


def check_language(content):
    """
    检测内容语言
    
    Args:
        content: 内容字符串
    
    Returns:
        bool: 是否为英文
    """
    return is_english(content)
