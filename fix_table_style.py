# 修改表格字体和边框设置
with open('data/报告word表格处理.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修改字体设置：所有非汉字使用 Times New Roman 五号
old_font = '''    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = 'Arial Narrow'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                    run.font.size = Pt(10.5)'''

new_font = '''    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    text = run.text
                    if text and not any('\u4e00' <= c <= '\u9fff' for c in text):
                        run.font.name = 'Times New Roman'
                    else:
                        run.font.name = 'Arial Narrow'
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                    run.font.size = Pt(10.5)'''

content = content.replace(old_font, new_font)

# 2. 修改边框：顶端和底端由1.5磅改为1磅 (24 -> 16)
content = content.replace('set_cell_border(cell, top={"sz": "24", "val": "single"})', 'set_cell_border(cell, top={"sz": "16", "val": "single"})')
content = content.replace('set_cell_border(cell, bottom={"sz": "24", "val": "single"})', 'set_cell_border(cell, bottom={"sz": "16", "val": "single"})')

with open('data/报告word表格处理.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('修改成功')