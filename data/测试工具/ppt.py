# -*- coding:utf-8 -*-
"""PowerPoint processing functionality module.

PowerPoint处理功能模块。

This module provides PowerPoint file processing capabilities including format conversion,
file merging, and more.

该模块提供了PowerPoint文件处理功能，包括格式转换、文件合并等。

Author:
    程序员晚枫

Project:
    https://www.python-office.com
"""

# 导入处理PPT的模块
import poppt


def ppt2pdf(path: str, output_path=r'./'):
    """Convert PowerPoint to PDF.
    
    将PPT转换为PDF。
    
    Args:
        path (str): PowerPoint file path / PPT文件路径
        output_path (str, optional): output PDF file path / 输出PDF文件路径。Default / 默认: current directory / 当前目录
    
    Returns:
        None
    """
    poppt.ppt2pdf(path=path, output_path=output_path)


def ppt2img(input_path: str, output_path=r'./', merge: bool = False):
    """Convert PowerPoint to images, can convert to long image.
    
    将PPT转换为图片，可以转为长图。
    
    Args:
        input_path (str): PowerPoint file location / 存放PPT的位置。For single file, write file path / 转换单个文件可以写文件的路径; for folder, write folder path / 转换文件夹可以写文件夹的路径
        output_path (str, optional): storage location for result images / 结果图片的存储位置。Default / 默认: current directory / 当前目录
        merge (bool, optional): True converts to 1 image / True转为1张图片, False converts to multiple images / False转为多张图片。Default / 默认: False
    
    Returns:
        None
    """
    poppt.ppt2img(input_path=input_path, output_path=output_path, merge=merge)


def merge4ppt(input_path: str, output_path=r'./', output_name: str = 'merge4ppt.pptx'):
    """Merge multiple PowerPoint files.
    
    合并多个PPT文件。
    
    Args:
        input_path (str): input PowerPoint file path / 输入PPT文件路径
        output_path (str, optional): output PowerPoint file path / 输出PPT文件路径。Default / 默认: current directory / 当前目录
        output_name (str, optional): merged PowerPoint filename / 合并后的PPT文件名。Default / 默认: 'merge4ppt.pptx'
    
    Returns:
        None
    """
    poppt.merge4ppt(input_path=input_path, output_path=output_path, output_name=output_name)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("PPT处理工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  ppt2pdf  - PPT转PDF")
        print("  ppt2img  - PPT转图片")
        print("  merge4ppt - 合并多个PPT")
        print("\n使用方式：python ppt.py <功能名> [参数...]")
        print("示例：python ppt.py ppt2pdf input.pptx")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "ppt2pdf" and len(args) >= 1:
            output_path = args[1] if len(args) > 1 else './'
            ppt2pdf(path=args[0], output_path=output_path)
            print(f"转换完成：{args[0]}")
        elif cmd == "ppt2img" and len(args) >= 1:
            output_path = args[1] if len(args) > 1 else './'
            merge = args[2].lower() == 'true' if len(args) > 2 else False
            ppt2img(input_path=args[0], output_path=output_path, merge=merge)
            print(f"转换完成：{args[0]}")
        elif cmd == "merge4ppt" and len(args) >= 1:
            output_path = args[1] if len(args) > 1 else './'
            output_name = args[2] if len(args) > 2 else 'merge4ppt.pptx'
            merge4ppt(input_path=args[0], output_path=output_path, output_name=output_name)
            print("合并完成")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python ppt.py <功能名> [参数...]")
    except Exception as e:
        print(f"操作失败：{e}")
