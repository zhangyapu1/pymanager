#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word表格批量格式化工具 - 顶线/底线 1.5 磅实线版 (GUI版)
功能：
  1. 表格内部全部 0.5 虚线
  2. 表格左右两侧边线空白
  3. 表格顶部和底部 1.5 实线
  4. 首行底线 0.5 实线（支持纵向合并单元格的首行识别）
  5. 中文宋体 + 左对齐；首行/尾行中文居中
  6. 非中文 Times New Roman + 右对齐；数字千分位
"""

import sys
import os
import re
import io
import zipfile
import xml.etree.ElementTree as ET
import threading

# ==================== tkinter GUI ====================
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    print("错误：无法加载 tkinter，请确保 Python 安装了 Tk 支持。")
    sys.exit(1)

# ==================== 配置 ====================
TOP_BOTTOM_SZ = "12"     # 1.5 磅实线
HEADER_BOTTOM_SZ = "4"   # 0.5 磅实线 (首行底线)
INSIDE_SZ = "4"          # 0.5 磅虚线 (内部线条)

# ==================== 命名空间 ====================
NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NSMAP = {
    "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
    "cx": "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "w": NS_W,
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16": "http://schemas.microsoft.com/office/word/2018/wordml",
}
for prefix, uri in NSMAP.items():
    ET.register_namespace(prefix, uri)

W = "{%s}" % NS_W


def has_chinese(text):
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def set_table_borders(tblPr):
    for old in tblPr.findall(f"{W}tblBorders"):
        tblPr.remove(old)
    borders = ET.SubElement(tblPr, f"{W}tblBorders")

    top = ET.SubElement(borders, f"{W}top")
    top.set(f"{W}val", "single")
    top.set(f"{W}sz", TOP_BOTTOM_SZ)
    top.set(f"{W}space", "0")
    top.set(f"{W}color", "auto")

    bottom = ET.SubElement(borders, f"{W}bottom")
    bottom.set(f"{W}val", "single")
    bottom.set(f"{W}sz", TOP_BOTTOM_SZ)
    bottom.set(f"{W}space", "0")
    bottom.set(f"{W}color", "auto")

    left = ET.SubElement(borders, f"{W}left")
    left.set(f"{W}val", "nil")

    right = ET.SubElement(borders, f"{W}right")
    right.set(f"{W}val", "nil")

    insideH = ET.SubElement(borders, f"{W}insideH")
    insideH.set(f"{W}val", "dotted")
    insideH.set(f"{W}sz", INSIDE_SZ)
    insideH.set(f"{W}space", "0")
    insideH.set(f"{W}color", "auto")

    insideV = ET.SubElement(borders, f"{W}insideV")
    insideV.set(f"{W}val", "dotted")
    insideV.set(f"{W}sz", INSIDE_SZ)
    insideV.set(f"{W}space", "0")
    insideV.set(f"{W}color", "auto")


def set_cell_borders(tcPr, is_table_top=False, is_header_bottom=False, is_table_bottom=False):
    for old in tcPr.findall(f"{W}tcBorders"):
        tcPr.remove(old)
    if not is_table_top and not is_header_bottom and not is_table_bottom:
        return
    borders = ET.SubElement(tcPr, f"{W}tcBorders")
    if is_table_top:
        top = ET.SubElement(borders, f"{W}top")
        top.set(f"{W}val", "single")
        top.set(f"{W}sz", TOP_BOTTOM_SZ)
        top.set(f"{W}space", "0")
        top.set(f"{W}color", "auto")
    if is_table_bottom:
        bottom = ET.SubElement(borders, f"{W}bottom")
        bottom.set(f"{W}val", "single")
        bottom.set(f"{W}sz", TOP_BOTTOM_SZ)
        bottom.set(f"{W}space", "0")
        bottom.set(f"{W}color", "auto")
    elif is_header_bottom:
        bottom = ET.SubElement(borders, f"{W}bottom")
        bottom.set(f"{W}val", "single")
        bottom.set(f"{W}sz", HEADER_BOTTOM_SZ)
        bottom.set(f"{W}space", "0")
        bottom.set(f"{W}color", "auto")


def get_header_span(rows):
    if not rows:
        return 0
    first_row = rows[0]
    first_cells = first_row.findall(f"{W}tc")
    max_span = 1
    for cell_idx, cell in enumerate(first_cells):
        tcPr = cell.find(f"{W}tcPr")
        if tcPr is not None:
            vmerge = tcPr.find(f"{W}vMerge")
            if vmerge is not None and vmerge.get(f"{W}val") == "restart":
                span = 1
                for ridx in range(1, len(rows)):
                    row = rows[ridx]
                    cells = row.findall(f"{W}tc")
                    if cell_idx < len(cells):
                        c_tcPr = cells[cell_idx].find(f"{W}tcPr")
                        if c_tcPr is not None:
                            c_vmerge = c_tcPr.find(f"{W}vMerge")
                            if c_vmerge is not None and c_vmerge.get(f"{W}val") is None:
                                span += 1
                            else:
                                break
                        else:
                            break
                    else:
                        break
                max_span = max(max_span, span)
    return max_span


def set_run_fonts(rPr, is_chinese):
    fonts = rPr.find(f"{W}rFonts")
    if fonts is None:
        fonts = ET.SubElement(rPr, f"{W}rFonts")
    fonts.set(f"{W}ascii", "Times New Roman")
    fonts.set(f"{W}hAnsi", "Times New Roman")
    fonts.set(f"{W}eastAsia", "宋体")
    fonts.set(f"{W}cs", "Times New Roman")

    sz = rPr.find(f"{W}sz")
    if sz is None:
        sz = ET.SubElement(rPr, f"{W}sz")
    sz.set(f"{W}val", "21")

    szCs = rPr.find(f"{W}szCs")
    if szCs is None:
        szCs = ET.SubElement(rPr, f"{W}szCs")
    szCs.set(f"{W}val", "21")


def set_paragraph_alignment(pPr, align):
    jc = pPr.find(f"{W}jc")
    if jc is None:
        jc = ET.SubElement(pPr, f"{W}jc")
    jc.set(f"{W}val", align)


def process_table(tbl):
    tblPr = tbl.find(f"{W}tblPr")
    if tblPr is None:
        tblPr = ET.SubElement(tbl, f"{W}tblPr")
    set_table_borders(tblPr)

    rows = tbl.findall(f"{W}tr")
    if not rows:
        return

    header_span = get_header_span(rows)
    header_last_idx = header_span - 1
    last_idx = len(rows) - 1

    for row_idx, row in enumerate(rows):
        is_table_top = row_idx == 0
        is_header_bottom = row_idx == header_last_idx and row_idx != last_idx
        is_table_bottom = row_idx == last_idx
        is_header_row = row_idx <= header_last_idx
        is_last_row = row_idx == last_idx

        cells = row.findall(f"{W}tc")
        for cell in cells:
            tcPr = cell.find(f"{W}tcPr")
            if tcPr is None:
                tcPr = ET.SubElement(cell, f"{W}tcPr")
            set_cell_borders(tcPr, is_table_top, is_header_bottom, is_table_bottom)

            paragraphs = cell.findall(f"{W}p")
            for para in paragraphs:
                pPr = para.find(f"{W}pPr")
                if pPr is None:
                    pPr = ET.SubElement(para, f"{W}pPr")

                all_text = "".join(t.text or "" for t in para.findall(f".//{W}t"))
                para_is_chinese = has_chinese(all_text)

                if is_header_row or is_last_row:
                    align = "center" if para_is_chinese else "right"
                else:
                    align = "left" if para_is_chinese else "right"

                set_paragraph_alignment(pPr, align)

                for r in para.findall(f"{W}r"):
                    rPr = r.find(f"{W}rPr")
                    if rPr is None:
                        rPr = ET.SubElement(r, f"{W}rPr")

                    run_text = "".join(t.text or "" for t in r.findall(f"{W}t"))
                    set_run_fonts(rPr, has_chinese(run_text))


def process_docx(input_path, output_path, progress_callback=None):
    with zipfile.ZipFile(input_path, "r") as zin:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    content = data.decode("utf-8")

                    doc_start = content.find('<w:document')
                    if doc_start != -1:
                        header_end = content.find('>', doc_start)
                        original_ns_declarations = content[doc_start:header_end+1]

                    tree = ET.parse(io.BytesIO(data))
                    root = tree.getroot()
                    tables = root.findall(f".//{W}tbl")
                    total = len(tables)

                    for idx, tbl in enumerate(tables, 1):
                        process_table(tbl)
                        if progress_callback:
                            progress_callback(idx, total)

                    buf = io.BytesIO()
                    tree.write(buf, encoding="utf-8", xml_declaration=True)
                    new_content = buf.getvalue().decode("utf-8")

                    new_doc_start = new_content.find('<w:document')
                    if new_doc_start != -1:
                        new_header_end = new_content.find('>', new_doc_start)
                        new_body_start = new_content.find('>', new_doc_start) + 1

                        while new_body_start < len(new_content) and new_content[new_body_start] == '\n':
                            new_body_start += 1

                        body_content = new_content[new_body_start:]

                        body_content = re.sub(r'<w:document[^>]*>', '', body_content, count=1)
                        body_content = body_content.replace('</w:document>', '')

                        if original_ns_declarations.endswith('>'):
                            final_content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + original_ns_declarations + body_content + '</w:document>'
                        else:
                            final_content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + original_ns_declarations + '>' + body_content + '</w:document>'

                        data = final_content.encode("utf-8")
                zout.writestr(item, data)


# ==================== GUI ====================
class FormatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Word表格批量格式化工具 - 顶线/底线 1.5 磅实线")
        self.root.geometry("600x320")
        self.root.resizable(False, False)

        # 文件选择
        tk.Label(root, text="选择 Word 文档 (.docx):", font=("Microsoft YaHei", 11)).pack(anchor="w", padx=20, pady=(15, 5))

        frame = tk.Frame(root)
        frame.pack(fill="x", padx=20, pady=5)

        self.entry_path = tk.Entry(frame, font=("Microsoft YaHei", 10))
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Button(frame, text="浏览...", font=("Microsoft YaHei", 10), command=self.browse_file).pack(side="right")

        # 输出路径预览
        self.lbl_output = tk.Label(root, text="输出路径: 未选择", font=("Microsoft YaHei", 9), fg="gray", wraplength=560, justify="left")
        self.lbl_output.pack(anchor="w", padx=20, pady=5)

        # 进度条
        self.progress = ttk.Progressbar(root, orient="horizontal", length=560, mode="determinate")
        self.progress.pack(padx=20, pady=10)

        # 状态标签
        self.lbl_status = tk.Label(root, text="就绪", font=("Microsoft YaHei", 10), fg="blue")
        self.lbl_status.pack(padx=20, pady=5)

        # 开始按钮
        self.btn_start = tk.Button(root, text="开始处理", font=("Microsoft YaHei", 12, "bold"), bg="#0078D4", fg="white",
                                   activebackground="#005A9E", width=15, command=self.start_processing)
        self.btn_start.pack(pady=15)

        # 说明
        tk.Label(root, text="说明：顶线/底线 1.5 磅实线 | 内部 0.5 磅虚线 | 左右空白 | 首行底线 0.5 磅实线",
                 font=("Microsoft YaHei", 8), fg="gray").pack(pady=(0, 10))

        self.input_path = ""

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="选择 Word 文档",
            filetypes=[("Word 文档", "*.docx"), ("所有文件", "*.*")]
        )
        if path:
            self.input_path = path
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, path)
            base, ext = os.path.splitext(path)
            out = base + "_optimized" + ext
            self.lbl_output.config(text=f"输出路径: {out}")

    def update_progress(self, current, total):
        self.progress["maximum"] = total
        self.progress["value"] = current
        self.lbl_status.config(text=f"正在处理第 {current}/{total} 个表格...")
        self.root.update_idletasks()

    def start_processing(self):
        path = self.entry_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showwarning("提示", "请先选择一个有效的 Word 文档。")
            return

        base, ext = os.path.splitext(path)
        output_path = base + "_optimized" + ext

        self.btn_start.config(state="disabled")
        self.lbl_status.config(text="正在处理...", fg="blue")
        self.progress["value"] = 0
        self.root.update_idletasks()

        def worker():
            try:
                process_docx(path, output_path, progress_callback=self.update_progress)
                self.root.after(0, lambda: self.on_done(output_path, True))
            except Exception as e:
                self.root.after(0, lambda: self.on_done(str(e), False))

        threading.Thread(target=worker, daemon=True).start()

    def on_done(self, msg, success):
        self.btn_start.config(state="normal")
        if success:
            self.lbl_status.config(text="处理完成！", fg="green")
            self.progress["value"] = self.progress["maximum"]
            messagebox.showinfo("完成", f"文档已处理完成，保存至:\n{msg}")
        else:
            self.lbl_status.config(text=f"处理失败: {msg}", fg="red")
            messagebox.showerror("错误", f"处理过程中发生错误:\n{msg}")


def main():
    # 如果传了命令行参数，走命令行模式
    if len(sys.argv) >= 2 and os.path.isfile(sys.argv[1]):
        input_path = sys.argv[1]
        base, ext = os.path.splitext(input_path)
        output_path = base + "_optimized" + ext
        process_docx(input_path, output_path)
        print(f"完成，已保存至: {output_path}")
        return

    root = tk.Tk()
    app = FormatApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
