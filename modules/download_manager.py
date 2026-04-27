"""
下载管理器 - 封装文件和仓库下载功能。

核心函数：
    download_file(url, save_path, **kwargs)：
        下载单个文件
        - 支持进度回调
        - 支持超时设置

    download_repository(repo_full_name, dest_dir, progress_callback=None)：
        下载整个仓库
        - 递归下载所有文件
        - 支持进度回调

    download_folder(repo_full_name, folder_path, dest_dir, progress_callback=None)：
        下载指定文件夹
        - 递归下载文件夹内容
        - 支持进度回调

    collect_repository_files(repo_full_name, path="")：
        收集仓库所有文件信息
        - 递归遍历目录结构
        - 返回文件列表

依赖：modules.utils, modules.repository_manager
"""
import os
from modules.utils import download_file as utils_download_file
from modules.repository_manager import get_repository_contents, get_file_content
from modules.config import SCRIPT_MARKET_CONFIG, DATA_DIR


def download_file(url, save_path, **kwargs):
    """
    下载单个文件
    
    Args:
        url: 文件 URL
        save_path: 保存路径
        **kwargs:
            chunk_size: 分块大小
            timeout: 超时时间
            callback: 进度回调函数
    
    Returns:
        bool: 下载是否成功
    """
    config = SCRIPT_MARKET_CONFIG.get("download", {})
    
    chunk_size = kwargs.get("chunk_size", config.get("chunk_size", 1024 * 1024))
    timeout = kwargs.get("timeout", config.get("timeout", 60))
    callback = kwargs.get("callback")
    
    return utils_download_file(
        url=url,
        save_path=save_path,
        chunk_size=chunk_size,
        timeout=timeout,
        callback=callback
    )


def collect_repository_files(repo_full_name, path=""):
    """
    收集仓库所有文件信息
    
    Args:
        repo_full_name: 仓库完整名称 (owner/repo)
        path: 起始路径
    
    Returns:
        list: 文件信息列表，每个元素为 (fpath, furl, fdest_dir)
    """
    owner, repo = repo_full_name.split("/", 1)
    file_list = []
    
    def _collect_files(current_path):
        items = get_repository_contents(owner, repo, current_path)
        if not isinstance(items, list):
            return
        
        for item in items:
            name = item.get("name", "")
            ftype = item.get("type", "")
            
            if ftype == "dir":
                sub_path = f"{current_path}/{name}" if current_path else name
                _collect_files(sub_path)
            elif ftype == "file":
                download_url = item.get("download_url", "")
                fpath = f"{current_path}/{name}" if current_path else name
                file_list.append((fpath, download_url))
    
    _collect_files(path)
    return file_list


def download_repository(repo_full_name, dest_dir, progress_callback=None):
    """
    下载整个仓库
    
    Args:
        repo_full_name: 仓库完整名称 (owner/repo)
        dest_dir: 目标目录
        progress_callback: 进度回调函数 (pct, message)
    
    Returns:
        bool: 下载是否成功
    """
    try:
        os.makedirs(dest_dir, exist_ok=True)
        
        file_list = collect_repository_files(repo_full_name)
        total = len(file_list)
        
        if total == 0:
            if progress_callback:
                progress_callback(100, "无文件可下载")
            return True
        
        for i, (fpath, furl) in enumerate(file_list):
            if furl:
                try:
                    file_path = os.path.join(dest_dir, fpath.replace("/", os.sep))
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    content = get_file_content(furl)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    pass
            
            if progress_callback:
                pct = int((i + 1) / total * 100)
                progress_callback(pct, f"{i+1}/{total} 文件")
        
        return True
    except Exception as e:
        if progress_callback:
            progress_callback(0, f"下载失败: {str(e)}")
        return False


def download_folder(repo_full_name, folder_path, dest_dir, progress_callback=None):
    """
    下载指定文件夹
    
    Args:
        repo_full_name: 仓库完整名称 (owner/repo)
        folder_path: 文件夹路径
        dest_dir: 目标目录
        progress_callback: 进度回调函数 (pct, message)
    
    Returns:
        bool: 下载是否成功
    """
    try:
        os.makedirs(dest_dir, exist_ok=True)
        
        file_list = collect_repository_files(repo_full_name, folder_path)
        total = len(file_list)
        
        if total == 0:
            if progress_callback:
                progress_callback(100, "无文件可下载")
            return True
        
        for i, (fpath, furl) in enumerate(file_list):
            if furl:
                try:
                    # 移除 folder_path 前缀，只保留相对路径
                    relative_path = fpath[len(folder_path):].lstrip("/")
                    file_path = os.path.join(dest_dir, relative_path.replace("/", os.sep))
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    content = get_file_content(furl)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    pass
            
            if progress_callback:
                pct = int((i + 1) / total * 100)
                progress_callback(pct, f"{i+1}/{total} 文件")
        
        return True
    except Exception as e:
        if progress_callback:
            progress_callback(0, f"下载失败: {str(e)}")
        return False
