# -*- coding: utf-8 -*-
"""
Excel转Markdown功能模块

提供Excel文件转Markdown格式功能。

使用方式：python Excel转Markdown.py <输入文件> [输出文件]
示例：python Excel转Markdown.py input.xlsx output.md
"""

import pomarkdown


def excel2markdown(input_file, output_file='./excel2markdown.md', sheet_name=None):
    """将Excel文件转换为Markdown格式。

    Args:
        input_file: 输入Excel文件路径
        output_file: 输出Markdown文件路径，默认为'./excel2markdown.md'
        sheet_name: 需要转换的Excel工作表名称，默认转换所有工作表

    Returns:
        None
    """
    pomarkdown.excel2markdown(input_file=input_file, output_file=output_file, sheet_name=sheet_name)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("Excel转Markdown工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n使用方式：python Excel转Markdown.py <输入文件> [输出文件] [工作表名]")
        print("示例：python Excel转Markdown.py input.xlsx output.md")
        print("      python Excel转Markdown.py input.xlsx output.md Sheet1")
        sys.exit(0)

    args = sys.argv[1:]

    try:
        input_file = args[0]
        output_file = args[1] if len(args) > 1 else './excel2markdown.md'
        sheet_name = args[2] if len(args) > 2 else None
        excel2markdown(input_file=input_file, output_file=output_file, sheet_name=sheet_name)
        print(f"转换完成：{output_file}")
    except Exception as e:
        print(f"操作失败：{e}")
