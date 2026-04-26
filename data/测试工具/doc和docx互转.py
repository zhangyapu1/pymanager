# -*- coding: UTF-8 -*-
"""
Doc和Docx互转功能模块

提供Word文档格式转换功能，包括：
- doc2docx: Doc转Docx
- docx2doc: Docx转Doc

使用方式：python doc和docx互转.py <功能名> [参数...]
示例：python doc和docx互转.py doc2docx input.doc output_dir
"""

import poword


def doc2docx(input_path, output_path='./'):
    """将Doc文件转换为Docx文件。

    Args:
        input_path: 输入Doc文件路径
        output_path: 输出目录路径，默认为当前目录

    Returns:
        None
    """
    poword.doc2docx(input_path=input_path, output_path=output_path)


def docx2doc(input_path, output_path='./'):
    """将Docx文件转换为Doc文件。

    Args:
        input_path: 输入Docx文件路径
        output_path: 输出目录路径，默认为当前目录

    Returns:
        None
    """
    poword.docx2doc(input_path=input_path, output_path=output_path)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("Doc/Docx互转工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  doc2docx - Doc转Docx")
        print("  docx2doc - Docx转Doc")
        print("\n使用方式：python doc和docx互转.py <功能名> <输入文件> [输出目录]")
        print("示例：python doc和docx互转.py doc2docx input.doc ./output")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "doc2docx" and len(args) >= 1:
            output_path = args[1] if len(args) > 1 else './'
            doc2docx(input_path=args[0], output_path=output_path)
            print(f"转换完成：{args[0]}")
        elif cmd == "docx2doc" and len(args) >= 1:
            output_path = args[1] if len(args) > 1 else './'
            docx2doc(input_path=args[0], output_path=output_path)
            print(f"转换完成：{args[0]}")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python doc和docx互转.py <功能名> <输入文件> [输出目录]")
    except Exception as e:
        print(f"操作失败：{e}")
