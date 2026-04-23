import os
import re
import tkinter as tk
from tkinter import filedialog, Tk, simpledialog, messagebox, ttk
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# ================== 进度条对话框 ==================
class ProgressDialog:
    # ...（与之前完全相同的代码）...
    pass  # 请将之前的 ProgressDialog 类代码复制在此处

# ================== 自定义行范围对话框 ==================
def get_start_end_row_dialog(parent, files, sheet_keyword):
    """自定义对话框：输入起始行和结束行，支持自动检测最大数据行"""
    dialog = tk.Toplevel(parent)
    dialog.title("设置行范围")
    dialog.geometry("480x220")
    dialog.transient(parent)
    dialog.grab_set()
    
    start_var = tk.IntVar(value=48)
    end_var = tk.IntVar(value=54)
    
    tk.Label(dialog, text="起始行号:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
    start_spin = tk.Spinbox(dialog, from_=1, to=1048576, textvariable=start_var, width=10)
    start_spin.grid(row=0, column=1, padx=5, pady=10, sticky='w')
    
    tk.Label(dialog, text="结束行号:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
    end_spin = tk.Spinbox(dialog, from_=1, to=1048576, textvariable=end_var, width=10)
    end_spin.grid(row=1, column=1, padx=5, pady=10, sticky='w')
    
    def auto_detect():
        if not files:
            messagebox.showwarning("提示", "尚未选择任何Excel文件，请先关闭此窗口并选择文件。")
            return
        sample_file = filedialog.askopenfilename(
            title="请选择一个示例Excel文件以检测最大数据行",
            filetypes=[("Excel文件", "*.xlsx *.xlsm"), ("所有文件", "*.*")]
        )
        if not sample_file:
            return
        try:
            wb = load_workbook(sample_file, read_only=True, data_only=True)
            max_row_all = 0
            for sheet_name in wb.sheetnames:
                if sheet_keyword and sheet_keyword.lower() not in sheet_name.lower():
                    continue
                # 获取该工作表的实际最大行（但只考虑从起始行之后的数据，起始行还不知道，所以先取整体最大值）
                max_row = wb[sheet_name].max_row
                if max_row > max_row_all:
                    max_row_all = max_row
            wb.close()
            if max_row_all > 0:
                end_var.set(max_row_all)
                messagebox.showinfo("检测完成", f"检测到最大数据行为第 {max_row_all} 行，已自动填充。")
            else:
                messagebox.showwarning("未检测到数据", "没有找到符合条件的工作表或数据为空。")
        except Exception as e:
            messagebox.showerror("错误", f"检测失败：{e}")
    
    auto_btn = tk.Button(dialog, text="有内容的所有行", command=auto_detect)
    auto_btn.grid(row=1, column=2, padx=10, pady=10)
    
    btn_frame = tk.Frame(dialog)
    btn_frame.grid(row=2, column=0, columnspan=3, pady=20)
    
    result = [None, None]
    def on_ok():
        start = start_var.get()
        end = end_var.get()
        if start < 1:
            messagebox.showwarning("错误", "起始行号必须>=1")
            return
        if end < start:
            messagebox.showwarning("错误", "结束行号不能小于起始行号")
            return
        result[0] = start
        result[1] = end
        dialog.destroy()
    
    def on_cancel():
        dialog.destroy()
    
    tk.Button(btn_frame, text="确定", width=10, command=on_ok).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="取消", width=10, command=on_cancel).pack(side=tk.LEFT, padx=10)
    
    dialog.update_idletasks()
    w = dialog.winfo_width()
    h = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (w // 2)
    y = (dialog.winfo_screenheight() // 2) - (h // 2)
    dialog.geometry(f'{w}x{h}+{x}+{y}')
    
    parent.wait_window(dialog)
    return result[0], result[1]

# ================== 主汇总函数 ==================
def 汇总Excel文件_按条件():
    root = Tk()
    root.withdraw()
    
    messagebox.showinfo("使用说明", 
                        "本工具将汇总多个Excel文件中符合条件的工作表\n\n"
                        "1. 输入工作表关键词（支持模糊匹配）\n"
                        "2. 选择多个Excel文件\n"
                        "3. 设置起始行和结束行（可自动检测全部数据行）\n"
                        "4. 自动生成汇总结果（带进度提示）")
    
    # 工作表关键词
    sheet_keyword = simpledialog.askstring("输入工作表关键词", 
                                           "请输入工作表名称关键词（支持模糊匹配）：\n"
                                           "例如：销售、Sheet、*所有*、2024\n\n"
                                           "留空表示汇总所有工作表",
                                           initialvalue="")
    if sheet_keyword is None:
        return
    
    # 选择Excel文件
    files = filedialog.askopenfilenames(
        title="请选择要汇总的Excel文件（可多选）",
        filetypes=[("Excel文件", "*.xlsx *.xlsm *.xls"), 
                   ("Excel 2007+", "*.xlsx"),
                   ("Excel 启用宏", "*.xlsm"),
                   ("Excel 97-2003", "*.xls"),
                   ("所有文件", "*.*")]
    )
    if not files:
        messagebox.showwarning("提示", "未选择任何文件，程序退出")
        return
    
    # 行范围（支持自动检测）
    start_row, end_row = get_start_end_row_dialog(root, files, sheet_keyword)
    if start_row is None or end_row is None:
        return
    
    # 是否包含表头
    include_header = messagebox.askyesno("是否包含表头", 
                                         "是否在汇总结果中包含原始数据的表头行？\n\n"
                                         "选择【是】：会复制原始数据的第1行作为表头\n"
                                         "选择【否】：使用默认表头（来源文件、工作表名称等）")
    
    # 输出文件名
    output_name = simpledialog.askstring("输入输出文件名", 
                                         "请输入输出文件名（不含扩展名）：\n"
                                         "例如：汇总结果",
                                         initialvalue="Excel汇总结果")
    if not output_name:
        output_name = "Excel汇总结果"
    
    # 开始汇总（带进度条）
    print(f"\n{'='*60}")
    print(f"开始处理，共选择 {len(files)} 个文件")
    print(f"筛选条件：工作表名称包含【{sheet_keyword if sheet_keyword else '所有'}】")
    print(f"行范围：第 {start_row} 行 到 第 {end_row} 行")
    print(f"{'='*60}\n")
    
    # 创建进度对话框
    progress_dlg = ProgressDialog(root, len(files))
    
    # 汇总工作簿
    wb_result = Workbook()
    ws_result = wb_result.active
    ws_result.title = "汇总结果"
    
    # 表头设置
    if include_header:
        header_copied = False
        default_headers = ["来源文件", "工作表名称", "原始行号"]
    else:
        default_headers = ["来源文件", "工作表名称", "原始行号"]
        ws_result.append(default_headers)
        header_copied = True
    
    # 样式定义
    header_font = Font(bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    if not include_header or header_copied:
        for cell in ws_result[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = thin_border
    
    current_row = 2 if header_copied else 1
    total_rows = 0
    processed_sheets = []
    error_files = []
    cancelled = False
    
    # 处理每个文件
    for file_index, file_path in enumerate(files, 1):
        file_name = os.path.basename(file_path)
        print(f"[{file_index}/{len(files)}] 正在处理: {file_name}")
        progress_dlg.update(file_path, total_rows, file_index)
        
        if progress_dlg.cancelled:
            cancelled = True
            messagebox.showinfo("已取消", "用户终止了汇总操作。")
            break
        
        try:
            # 跳过旧格式 .xls
            if file_name.lower().endswith('.xls') and not file_name.lower().endswith(('.xlsx', '.xlsm')):
                print(f"  ⚠ 跳过旧格式文件（请转换为.xlsx格式）: {file_name}")
                error_files.append(f"{file_name} (旧格式，不支持)")
                continue
            
            wb_src = load_workbook(file_path, data_only=True, read_only=True)
            sheet_found = False
            
            for sheet_name in wb_src.sheetnames:
                if sheet_keyword and sheet_keyword.lower() not in sheet_name.lower():
                    continue
                sheet_found = True
                print(f"  ✓ 匹配工作表: [{sheet_name}]")
                ws_src = wb_src[sheet_name]
                
                # 计算最大列数（在指定行范围内）
                max_col = 1
                for row in range(start_row, min(end_row, ws_src.max_row) + 1):
                    for col in range(1, ws_src.max_column + 1):
                        try:
                            if ws_src.cell(row, col).value is not None and str(ws_src.cell(row, col).value).strip() != "":
                                if col > max_col:
                                    max_col = col
                        except:
                            pass
                
                # 复制表头（如果需要）
                if include_header and not header_copied and start_row > 1:
                    header_row_data = []
                    for col in range(1, max_col + 1):
                        header_value = ws_src.cell(1, col).value
                        header_row_data.append(header_value if header_value is not None else f"列{col}")
                    full_headers = default_headers + header_row_data
                    ws_result.append(full_headers)
                    for cell in ws_result[1]:
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = header_align
                        cell.border = thin_border
                    header_copied = True
                    current_row = 2
                
                # 提取数据
                row_count = 0
                for row in range(start_row, min(end_row, ws_src.max_row) + 1):
                    is_empty = True
                    row_data = []
                    for col in range(1, max_col + 1):
                        try:
                            val = ws_src.cell(row, col).value
                            if val is not None and str(val).strip() != "":
                                is_empty = False
                            row_data.append(val if val is not None else "")
                        except:
                            row_data.append("")
                    if not is_empty:
                        ws_result.append([file_name, sheet_name, row] + row_data)
                        current_row += 1
                        total_rows += 1
                        row_count += 1
                
                if row_count > 0:
                    print(f"    └─ 提取了 {row_count} 行数据")
                    processed_sheets.append(f"{file_name} - {sheet_name} ({row_count}行)")
                else:
                    print(f"    └─ 指定范围内无有效数据")
            
            if not sheet_found:
                print(f"  ✗ 未找到符合条件的工作表（关键词: {sheet_keyword}）")
                error_files.append(f"{file_name} (无匹配工作表)")
            wb_src.close()
        except Exception as e:
            print(f"  ✗ 处理失败: {str(e)}")
            error_files.append(f"{file_name} ({str(e)})")
        print()
    
    if not cancelled:
        progress_dlg.close()
    
    # 保存结果
    if not cancelled and total_rows > 0:
        # 自动调整列宽（与之前相同）
        for column in ws_result.columns:
            max_length = 0
            col_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    cell_len = len(str(cell.value))
                    chinese_cnt = len(re.findall(r'[\u4e00-\u9fff]', str(cell.value)))
                    cell_len += chinese_cnt
                    if cell_len > max_length:
                        max_length = cell_len
            adjusted_width = min(max(max_length + 2, 8), 50)
            ws_result.column_dimensions[col_letter].width = adjusted_width
        
        # 数据行样式
        data_font = Font(size=10)
        data_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
        for row in ws_result.iter_rows(min_row=2, max_row=current_row-1):
            for cell in row:
                cell.font = data_font
                cell.alignment = data_align
                cell.border = thin_border
        
        ws_result.row_dimensions[1].height = 25
        for r in range(2, current_row):
            ws_result.row_dimensions[r].height = 18
        ws_result.freeze_panes = 'A2'
        ws_result.auto_filter.ref = ws_result.dimensions
        
        # 保存文件
        output_dir = os.path.dirname(files[0])
        output_path = os.path.join(output_dir, f"{output_name}.xlsx")
        cnt = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{output_name}_{cnt}.xlsx")
            cnt += 1
        wb_result.save(output_path)
        
        # 输出统计
        print(f"\n{'='*60}")
        print(f"✅ 汇总完成！")
        print(f"📁 输出文件: {output_path}")
        print(f"📊 处理文件数: {len(files)}")
        print(f"📋 匹配工作表数: {len(processed_sheets)}")
        print(f"📝 汇总数据行数: {total_rows}")
        if error_files:
            print(f"\n⚠ 处理失败的文件 ({len(error_files)}个):")
            for err in error_files:
                print(f"   - {err}")
        if processed_sheets and len(processed_sheets) <= 20:
            print(f"\n📑 详细列表:")
            for sheet in processed_sheets:
                print(f"   - {sheet}")
        elif processed_sheets:
            print(f"\n📑 共处理 {len(processed_sheets)} 个工作表")
        print(f"\n{'='*60}")
        
        messagebox.showinfo("完成", 
                           f"汇总完成！\n\n"
                           f"输出文件：{os.path.basename(output_path)}\n"
                           f"处理文件：{len(files)} 个\n"
                           f"汇总数据：{total_rows} 行\n\n"
                           f"文件保存在：{output_dir}")
    elif not cancelled and total_rows == 0:
        messagebox.showwarning("警告", "未提取到任何有效数据！\n请检查参数设置。")
    elif cancelled:
        print("已取消操作，未保存文件。")

if __name__ == "__main__":
    汇总Excel文件_按条件()
