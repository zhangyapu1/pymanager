"""
PDF处理功能模块

提供PDF文件处理功能，包括格式转换、加密解密、水印添加等。

功能列表：
- pdf2docx: PDF转Word文档
- pdf2imgs: PDF转图片
- txt2pdf: 文本文件转PDF
- split4pdf: 拆分PDF文件
- encrypt4pdf: 加密PDF文件
- decrypt4pdf: 解密PDF文件
- add_text_watermark: 添加文本水印
- merge2pdf: 合并多个PDF文件
- del4pdf: 删除PDF指定页面
- add_watermark_by_parameters: 参数化添加水印
"""

import warnings
from pathlib import Path

import popdf


def pdf2docx(input_file=None, output_file=None, input_path=None, output_path=None, file_path=None):
    if file_path is not None:
        warnings.warn("参数 'file_path' 已被弃用，请改用 'input_file' 参数。", DeprecationWarning, stacklevel=2)
        if input_file is None:
            input_file = file_path

    if input_file is not None and output_path is not None:
        input_path_obj = Path(input_file)
        output_file = str(Path(output_path) / f"{input_path_obj.stem}.docx")
        popdf.pdf2docx(input_file=input_file, output_file=output_file)
    elif input_file is not None and output_file is not None:
        popdf.pdf2docx(input_file=input_file, output_file=output_file)
    elif input_path is not None and output_path is not None:
        popdf.pdf2docx(input_path=input_path, output_path=output_path)


def pdf2imgs(input_file=None, output_file=None, merge=False, pdf_path=None, out_dir=None):
    if pdf_path is not None:
        warnings.warn("参数 'pdf_path' 已被弃用，请改用 'input_file' 参数。", DeprecationWarning, stacklevel=2)
        if input_file is None:
            input_file = pdf_path
    if out_dir is not None:
        warnings.warn("参数 'out_dir' 已被弃用，请改用 'output_file' 参数。", DeprecationWarning, stacklevel=2)
        if output_file is None:
            output_file = out_dir

    popdf.pdf2imgs(input_file=input_file, output_path=output_file, merge=merge)


def txt2pdf(input_file=None, output_file=None):
    if output_file is None:
        output_file = 'txt2pdf.pdf'
    popdf.txt2pdf(input_file=input_file, output_file=output_file)


def split4pdf(input_file=None, output_file=None, from_page=-1, to_page=-1):
    if output_file is None:
        output_file = r'./output_path/split_pdf.pdf'
    popdf.split4pdf(input_file=input_file, output_file=output_file, from_page=from_page, to_page=to_page)


def encrypt4pdf(password, input_file=None, output_file=None, input_path=None, output_path=None):
    popdf.encrypt4pdf(password=password, input_file=input_file, output_file=output_file, input_path=input_path, output_path=output_path)


def decrypt4pdf(password, input_file=None, output_file=None, input_path=None, output_path=None):
    popdf.decrypt4pdf(password=password, input_file=input_file, output_file=output_file, input_path=input_path, output_path=output_path)


def add_text_watermark(input_file=None, point=None, text='python-office', output_file=None, fontname="Helvetica", fontsize=12, color=(1, 0, 0)):
    if output_file is None:
        output_file = './pdf_watermark.pdf'
    popdf.add_watermark(input_file=input_file, point=point, text=text, output_file=output_file, fontname=fontname, fontsize=fontsize, color=color)


def merge2pdf(input_file_list=None, output_file=None, one_by_one=None, output=None):
    if one_by_one is not None:
        warnings.warn("参数 'one_by_one' 已被弃用，请改用 'input_file_list' 参数。", DeprecationWarning, stacklevel=2)
        if input_file_list is None:
            input_file_list = one_by_one
    if output is not None:
        warnings.warn("参数 'output' 已被弃用，请改用 'output_file' 参数。", DeprecationWarning, stacklevel=2)
        if output_file is None:
            output_file = output
    popdf.merge2pdf(input_file_list=input_file_list, output_file=output_file)


def del4pdf(input_file=None, output_file=None, page_nums=None):
    popdf.del4pdf(page_nums=page_nums, input_file=input_file, output_file=output_file)


