# -*- coding: UTF-8 -*-
"""Excel processing functionality module.

Excel处理功能模块。

This module provides rich Excel file processing capabilities including data simulation,
file merging/splitting, format conversion, and more.

该模块提供了丰富的Excel文件处理功能，包括数据模拟、文件合并拆分、格式转换等。

Main Features:
- fake2excel: Automatically create Excel files with mock data
- merge2excel: Merge multiple Excel files into different sheets
- sheet2excel: Split different sheets from one Excel into separate files
- merge2sheet: Merge multiple sheets from multiple Excel files
- find_excel_data: Search for specific content in Excel files
- split_excel_by_column: Split Excel by specified column values
- excel2pdf: Convert Excel to PDF format

主要功能：
- fake2excel: 自动创建Excel并模拟数据
- merge2excel: 多个Excel合并到一个文件的不同sheet中
- sheet2excel: 同一个Excel的不同sheet拆分为不同文件
- merge2sheet: 多个Excel的多个sheet自动合并
- find_excel_data: 搜索Excel中指定内容
- split_excel_by_column: 按指定列拆分Excel
- excel2pdf: Excel转PDF格式

Author:
    程序员晚枫

Project:
    https://www.python-office.com
"""

import poexcel


def fake2excel(columns=['name'], rows=1, path='./fake2excel.xlsx', language='zh_CN'):
    """Automatically create Excel file with mock data.
    
    自动创建Excel文件并模拟数据。
    
    Video tutorial: https://www.bilibili.com/video/BV1wr4y1b7uk/
    
    Args:
        columns (list): column names to generate / 需要生成的列名。Available columns / 可以模拟的列：https://www.python4office.cn/python-office/fake2excel/
        rows (int): number of rows to generate / 生成的行数。Default / 默认值: 1
        path (str): output file path and name / 生成的Excel文件路径和名称
        language (str): language for generated data / 数据语言。Default / 默认: 'zh_CN' (Chinese / 中文), can be 'english' / 可以填 'english'
    
    Returns:
        None
    """
    poexcel.fake2excel(columns=columns, rows=rows, path=path, language=language)


def merge2excel(dir_path, output_file='merge2excel.xlsx'):
    """Merge multiple Excel files into different sheets of one Excel file.
    
    将多个Excel文件合并到一个Excel的不同sheet中。
    
    Documentation: https://mp.weixin.qq.com/s/3ZhZZfGlpNhszCWnOBeklg
    Video tutorial: https://www.bilibili.com/video/BV1Th4y1Y7kd/
    
    Args:
        dir_path (str): directory path containing multiple Excel files / 包含多个Excel文件的目录路径
        output_file (str): output merged Excel file path / 合并后的Excel文件路径。Default / 默认: 'merge2excel.xlsx'
    
    Returns:
        None
    """
    poexcel.merge2excel(dir_path=dir_path, output_file=output_file)


def sheet2excel(file_path, output_path='./'):
    """Split different sheets from one Excel file into separate Excel files.
    
    将同一个Excel里的不同sheet拆分为不同的Excel文件。
    
    Video tutorial: https://www.bilibili.com/video/BV1714y147Ao/
    
    Args:
        file_path (str): path to the Excel file to be split / 需要拆分的Excel文件路径
        output_path (str): output directory for split files / 拆分后文件的输出目录。Default / 默认: current directory / 当前目录
    
    Returns:
        None
    """
    poexcel.sheet2excel(file_path=file_path, output_path=output_path)


def merge2sheet(dir_path, output_sheet_name: str = 'Sheet1', output_excel_name: str = 'merge2sheet'):
    """Automatically merge multiple sheets from multiple Excel files.
    
    自动合并多个Excel文件的多个sheet。
    
    Documentation: https://mp.weixin.qq.com/s/qQxIsSPHfILTCxZ8PBv6QA
    
    Args:
        dir_path (str): directory path containing multiple Excel files / 包含多个Excel文件的目录路径
        output_sheet_name (str): name of the merged sheet / 合并后的sheet名称。Default / 默认: 'Sheet1'
        output_excel_name (str): name of the merged Excel file / 合并后的Excel文件名。Default / 默认: 'merge2sheet'
    
    Returns:
        None
    """
    poexcel.merge2sheet(dir_path=dir_path, output_sheet_name=output_sheet_name, output_excel_name=output_excel_name)


