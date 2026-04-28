"""
PDF 批处理工具 - 批量合并、拆分和转换 PDF 文件。

功能：
    - 合并 PDF：将多个 PDF 文件合并为一个文件
    - 拆分 PDF：将一个 PDF 按页码范围拆分为多个文件
    - 提取页面：从 PDF 中提取指定页面
    - 添加水印：为 PDF 添加文字水印（支持自定义文字、颜色、透明度、角度）
    - 页面旋转：旋转 PDF 页面（90°/180°/270°）
    - 删除页面：删除 PDF 中的指定页面

界面：
    - 左侧文件列表：支持拖拽添加文件，可调整顺序
    - 右侧操作面板：选择操作类型和参数
    - 底部输出目录：记忆上次输出目录
    - 进度条显示处理进度

配置：
    - 输出目录记忆：保存到 config/pdf_tool.json
    - 水印参数记忆：上次使用的水印文字、颜色等

依赖：PyMuPDF, reportlab, pypdf
"""
import os
import sys
import copy
import math
import threading
import tkinter as tk
import json
from tkinter import messagebox, filedialog, ttk, colorchooser


def _showinfo(title, msg, **kw):
    print(f"[{title}] {msg}")
    messagebox.showinfo(title, msg, **kw)


def _showerror(title, msg, **kw):
    print(f"[{title}] {msg}")
    messagebox.showerror(title, msg, **kw)


def _showwarning(title, msg, **kw):
    print(f"[{title}] {msg}")
    messagebox.showwarning(title, msg, **kw)


def _askyesno(title, msg, **kw):
    print(f"[{title}] {msg}")
    return messagebox.askyesno(title, msg, **kw)

THIS_FILE = os.path.abspath(__file__)
sys.dont_write_bytecode = True
_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(THIS_FILE), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

CONFIG_FILE = os.path.join(_PROJECT_ROOT, 'config', 'pdf_tool.json')

import fitz
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color

from pypdf import PdfReader, PdfWriter

_FONT_REGISTERED = False

def _register_fonts():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    _FONT_REGISTERED = True
    font_dirs = [
        os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts'),
    ]
    simhei = None
    simsun = None
    for d in font_dirs:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            fl = fn.lower()
            if fl == 'simhei.ttf' and simhei is None:
                simhei = os.path.join(d, fn)
            elif fl == 'simsun.ttc' and simsun is None:
                simsun = os.path.join(d, fn)
            elif fl == 'msyh.ttc' and simhei is None:
                simhei = os.path.join(d, fn)
            elif fl == 'msyhbd.ttc' and simhei is None:
                simhei = os.path.join(d, fn)
    if simhei:
        try:
            pdfmetrics.registerFont(TTFont('SimHei', simhei))
        except Exception:
            pass
    if simsun:
        try:
            pdfmetrics.registerFont(TTFont('SimSun', simsun))
        except Exception:
            pass

_register_fonts()

_CN_FONT = 'SimHei' if 'SimHei' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'


def load_config():
    """加载配置文件"""
    default_config = {
        'output_dir': os.path.join(os.path.expanduser('~'), 'Desktop')
    }
    if not os.path.exists(CONFIG_FILE):
        return default_config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return {**default_config, **config}
    except Exception:
        return default_config

