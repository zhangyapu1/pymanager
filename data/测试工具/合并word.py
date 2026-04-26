# -*- coding: UTF-8 -*-
"""
合并Word文档功能模块

提供多个Word文档合并功能。

使用方式：python 合并word.py <输入目录> <输出目录> [合并后文件名]
示例：python 合并word.py ./word-in ./word-out
"""

import poword


def merge4docx(input_path, output_path, new_word_name='merge4docx'):
    """合并多个Docx文件为一个文件。

    Args:
        input_path: 输入文件路径，可以是单个文件或文件夹路径
        output_path: 输出合并后文件的路径
        new_word_name: 合并后新文件的名称，默认为'merge4docx'

    Returns:
        None
    """
    poword.merge4docx(input_path=input_path, output_path=output_path, new_word_name=new_word_name)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("合并Word文档工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  merge4docx - 合并多个Docx文件")
        print("\n使用方式：python 合并word.py <输入目录> <输出目录> [合并后文件名]")
        print("示例：python 合并word.py ./word-in ./word-out")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "merge4docx" and len(args) >= 2:
            new_word_name = args[2] if len(args) > 2 else 'merge4docx'
            merge4docx(input_path=args[0], output_path=args[1], new_word_name=new_word_name)
            print(f"合并完成，输出目录：{args[1]}")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python 合并word.py <输入目录> <输出目录> [合并后文件名]")
    except Exception as e:
        print(f"操作失败：{e}")
