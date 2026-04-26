# -*- coding:utf-8 -*-

import pospider

def url2ebook(url, tile):
    """将指定的URL转换为电子书格式。
    
    本函数通过调用pospider模块的url2ebook方法，将给定的URL转换为电子书。
    
    Args:
        url (str): 需要转换为电子书的网页URL
        tile (str): 电子书的标题
    
    Returns:
        None，但会生成电子书文件
    """
    pospider.url.url2ebook(url=url, tile=tile)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("网页处理工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  url2ebook - 将网页URL转换为电子书")
        print("\n使用方式：python web.py <功能名> [参数...]")
        print("示例：python web.py url2ebook https://example.com 我的电子书")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "url2ebook" and len(args) >= 2:
            url2ebook(url=args[0], tile=args[1])
            print(f"电子书已生成：{args[1]}")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python web.py <功能名> [参数...]")
    except Exception as e:
        print(f"操作失败：{e}")
