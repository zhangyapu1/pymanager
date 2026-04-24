import re

def parse_dropped_files(raw):
    """解析拖拽事件返回的文件路径字符串，返回路径列表"""
    files = []
    raw = raw.strip('{}')
    pattern = r'\{([^{}]+)\}|([^\s]+)'
    for match in re.findall(pattern, raw):
        p = match[0] if match[0] else match[1]
        if p:
            files.append(p)
    return files