def add_img_water(input_file=None, mark_file=None, output_file=None, pdf_file_in=None, pdf_file_mark=None, pdf_file_out=None):
    if pdf_file_in is not None:
        warnings.warn("参数 'pdf_file_in' 已被弃用，请改用 'input_file' 参数。", DeprecationWarning, stacklevel=2)
        if input_file is None:
            input_file = pdf_file_in
    if pdf_file_mark is not None:
        warnings.warn("参数 'pdf_file_mark' 已被弃用，请改用 'mark_file' 参数。", DeprecationWarning, stacklevel=2)
        if mark_file is None:
            mark_file = pdf_file_mark
    if pdf_file_out is not None:
        warnings.warn("参数 'pdf_file_out' 已被弃用，请改用 'output_file' 参数。", DeprecationWarning, stacklevel=2)
        if output_file is None:
            output_file = pdf_file_out


def add_mark(input_file=None, mark_str=None, output_path=None, output_file=None, pdf_file=None, output_file_name=None):
    if pdf_file is not None:
        warnings.warn("参数 'pdf_file' 已被弃用，请改用 'input_file' 参数。", DeprecationWarning, stacklevel=2)
        if input_file is None:
            input_file = pdf_file
    if output_file_name is not None:
        warnings.warn("参数 'output_file_name' 已被弃用，请改用 'output_file' 参数。", DeprecationWarning, stacklevel=2)
        if output_file is None:
            output_file = output_file_name
    popdf.add_watermark_by_parameters(pdf_file=input_file, mark_str=mark_str, output_path=output_path, output_file_name=output_file)


def add_watermark_by_parameters(input_file=None, mark_str=None, output_path=None, output_file=None, pdf_file=None, output_file_name=None):
    if pdf_file is not None:
        warnings.warn("参数 'pdf_file' 已被弃用，请改用 'input_file' 参数。", DeprecationWarning, stacklevel=2)
        if input_file is None:
            input_file = pdf_file
    if output_file_name is not None:
        warnings.warn("参数 'output_file_name' 已被弃用，请改用 'output_file' 参数。", DeprecationWarning, stacklevel=2)
        if output_file is None:
            output_file = output_file_name
    popdf.add_watermark_by_parameters(pdf_file=input_file, mark_str=mark_str, output_path=output_path, output_file_name=output_file)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("PDF处理工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  pdf2docx  - PDF转Word")
        print("  pdf2imgs  - PDF转图片")
        print("  txt2pdf   - 文本转PDF")
        print("  split4pdf - 拆分PDF")
        print("  encrypt4pdf - 加密PDF")
        print("  decrypt4pdf - 解密PDF")
        print("  merge2pdf - 合并PDF")
        print("  del4pdf   - 删除PDF页面")
        print("  add_mark  - 添加水印")
        print("\n使用方式：python pdf.py <功能名> [参数...]")
        print("示例：python pdf.py pdf2docx input.pdf output.docx")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "pdf2docx" and len(args) >= 1:
            pdf2docx(input_file=args[0], output_file=args[1] if len(args) > 1 else None)
            print(f"转换完成：{args[0]}")
        elif cmd == "pdf2imgs" and len(args) >= 1:
            pdf2imgs(input_file=args[0], output_file=args[1] if len(args) > 1 else None)
            print(f"转换完成：{args[0]}")
        elif cmd == "txt2pdf" and len(args) >= 1:
            txt2pdf(input_file=args[0], output_file=args[1] if len(args) > 1 else None)
            print(f"转换完成")
        elif cmd == "split4pdf" and len(args) >= 1:
            from_page = int(args[1]) if len(args) > 1 else -1
            to_page = int(args[2]) if len(args) > 2 else -1
            split4pdf(input_file=args[0], from_page=from_page, to_page=to_page)
            print(f"拆分完成：{args[0]}")
        elif cmd == "encrypt4pdf" and len(args) >= 2:
            encrypt4pdf(password=args[1], input_file=args[0])
            print(f"加密完成：{args[0]}")
        elif cmd == "decrypt4pdf" and len(args) >= 2:
            decrypt4pdf(password=args[1], input_file=args[0])
            print(f"解密完成：{args[0]}")
        elif cmd == "merge2pdf" and len(args) >= 1:
            merge2pdf(input_file_list=args)
            print("合并完成")
        elif cmd == "del4pdf" and len(args) >= 2:
            del4pdf(input_file=args[0], page_nums=[int(p) for p in args[1:]])
            print(f"删除页面完成：{args[0]}")
        elif cmd == "add_mark" and len(args) >= 2:
            add_mark(input_file=args[0], mark_str=args[1])
            print(f"水印添加完成：{args[0]}")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python pdf.py <功能名> [参数...]")
    except Exception as e:
        print(f"操作失败：{e}")