def save_config(config):
    """保存配置文件"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def _center_window(win, parent, w, h):
    win.geometry(f"{w}x{h}")
    win.update_idletasks()
    px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    px = max(0, px)
    py = max(0, py)
    win.geometry(f"+{px}+{py}")


class PDFToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 批处理工具")
        self.root.geometry("1000x680")  # 增加宽度
        self.root.minsize(900, 550)  # 增加最小宽度

        # 加载配置
        self.config = load_config()
        self.pdf_files = []
        self.output_dir = tk.StringVar(value=self.config.get('output_dir', os.path.join(os.path.expanduser('~'), 'Desktop')))
        self.processing = False

        self._build_menu()
        self._build_ui()
        self._setup_drag_drop()  # 添加拖放支持
        self._update_status()

    # ==================== UI 构建 ====================

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开文件...", command=self.open_files, accelerator="Ctrl+O")
        file_menu.add_command(label="打开文件夹...", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="清空列表", command=self.clear_files)
        file_menu.add_separator()
        file_menu.add_command(label="设置输出目录...", command=self.set_output_dir)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="全选", command=self.select_all)
        edit_menu.add_command(label="取消全选", command=self.deselect_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="删除选中", command=self.remove_selected)
        edit_menu.add_command(label="上移", command=self.move_up)
        edit_menu.add_command(label="下移", command=self.move_down)
        menubar.add_cascade(label="编辑", menu=edit_menu)

        tool_menu = tk.Menu(menubar, tearoff=0)
        tool_menu.add_command(label="批量水印...", command=self.watermark_wizard)
        tool_menu.add_command(label="合并PDF...", command=self.merge_wizard)
        tool_menu.add_command(label="拆分PDF...", command=self.split_wizard)
        tool_menu.add_command(label="提取页面...", command=self.extract_pages_wizard)
        tool_menu.add_command(label="加密/解密...", command=self.encrypt_wizard)
        tool_menu.add_command(label="旋转页面...", command=self.rotate_wizard)
        tool_menu.add_command(label="删除页面...", command=self.delete_pages_wizard)
        tool_menu.add_command(label="PDF转图片...", command=self.pdf_to_images_wizard)
        menubar.add_cascade(label="工具", menu=tool_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menubar)
        self.root.bind('<Control-o>', lambda e: self.open_files())

    def _build_ui(self):
        top_frame = ttk.Frame(self.root, padding=5)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="输出目录:").pack(side=tk.LEFT)
        ttk.Entry(top_frame, textvariable=self.output_dir, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(top_frame, text="浏览...", command=self.set_output_dir).pack(side=tk.LEFT)

        list_frame = ttk.LabelFrame(self.root, text="PDF 文件列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        cols = ('select', 'filename', 'pages', 'size', 'path')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=12)
        self.tree.heading('select', text='✔')
        self.tree.heading('filename', text='文件名')
        self.tree.heading('pages', text='页数')
        self.tree.heading('size', text='大小')
        self.tree.heading('path', text='路径')
        self.tree.column('select', width=40, anchor='center', stretch=False)
        self.tree.column('filename', width=250, minwidth=150)
        self.tree.column('pages', width=60, anchor='center', stretch=False)
        self.tree.column('size', width=80, anchor='center', stretch=False)
        self.tree.column('path', width=300, minwidth=200)

        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.config(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<Button-1>', self._on_tree_click)
        self.tree.bind('<Double-Button-1>', self._on_tree_dblclick)

        btn_frame = ttk.Frame(self.root, padding=5)
        btn_frame.pack(fill=tk.X, padx=5)

        ttk.Button(btn_frame, text="打开文件", command=self.open_files).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="移除选中", command=self.remove_selected).pack(side=tk.LEFT, padx=3)
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        self.btn_watermark = ttk.Button(btn_frame, text="💧 批量水印", command=self.watermark_wizard)
        self.btn_watermark.pack(side=tk.LEFT, padx=3)

        self.btn_merge = ttk.Button(btn_frame, text="📎 合并PDF", command=self.merge_wizard)
        self.btn_merge.pack(side=tk.LEFT, padx=3)

        self.btn_split = ttk.Button(btn_frame, text="✂ 拆分PDF", command=self.split_wizard)
        self.btn_split.pack(side=tk.LEFT, padx=3)

        self.btn_extract = ttk.Button(btn_frame, text="📄 提取页面", command=self.extract_pages_wizard)
        self.btn_extract.pack(side=tk.LEFT, padx=3)

        self.btn_encrypt = ttk.Button(btn_frame, text="🔒 加密/解密", command=self.encrypt_wizard)
        self.btn_encrypt.pack(side=tk.LEFT, padx=3)

        self.btn_rotate = ttk.Button(btn_frame, text="🔄 旋转页面", command=self.rotate_wizard)
        self.btn_rotate.pack(side=tk.LEFT, padx=3)

        self.btn_toimg = ttk.Button(btn_frame, text="🖼 PDF转图片", command=self.pdf_to_images_wizard)
        self.btn_toimg.pack(side=tk.LEFT, padx=3)

        self.btn_delete_pages = ttk.Button(btn_frame, text="🗑 删除页面", command=self.delete_pages_wizard)
        self.btn_delete_pages.pack(side=tk.LEFT, padx=3)

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(status_frame, mode='determinate', length=200)
        self.progress.pack(side=tk.RIGHT)

    # ==================== 文件管理 ====================

    def open_files(self):
        paths = filedialog.askopenfilenames(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if paths:
            self._add_files(list(paths))

    def open_folder(self):
        folder = filedialog.askdirectory(title="选择包含PDF的文件夹")
        if not folder:
            return
        pdfs = []
        for fn in os.listdir(folder):
            if fn.lower().endswith('.pdf'):
                pdfs.append(os.path.join(folder, fn))
        if pdfs:
            self._add_files(pdfs)
        else:
            _showinfo("提示", "该文件夹中没有PDF文件")

    def _add_files(self, paths):
        existing = {self.tree.item(item, 'values')[4] for item in self.tree.get_children()}
        added = 0
        # 如果是第一次添加文件，设置默认输出目录为第一个文件的所在目录
        if not self.pdf_files and paths:
            first_file_dir = os.path.dirname(paths[0])
            self.output_dir.set(first_file_dir)
            self.config['output_dir'] = first_file_dir
            save_config(self.config)
        for p in paths:
            if p in existing:
                continue
            try:
                info = self._get_pdf_info(p)
                self.tree.insert('', tk.END, values=('✔', info['name'], info['pages'], info['size_str'], p))
                self.pdf_files.append(p)
                added += 1
            except Exception as e:
                _showwarning("无法读取", f"{os.path.basename(p)}\n{e}")
        self._update_status()

    def _get_pdf_info(self, path):
        doc = fitz.open(path)
        pages = len(doc)
        doc.close()
        fsize = os.path.getsize(path)
        if fsize > 1024 * 1024:
            size_str = f"{fsize / (1024*1024):.1f} MB"
        else:
            size_str = f"{fsize / 1024:.0f} KB"
        return {'name': os.path.basename(path), 'pages': pages, 'size_str': size_str}

    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        col = self.tree.identify_column(event.x)
        if col != '#1':
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        vals = list(self.tree.item(item, 'values'))
        vals[0] = '' if vals[0] == '✔' else '✔'
        self.tree.item(item, values=vals)

    def _on_tree_dblclick(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == 'cell':
            col = self.tree.identify_column(event.x)
            if col == '#1':
                return
        item = self.tree.identify_row(event.y)
        if item:
            path = self.tree.item(item, 'values')[4]
            os.startfile(path)

    def select_all(self):
        for item in self.tree.get_children():
            vals = list(self.tree.item(item, 'values'))
            vals[0] = '✔'
            self.tree.item(item, values=vals)

    def deselect_all(self):
        for item in self.tree.get_children():
            vals = list(self.tree.item(item, 'values'))
            vals[0] = ''
            self.tree.item(item, values=vals)

    def remove_selected(self):
        to_remove = [item for item in self.tree.get_children()
                     if self.tree.item(item, 'values')[0] == '✔']
        if not to_remove:
            _showinfo("提示", "请先勾选要移除的文件")
            return
        for item in to_remove:
            path = self.tree.item(item, 'values')[4]
            if path in self.pdf_files:
                self.pdf_files.remove(path)
            self.tree.delete(item)
        self._update_status()

    def move_up(self):
        sel = self.tree.selection()
        if not sel:
            return
        for item in sel:
            idx = self.tree.index(item)
            if idx > 0:
                self.tree.move(item, '', idx - 1)

    def move_down(self):
        sel = self.tree.selection()
        if not sel:
            return
        for item in reversed(sel):
            idx = self.tree.index(item)
            if idx < len(self.tree.get_children()) - 1:
                self.tree.move(item, '', idx + 1)

    def clear_files(self):
        self.tree.delete(*self.tree.get_children())
        self.pdf_files.clear()
        self._update_status()

    def set_output_dir(self):
        d = filedialog.askdirectory(title="选择输出目录", initialdir=self.output_dir.get())
        if d:
            self.output_dir.set(d)
            # 保存配置
            self.config['output_dir'] = d
            save_config(self.config)

    def _get_checked_files(self):
        result = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, 'values')
            if vals[0] == '✔':
                result.append({'path': vals[4], 'name': vals[1], 'pages': vals[2]})
        return result

    def _get_all_files(self):
        result = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, 'values')
            result.append({'path': vals[4], 'name': vals[1], 'pages': vals[2]})
        return result

    def _update_status(self):
        total = len(self.tree.get_children())
        checked = len(self._get_checked_files())
        self.status_var.set(f"共 {total} 个文件，已选 {checked} 个")

    def _setup_drag_drop(self):
        """设置拖放支持"""
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD
            if isinstance(self.root, TkinterDnD.Tk):
                self.tree.drop_target_register(DND_FILES)
                self.tree.dnd_bind('<<Drop>>', self._on_drop)
                self.status_var.set("就绪 - 可拖拽PDF文件到列表中")
        except ImportError:
            pass

    def _on_drop(self, event):
        """处理拖放事件"""
        files = self._parse_dropped_files(event.data)
        if files:
            self._add_files(files)

    def _parse_dropped_files(self, data):
        """解析拖放的文件路径"""
        files = []
        if data:
            # 处理不同格式的拖放数据
            if data.startswith('{') and data.endswith('}'):
                # Windows 格式: {C:\path\to\file.pdf}
                paths = data.strip('{}').split('} {')
            else:
                # 其他格式，按空格分割
                paths = data.split()
            for path in paths:
                path = path.strip()
                if path and path.lower().endswith('.pdf') and os.path.exists(path):
                    files.append(path)
        return files

    # ==================== 水印功能 ====================

    def watermark_wizard(self):
        files = self._get_checked_files()
        if not files:
            files = self._get_all_files()
        if not files:
            _showinfo("提示", "请先打开PDF文件")
            return

        config = {'files': files}

        # ---- 第1步：水印内容 ----
        dlg = tk.Toplevel(self.root)
        dlg.title("第 1 步 / 共 5 步 — 水印内容")
        _center_window(dlg, self.root, 500, 300)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        ttk.Label(dlg, text="选择水印内容来源：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=20, pady=(15, 8))
        content_mode = tk.StringVar(value='custom')
        ttk.Radiobutton(dlg, text="自定义输入水印文字", variable=content_mode, value='custom').pack(anchor=tk.W, padx=30, pady=2)
        ttk.Radiobutton(dlg, text="使用文件名作为水印", variable=content_mode, value='filename').pack(anchor=tk.W, padx=30, pady=2)
        ttk.Radiobutton(dlg, text="自定义 + 文件名（组合）", variable=content_mode, value='both').pack(anchor=tk.W, padx=30, pady=2)

        ttk.Separator(dlg, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=8)
        ttk.Label(dlg, text="自定义水印文字：").pack(anchor=tk.W, padx=20)
        custom_text = tk.StringVar(value="机密文件")
        ttk.Entry(dlg, textvariable=custom_text, font=('', 12), width=40).pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(dlg, text="预览：自定义文字 + 文件名 = \"机密文件 - 报表.pdf\"", foreground='gray').pack(anchor=tk.W, padx=20)

        step1_next = [None]

        def on_step1_next():
            config['content_mode'] = content_mode.get()
            config['custom_text'] = custom_text.get()
            dlg.destroy()
            step1_next[0]()

        bf = ttk.Frame(dlg)
        bf.pack(fill=tk.X, side=tk.BOTTOM, pady=10, padx=20)
        ttk.Button(bf, text="取消", command=dlg.destroy, width=8).pack(side=tk.RIGHT)
        ttk.Button(bf, text="下一步 ▶", command=on_step1_next, width=12).pack(side=tk.RIGHT, padx=5)

        def step2():
            # ---- 第2步：水印样式 ----
            d2 = tk.Toplevel(self.root)
            d2.title("第 2 步 / 共 5 步 — 水印样式")
            _center_window(d2, self.root, 500, 420)
            d2.transient(self.root)
            d2.grab_set()
            d2.resizable(False, False)

            ttk.Label(d2, text="选择水印样式：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=20, pady=(15, 8))
            wm_style = tk.StringVar(value='diagonal_full')
            styles = [
                ('center_large', '整页大水印（居中）'),
                ('diagonal_full', '45度倾斜布满全页'),
                ('tile_horizontal', '水平平铺'),
                ('tile_vertical', '垂直平铺'),
                ('tile_grid', '网格平铺'),
                ('corners', '仅四角'),
                ('top_banner', '顶部横幅'),
                ('bottom_banner', '底部横幅'),
            ]
            for val, text in styles:
                ttk.Radiobutton(d2, text=text, variable=wm_style, value=val).pack(anchor=tk.W, padx=30, pady=2)

            ttk.Separator(d2, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=8)
            ttk.Label(d2, text="水印字体大小：").pack(anchor=tk.W, padx=20)
            font_size = tk.IntVar(value=30)
            sf = ttk.Frame(d2)
            sf.pack(fill=tk.X, padx=20)
            ttk.Scale(sf, from_=10, to=80, variable=font_size, orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(sf, textvariable=font_size, width=4).pack(side=tk.RIGHT)

            def on_step2_next():
                config['style'] = wm_style.get()
                config['font_size'] = font_size.get()
                d2.destroy()
                step3()

            def on_step2_prev():
                d2.destroy()
                self.root.after(100, watermark_wizard)

            bf2 = ttk.Frame(d2)
            bf2.pack(fill=tk.X, side=tk.BOTTOM, pady=10, padx=20)
            ttk.Button(bf2, text="取消", command=d2.destroy, width=8).pack(side=tk.RIGHT)
            ttk.Button(bf2, text="下一步 ▶", command=on_step2_next, width=12).pack(side=tk.RIGHT, padx=5)
            ttk.Button(bf2, text="◀ 上一步", command=on_step2_prev, width=10).pack(side=tk.LEFT)

            d2.wait_window()

        def step3():
            # ---- 第3步：颜色深度 ----
            d3 = tk.Toplevel(self.root)
            d3.title("第 3 步 / 共 5 步 — 颜色深度")
            _center_window(d3, self.root, 500, 300)
            d3.transient(self.root)
            d3.grab_set()
            d3.resizable(False, False)

            ttk.Label(d3, text="水印颜色与透明度：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=20, pady=(15, 8))

            ttk.Label(d3, text="水印颜色：").pack(anchor=tk.W, padx=20, pady=(5, 0))
            cf = ttk.Frame(d3)
            cf.pack(fill=tk.X, padx=20, pady=5)
            wm_color = tk.StringVar(value='#808080')
            color_preview = tk.Label(cf, bg='#808080', width=6, height=1, relief=tk.SUNKEN)
            color_preview.pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(cf, text="选择颜色...", command=lambda: self._pick_color(wm_color, color_preview)).pack(side=tk.LEFT)

            ttk.Separator(d3, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=8)
            ttk.Label(d3, text="透明度（0=全透明，100=不透明）：").pack(anchor=tk.W, padx=20)
            opacity = tk.IntVar(value=20)
            of = ttk.Frame(d3)
            of.pack(fill=tk.X, padx=20, pady=5)
            ttk.Scale(of, from_=0, to=100, variable=opacity, orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(of, textvariable=opacity, width=4).pack(side=tk.RIGHT)
            ttk.Label(d3, text="提示：文档水印通常使用 10~30 的透明度", foreground='gray').pack(anchor=tk.W, padx=20, pady=5)

            def on_step3_next():
                config['color'] = wm_color.get()
                config['opacity'] = opacity.get() / 100.0
                d3.destroy()
                step4()

            def on_step3_prev():
                d3.destroy()
                step2()

            bf3 = ttk.Frame(d3)
            bf3.pack(fill=tk.X, side=tk.BOTTOM, pady=10, padx=20)
            ttk.Button(bf3, text="取消", command=d3.destroy, width=8).pack(side=tk.RIGHT)
            ttk.Button(bf3, text="下一步 ▶", command=on_step3_next, width=12).pack(side=tk.RIGHT, padx=5)
            ttk.Button(bf3, text="◀ 上一步", command=on_step3_prev, width=10).pack(side=tk.LEFT)

            d3.wait_window()

        def step4():
            # ---- 第4步：水印层次 ----
            d4 = tk.Toplevel(self.root)
            d4.title("第 4 步 / 共 5 步 — 水印层次")
            _center_window(d4, self.root, 520, 300)
            d4.transient(self.root)
            d4.grab_set()
            d4.resizable(False, False)

            ttk.Label(d4, text="水印在页面中的层次位置：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=20, pady=(15, 8))
            wm_layer = tk.StringVar(value='under')
            layers = [
                ('under', '最底层（水印在内容下方）— 推荐，不影响阅读'),
                ('over', '最上层（水印在内容上方）— 防篡改效果好'),
                ('under_over', '双层（上下各一层）— 防篡改最强'),
            ]
            for val, text in layers:
                ttk.Radiobutton(d4, text=text, variable=wm_layer, value=val).pack(anchor=tk.W, padx=30, pady=5)

            ttk.Separator(d4, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=8)
            ttk.Label(d4, text="水印旋转角度（仅对居中大水印有效）：").pack(anchor=tk.W, padx=20)
            wm_angle = tk.IntVar(value=45)
            af = ttk.Frame(d4)
            af.pack(fill=tk.X, padx=20, pady=5)
            ttk.Scale(af, from_=-90, to=90, variable=wm_angle, orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(af, textvariable=wm_angle, width=4).pack(side=tk.RIGHT)

            def on_step4_next():
                config['layer'] = wm_layer.get()
                config['angle'] = wm_angle.get()
                d4.destroy()
                step5()

            def on_step4_prev():
                d4.destroy()
                step3()

            bf4 = ttk.Frame(d4)
            bf4.pack(fill=tk.X, side=tk.BOTTOM, pady=10, padx=20)
            ttk.Button(bf4, text="取消", command=d4.destroy, width=8).pack(side=tk.RIGHT)
            ttk.Button(bf4, text="下一步 ▶", command=on_step4_next, width=12).pack(side=tk.RIGHT, padx=5)
            ttk.Button(bf4, text="◀ 上一步", command=on_step4_prev, width=10).pack(side=tk.LEFT)

            d4.wait_window()

        def step5():
            # ---- 第5步：保存设置 ----
            d5 = tk.Toplevel(self.root)
            d5.title("第 5 步 / 共 5 步 — 保存设置")
            _center_window(d5, self.root, 520, 320)
            d5.transient(self.root)
            d5.grab_set()
            d5.resizable(False, False)

            ttk.Label(d5, text="输出设置：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=20, pady=(15, 8))

            ttk.Label(d5, text="保存位置：").pack(anchor=tk.W, padx=20)
            out_dir = tk.StringVar(value=self.output_dir.get())
            df = ttk.Frame(d5)
            df.pack(fill=tk.X, padx=20, pady=5)
            ttk.Entry(df, textvariable=out_dir, width=45).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(df, text="浏览...", command=lambda: out_dir.set(
                filedialog.askdirectory(title="选择输出目录", initialdir=out_dir.get()) or out_dir.get()
            )).pack(side=tk.LEFT, padx=5)

            ttk.Separator(d5, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=8)

            save_mode = tk.StringVar(value='suffix')
            ttk.Radiobutton(d5, text="保留原文件，新文件添加后缀（如 xxx_水印.pdf）", variable=save_mode, value='suffix').pack(anchor=tk.W, padx=30, pady=3)
            ttk.Radiobutton(d5, text="覆盖原文件（请谨慎）", variable=save_mode, value='overwrite').pack(anchor=tk.W, padx=30, pady=3)

            ttk.Separator(d5, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=8)
            info_text = f"将对 {len(files)} 个PDF文件添加水印"
            ttk.Label(d5, text=info_text, foreground='blue', font=('', 10)).pack(anchor=tk.W, padx=20, pady=5)

            def on_apply():
                config['output_dir'] = out_dir.get()
                config['save_mode'] = save_mode.get()
                d5.destroy()
                self._apply_watermark(config)

            def on_step5_prev():
                d5.destroy()
                step4()

            bf5 = ttk.Frame(d5)
            bf5.pack(fill=tk.X, side=tk.BOTTOM, pady=10, padx=20)
            ttk.Button(bf5, text="取消", command=d5.destroy, width=8).pack(side=tk.RIGHT)
            ttk.Button(bf5, text="✓ 开始添加水印", command=on_apply, width=14).pack(side=tk.RIGHT, padx=5)
            ttk.Button(bf5, text="◀ 上一步", command=on_step5_prev, width=10).pack(side=tk.LEFT)

            d5.wait_window()

        step1_next[0] = step2
        dlg.wait_window()

    def _pick_color(self, color_var, preview_label):
        result = colorchooser.askcolor(color=color_var.get(), title="选择水印颜色")
        if result and result[1]:
            color_var.set(result[1])
            preview_label.config(bg=result[1])

    def _apply_watermark(self, config):
        if self.processing:
            return
        self.processing = True

        def worker():
            files = config['files']
            total = len(files)
            success = 0
            errors = []

            for idx, f in enumerate(files):
                try:
                    self.root.after(0, lambda i=idx, n=f['name']: self.status_var.set(f"正在处理 ({i+1}/{total}): {n}"))
                    self.root.after(0, lambda i=idx: self.progress.configure(value=int((i / total) * 100)))

                    src_path = f['path']
                    if config['content_mode'] == 'filename':
                        wm_text = os.path.splitext(f['name'])[0]
                    elif config['content_mode'] == 'both':
                        wm_text = f"{config['custom_text']} - {os.path.splitext(f['name'])[0]}"
                    else:
                        wm_text = config['custom_text']

                    if not wm_text.strip():
                        errors.append(f"{f['name']}: 水印文字为空")
                        continue

                    doc = fitz.open(src_path)

                    for page in doc:
                        pw, ph = page.rect.width, page.rect.height
                        wm_pdf = self._create_watermark_pdf(wm_text, config, pw, ph)
                        wm_doc = fitz.open(wm_pdf)

                        if config['layer'] == 'under':
                            page.show_pdf_page(page.rect, wm_doc, 0, overlay=False)
                        elif config['layer'] == 'over':
                            page.show_pdf_page(page.rect, wm_doc, 0, overlay=True)
                        elif config['layer'] == 'under_over':
                            page.show_pdf_page(page.rect, wm_doc, 0, overlay=False)
                            page.show_pdf_page(page.rect, wm_doc, 0, overlay=True)

                        wm_doc.close()
                        try:
                            os.remove(wm_pdf)
                        except Exception:
                            pass

                    if config['save_mode'] == 'overwrite':
                        tmp_path = src_path + '.tmp.pdf'
                        doc.save(tmp_path)
                        doc.close()
                        try:
                            os.replace(tmp_path, src_path)
                        except Exception:
                            os.remove(tmp_path)
                            errors.append(f"{f['name']}: 覆盖保存失败")
                            continue
                    else:
                        base = os.path.splitext(f['name'])[0]
                        out_path = os.path.join(config['output_dir'], f"{base}_水印.pdf")
                        os.makedirs(os.path.dirname(out_path), exist_ok=True)
                        doc.save(out_path)
                        doc.close()

                    success += 1
                except Exception as e:
                    errors.append(f"{f['name']}: {e}")

            self.root.after(0, lambda: self.progress.configure(value=100))
            msg = f"水印添加完成！\n\n成功：{success} 个"
            if errors:
                msg += f"\n失败：{len(errors)} 个\n" + "\n".join(errors[:5])
            self.root.after(0, lambda: _showinfo("完成", msg))
            self.root.after(0, lambda: self.status_var.set(f"水印完成：{success} 成功，{len(errors)} 失败"))
            self.processing = False

        threading.Thread(target=worker, daemon=True).start()

    def _create_watermark_pdf(self, text, config, page_w=595, page_h=842):
        style = config['style']
        font_size = int(config['font_size'])
        opacity = config['opacity']
        color_hex = config['color']
        angle = config.get('angle', 45)

        r = int(color_hex[1:3], 16) / 255.0
        g = int(color_hex[3:5], 16) / 255.0
        b = int(color_hex[5:7], 16) / 255.0

        tmp_path = os.path.join(os.environ.get('TEMP', '.'), f'_pdf_wm_{os.getpid()}.pdf')
        w, h = int(page_w), int(page_h)
        c = rl_canvas.Canvas(tmp_path, pagesize=(w, h))
        c.setFillAlpha(opacity)
        c.setFillColor(Color(r, g, b, alpha=opacity))
        c.setFont(_CN_FONT, font_size)

        tw = c.stringWidth(text, _CN_FONT, font_size)

        if style == 'diagonal_full':
            c.saveState()
            c.translate(w / 2, h / 2)
            c.rotate(45)
            step_x = int(max(tw + 60, 120))
            step_y = int(max(font_size + 30, 60))
            for y in range(-h, h * 2, step_y):
                for x in range(-w, w * 2, step_x):
                    c.drawString(x, y, text)
            c.restoreState()
        elif style == 'tile_horizontal':
            step_x = int(max(tw + 60, 120))
            step_y = int(max(font_size + 30, 60))
            for y in range(step_y, h, step_y):
                for x in range(0, w + step_x, step_x):
                    c.drawString(x, y, text)
        elif style == 'tile_vertical':
            c.saveState()
            c.translate(w / 2, h / 2)
            c.rotate(90)
            step_x = int(max(tw + 60, 120))
            step_y = int(max(font_size + 30, 60))
            for y in range(-h, h * 2, step_y):
                for x in range(-w, w * 2, step_x):
                    c.drawString(x, y, text)
            c.restoreState()
        elif style == 'tile_grid':
            step_x = int(max(tw + 80, 150))
            step_y = int(max(font_size + 40, 80))
            for y in range(step_y, h, step_y):
                for x in range(0, w + step_x, step_x):
                    c.drawString(x, y, text)
            c.saveState()
            c.translate(w / 2, h / 2)
            c.rotate(45)
            for y in range(-h, h * 2, step_y):
                for x in range(-w, w * 2, step_x):
                    c.drawString(x, y, text)
            c.restoreState()
        elif style == 'center_large':
            c.saveState()
            big_size = int(min(font_size * 3, 80))
            c.setFont(_CN_FONT, big_size)
            c.translate(w / 2, h / 2)
            c.rotate(angle)
            bt = c.stringWidth(text, _CN_FONT, big_size)
            c.drawString(-bt / 2, -big_size / 3, text)
            c.restoreState()
        elif style == 'corners':
            margin = 40
            small_size = max(font_size - 4, 10)
            c.setFont(_CN_FONT, small_size)
            stw = c.stringWidth(text, _CN_FONT, small_size)
            c.drawString(margin, h - margin - small_size, text)
            c.drawString(w - margin - stw, h - margin - small_size, text)
            c.drawString(margin, margin, text)
            c.drawString(w - margin - stw, margin, text)
        elif style == 'top_banner':
            banner_h = font_size + 20
            c.setFillColor(Color(r, g, b, alpha=opacity * 0.3))
            c.rect(0, h - banner_h, w, banner_h, fill=True, stroke=False)
            c.setFillColor(Color(r, g, b, alpha=opacity))
            bt = c.stringWidth(text, _CN_FONT, font_size)
            c.drawString((w - bt) / 2, h - banner_h + 8, text)
        elif style == 'bottom_banner':
            banner_h = font_size + 20
            c.setFillColor(Color(r, g, b, alpha=opacity * 0.3))
            c.rect(0, 0, w, banner_h, fill=True, stroke=False)
            c.setFillColor(Color(r, g, b, alpha=opacity))
            bt = c.stringWidth(text, _CN_FONT, font_size)
            c.drawString((w - bt) / 2, 8, text)

        c.save()
        return tmp_path

    # ==================== 合并PDF ====================

    def merge_wizard(self):
        files = self._get_checked_files()
        if not files:
            files = self._get_all_files()
        if not files:
            _showinfo("提示", "请先打开PDF文件")
            return
        if len(files) < 2:
            _showinfo("提示", "合并至少需要2个PDF文件")
            return

        win = tk.Toplevel(self.root)
        win.title("合并PDF向导")
        _center_window(win, self.root, 650, 580)
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text="拖动调整合并顺序（上下拖动行）：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))

        list_frame = ttk.Frame(win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        lb = tk.Listbox(list_frame, font=('', 11), selectmode=tk.SINGLE, height=12)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=lb.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb.config(yscrollcommand=sb.set)

        ordered = list(files)
        for f in ordered:
            lb.insert(tk.END, f"  {f['name']}  ({f['pages']}页)")

        def move_item(direction):
            sel = lb.curselection()
            if not sel:
                return
            idx = sel[0]
            new_idx = idx + direction
            if new_idx < 0 or new_idx >= lb.size():
                return
            lb.delete(idx)
            item = ordered.pop(idx)
            lb.insert(new_idx, f"  {item['name']}  ({item['pages']}页)")
            ordered.insert(new_idx, item)
            lb.selection_set(new_idx)

        btn_up_down = ttk.Frame(win)
        btn_up_down.pack(pady=5)
        ttk.Button(btn_up_down, text="▲ 上移", command=lambda: move_item(-1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_up_down, text="▼ 下移", command=lambda: move_item(1)).pack(side=tk.LEFT, padx=5)

        lb.bind('<Button-1>', lambda e: lb.focus_set())
        lb.bind('<B1-Motion>', lambda e: None)

        ttk.Separator(win, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(win, text="合并选项：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=10)

        add_wm = tk.BooleanVar(value=False)
        ttk.Checkbutton(win, text="合并后添加水印", variable=add_wm).pack(anchor=tk.W, padx=20)

        ttk.Separator(win, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(win, text="输出文件名：").pack(anchor=tk.W, padx=10)
        out_name = tk.StringVar(value="合并结果.pdf")
        ttk.Entry(win, textvariable=out_name, width=40).pack(fill=tk.X, padx=20, pady=5)

        out_dir_merge = tk.StringVar(value=self.output_dir.get())
        dir_frame = ttk.Frame(win)
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(dir_frame, text="保存到：").pack(side=tk.LEFT)
        ttk.Entry(dir_frame, textvariable=out_dir_merge, width=45).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=lambda: out_dir_merge.set(
            filedialog.askdirectory(title="选择输出目录", initialdir=out_dir_merge.get()) or out_dir_merge.get()
        )).pack(side=tk.LEFT)

        def do_merge():
            win.destroy()
            self._do_merge(ordered, out_name.get(), out_dir_merge.get(), add_wm.get())

        btn_frame = ttk.Frame(win, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="开始合并", command=do_merge).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _do_merge(self, files, out_name, out_dir, add_watermark):
        if self.processing:
            return
        self.processing = True

        def worker():
            try:
                self.root.after(0, lambda: self.status_var.set("正在合并PDF..."))
                self.root.after(0, lambda: self.progress.configure(value=10))

                merged = fitz.open()
                for f in files:
                    src = fitz.open(f['path'])
                    merged.insert_pdf(src)
                    src.close()

                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, out_name)
                merged.save(out_path)
                merged.close()

                self.root.after(0, lambda: self.progress.configure(value=70))

                if add_watermark:
                    wm_config = {
                        'content_mode': 'custom',
                        'custom_text': os.path.splitext(out_name)[0],
                        'style': 'diagonal_full',
                        'font_size': 30,
                        'color': '#808080',
                        'opacity': 0.2,
                        'layer': 'over',
                        'angle': 45,
                        'output_dir': out_dir,
                        'save_mode': 'overwrite',
                        'files': [{'path': out_path, 'name': out_name, 'pages': '?'}],
                    }
                    doc = fitz.open(out_path)
                    for page in doc:
                        pw, ph = page.rect.width, page.rect.height
                        wm_pdf = self._create_watermark_pdf(wm_config['custom_text'], wm_config, pw, ph)
                        wm_doc = fitz.open(wm_pdf)
                        page.show_pdf_page(page.rect, wm_doc, 0, overlay=False)
                        wm_doc.close()
                        try:
                            os.remove(wm_pdf)
                        except Exception:
                            pass
                    doc.save(out_path + '.tmp.pdf')
                    doc.close()
                    os.replace(out_path + '.tmp.pdf', out_path)

                self.root.after(0, lambda: self.progress.configure(value=100))
                self.root.after(0, lambda: _showinfo("完成", f"PDF合并完成！\n\n保存至：{out_path}"))
                self.root.after(0, lambda: self.status_var.set("合并完成"))

            except Exception as e:
                self.root.after(0, lambda: _showerror("合并失败", str(e)))
                self.root.after(0, lambda: self.status_var.set("合并失败"))
            finally:
                self.processing = False

        threading.Thread(target=worker, daemon=True).start()

    # ==================== 拆分PDF ====================

    def split_wizard(self):
        files = self._get_checked_files()
        if not files:
            files = self._get_all_files()
        if not files:
            _showinfo("提示", "请先打开PDF文件")
            return

        win = tk.Toplevel(self.root)
        win.title("拆分PDF")
        _center_window(win, self.root, 520, 430)
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text="拆分方式：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))

        split_mode = tk.StringVar(value='each_page')
        modes = [
            ('each_page', '每页拆分为单独PDF'),
            ('every_n', '每N页拆分为一个PDF'),
            ('range', '按页码范围拆分（如 1-3,5,7-10）'),
        ]
        for val, text in modes:
            ttk.Radiobutton(win, text=text, variable=split_mode, value=val).pack(anchor=tk.W, padx=20, pady=3)

        ttk.Separator(win, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)

        n_frame = ttk.Frame(win)
        n_frame.pack(fill=tk.X, padx=20)
        ttk.Label(n_frame, text="每N页：").pack(side=tk.LEFT)
        n_var = tk.IntVar(value=5)
        ttk.Spinbox(n_frame, from_=1, to=999, textvariable=n_var, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Label(win, text="页码范围：").pack(anchor=tk.W, padx=20, pady=(10, 0))
        range_var = tk.StringVar()
        ttk.Entry(win, textvariable=range_var, width=30).pack(anchor=tk.W, padx=20, pady=5)

        out_dir_split = tk.StringVar(value=self.output_dir.get())
        dir_frame = ttk.Frame(win)
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(dir_frame, text="保存到：").pack(side=tk.LEFT)
        ttk.Entry(dir_frame, textvariable=out_dir_split, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=lambda: out_dir_split.set(
            filedialog.askdirectory(title="选择输出目录", initialdir=out_dir_split.get()) or out_dir_split.get()
        )).pack(side=tk.LEFT)

        def do_split():
            win.destroy()
            self._do_split(files, split_mode.get(), n_var.get(), range_var.get(), out_dir_split.get())

        btn_frame = ttk.Frame(win, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="开始拆分", command=do_split).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _do_split(self, files, mode, n, range_str, out_dir):
        if self.processing:
            return
        self.processing = True

        def worker():
            total = len(files)
            success = 0
            errors = []
            for idx, f in enumerate(files):
                try:
                    self.root.after(0, lambda i=idx, n=f['name']: self.status_var.set(f"拆分 ({i+1}/{total}): {n}"))
                    doc = fitz.open(f['path'])
                    base = os.path.splitext(f['name'])[0]
                    sub_dir = os.path.join(out_dir, base)
                    os.makedirs(sub_dir, exist_ok=True)

                    if mode == 'each_page':
                        for pi in range(len(doc)):
                            new_doc = fitz.open()
                            new_doc.insert_pdf(doc, from_page=pi, to_page=pi)
                            new_doc.save(os.path.join(sub_dir, f"{base}_第{pi+1}页.pdf"))
                            new_doc.close()
                    elif mode == 'every_n':
                        total_pages = len(doc)
                        for start in range(0, total_pages, n):
                            end = min(start + n - 1, total_pages - 1)
                            new_doc = fitz.open()
                            new_doc.insert_pdf(doc, from_page=start, to_page=end)
                            new_doc.save(os.path.join(sub_dir, f"{base}_第{start+1}-{end+1}页.pdf"))
                            new_doc.close()
                    elif mode == 'range':
                        ranges = self._parse_page_ranges(range_str, len(doc))
                        for ri, (s, e) in enumerate(ranges):
                            new_doc = fitz.open()
                            new_doc.insert_pdf(doc, from_page=s - 1, to_page=e - 1)
                            new_doc.save(os.path.join(sub_dir, f"{base}_范围{ri+1}_{s}-{e}.pdf"))
                            new_doc.close()

                    doc.close()
                    success += 1
                except Exception as e:
                    errors.append(f"{f['name']}: {e}")

            msg = f"拆分完成！\n\n成功：{success} 个"
            if errors:
                msg += f"\n失败：{len(errors)} 个\n" + "\n".join(errors[:5])
            self.root.after(0, lambda: _showinfo("完成", msg))
            self.root.after(0, lambda: self.status_var.set(f"拆分完成：{success} 成功"))
            self.processing = False

        threading.Thread(target=worker, daemon=True).start()

    def _parse_page_ranges(self, range_str, total_pages):
        ranges = []
        # 将中文逗号替换为英文逗号
        range_str = range_str.replace('，', ',')
        for part in range_str.split(','):
            part = part.strip()
            if not part:
                continue
            try:
                if '-' in part:
                    s, e = part.split('-', 1)
                    s, e = int(s), int(e)
                    if s > e:
                        s, e = e, s
                    ranges.append((max(1, s), min(e, total_pages)))
                else:
                    p = int(part)
                    ranges.append((max(1, p), min(p, total_pages)))
            except ValueError:
                # 跳过无效的页码格式
                pass
        return ranges

    # ==================== 提取页面 ====================

    def extract_pages_wizard(self):
        files = self._get_checked_files()
        if not files:
            files = self._get_all_files()
        if not files:
            _showinfo("提示", "请先打开PDF文件")
            return

        win = tk.Toplevel(self.root)
        win.title("提取页面")
        _center_window(win, self.root, 520, 380)
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text="提取页面：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        ttk.Label(win, text="输入要提取的页码（如 1,3,5-8,12）：").pack(anchor=tk.W, padx=20)
        pages_var = tk.StringVar()
        ttk.Entry(win, textvariable=pages_var, width=30).pack(anchor=tk.W, padx=20, pady=5)

        out_dir_ext = tk.StringVar(value=self.output_dir.get())
        dir_frame = ttk.Frame(win)
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(dir_frame, text="保存到：").pack(side=tk.LEFT)
        ttk.Entry(dir_frame, textvariable=out_dir_ext, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=lambda: out_dir_ext.set(
            filedialog.askdirectory(title="选择输出目录", initialdir=out_dir_ext.get()) or out_dir_ext.get()
        )).pack(side=tk.LEFT)

        def do_extract():
            win.destroy()
            self._do_extract(files, pages_var.get(), out_dir_ext.get())

        btn_frame = ttk.Frame(win, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="开始提取", command=do_extract).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _do_extract(self, files, pages_str, out_dir):
        if self.processing:
            return
        self.processing = True

        def worker():
            success = 0
            errors = []
            try:
                for f in files:
                    try:
                        doc = fitz.open(f['path'])
                        base = os.path.splitext(f['name'])[0]
                        ranges = self._parse_page_ranges(pages_str, len(doc))
                        
                        # 检查是否有有效页码范围
                        if not ranges:
                            errors.append(f"{f['name']}: 未指定有效页码范围")
                            doc.close()
                            continue
                        
                        new_doc = fitz.open()
                        extracted = False
                        for s, e in ranges:
                            for pi in range(s - 1, e):
                                if 0 <= pi < len(doc):
                                    new_doc.insert_pdf(doc, from_page=pi, to_page=pi)
                                    extracted = True
                        
                        # 检查是否提取到页面
                        if not extracted:
                            errors.append(f"{f['name']}: 未提取到有效页面")
                            new_doc.close()
                            doc.close()
                            continue
                        
                        os.makedirs(out_dir, exist_ok=True)
                        new_doc.save(os.path.join(out_dir, f"{base}_提取.pdf"))
                        new_doc.close()
                        doc.close()
                        success += 1
                    except Exception as e:
                        errors.append(f"{f['name']}: {e}")
            finally:
                msg = f"提取完成！\n\n成功：{success} 个"
                if errors:
                    msg += f"\n失败：{len(errors)} 个\n" + "\n".join(errors[:5])
                self.root.after(0, lambda: _showinfo("完成", msg))
                self.root.after(0, lambda: self.status_var.set(f"提取完成：{success} 成功"))
                self.processing = False

        threading.Thread(target=worker, daemon=True).start()

    # ==================== 加密/解密 ====================

    def encrypt_wizard(self):
        files = self._get_checked_files()
        if not files:
            files = self._get_all_files()
        if not files:
            _showinfo("提示", "请先打开PDF文件")
            return

        win = tk.Toplevel(self.root)
        win.title("加密/解密PDF")
        _center_window(win, self.root, 520, 450)
        win.transient(self.root)
        win.grab_set()

        enc_mode = tk.StringVar(value='encrypt')
        ttk.Radiobutton(win, text="加密PDF", variable=enc_mode, value='encrypt').pack(anchor=tk.W, padx=20, pady=(10, 3))
        ttk.Radiobutton(win, text="解密PDF（需要原密码）", variable=enc_mode, value='decrypt').pack(anchor=tk.W, padx=20, pady=3)

        ttk.Separator(win, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(win, text="用户密码（打开PDF需要输入）：").pack(anchor=tk.W, padx=20)
        user_pwd = tk.StringVar()
        ttk.Entry(win, textvariable=user_pwd, show='*', width=30).pack(anchor=tk.W, padx=20, pady=5)

        ttk.Label(win, text="所有者密码（完全控制权限）：").pack(anchor=tk.W, padx=20)
        owner_pwd = tk.StringVar()
        ttk.Entry(win, textvariable=owner_pwd, show='*', width=30).pack(anchor=tk.W, padx=20, pady=5)

        ttk.Label(win, text="解密密码（解密时使用）：").pack(anchor=tk.W, padx=20)
        decrypt_pwd = tk.StringVar()
        ttk.Entry(win, textvariable=decrypt_pwd, show='*', width=30).pack(anchor=tk.W, padx=20, pady=5)

        out_dir_enc = tk.StringVar(value=self.output_dir.get())
        dir_frame = ttk.Frame(win)
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(dir_frame, text="保存到：").pack(side=tk.LEFT)
        ttk.Entry(dir_frame, textvariable=out_dir_enc, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=lambda: out_dir_enc.set(
            filedialog.askdirectory(title="选择输出目录", initialdir=out_dir_enc.get()) or out_dir_enc.get()
        )).pack(side=tk.LEFT)

        def do_encrypt():
            win.destroy()
            self._do_encrypt(files, enc_mode.get(), user_pwd.get(), owner_pwd.get(), decrypt_pwd.get(), out_dir_enc.get())

        btn_frame = ttk.Frame(win, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="开始", command=do_encrypt).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _do_encrypt(self, files, mode, user_pwd, owner_pwd, decrypt_pwd, out_dir):
        if self.processing:
            return
        self.processing = True

        def worker():
            success = 0
            errors = []
            for f in files:
                try:
                    if mode == 'encrypt':
                        doc = fitz.open(f['path'])
                        base = os.path.splitext(f['name'])[0]
                        out_path = os.path.join(out_dir, f"{base}_加密.pdf")
                        os.makedirs(out_dir, exist_ok=True)
                        doc.save(out_path, encryption=fitz.PDF_ENCRYPT_AES_256,
                                 owner_pw=owner_pwd or user_pwd, user_pw=user_pwd)
                        doc.close()
                    else:
                        doc = fitz.open(f['path'])
                        if doc.is_encrypted:
                            doc.authenticate(decrypt_pwd)
                        base = os.path.splitext(f['name'])[0]
                        out_path = os.path.join(out_dir, f"{base}_解密.pdf")
                        os.makedirs(out_dir, exist_ok=True)
                        doc.save(out_path)
                        doc.close()
                    success += 1
                except Exception as e:
                    errors.append(f"{f['name']}: {e}")

            msg = f"{'加密' if mode == 'encrypt' else '解密'}完成！\n\n成功：{success} 个"
            if errors:
                msg += f"\n失败：{len(errors)} 个\n" + "\n".join(errors[:5])
            self.root.after(0, lambda: _showinfo("完成", msg))
            self.root.after(0, lambda: self.status_var.set(f"处理完成：{success} 成功"))
            self.processing = False

        threading.Thread(target=worker, daemon=True).start()

    # ==================== 旋转页面 ====================

    def rotate_wizard(self):
        files = self._get_checked_files()
        if not files:
            files = self._get_all_files()
        if not files:
            _showinfo("提示", "请先打开PDF文件")
            return

        win = tk.Toplevel(self.root)
        win.title("旋转页面")
        _center_window(win, self.root, 500, 380)
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text="旋转角度：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))

        angle_var = tk.IntVar(value=90)
        for a, t in [(90, "顺时针90°"), (180, "180°"), (270, "逆时针90°")]:
            ttk.Radiobutton(win, text=t, variable=angle_var, value=a).pack(anchor=tk.W, padx=20, pady=3)

        ttk.Label(win, text="应用范围：").pack(anchor=tk.W, padx=20, pady=(10, 0))
        scope_var = tk.StringVar(value='all')
        ttk.Radiobutton(win, text="所有页面", variable=scope_var, value='all').pack(anchor=tk.W, padx=30)
        ttk.Radiobutton(win, text="指定页面（如 1,3,5-8）", variable=scope_var, value='custom').pack(anchor=tk.W, padx=30)
        pages_var = tk.StringVar()
        ttk.Entry(win, textvariable=pages_var, width=25).pack(anchor=tk.W, padx=40, pady=5)

        out_dir_rot = tk.StringVar(value=self.output_dir.get())
        dir_frame = ttk.Frame(win)
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(dir_frame, text="保存到：").pack(side=tk.LEFT)
        ttk.Entry(dir_frame, textvariable=out_dir_rot, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=lambda: out_dir_rot.set(
            filedialog.askdirectory(title="选择输出目录", initialdir=out_dir_rot.get()) or out_dir_rot.get()
        )).pack(side=tk.LEFT)

        def do_rotate():
            win.destroy()
            self._do_rotate(files, angle_var.get(), scope_var.get(), pages_var.get(), out_dir_rot.get())

        btn_frame = ttk.Frame(win, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="开始旋转", command=do_rotate).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _do_rotate(self, files, angle, scope, pages_str, out_dir):
        if self.processing:
            return
        self.processing = True

        def worker():
            success = 0
            errors = []
            for f in files:
                try:
                    doc = fitz.open(f['path'])
                    if scope == 'all':
                        for page in doc:
                            page.set_rotation((page.rotation + angle) % 360)
                    else:
                        ranges = self._parse_page_ranges(pages_str, len(doc))
                        for s, e in ranges:
                            for pi in range(s - 1, e):
                                if 0 <= pi < len(doc):
                                    doc[pi].set_rotation((doc[pi].rotation + angle) % 360)

                    base = os.path.splitext(f['name'])[0]
                    os.makedirs(out_dir, exist_ok=True)
                    doc.save(os.path.join(out_dir, f"{base}_旋转.pdf"))
                    doc.close()
                    success += 1
                except Exception as e:
                    errors.append(f"{f['name']}: {e}")

            msg = f"旋转完成！\n\n成功：{success} 个"
            if errors:
                msg += f"\n失败：{len(errors)} 个\n" + "\n".join(errors[:5])
            self.root.after(0, lambda: _showinfo("完成", msg))
            self.root.after(0, lambda: self.status_var.set(f"旋转完成：{success} 成功"))
            self.processing = False

        threading.Thread(target=worker, daemon=True).start()

    # ==================== 删除页面 ====================

    def delete_pages_wizard(self):
        files = self._get_checked_files()
        if not files:
            files = self._get_all_files()
        if not files:
            _showinfo("提示", "请先打开PDF文件")
            return

        win = tk.Toplevel(self.root)
        win.title("删除页面")
        _center_window(win, self.root, 500, 340)
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text="输入要删除的页码（如 1,3,5-8）：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        pages_var = tk.StringVar()
        ttk.Entry(win, textvariable=pages_var, width=30).pack(anchor=tk.W, padx=20, pady=5)

        ttk.Label(win, text="注意：删除操作不可逆，请确认页码", foreground='red').pack(anchor=tk.W, padx=20, pady=5)

        out_dir_del = tk.StringVar(value=self.output_dir.get())
        dir_frame = ttk.Frame(win)
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(dir_frame, text="保存到：").pack(side=tk.LEFT)
        ttk.Entry(dir_frame, textvariable=out_dir_del, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=lambda: out_dir_del.set(
            filedialog.askdirectory(title="选择输出目录", initialdir=out_dir_del.get()) or out_dir_del.get()
        )).pack(side=tk.LEFT)

        def do_delete():
            if not _askyesno("确认", "确定要删除指定页面吗？此操作不可撤销。"):
                return
            win.destroy()
            self._do_delete_pages(files, pages_var.get(), out_dir_del.get())

        btn_frame = ttk.Frame(win, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="开始删除", command=do_delete).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _do_delete_pages(self, files, pages_str, out_dir):
        if self.processing:
            return
        self.processing = True

        def worker():
            success = 0
            errors = []
            for f in files:
                try:
                    doc = fitz.open(f['path'])
                    ranges = self._parse_page_ranges(pages_str, len(doc))
                    pages_to_delete = set()
                    for s, e in ranges:
                        for pi in range(s - 1, e):
                            pages_to_delete.add(pi)

                    new_doc = fitz.open()
                    for pi in range(len(doc)):
                        if pi not in pages_to_delete:
                            new_doc.insert_pdf(doc, from_page=pi, to_page=pi)

                    base = os.path.splitext(f['name'])[0]
                    os.makedirs(out_dir, exist_ok=True)
                    new_doc.save(os.path.join(out_dir, f"{base}_删页.pdf"))
                    new_doc.close()
                    doc.close()
                    success += 1
                except Exception as e:
                    errors.append(f"{f['name']}: {e}")

            msg = f"删除页面完成！\n\n成功：{success} 个"
            if errors:
                msg += f"\n失败：{len(errors)} 个\n" + "\n".join(errors[:5])
            self.root.after(0, lambda: _showinfo("完成", msg))
            self.root.after(0, lambda: self.status_var.set(f"删页完成：{success} 成功"))
            self.processing = False

        threading.Thread(target=worker, daemon=True).start()

    # ==================== PDF转图片 ====================

    def pdf_to_images_wizard(self):
        files = self._get_checked_files()
        if not files:
            files = self._get_all_files()
        if not files:
            _showinfo("提示", "请先打开PDF文件")
            return

        win = tk.Toplevel(self.root)
        win.title("PDF转图片")
        _center_window(win, self.root, 500, 400)
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text="图片格式：", font=('', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        img_fmt = tk.StringVar(value='png')
        fmt_frame = ttk.Frame(win)
        fmt_frame.pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(fmt_frame, text="PNG（无损）", variable=img_fmt, value='png').pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(fmt_frame, text="JPG（较小）", variable=img_fmt, value='jpg').pack(side=tk.LEFT, padx=5)

        ttk.Label(win, text="分辨率（DPI）：").pack(anchor=tk.W, padx=20, pady=(10, 0))
        dpi_var = tk.IntVar(value=150)
        dpi_frame = ttk.Frame(win)
        dpi_frame.pack(fill=tk.X, padx=20)
        ttk.Scale(dpi_frame, from_=72, to=300, variable=dpi_var, orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(dpi_frame, textvariable=dpi_var, width=4).pack(side=tk.RIGHT)

        out_dir_img = tk.StringVar(value=self.output_dir.get())
        dir_frame = ttk.Frame(win)
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(dir_frame, text="保存到：").pack(side=tk.LEFT)
        ttk.Entry(dir_frame, textvariable=out_dir_img, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=lambda: out_dir_img.set(
            filedialog.askdirectory(title="选择输出目录", initialdir=out_dir_img.get()) or out_dir_img.get()
        )).pack(side=tk.LEFT)

        def do_convert():
            win.destroy()
            self._do_pdf_to_images(files, img_fmt.get(), dpi_var.get(), out_dir_img.get())

        btn_frame = ttk.Frame(win, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="开始转换", command=do_convert).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _do_pdf_to_images(self, files, fmt, dpi, out_dir):
        if self.processing:
            return
        self.processing = True

        def worker():
            total = len(files)
            success = 0
            errors = []
            for idx, f in enumerate(files):
                try:
                    self.root.after(0, lambda i=idx, n=f['name']: self.status_var.set(f"转换 ({i+1}/{total}): {n}"))
                    doc = fitz.open(f['path'])
                    base = os.path.splitext(f['name'])[0]
                    sub_dir = os.path.join(out_dir, base)
                    os.makedirs(sub_dir, exist_ok=True)

                    zoom = dpi / 72.0
                    mat = fitz.Matrix(zoom, zoom)

                    for pi in range(len(doc)):
                        page = doc[pi]
                        pix = page.get_pixmap(matrix=mat)
                        ext = fmt if fmt != 'jpg' else 'jpeg'
                        out_file = os.path.join(sub_dir, f"{base}_第{pi+1}页.{fmt}")
                        pix.save(out_file)

                    doc.close()
                    success += 1
                except Exception as e:
                    errors.append(f"{f['name']}: {e}")

            msg = f"转换完成！\n\n成功：{success} 个"
            if errors:
                msg += f"\n失败：{len(errors)} 个\n" + "\n".join(errors[:5])
            self.root.after(0, lambda: _showinfo("完成", msg))
            self.root.after(0, lambda: self.status_var.set(f"转换完成：{success} 成功"))
            self.processing = False

        threading.Thread(target=worker, daemon=True).start()

    # ==================== 关于 ====================

    def show_about(self):
        _showinfo(
            "关于 PDF 批处理工具",
            "PDF 批处理工具 v1.0\n\n"
            "功能列表：\n"
            "  💧 批量水印（9种样式）\n"
            "  📎 合并PDF（可加水印）\n"
            "  ✂ 拆分PDF\n"
            "  📄 提取页面\n"
            "  🔒 加密/解密\n"
            "  🔄 旋转页面\n"
            "  🗑 删除页面\n"
            "  🖼 PDF转图片\n\n"
            "基于 PyMuPDF + ReportLab + pypdf"
        )


if __name__ == '__main__':
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        root = tk.Tk()
    app = PDFToolApp(root)
    root.mainloop()
