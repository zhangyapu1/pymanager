# -*- coding: UTF-8 -*-
"""Word processing functionality module.

Word处理功能模块。

This module provides Word document processing capabilities including format conversion,
file merging, image extraction, and more.

该模块提供了Word文档处理功能，包括格式转换、文件合并、图片提取等。

Author:
    程序员晚枫

Project:
    https://www.python-office.com
"""

import poword


def docx2pdf(path: str, output_path: str = None):
    """Convert Word to PDF.
    
    将Word转换为PDF。
    
    Args:
        path (str): Word file location / Word文件的位置。Supports batch processing / 支持批量处理: fill in folder location / 填写文件夹位置
        output_path (str, optional): output location after conversion / 转换后的输出位置。Will be created automatically if not exists / 如果不存在会自动创建
    
    Returns:
        None
    """
    if output_path is None:
        output_path = path
    poword.docx2pdf(path=path, output_path=output_path)

def merge4docx(input_path: str, output_path: str, new_word_name: str = 'merge4docx'):
    """Merge multiple Docx files into one file.
    
    合并多个Docx文件为一个文件。
    
    Args:
        input_path (str): input file path / 输入文件的路径。Can be a single file or folder path / 可以是单个文件或文件夹路径
        output_path (str): output path for merged file / 输出合并后文件的路径
        new_word_name (str, optional): name of merged new file / 合并后新文件的名称。Default / 默认: 'merge4docx'
    
    Returns:
        None
    """
    poword.merge4docx(input_path=input_path, output_path=output_path, new_word_name=new_word_name)


def doc2docx(input_path: str, output_path: str = r'./', output_name: str = None):
    """Convert Doc file to Docx file.
    
    将Doc文件转换为Docx文件。
    
    Args:
        input_path (str): input Doc file path / 输入Doc文件的路径
        output_path (str, optional): output Docx file path / 输出Docx文件的路径。Default / 默认: current directory / 当前目录
        output_name (str, optional): output Docx file name / 输出Docx文件的名称。Default / 默认: original filename / 原文件名
    
    Returns:
        None
    """
    poword.doc2docx(input_path=input_path, output_path=output_path, output_name=output_name)


def docx2doc(input_path: str, output_path: str = r'./', output_name: str = None):
    """Convert Docx file to Doc file.
    
    将Docx文件转换为Doc文件。
    
    Args:
        input_path (str): input Docx file path / 输入Docx文件的路径
        output_path (str, optional): output Doc file path / 输出Doc文件的路径。Default / 默认: current directory / 当前目录
        output_name (str, optional): output Doc file name / 输出Doc文件的名称。Default / 默认: original filename / 原文件名
    
    Returns:
        None
    """
    poword.docx2doc(input_path=input_path, output_path=output_path, output_name=output_name)

def docx4imgs(word_path, img_path):
    """Extract images from Word document.
    
    从Word里提取图片。
    
    Args:
        word_path (str): Word document path / Word文档的路径
        img_path (str): storage location for extracted images / 提取图片的存储位置。Will automatically generate a subdirectory / 会自动根据word名称在指定文件夹下生成一个子目录
    
    Returns:
        None
    """
    poword.docx4imgs(word_path=word_path, img_path=img_path)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("Word处理工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  docx2pdf    - Word转PDF")
        print("  merge4docx  - 合并多个Docx文件")
        print("  doc2docx    - Doc转Docx")
        print("  docx2doc    - Docx转Doc")
        print("  docx4imgs   - 从Word提取图片")
        print("\n使用方式：python word.py <功能名> [参数...]")
        print("示例：python word.py docx2pdf input.docx")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "docx2pdf" and len(args) >= 1:
            output_path = args[1] if len(args) > 1 else None
            docx2pdf(path=args[0], output_path=output_path)
            print(f"转换完成：{args[0]}")
        elif cmd == "merge4docx" and len(args) >= 2:
            new_word_name = args[2] if len(args) > 2 else 'merge4docx'
            merge4docx(input_path=args[0], output_path=args[1], new_word_name=new_word_name)
            print("合并完成")
        elif cmd == "doc2docx" and len(args) >= 1:
            output_path = args[1] if len(args) > 1 else './'
            output_name = args[2] if len(args) > 2 else None
            doc2docx(input_path=args[0], output_path=output_path, output_name=output_name)
            print(f"转换完成：{args[0]}")
        elif cmd == "docx2doc" and len(args) >= 1:
            output_path = args[1] if len(args) > 1 else './'
            output_name = args[2] if len(args) > 2 else None
            docx2doc(input_path=args[0], output_path=output_path, output_name=output_name)
            print(f"转换完成：{args[0]}")
        elif cmd == "docx4imgs" and len(args) >= 2:
            docx4imgs(word_path=args[0], img_path=args[1])
            print(f"图片提取完成：{args[1]}")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python word.py <功能名> [参数...]")
    except Exception as e:
        print(f"操作失败：{e}")
