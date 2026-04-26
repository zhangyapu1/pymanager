"""
Markdown 渲染 - 将 Markdown/HTML 混合文本渲染为纯文本显示。

核心函数：
    render_markdown(text)：
        将 Markdown 和 HTML 混合文本转换为可读纯文本
        - HTML 标签转换：h1-h6、a、img、p、li、blockquote、code、pre 等
        - Markdown 语法转换：标题、列表、粗体、斜体、代码、链接、图片、引用
        - HTML 实体解码：&amp; &lt; &gt; &nbsp; &quot; &#39;
        - 多余空行压缩
"""
import re


def render_markdown(text):
    result = text
    result = re.sub(r'<div[^>]*>', '', result, flags=re.IGNORECASE)
    result = re.sub(r'</div>', '', result, flags=re.IGNORECASE)
    result = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'\2 (\1)', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*src=["\']([^"\']*)["\'][^>]*/?\s*>', r'[图片: \1]', result, flags=re.IGNORECASE)
    result = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?\s*>', r'[图片: \2]', result, flags=re.IGNORECASE)
    result = re.sub(r'<img[^>]*/?\s*>', '', result, flags=re.IGNORECASE)
    result = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n══════════════════════════════\n  \1\n══════════════════════════════\n', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n──────────────────────────────\n  \1\n──────────────────────────────\n', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n  ■ \1\n', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n  ● \1\n', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<h5[^>]*>(.*?)</h5>', r'\n  ○ \1\n', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<h6[^>]*>(.*?)</h6>', r'\n  · \1\n', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<br\s*/?\s*>', '\n', result, flags=re.IGNORECASE)
    result = re.sub(r'<hr\s*/?\s*>', '\n──────────────────────────────\n', result, flags=re.IGNORECASE)
    result = re.sub(r'<li[^>]*>(.*?)</li>', r'  • \1\n', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<(ul|ol)[^>]*>', '\n', result, flags=re.IGNORECASE)
    result = re.sub(r'</(ul|ol)>', '\n', result, flags=re.IGNORECASE)
    result = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<strong[^>]*>(.*?)</strong>', r'\1', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<b[^>]*>(.*?)</b>', r'\1', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<em[^>]*>(.*?)</em>', r'\1', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<i[^>]*>(.*?)</i>', r'\1', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<code[^>]*>(.*?)</code>', r'\1', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n\1\n', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'\n  │ \1\n', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<[^>]+>', '', result)
    result = re.sub(r'&amp;', '&', result)
    result = re.sub(r'&lt;', '<', result)
    result = re.sub(r'&gt;', '>', result)
    result = re.sub(r'&nbsp;', ' ', result)
    result = re.sub(r'&quot;', '"', result)
    result = re.sub(r'&#39;', "'", result)
    result = re.sub(r'^#{1}\s+(.+)$', r'\n══════════════════════════════\n  \1\n══════════════════════════════', result, flags=re.MULTILINE)
    result = re.sub(r'^#{2}\s+(.+)$', r'\n──────────────────────────────\n  \1\n──────────────────────────────', result, flags=re.MULTILINE)
    result = re.sub(r'^#{3}\s+(.+)$', r'\n  ■ \1', result, flags=re.MULTILINE)
    result = re.sub(r'^#{4}\s+(.+)$', r'\n  ● \1', result, flags=re.MULTILINE)
    result = re.sub(r'^#{5,6}\s+(.+)$', r'\n  ○ \1', result, flags=re.MULTILINE)
    result = re.sub(r'^[-*+]\s+', '  • ', result, flags=re.MULTILINE)
    result = re.sub(r'^\d+\.\s+', '  • ', result, flags=re.MULTILINE)
    result = re.sub(r'`{3}[\w]*\n', '', result)
    result = re.sub(r'`{3}', '', result)
    result = re.sub(r'`([^`]+)`', r'\1', result)
    result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)
    result = re.sub(r'\*([^*]+)\*', r'\1', result)
    result = re.sub(r'__([^_]+)__', r'\1', result)
    result = re.sub(r'_([^_]+)_', r'\1', result)
    result = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'[图片: \1]', result)
    result = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', result)
    result = re.sub(r'^>\s+(.+)$', r'  │ \1', result, flags=re.MULTILINE)
    result = re.sub(r'^---+$', '──────────────────────────────', result, flags=re.MULTILINE)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()
