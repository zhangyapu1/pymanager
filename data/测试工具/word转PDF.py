# -*- coding: UTF-8 -*-
"""
Word转PDF功能模块

提供Word文档转PDF功能，支持批量转换。

使用方式：python word转PDF.py <输入路径> [输出路径]
示例：python word转PDF.py input.docx
      python word转PDF.py ./docx_dir ./pdf_dir
"""

import poword


def docx2pdf(path, output_path=None):
    """将Word转换为PDF。

    Args:
        path: Word文件路径或文件夹路径（支持批量转换）
        output_path: 转换后的输出路径，如果不存在会自动创建

    Returns:
        None
    """
    if output_path is None:
        output_path = path
    poword.docx2pdf(path=path, output_path=output_path)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("Word转PDF工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  docx2pdf - Word转PDF（支持批量转换文件夹）")
        print("\n使用方式：python word转PDF.py <输入路径> [输出路径]")
        print("示例：python word转PDF.py input.docx")
        print("      python word转PDF.py ./docx_dir ./pdf_dir")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "docx2pdf" and len(args) >= 1:
            output_path = args[1] if len(args) > 1 else None
            docx2pdf(path=args[0], output_path=output_path)
            print(f"转换完成：{args[0]}")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python word转PDF.py <输入路径> [输出路径]")
    except Exception as e:
        print(f"操作失败：{e}")
