"""
预览管理器 - 封装文件预览和渲染功能。

核心函数：
    preview_file(url, filename)：
        预览文件内容
        - 根据文件类型选择预览方式
        - 返回预览内容和类型

    preview_markdown(content)：
        预览 Markdown 内容
        - 渲染 Markdown 为 HTML
        - 返回渲染后的内容

    preview_python(content)：
        预览 Python 代码
        - 保持代码格式
        - 返回代码内容

    render_markdown_content(content)：
        渲染 Markdown 内容
        - 调用 markdown_renderer 进行渲染
        - 返回渲染结果

依赖：modules.markdown_renderer
"""
from modules.markdown_renderer import render_markdown
from modules.repository_manager import get_file_content
from modules.config import SCRIPT_MARKET_CONFIG


def render_markdown_content(content):
    """
    渲染 Markdown 内容
    
    Args:
        content: Markdown 内容
    
    Returns:
        str: 渲染后的 HTML 内容
    """
    return render_markdown(content)


def preview_markdown(content):
    """
    预览 Markdown 内容
    
    Args:
        content: Markdown 内容
    
    Returns:
        tuple: (预览内容, 是否为 Markdown)
    """
    rendered = render_markdown_content(content)
    return rendered, True


def preview_python(content):
    """
    预览 Python 代码
    
    Args:
        content: Python 代码内容
    
    Returns:
        tuple: (预览内容, 是否为 Markdown)
    """
    return content, False


def preview_file(url, filename):
    """
    预览文件内容
    
    Args:
        url: 文件 URL
        filename: 文件名
    
    Returns:
        tuple: (预览内容, 是否为 Markdown)
    """
    try:
        content = get_file_content(url)
        
        if filename.endswith(".md"):
            return preview_markdown(content)
        elif filename.endswith(".py"):
            return preview_python(content)
        else:
            return "（不支持预览此类型文件）", False
    except Exception as e:
        return f"加载失败：{str(e)}", False


def get_preview_config():
    """
    获取预览配置
    
    Returns:
        dict: 预览配置
    """
    return SCRIPT_MARKET_CONFIG.get("preview", {})
