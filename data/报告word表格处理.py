import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Word表格一键优化工具 - 批量优化Word文档中的表格样式。

功能：
    - 批量处理Word文档中的表格
    - 自动应用专业表格样式（边框、字体、对齐等）

使用方式：
    from data.报告word表格处理 import process_word_tables
    process_word_tables(file_list, output_dir)

依赖：python-docx
"""

import os
import re
from docx import Document
from docx.shared import Pt, Twips
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from modules.logger import log_output


def set_cell_border(cell, **kwargs):
    """设置单元格边框"""
    try:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        for edge in ("top", "bottom", "left", "right"):
            edge_data = kwargs.get(edge)
            if edge_data:
                tag = f"w:{edge}"
                try:
                    element = OxmlElement(tag)
                    tcPr.append(element)
                    for key, value in edge_data.items():
                        element.set(qn(f"w:{key}"), str(value))
                except Exception:
                    pass
    except Exception:
        pass


def apply_table_style(table):
    """将专业表格样式应用到给定的表格对象上"""
    n_rows = len(table.rows)
    n_cols = len(table.columns)

    for i, row in enumerate(table.rows):
        for j, cell in enumerate(row.cells):
            set_cell_border(cell, top={}, bottom={}, left={}, right={})

            if i == 0:
                set_cell_border(cell, top={"sz": "24", "val": "single"})
            if i == n_rows - 1:
                set_cell_border(cell, bottom={"sz": "24", "val": "single"})

            if i > 0:
                set_cell_border(cell, top={"sz": "8", "val": "dashed"})
            if j > 0:
                set_cell_border(cell, left={"sz": "8", "val": "dashed"})

    if n_rows > 0:
        for cell in table.rows[0].cells:
            set_cell_border(cell, bottom={"sz": "16", "val": "single"})

    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = 'Arial Narrow'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                    run.font.size = Pt(10.5)
                paragraph.paragraph_format.line_spacing = Pt(20)
                paragraph.paragraph_format.line_spacing_rule = 3

    if n_rows > 0:
        for cell in table.rows[0].cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.bold = False

    for row in table.rows[1:]:
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

    for row in table.rows[1:]:
        for cell in row.cells:
            text = cell.text.strip()
            if text == "合计":
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                continue

            cleaned = re.sub(r',', '', text)
            if cleaned.replace('.', '', 1).isdigit():
                try:
                    num = float(cleaned)
                    parts = text.split('.')
                    decimals = len(parts[1]) if len(parts) > 1 else 0
                    format_str = f"{{:,.{decimals}f}}" if decimals > 0 else "{:,.0f}"
                    formatted = format_str.format(num)
                    if formatted != text:
                        cell.text = formatted
                    for paragraph in cell.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                        for run in paragraph.runs:
                            run.font.name = 'Arial Narrow'
                except:
                    pass


def process_word_tables(file_list, output_dir):
    """
    批量处理Word文档中的表格

    Args:
        file_list: 文件路径列表
        output_dir: 输出目录

    Returns:
        tuple: (成功数, 失败数)
    """
    success_count = 0
    fail_count = 0
    total = len(file_list)

    log_output(f"开始批量处理：共 {total} 个文件")
    log_output(f"输出目录：{output_dir}")

    for idx, src_path in enumerate(file_list, 1):
        base = os.path.basename(src_path)
        name, ext = os.path.splitext(base)

        log_output(f"[{idx}/{total}] 正在处理: {base}")

        try:
            doc = Document(src_path)
            for table in doc.tables:
                apply_table_style(table)

            os.makedirs(output_dir, exist_ok=True)
            dst_path = os.path.join(output_dir, f"{name}_优化后{ext}")
            doc.save(dst_path)

            success_count += 1
            log_output(f"✓ 成功: {base} -> {os.path.basename(dst_path)}")

        except Exception as e:
            fail_count += 1
            import traceback
            log_output(f"✗ 失败: {base}")
            log_output(f"错误: {str(e)}")
            log_output(f"详细: {traceback.format_exc()}")

    log_output(f"处理完成：成功 {success_count} / 总计 {total}")

    return success_count, fail_count


if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import threading

    root = tk.Tk()
    root.withdraw()

    files = filedialog.askopenfilenames(
        title="选择Word文档",
        filetypes=[("Word文档", "*.docx")]
    )

    if not files:
        exit(0)

    output_dir = filedialog.askdirectory(title="选择输出目录")
    if not output_dir:
        exit(0)

    def run():
        success, fail = process_word_tables(list(files), output_dir)
        root.after(0, lambda: messagebox.showinfo("完成", f"成功 {success}，失败 {fail}"))
        root.after(0, root.destroy)

    thread = threading.Thread(target=run)
    thread.start()
    root.mainloop()