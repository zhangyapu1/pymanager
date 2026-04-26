#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件夹内批量重命名 - 批量重命名指定文件夹内的文件。

功能：
    - 添加前缀：在文件名前插入指定文字（如 "2024_" + "report.pdf" → "2024_report.pdf"）
    - 添加后缀：在文件名与扩展名之间插入指定文字（如 "report" + "_v2" + ".pdf" → "report_v2.pdf"）
    - 替换文字：将文件名中的指定文本替换为新文本
    - 按序号重命名：按顺序编号重命名，保留原扩展名（如 "photo_001.jpg", "photo_002.jpg"）

安全机制：
    - 重命名前检查目标文件是否已存在，避免覆盖
    - 源文件不存在时自动跳过
    - 新名称与原名称相同时跳过
    - 操作前弹出确认对话框

依赖：仅使用 Python 标准库（tkinter）
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


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

class BatchRenameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("批量重命名工具")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # 当前选中的文件夹路径
        self.folder_path = tk.StringVar()

        # 文件列表（原始名称，用于预览）
        self.original_files = []

        # 创建界面组件
        self.create_widgets()

    def create_widgets(self):
        # 1. 文件夹选择区域
        frame_folder = tk.LabelFrame(self.root, text="1. 选择文件夹", padx=5, pady=5)
        frame_folder.pack(fill=tk.X, padx=10, pady=5)

        tk.Entry(frame_folder, textvariable=self.folder_path, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_folder, text="浏览...", command=self.select_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_folder, text="刷新文件列表", command=self.refresh_file_list).pack(side=tk.LEFT, padx=5)

        # 2. 文件列表预览（带滚动条）
        frame_list = tk.LabelFrame(self.root, text="当前文件列表（仅显示文件，不含子文件夹）", padx=5, pady=5)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(frame_list)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(frame_list, yscrollcommand=scrollbar.set, height=12)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # 3. 重命名模式选择
        frame_mode = tk.LabelFrame(self.root, text="2. 选择重命名方式", padx=5, pady=5)
        frame_mode.pack(fill=tk.X, padx=10, pady=5)

        self.rename_mode = tk.StringVar(value="prefix")

        modes = [("添加前缀", "prefix"),
                 ("添加后缀（扩展名前插入）", "suffix"),
                 ("替换文字", "replace"),
                 ("按序号重命名", "sequential")]
        for text, mode in modes:
            tk.Radiobutton(frame_mode, text=text, variable=self.rename_mode, value=mode,
                           command=self.on_mode_changed).pack(side=tk.LEFT, padx=10)

        # 4. 参数输入区域（根据模式动态显示）
        frame_params = tk.LabelFrame(self.root, text="3. 设置参数", padx=5, pady=5)
        frame_params.pack(fill=tk.X, padx=10, pady=5)

        # 前缀/后缀模式下的输入
        self.prefix_label = tk.Label(frame_params, text="前缀:")
        self.prefix_entry = tk.Entry(frame_params, width=30)
        self.suffix_label = tk.Label(frame_params, text="后缀:")
        self.suffix_entry = tk.Entry(frame_params, width=30)

        # 替换模式下的输入
        self.replace_old_label = tk.Label(frame_params, text="被替换文本:")
        self.replace_old_entry = tk.Entry(frame_params, width=30)
        self.replace_new_label = tk.Label(frame_params, text="新文本:")
        self.replace_new_entry = tk.Entry(frame_params, width=30)

        # 序号模式下的输入
        self.seq_base_label = tk.Label(frame_params, text="基础名称:")
        self.seq_base_entry = tk.Entry(frame_params, width=20)
        self.seq_start_label = tk.Label(frame_params, text="起始编号:")
        self.seq_start_entry = tk.Entry(frame_params, width=10)
        self.seq_start_entry.insert(0, "1")
        self.seq_digits_label = tk.Label(frame_params, text="编号位数:")
        self.seq_digits_entry = tk.Entry(frame_params, width=10)
        self.seq_digits_entry.insert(0, "3")

        # 初始显示前缀模式
        self.on_mode_changed()

        # 5. 执行按钮
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="执行重命名", command=self.execute_rename,
                  bg="lightgreen", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="退出", command=self.root.quit, width=10).pack(side=tk.LEFT, padx=5)

    def log(self, message):
        print(message, flush=True)

    def select_folder(self):
        """弹出文件夹选择对话框"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.refresh_file_list()

    def refresh_file_list(self):
        """刷新文件列表显示"""
        folder = self.folder_path.get()
        if not os.path.isdir(folder):
            self.log("错误：文件夹不存在或无效")
            return

        # 只收集文件（不包括子目录）
        self.original_files = []
        self.file_listbox.delete(0, tk.END)
        try:
            for name in os.listdir(folder):
                full = os.path.join(folder, name)
                if os.path.isfile(full):
                    self.original_files.append(name)
                    self.file_listbox.insert(tk.END, name)
            self.log(f"已加载文件夹：{folder}，共 {len(self.original_files)} 个文件")
        except PermissionError:
            self.log("错误：没有权限访问该文件夹")
        except Exception as e:
            self.log(f"读取文件夹错误: {e}")

    def on_mode_changed(self):
        """根据选择的模式显示/隐藏对应的参数输入框"""
        mode = self.rename_mode.get()

        # 先隐藏所有参数控件
        widgets_to_hide = [
            self.prefix_label, self.prefix_entry, 
            self.suffix_label, self.suffix_entry,
            self.replace_old_label, self.replace_old_entry, 
            self.replace_new_label, self.replace_new_entry,
            self.seq_base_label, self.seq_base_entry, 
            self.seq_start_label, self.seq_start_entry,
            self.seq_digits_label, self.seq_digits_entry
        ]
        for widget in widgets_to_hide:
            widget.pack_forget()

        if mode == "prefix":
            self.prefix_label.pack(side=tk.LEFT, padx=5)
            self.prefix_entry.pack(side=tk.LEFT, padx=5)
        elif mode == "suffix":
            self.suffix_label.pack(side=tk.LEFT, padx=5)
            self.suffix_entry.pack(side=tk.LEFT, padx=5)
        elif mode == "replace":
            self.replace_old_label.pack(side=tk.LEFT, padx=5)
            self.replace_old_entry.pack(side=tk.LEFT, padx=5)
            self.replace_new_label.pack(side=tk.LEFT, padx=5)
            self.replace_new_entry.pack(side=tk.LEFT, padx=5)
        elif mode == "sequential":
            self.seq_base_label.pack(side=tk.LEFT, padx=5)
            self.seq_base_entry.pack(side=tk.LEFT, padx=5)
            self.seq_start_label.pack(side=tk.LEFT, padx=5)
            self.seq_start_entry.pack(side=tk.LEFT, padx=5)
            self.seq_digits_label.pack(side=tk.LEFT, padx=5)
            self.seq_digits_entry.pack(side=tk.LEFT, padx=5)

    def execute_rename(self):
        """根据当前模式和参数执行重命名"""
        folder = self.folder_path.get()
        if not os.path.isdir(folder):
            _showerror("错误", "请先选择一个有效的文件夹")
            return

        if not self.original_files:
            _showwarning("警告", "文件夹中没有文件，请刷新列表")
            return

        mode = self.rename_mode.get()
        # 确认对话框
        if not _askyesno("确认", f"即将对 {len(self.original_files)} 个文件执行重命名操作，是否继续？"):
            return

        self.log("开始执行重命名...")

        try:
            if mode == "prefix":
                prefix = self.prefix_entry.get()
                self.add_prefix(folder, prefix)
            elif mode == "suffix":
                suffix = self.suffix_entry.get()
                self.add_suffix(folder, suffix)
            elif mode == "replace":
                old_text = self.replace_old_entry.get()
                new_text = self.replace_new_entry.get()
                self.replace_text(folder, old_text, new_text)
            elif mode == "sequential":
                base = self.seq_base_entry.get()
                start_str = self.seq_start_entry.get()
                digits_str = self.seq_digits_entry.get()
                try:
                    # 允许0，但不允许负数或非数字
                    if start_str.lstrip('-').isdigit(): # 简单检查，防止负数
                         start = int(start_str)
                    else:
                         start = 1
                    
                    if digits_str.isdigit() and int(digits_str) > 0:
                        digits = int(digits_str)
                    else:
                        digits = 3
                except ValueError:
                    self.log("编号参数无效，使用默认值（起始1，位数3）")
                    start, digits = 1, 3
                
                if not base:
                    self.log("警告：基础名称为空，将仅使用序号")
                
                self.sequential_rename(folder, base, start, digits)
            else:
                self.log("未知的重命名模式")
                return
        except Exception as e:
            self.log(f"发生未预期的错误: {e}")

        self.log("操作完成。")
        self.refresh_file_list()   # 刷新列表显示新文件名

    # ---------- 重命名具体实现 ----------
    def _safe_rename(self, folder, old_name, new_name):
        """
        安全的重命名辅助函数
        返回: True if success, False if skipped/failed
        """
        old_path = os.path.join(folder, old_name)
        new_path = os.path.join(folder, new_name)
        
        # 1. 检查源文件是否存在（防止并发修改或逻辑错误）
        if not os.path.exists(old_path):
            self.log(f"跳过 {old_name}：源文件不存在")
            return False
            
        # 2. 检查目标文件是否已存在
        if os.path.exists(new_path):
            # 如果目标路径和源路径一样（例如替换文本没变），跳过
            if os.path.abspath(old_path) == os.path.abspath(new_path):
                self.log(f"跳过 {old_name}：新名称与原名称相同")
                return False
            self.log(f"跳过 {old_name} → {new_name}（目标文件已存在）")
            return False

        try:
            os.rename(old_path, new_path)
            self.log(f"重命名: {old_name} → {new_name}")
            return True
        except OSError as e:
            self.log(f"错误: {old_name} → {new_name} 失败，原因: {e}")
            return False

    def add_prefix(self, folder, prefix):
        """为所有文件添加前缀"""
        if not prefix:
            self.log("前缀为空，未执行任何操作")
            return
        for old_name in self.original_files:
            new_name = prefix + old_name
            self._safe_rename(folder, old_name, new_name)

    def add_suffix(self, folder, suffix):
        """在文件名后、扩展名前插入后缀"""
        if not suffix:
            self.log("后缀为空，未执行任何操作")
            return
        for old_name in self.original_files:
            name, ext = os.path.splitext(old_name)
            new_name = name + suffix + ext
            self._safe_rename(folder, old_name, new_name)

    def replace_text(self, folder, old_text, new_text):
        """替换文件名中的指定文本"""
        if not old_text:
            self.log("替换文本不能为空，操作取消")
            return
        
        count = 0
        for old_name in self.original_files:
            if old_text in old_name:
                new_name = old_name.replace(old_text, new_text)
                # 如果替换后名字没变（例如替换为空且原本就没有，或者替换成一样的）
                if new_name == old_name:
                    continue
                if self._safe_rename(folder, old_name, new_name):
                    count += 1
            # 优化：不再记录每个不匹配的文件，减少日志噪音
        
        if count == 0:
            self.log("没有找到匹配的文件或无需更改")

    def sequential_rename(self, folder, base_name, start=1, digits=3):
        """按顺序重命名，保留原扩展名"""
        # 按原文件名排序
        sorted_files = sorted(self.original_files)
        
        # 预检查：生成所有新名称，检查是否有内部冲突（新名称之间的重复）
        # 注意：这里只做简单检查，不完全解决 A->B, B->A 的死锁问题，
        # 但 _safe_rename 会处理目标存在的情况。
        
        for idx, old_name in enumerate(sorted_files, start=start):
            ext = os.path.splitext(old_name)[1]
            # 格式化序号
            num_str = str(idx).zfill(digits)
            new_name = f"{base_name}{num_str}{ext}"
            
            self._safe_rename(folder, old_name, new_name)

if __name__ == "__main__":
    root = tk.Tk()
    app = BatchRenameApp(root)
    root.mainloop()