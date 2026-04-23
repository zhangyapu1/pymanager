import os
import re
import tkinter as tk
from tkinter import filedialog, Tk, simpledialog, messagebox, ttk
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


class ProgressDialog:
    """
    改进版进度对话框：
    - 双层进度条（文件级 + 行级）
    - 实时更新当前文件、工作表、已处理行数
    - 支持取消
    """

    def __init__(self, parent, total_files):
        self.parent = parent
        self.total_files = total_files
        self.cancelled = False

        self.window = tk.Toplevel(parent)
        self.window.title("正在汇总...")
        self.window.geometry("560x300")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)

        pad = {"padx": 20, "pady": 3, "anchor": "w"}

        # 标题
        tk.Label(self.window, text="正在处理 Excel 文件，请稍候…",
                 font=("微软雅黑", 10, "bold")).pack(padx=20, pady=(16, 4))

        # 当前文件
        self.var_file = tk.StringVar(value="–")
        tk.Label(self.window, textvariable=self.var_file,
                 font=("微软雅黑", 9), fg="#1a56db").pack(**pad)

        # 当前工作表
        self.var_sheet = tk.StringVar(value="")
        tk.Label(self.window, textvariable=self.var_sheet,
                 font=("微软雅黑", 9), fg="#0e7d5a").pack(**pad)

        # 文件进度条
        tk.Label(self.window, text="文件进度：",
                 font=("微软雅黑", 9), fg="gray").pack(padx=20, anchor="w")
        self.bar_file = ttk.Progressbar(self.window, length=520,
                                         mode="determinate",
                                         maximum=max(total_files, 1))
        self.bar_file.pack(padx=20, pady=2)

        # 行级进度条（当前工作表内）
        tk.Label(self.window, text="当前工作表行进度：",
                 font=("微软雅黑", 9), fg="gray").pack(padx=20, anchor="w")
        self.bar_row = ttk.Progressbar(self.window, length=520,
                                        mode="determinate", maximum=100)
        self.bar_row.pack(padx=20, pady=2)

        # 状态文字
        self.var_status = tk.StringVar(value="")
        tk.Label(self.window, textvariable=self.var_status,
                 font=("微软雅黑", 9), fg="gray").pack(padx=20, pady=(4, 0), anchor="w")

        # 取消按钮
        tk.Button(self.window, text="取消", width=10,
                  command=self.on_cancel).pack(pady=10)

        # 居中显示
        self.window.update_idletasks()
        w, h = self.window.winfo_width(), self.window.winfo_height()
        x = (self.window.winfo_screenwidth() - w) // 2
        y = (self.window.winfo_screenheight() - h) // 2
        self.window.geometry(f"{w}x{h}+{x}+{y}")
        self.window.update()

    # ── 外部调用接口 ────────────────────────────────────────────────

    def set_file(self, file_path, file_index):
        """切换到新文件时调用"""
        name = os.path.basename(file_path)
        self.var_file.config(text=f"文件 {file_index}/{self.total_files}：{name}") \
            if hasattr(self.var_file, 'config') else self.var_file.set(
            f"文件 {file_index}/{self.total_files}：{name}")
        self.bar_file["value"] = file_index - 1   # 开始处理时先移到前一格
        self.bar_row["value"] = 0
        self._flush()

    def set_sheet(self, sheet_name, total_rows_in_range):
        """切换到新工作表时调用"""
        self.var_sheet.set(f"工作表：{sheet_name}  （目标行范围 {total_rows_in_range} 行）")
        self.bar_row["maximum"] = max(total_rows_in_range, 1)
        self.bar_row["value"] = 0
        self._flush()

    def update_row(self, rows_done_in_sheet, total_rows_extracted):
        """每处理一行（或若干行）后调用"""
        self.bar_row["value"] = rows_done_in_sheet
        self.var_status.set(f"累计已提取有效数据：{total_rows_extracted} 行")
        # 每 10 行才真正刷新一次界面，减少 tkinter 调度开销
        if rows_done_in_sheet % 10 == 0:
            self._flush()

    def finish_file(self, file_index):
        """一个文件处理完毕时调用"""
        self.bar_file["value"] = file_index
        self._flush()

    def close(self):
        if self.window.winfo_exists():
            self.window.destroy()

    def on_cancel(self):
        self.cancelled = True
        self.close()

    # ── 内部工具 ────────────────────────────────────────────────────

    def _flush(self):
        if self.window.winfo_exists():
            self.window.update()


# ════════════════════════════════════════════════════════════════════


