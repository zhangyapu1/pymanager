import os
import re
import sys
import time
import logging
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from openpyxl.utils import get_column_letter
from typing import List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 常量定义
MAX_SHEET_NAME_LEN = 31
ILLEGAL_CHARS_PATTERN = re.compile(r'[\/*?:\[\]]')
DEFAULT_COL_WIDTH = 10
MIN_COL_WIDTH = 5
MAX_COL_WIDTH = 50
PADDING = 2
BEEP_FREQ = 800
BEEP_DURATION = 300

def progress_bar(current: int, total: int, bar_length: int = 50) -> None:
    """显示进度条"""
    if total == 0:
        percent = 1.0
    else:
        percent = current / total
    filled_length = int(bar_length * percent)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    # 使用 sys.stdout.write 和 flush 确保在某些环境下能实时刷新
    sys.stdout.write(f'\r[{bar}] {current}/{total} ({percent:.1%})')
    sys.stdout.flush()

def sanitize_sheet_name(name: str, existing_names: set, max_len: int = MAX_SHEET_NAME_LEN) -> str:
    """
    清理工作表名称，确保合法且唯一。
    
    :param name: 原始名称
    :param existing_names: 已使用的名称集合，用于避免冲突
    :param max_len: 最大允许长度
    :return: 唯一的、合法的工作表名称
    """
    # 替换非法字符
    sanitized = ILLEGAL_CHARS_PATTERN.sub('_', name)
    
    # 截断长度
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len]
        
    # 处理空名称或纯空白
    if not sanitized.strip():
        sanitized = "Sheet"
        
    # 确保唯一性
    final_name = sanitized
    counter = 1
    while final_name in existing_names:
        # 如果添加后缀导致超长，需要重新截断基础名称
        suffix = f"_{counter}"
        base_limit = max_len - len(suffix)
        if base_limit < 1:
            # 极端情况，几乎不可能，但为了健壮性
            base_limit = 1
        base_part = sanitized[:base_limit]
        final_name = f"{base_part}{suffix}"
        counter += 1
        
    return final_name

def auto_adjust_column_width(writer, sheet_name: str, df: pd.DataFrame) -> None:
    """
    自动调整 Excel 列宽。
    """
    try:
        workbook = writer.book
        worksheet = workbook[sheet_name]
        
        # 获取列数
        num_cols = len(df.columns)
        if num_cols == 0:
            return

        for i, col in enumerate(df.columns):
            col_letter = get_column_letter(i + 1)
            
            # 计算表头长度
            header_len = len(str(col))
            
            # 计算数据最大长度
            max_data_len = 0
            if not df.empty:
                try:
                    # 转换为字符串并填充空值，计算长度
                    # 注意：astype(str) 将 NaN 转换为 'nan'，所以先 fillna
                    col_str_series = df[col].fillna('').astype(str)
                    if not col_str_series.empty:
                        max_data_len = col_str_series.map(len).max()
                except Exception:
                    max_data_len = 0
            
            # 确定最终宽度
            max_len = max(header_len, max_data_len)
            adjusted_width = min(max(max_len + PADDING, MIN_COL_WIDTH), MAX_COL_WIDTH)
            
            worksheet.column_dimensions[col_letter].width = adjusted_width
            
    except Exception as e:
        logger.warning(f"警告：工作表 '{sheet_name}' 调整列宽时出错：{e}")

def merge_excel_files(file_paths: List[str], output_file: str) -> None:
    total_files = len(file_paths)
    if total_files == 0:
        logger.info("没有文件需要处理。")
        return

    logger.info(f"开始合并 {total_files} 个Excel文件...")
    
    # 用于跟踪已使用的工作表名称，防止冲突
    used_sheet_names = set()
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for i, file_path in enumerate(file_paths, 1):
            # 更新进度条
            progress_bar(i, total_files)
            
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            try:
                # sheet_name=None 返回一个字典: {sheet_name: DataFrame}
                sheets_dict = pd.read_excel(file_path, sheet_name=None)
            except Exception as e:
                logger.error(f"\n读取文件失败：{file_path}，错误：{e}")
                continue
            
            if not sheets_dict:
                logger.warning(f"文件 {file_path} 中没有找到工作表，跳过。")
                continue

            for original_sheet_name, df in sheets_dict.items():
                # 生成唯一且合法的工作表名称
                if len(sheets_dict) == 1:
                    # 如果只有一个 sheet，通常用户希望用文件名作为 sheet 名
                    proposed_name = base_name
                else:
                    # 如果有多个 sheet，用 文件名_原sheet名
                    proposed_name = f"{base_name}_{original_sheet_name}"
                
                # 获取清理后且唯一的名称，并更新集合
                final_sheet_name = sanitize_sheet_name(proposed_name, used_sheet_names)
                used_sheet_names.add(final_sheet_name)
                
                try:
                    df.to_excel(writer, sheet_name=final_sheet_name, index=False)
                    auto_adjust_column_width(writer, final_sheet_name, df)
                except Exception as e:
                    logger.error(f"写入工作表 '{final_sheet_name}' 时出错：{e}")
        
        # 完成进度条
        progress_bar(total_files, total_files)
        print()  # 换行
        logger.info("\n✅ 合并完成！")
        logger.info(f"📁 输出文件：{os.path.abspath(output_file)}")
        logger.info(f"📊 处理文件数：{total_files}")
        
        # 播放完成提示音（如果系统支持）
        try:
            import winsound
            winsound.Beep(BEEP_FREQ, BEEP_DURATION)
        except ImportError:
            pass # Windows 以外的系统可能没有 winsound
        except Exception:
            pass # 其他声音错误忽略

if __name__ == "__main__":
    print("=" * 60)
    print("Excel文件合并工具")
    print("=" * 60)
    
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    try:
        # 立即弹出文件选择对话框
        file_paths = filedialog.askopenfilenames(
            title="请选择要合并的 Excel 文件",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not file_paths:
            print("未选择任何文件，程序退出。")
            root.destroy()
            exit()
        
        output_file = filedialog.asksaveasfilename(
            title="保存合并后的文件",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if not output_file:
            print("未指定输出文件，程序退出。")
            root.destroy()
            exit()
            
        # 重要：在使用完 tkinter 对话框后销毁窗口，释放资源
        root.destroy()
        
        # 显示选择的文件
        print(f"\n已选择 {len(file_paths)} 个文件：")
        for file in file_paths:
            print(f"  - {os.path.basename(file)}")
        print()
        
        # 执行合并
        start_time = time.time()
        # tuple to list conversion just in case, though askopenfilenames returns tuple usually
        merge_excel_files(list(file_paths), output_file)
        end_time = time.time()
        print(f"⏱ 耗时：{end_time - start_time:.2f}秒")
        
        print("=" * 60)
        input("按回车键退出...")
        
    except KeyboardInterrupt:
        print("\n程序被用户中断。")
        root.destroy()
    except Exception as e:
        logger.error(f"发生未知错误：{e}")
        root.destroy()