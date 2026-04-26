"""Markdown processing functionality module.

Markdown处理功能模块。

This module provides Markdown file processing capabilities including format conversion.

该模块提供了Markdown文件处理功能，包括格式转换。

Author:
    程序员晚枫

Project:
    https://www.python-office.com
"""

import pomarkdown


def excel2markdown(input_file, output_file=r'./excel2markdown.md', sheet_name=None):
    """Convert Excel file to Markdown format file.
    
    将Excel文件转换为Markdown格式的文件。
    
    This function uses the excel2markdown function in the pomarkdown library to perform conversion.
    It is mainly responsible for defining the input/output paths and worksheet names for conversion.
    
    本函数利用pomarkdown库中的excel2markdown函数执行转换操作。
    主要负责定义转换的输入输出路径及工作表名称。
    
    Args:
        input_file (str): input Excel file path / 输入Excel文件的路径
        output_file (str, optional): output Markdown file path / 输出Markdown文件的路径。Default / 默认: './excel2markdown.md' in current directory / 当前目录下的'excel2markdown.md'
        sheet_name (str, optional): Excel worksheet name to convert / 需要转换的Excel工作表名称。Default / 默认: None (convert all worksheets / 转换所有工作表)
    
    Returns:
        None
    """
    # 调用pomarkdown库中的excel2markdown函数执行Excel到Markdown的转换
    pomarkdown.excel2markdown(input_file=input_file, output_file=output_file, sheet_name=sheet_name)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("Markdown处理工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  excel2markdown - Excel转Markdown")
        print("\n使用方式：python markdown.py <功能名> [参数...]")
        print("示例：python markdown.py excel2markdown input.xlsx output.md")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "excel2markdown" and len(args) >= 1:
            output_file = args[1] if len(args) > 1 else './excel2markdown.md'
            sheet_name = args[2] if len(args) > 2 else None
            excel2markdown(input_file=args[0], output_file=output_file, sheet_name=sheet_name)
            print(f"转换完成：{output_file}")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python markdown.py <功能名> [参数...]")
    except Exception as e:
        print(f"操作失败：{e}")

