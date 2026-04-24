import os
import re
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from openpyxl.utils import get_column_letter
import time

# 进度条函数
def progress_bar(current, total, bar_length=50):
    """显示进度条"""
    percent = current / total
    filled_length = int(bar_length * percent)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r[{bar}] {current}/{total} ({percent:.1%})', end='')

def sanitize_sheet_name(name, max_len=31):
    illegal_chars = r'[\/*?:\[\]]'
    sanitized = re.sub(illegal_chars, '_', name)
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len]
    return sanitized

def auto_adjust_column_width(writer, sheet_name, df):
    try:
        workbook = writer.book
        worksheet = workbook[sheet_name]
        if df.empty:
            for i, col in enumerate(df.columns):
                col_letter = get_column_letter(i + 1)
                worksheet.column_dimensions[col_letter].width = 10
            return
        for i, col in enumerate(df.columns):
            col_letter = get_column_letter(i + 1)
            header_len = len(str(col))
            try:
                col_str = df[col].fillna('').astype(str)
                max_data_len = col_str.map(len).max() if not col_str.empty else 0
            except Exception:
                max_data_len = 0
            max_len = max(header_len, max_data_len)
            adjusted_width = min(max(max_len + 2, 5), 50)
            worksheet.column_dimensions[col_letter].width = adjusted_width
    except Exception as e:
        print(f"  警告：工作表 {sheet_name} 调整列宽时出错：{e}")

def merge_excel_files(file_paths, output_file):
    total_files = len(file_paths)
    print(f"开始合并 {total_files} 个Excel文件...")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for i, file_path in enumerate(file_paths, 1):
            # 更新进度条
            progress_bar(i, total_files)
            
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            try:
                sheets = pd.read_excel(file_path, sheet_name=None)
            except Exception as e:
                print(f"\n读取文件失败：{file_path}，错误：{e}")
                continue
            if len(sheets) == 1:
                sheet_name, df = list(sheets.items())[0]
                new_name = sanitize_sheet_name(base_name)
                df.to_excel(writer, sheet_name=new_name, index=False)
                auto_adjust_column_width(writer, new_name, df)
            else:
                for original_name, df in sheets.items():
                    new_name = sanitize_sheet_name(f"{base_name}_{original_name}")
                    df.to_excel(writer, sheet_name=new_name, index=False)
                    auto_adjust_column_width(writer, new_name, df)
        
        # 完成进度条
        progress_bar(total_files, total_files)
        print()  # 换行
        print(f"\n✅ 合并完成！")
        print(f"📁 输出文件：{os.path.abspath(output_file)}")
        print(f"📊 处理文件数：{total_files}")
        
        # 播放完成提示音（如果系统支持）
        try:
            import winsound
            winsound.Beep(800, 300)  # 频率800Hz，持续300ms1
        except:
            pass

if __name__ == "__main__":
    print("=" * 60)
    print("Excel文件合并工具")
    print("=" * 60)
    
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    # 立即弹出文件选择对话框，无需任何键盘操作
    file_paths = filedialog.askopenfilenames(
        title="请选择要合并的 Excel 文件",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
    )
    if not file_paths:
        print("未选择任何文件，程序退出。")
        # 可选：加一个暂停，防止窗口一闪而过（但会引入回车，您可自行决定）
        # input("按回车键退出...")
        exit()
    
    output_file = filedialog.asksaveasfilename(
        title="保存合并后的文件",
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
    )
    if not output_file:
        print("未指定输出文件，程序退出。")
        exit()
    
    # 显示选择的文件
    print(f"\n已选择 {len(file_paths)} 个文件：")
    for file in file_paths:
        print(f"  - {os.path.basename(file)}")
    print()
    
    # 执行合并
    start_time = time.time()
    merge_excel_files(list(file_paths), output_file)
    end_time = time.time()
    print(f"⏱ 耗时：{end_time - start_time:.2f}秒")
    
    print("=" * 60)
    # 如果您不希望窗口自动关闭，可以取消下面一行的注释（会需要按回车）
    input("按回车键退出...")