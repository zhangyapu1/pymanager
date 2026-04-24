import re

# 预编译正则表达式以提高性能（如果函数被频繁调用）
# 匹配模式：
# 1. \{([^{}]*)\} : 匹配花括号内的内容（不支持嵌套花括号），捕获组1
# 2. ([^\s]+)     : 匹配非空白字符序列，捕获组2
# 注意：原代码逻辑中，如果花括号内为空，match[0]为空字符串，if p: 会过滤掉。
# 这里使用 * 允许空匹配，随后通过 if p 过滤，行为与原代码一致但更健壮。
_PATTERN = re.compile(r'\{([^{}]*)\}|([^\s]+)')

def parse_dropped_files(raw):
    """解析拖拽事件返回的文件路径字符串，返回路径列表"""
    # 1. 输入验证
    if not isinstance(raw, str):
        return []
    
    files = []
    # 2. 直接使用正则查找，移除不安全的 strip 操作
    # findall 返回元组列表: [('path_in_braces', ''), ('', 'path_no_spaces'), ...]
    matches = _PATTERN.findall(raw)
    
    for match in matches:
        # match[0] 是花括号内的内容，match[1] 是非空白内容
        # 如果花括号匹配成功，match[0] 有值，match[1] 为空
        # 如果非空白匹配成功，match[0] 为空，match[1] 有值
        p = match[0] if match[0] else match[1]
        
        # 3. 过滤空字符串（例如空花括号 {} 或纯空白）
        if p:
            files.append(p)
            
    return files