def 汇总Excel文件_按条件():
    """汇总多个 Excel 文件中符合条件的工作表指定行范围（带双层实时进度条）"""

    root = Tk()
    root.withdraw()

    messagebox.showinfo(
        "使用说明",
        "本工具将汇总多个 Excel 文件中符合条件的工作表\n\n"
        "1. 输入工作表关键词（支持模糊匹配）\n"
        "2. 输入起始行和结束行\n"
        "3. 选择多个 Excel 文件\n"
        "4. 自动生成汇总结果（带实时双层进度条）",
    )

    sheet_keyword = simpledialog.askstring(
        "输入工作表关键词",
        "请输入工作表名称关键词（支持模糊匹配）：\n"
        "例如：销售、Sheet、2024\n\n留空表示汇总所有工作表",
        initialvalue="",
    )
    if sheet_keyword is None:
        return

    start_row = simpledialog.askinteger(
        "输入起始行",
        "请输入要汇总的起始行号：",
        initialvalue=48, minvalue=1, maxvalue=1048576,
    )
    if start_row is None:
        return

    end_row = simpledialog.askinteger(
        "输入结束行",
        "请输入要汇总的结束行号：",
        initialvalue=54, minvalue=start_row, maxvalue=1048576,
    )
    if end_row is None:
        return

    include_header = messagebox.askyesno(
        "是否包含表头",
        "是否在汇总结果中包含原始数据的表头行？\n\n"
        "【是】：复制原始数据第 1 行作为表头\n"
        "【否】：使用默认表头（来源文件、工作表名称等）",
    )

    output_name = simpledialog.askstring(
        "输出文件名", "请输入输出文件名（不含扩展名）：",
        initialvalue="Excel汇总结果",
    )
    if not output_name:
        output_name = "Excel汇总结果"

    files = filedialog.askopenfilenames(
        title="请选择要汇总的 Excel 文件（可多选）",
        filetypes=[
            ("Excel 文件", "*.xlsx *.xlsm *.xls"),
            ("所有文件", "*.*"),
        ],
    )
    if not files:
        messagebox.showwarning("提示", "未选择任何文件，程序退出")
        return

    print(f"\n{'='*60}")
    print(f"开始处理，共选择 {len(files)} 个文件")
    print(f"筛选条件：工作表名称包含【{sheet_keyword or '所有'}】")
    print(f"行范围：第 {start_row} 行 — 第 {end_row} 行")
    print(f"{'='*60}\n")

    # ── 样式常量 ────────────────────────────────────────────────────
    header_font  = Font(bold=True, size=11, color="FFFFFF")
    header_fill  = PatternFill(start_color="4472C4", end_color="4472C4",
                               fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    data_font    = Font(size=10)
    data_align   = Alignment(horizontal="left", vertical="center",
                              wrap_text=True)
    thin_border  = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"),  bottom=Side(style="thin"),
    )

    # ── 结果工作簿 ──────────────────────────────────────────────────
    wb_result = Workbook()
    ws_result  = wb_result.active
    ws_result.title = "汇总结果"

    default_headers = ["来源文件", "工作表名称", "原始行号"]
    header_copied   = False

    if not include_header:
        ws_result.append(default_headers)
        for cell in ws_result[1]:
            cell.font      = header_font
            cell.fill      = header_fill
            cell.alignment = header_align
            cell.border    = thin_border
        header_copied = True

    current_result_row = 2 if header_copied else 1
    total_rows         = 0
    processed_sheets   = []
    error_files        = []

    progress = ProgressDialog(root, len(files))

    # ── 逐文件处理 ──────────────────────────────────────────────────
    for file_index, file_path in enumerate(files, 1):
        file_name = os.path.basename(file_path)
        print(f"[{file_index}/{len(files)}] 正在处理: {file_name}")

        progress.set_file(file_path, file_index)

        if progress.cancelled:
            messagebox.showinfo("已取消", "用户终止了汇总操作。")
            break

        try:
            if (file_name.lower().endswith(".xls") and
                    not file_name.lower().endswith((".xlsx", ".xlsm"))):
                print(f"  ⚠ 跳过旧格式文件（请转换为 .xlsx）: {file_name}")
                error_files.append(f"{file_name} (旧格式，不支持)")
                progress.finish_file(file_index)
                continue

            wb_src     = load_workbook(file_path, data_only=True, read_only=True)
            sheet_found = False

            for sheet_name in wb_src.sheetnames:
                if sheet_keyword and sheet_keyword.lower() not in sheet_name.lower():
                    continue

                sheet_found = True
                print(f"  ✓ 匹配工作表: [{sheet_name}]")

                ws_src         = wb_src[sheet_name]
                range_size     = max(end_row - start_row + 1, 1)
                actual_end_row = min(end_row, ws_src.max_row or end_row)

                progress.set_sheet(sheet_name, range_size)

                # ── 第一遍：确定最大有效列 ──────────────────────────
                max_col = 1
                for r_idx, row in enumerate(
                    ws_src.iter_rows(
                        min_row=start_row, max_row=actual_end_row,
                        values_only=True
                    )
                ):
                    for c_idx, val in enumerate(row, 1):
                        if val is not None and str(val).strip():
                            if c_idx > max_col:
                                max_col = c_idx
                    # 每 5 行刷新一次
                    if r_idx % 5 == 0:
                        progress.update_row(r_idx, total_rows)
                        if progress.cancelled:
                            break

                if progress.cancelled:
                    break

                # ── 复制原始表头（可选）──────────────────────────────
                if include_header and not header_copied and start_row > 1:
                    header_row_data = []
                    for col in range(1, max_col + 1):
                        val = ws_src.cell(1, col).value
                        header_row_data.append(
                            val if val is not None else f"列{col}"
                        )
                    ws_result.append(default_headers + header_row_data)
                    for cell in ws_result[1]:
                        cell.font      = header_font
                        cell.fill      = header_fill
                        cell.alignment = header_align
                        cell.border    = thin_border
                    header_copied      = True
                    current_result_row = 2
                    progress._flush()

                # ── 第二遍：提取数据（实时更新进度）─────────────────
                row_count = 0
                for r_offset, row_vals in enumerate(
                    ws_src.iter_rows(
                        min_row=start_row, max_row=actual_end_row,
                        max_col=max_col, values_only=True
                    )
                ):
                    actual_row_num = start_row + r_offset

                    row_data = [
                        (v if v is not None else "") for v in row_vals
                    ]
                    # 补齐列数（read_only 模式可能返回较短的行）
                    while len(row_data) < max_col:
                        row_data.append("")

                    if any(str(v).strip() for v in row_data):
                        ws_result.append(
                            [file_name, sheet_name, actual_row_num] + row_data
                        )
                        current_result_row += 1
                        total_rows         += 1
                        row_count          += 1

                    # 实时刷新：每行都更新进度条数值，每 10 行才真正绘制
                    progress.update_row(r_offset + 1, total_rows)
                    if progress.cancelled:
                        break

                if row_count:
                    print(f"    └─ 提取了 {row_count} 行数据")
                    processed_sheets.append(
                        f"{file_name} - {sheet_name} ({row_count} 行)"
                    )
                else:
                    print(f"    └─ 指定范围内无有效数据")

                if progress.cancelled:
                    break

            if not sheet_found:
                print(f"  ✗ 无匹配工作表（关键词: {sheet_keyword or '全部'}）")
                error_files.append(f"{file_name} (无匹配工作表)")

            wb_src.close()

        except Exception as exc:
            print(f"  ✗ 处理失败: {exc}")
            error_files.append(f"{file_name} ({exc})")

        progress.finish_file(file_index)
        print()

        if progress.cancelled:
            messagebox.showinfo("已取消", "用户终止了汇总操作。")
            break

    # ── 关闭进度对话框 ──────────────────────────────────────────────
    progress.close()

    cancelled = progress.cancelled

    # ── 后处理与保存 ────────────────────────────────────────────────
    if not cancelled and total_rows > 0:

        # 自动调整列宽
        for column in ws_result.columns:
            max_len = 0
            col_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    raw_len      = len(str(cell.value))
                    chinese_cnt  = len(re.findall(r"[\u4e00-\u9fff]",
                                                   str(cell.value)))
                    raw_len     += chinese_cnt
                    if raw_len > max_len:
                        max_len = raw_len
            ws_result.column_dimensions[col_letter].width = min(
                max(max_len + 2, 8), 50
            )

        # 数据行样式
        for row in ws_result.iter_rows(min_row=2,
                                        max_row=current_result_row - 1):
            for cell in row:
                cell.font      = data_font
                cell.alignment = data_align
                cell.border    = thin_border

        # 行高
        ws_result.row_dimensions[1].height = 25
        for r in range(2, current_result_row):
            ws_result.row_dimensions[r].height = 18

        # 冻结首行 & 自动筛选
        ws_result.freeze_panes    = "A2"
        ws_result.auto_filter.ref = ws_result.dimensions

        # 输出路径（避免覆盖）
        output_dir  = os.path.dirname(files[0])
        output_path = os.path.join(output_dir, f"{output_name}.xlsx")
        counter     = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir,
                                        f"{output_name}_{counter}.xlsx")
            counter += 1

        wb_result.save(output_path)

        print(f"\n{'='*60}")
        print(f"✅ 汇总完成！")
        print(f"📁 输出文件: {output_path}")
        print(f"📊 处理文件数: {len(files)}")
        print(f"📋 匹配工作表数: {len(processed_sheets)}")
        print(f"📝 汇总数据行数: {total_rows}")
        if error_files:
            print(f"\n⚠ 处理失败 ({len(error_files)} 个):")
            for e in error_files:
                print(f"   - {e}")
        if processed_sheets and len(processed_sheets) <= 20:
            print(f"\n📑 详细列表:")
            for s in processed_sheets:
                print(f"   - {s}")
        elif processed_sheets:
            print(f"\n📑 共处理 {len(processed_sheets)} 个工作表")
        print(f"{'='*60}")

        messagebox.showinfo(
            "完成",
            f"汇总完成！\n\n"
            f"输出文件：{os.path.basename(output_path)}\n"
            f"处理文件：{len(files)} 个\n"
            f"汇总数据：{total_rows} 行\n\n"
            f"文件保存在：{output_dir}",
        )

    elif not cancelled and total_rows == 0:
        messagebox.showwarning(
            "警告",
            "未提取到任何有效数据！\n\n"
            "请检查：\n"
            "1. 工作表关键词是否正确\n"
            "2. 指定行范围内是否有数据\n"
            "3. Excel 文件是否为空",
        )
    else:
        print("已取消操作，未保存任何文件。")


if __name__ == "__main__":
    汇总Excel文件_按条件()