# PR内容 & 作者：https://gitee.com/CoderWanFeng/python-office/pulls/10
def find_excel_data(search_key: str, target_dir: str):
    """Search for specific content in Excel files including file name, row number, and details.
    
    搜索Excel中指定内容的文件、行数、内容详情。
    
    Video tutorial: https://www.bilibili.com/video/BV1Bd4y1B7yr/
    
    Args:
        search_key (str): keyword to search for / 需要搜索的关键词
        target_dir (str): directory path to search in / 搜索的目录路径
    
    Returns:
        None
    """
    poexcel.find_excel_data(search_key=search_key, target_dir=target_dir)


# PR内容 & 作者：：https://gitee.com/CoderWanFeng/python-office/pulls/11

def split_excel_by_column(filepath: str, column: int, worksheet_name: str = None):
    """Split Excel file based on the content of a specified column.
    
    按指定列的内容拆分Excel文件。
    
    Args:
        filepath (str): path to the Excel file to be split / 需要拆分的Excel文件路径
        column (int): column index to split by / 按哪一列的内容进行拆分
        worksheet_name (str, optional): worksheet name to process / 指定工作表名称。Default / 默认: None (first worksheet / 第一个工作表)
    
    Returns:
        None
    """
    poexcel.split_excel_by_column(filepath=filepath, column=column, worksheet_name=worksheet_name)


def excel2pdf(excel_path, pdf_path, sheet_id: int = 0):
    """Convert specified worksheet from Excel file to PDF format.
    
    将Excel文件的指定工作表转换为PDF格式。
    
    Video tutorial: https://www.bilibili.com/video/BV1A84y1N7or/
    
    Args:
        excel_path (str): path to the Excel file / Excel文件的路径
        pdf_path (str): path for the output PDF file / 转换后生成的PDF文件的路径
        sheet_id (int): worksheet index / 工作表的索引。Default / 默认: 0 (first worksheet / 第一个工作表)
    
    Returns:
        None
    """
    poexcel.excel2pdf(excel_path=excel_path, pdf_path=pdf_path, sheet_id=sheet_id)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("Excel处理工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  fake2excel           - 自动创建Excel并模拟数据")
        print("  merge2excel          - 多个Excel合并到一个文件的不同sheet")
        print("  sheet2excel          - 同一个Excel的不同sheet拆分为不同文件")
        print("  merge2sheet          - 多个Excel的多个sheet自动合并")
        print("  find_excel_data      - 搜索Excel中指定内容")
        print("  split_excel_by_column - 按指定列拆分Excel")
        print("  excel2pdf            - Excel转PDF格式")
        print("\n使用方式：python excel.py <功能名> [参数...]")
        print("示例：python excel.py fake2excel name 10")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "fake2excel":
            columns = args[0].split(',') if len(args) > 0 else ['name']
            rows = int(args[1]) if len(args) > 1 else 1
            path = args[2] if len(args) > 2 else './fake2excel.xlsx'
            fake2excel(columns=columns, rows=rows, path=path)
            print(f"Excel文件已生成：{path}")
        elif cmd == "merge2excel" and len(args) >= 1:
            output_file = args[1] if len(args) > 1 else 'merge2excel.xlsx'
            merge2excel(dir_path=args[0], output_file=output_file)
            print(f"合并完成：{output_file}")
        elif cmd == "sheet2excel" and len(args) >= 1:
            output_path = args[1] if len(args) > 1 else './'
            sheet2excel(file_path=args[0], output_path=output_path)
            print(f"拆分完成：{args[0]}")
        elif cmd == "merge2sheet" and len(args) >= 1:
            output_sheet_name = args[1] if len(args) > 1 else 'Sheet1'
            output_excel_name = args[2] if len(args) > 2 else 'merge2sheet'
            merge2sheet(dir_path=args[0], output_sheet_name=output_sheet_name, output_excel_name=output_excel_name)
            print(f"合并完成")
        elif cmd == "find_excel_data" and len(args) >= 2:
            find_excel_data(search_key=args[0], target_dir=args[1])
            print("搜索完成")
        elif cmd == "split_excel_by_column" and len(args) >= 2:
            worksheet_name = args[2] if len(args) > 2 else None
            split_excel_by_column(filepath=args[0], column=int(args[1]), worksheet_name=worksheet_name)
            print(f"拆分完成：{args[0]}")
        elif cmd == "excel2pdf" and len(args) >= 2:
            sheet_id = int(args[2]) if len(args) > 2 else 0
            excel2pdf(excel_path=args[0], pdf_path=args[1], sheet_id=sheet_id)
            print(f"转换完成：{args[1]}")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python excel.py <功能名> [参数...]")
    except Exception as e:
        print(f"操作失败：{e}")
