#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class BatchCreateFoldersApp:
    def __init__(self, root):
        self.root = root
        self.root.title("批量新建文件夹工具")
        self.root.geometry("800x650")
        self.root.resizable(True, True)

        # 当前选中的父目录路径
        self.parent_path = tk.StringVar()

        # 存储将要创建的文件夹名称列表（预览用）
        self.folder_names = []

        self.create_widgets()

    def create_widgets(self):
        # 1. 父目录选择区域
        frame_parent = tk.LabelFrame(self.root, text="1. 选择父目录（在此目录下新建文件夹）", padx=5, pady=5)
        frame_parent.pack(fill=tk.X, padx=10, pady=5)

        tk.Entry(frame_parent, textvariable=self.parent_path, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_parent, text="浏览...", command=self.select_parent_dir).pack(side=tk.LEFT, padx=5)

        # 2. 创建模式选择
        frame_mode = tk.LabelFrame(self.root, text="2. 选择创建方式", padx=5, pady=5)
        frame_mode.pack(fill=tk.X, padx=10, pady=5)

        self.create_mode = tk.StringVar(value="sequential")

        modes = [("按序号创建（如 folder001, folder002...）", "sequential"),
                 ("添加前缀", "prefix"),
                 ("添加后缀", "suffix"),
                 ("自定义名称列表（每行一个）", "custom")]
        for text, mode in modes:
            tk.Radiobutton(frame_mode, text=text, variable=self.create_mode, value=mode,
                           command=self.on_mode_changed).pack(anchor=tk.W, padx=10, pady=2)

        # 3. 参数输入区域（根据模式动态显示）
        frame_params = tk.LabelFrame(self.root, text="3. 设置参数", padx=5, pady=5)
        frame_params.pack(fill=tk.X, padx=10, pady=5)

        # 序号模式参数
        self.seq_base_label = tk.Label(frame_params, text="基础名称:")
        self.seq_base_entry = tk.Entry(frame_params, width=20)
        self.seq_base_entry.insert(0, "folder")
        self.seq_start_label = tk.Label(frame_params, text="起始编号:")
        self.seq_start_entry = tk.Entry(frame_params, width=10)
        self.seq_start_entry.insert(0, "1")
        self.seq_digits_label = tk.Label(frame_params, text="编号位数:")
        self.seq_digits_entry = tk.Entry(frame_params, width=10)
        self.seq_digits_entry.insert(0, "3")
        self.seq_count_label = tk.Label(frame_params, text="创建数量:")
        self.seq_count_entry = tk.Entry(frame_params, width=10)
        self.seq_count_entry.insert(0, "5")

        # 前缀/后缀模式参数（共享基础名称列表或单独输入？为简单起见，让用户输入基础名称（每行一个）和前缀/后缀）
        self.prefix_suffix_label = tk.Label(frame_params, text="基础名称（每行一个）:")
        self.prefix_suffix_text = tk.Text(frame_params, height=6, width=40)
        self.prefix_suffix_scroll = tk.Scrollbar(frame_params, command=self.prefix_suffix_text.yview)
        self.prefix_suffix_text.configure(yscrollcommand=self.prefix_suffix_scroll.set)
        self.affix_label = tk.Label(frame_params, text="要添加的前缀/后缀:")
        self.affix_entry = tk.Entry(frame_params, width=30)

        # 自定义模式参数：文本框输入名称列表
        self.custom_label = tk.Label(frame_params, text="文件夹名称列表（每行一个）:")
        self.custom_text = tk.Text(frame_params, height=10, width=50)
        self.custom_scroll = tk.Scrollbar(frame_params, command=self.custom_text.yview)
        self.custom_text.configure(yscrollcommand=self.custom_scroll.set)

        # 4. 预览区域
        frame_preview = tk.LabelFrame(self.root, text="4. 预览即将创建的文件夹", padx=5, pady=5)
        frame_preview.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.preview_listbox = tk.Listbox(frame_preview, height=8)
        self.preview_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        preview_scroll = tk.Scrollbar(frame_preview, command=self.preview_listbox.yview)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_listbox.configure(yscrollcommand=preview_scroll.set)

        # 5. 按钮区域
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="刷新预览", command=self.update_preview, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="执行创建", command=self.execute_create, bg="lightgreen", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="退出", command=self.root.quit, width=8).pack(side=tk.LEFT, padx=5)

        # 6. 日志区域
        frame_log = tk.LabelFrame(self.root, text="操作日志", padx=5, pady=5)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = tk.Text(frame_log, height=8, state=tk.DISABLED, wrap=tk.WORD)
        log_scroll = tk.Scrollbar(frame_log, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 所有组件创建完成后，再初始化界面状态（显示默认模式对应的参数并刷新预览）
        self.on_mode_changed()

    def log(self, message):
        """在日志区域追加消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def select_parent_dir(self):
        """选择父目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.parent_path.set(directory)
            self.update_preview()

    def on_mode_changed(self):
        """根据选择的模式显示/隐藏对应的参数输入框"""
        mode = self.create_mode.get()

        # 隐藏所有参数控件
        for widget in [self.seq_base_label, self.seq_base_entry,
                       self.seq_start_label, self.seq_start_entry,
                       self.seq_digits_label, self.seq_digits_entry,
                       self.seq_count_label, self.seq_count_entry,
                       self.prefix_suffix_label, self.prefix_suffix_text, self.prefix_suffix_scroll,
                       self.affix_label, self.affix_entry,
                       self.custom_label, self.custom_text, self.custom_scroll]:
            widget.pack_forget()

        if mode == "sequential":
            # 序号模式：一行显示多个控件
            self.seq_base_label.pack(side=tk.LEFT, padx=5)
            self.seq_base_entry.pack(side=tk.LEFT, padx=5)
            self.seq_start_label.pack(side=tk.LEFT, padx=5)
            self.seq_start_entry.pack(side=tk.LEFT, padx=5)
            self.seq_digits_label.pack(side=tk.LEFT, padx=5)
            self.seq_digits_entry.pack(side=tk.LEFT, padx=5)
            self.seq_count_label.pack(side=tk.LEFT, padx=5)
            self.seq_count_entry.pack(side=tk.LEFT, padx=5)
        elif mode in ("prefix", "suffix"):
            # 前缀/后缀模式：显示基础名称列表（文本框）和添加的文本
            self.prefix_suffix_label.pack(anchor=tk.W, pady=2)
            self.prefix_suffix_text.pack(fill=tk.BOTH, expand=True, pady=2)
            self.prefix_suffix_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.affix_label.pack(anchor=tk.W, pady=2)
            self.affix_entry.pack(fill=tk.X, pady=2)
        elif mode == "custom":
            self.custom_label.pack(anchor=tk.W, pady=2)
            self.custom_text.pack(fill=tk.BOTH, expand=True, pady=2)
            self.custom_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.update_preview()

    def generate_folder_names(self):
        """根据当前模式和参数生成文件夹名称列表"""
        mode = self.create_mode.get()
        names = []

        if mode == "sequential":
            try:
                base = self.seq_base_entry.get().strip()
                start = int(self.seq_start_entry.get())
                digits = int(self.seq_digits_entry.get())
                count = int(self.seq_count_entry.get())
                if count <= 0:
                    raise ValueError
                for i in range(start, start + count):
                    names.append(f"{base}{str(i).zfill(digits)}")
            except ValueError:
                self.log("序号参数无效，请检查（起始编号、位数、数量必须为正整数）")
                return []
        elif mode == "prefix":
            base_text = self.prefix_suffix_text.get("1.0", tk.END).strip()
            if not base_text:
                self.log("请在基础名称列表中输入至少一个名称")
                return []
            base_names = [line.strip() for line in base_text.splitlines() if line.strip()]
            prefix = self.affix_entry.get().strip()
            names = [prefix + name for name in base_names]
        elif mode == "suffix":
            base_text = self.prefix_suffix_text.get("1.0", tk.END).strip()
            if not base_text:
                self.log("请在基础名称列表中输入至少一个名称")
                return []
            base_names = [line.strip() for line in base_text.splitlines() if line.strip()]
            suffix = self.affix_entry.get().strip()
            names = [name + suffix for name in base_names]
        elif mode == "custom":
            text = self.custom_text.get("1.0", tk.END).strip()
            if not text:
                self.log("请在自定义列表中输入至少一个文件夹名称")
                return []
            names = [line.strip() for line in text.splitlines() if line.strip()]
        else:
            self.log("未知模式")
            return []

        # 去除空字符串
        names = [n for n in names if n]
        return names

    def update_preview(self):
        """刷新预览列表"""
        # 安全检查：确保预览控件已创建（防止初始化顺序错误）
        if not hasattr(self, 'preview_listbox'):
            return

        self.preview_listbox.delete(0, tk.END)
        self.folder_names = self.generate_folder_names()
        if not self.folder_names:
            self.preview_listbox.insert(tk.END, "(无有效名称，请检查参数)")
            return

        parent = self.parent_path.get()
        for name in self.folder_names:
            full_path = os.path.join(parent, name) if parent else name
            exists = os.path.exists(full_path) if parent else False
            display = f"{name}  {'(已存在！)' if exists else ''}"
            self.preview_listbox.insert(tk.END, display)

        self.log(f"预览已更新，共 {len(self.folder_names)} 个文件夹待创建")

    def execute_create(self):
        """执行创建文件夹操作"""
        parent = self.parent_path.get()
        if not parent or not os.path.isdir(parent):
            messagebox.showerror("错误", "请先选择一个有效的父目录")
            return

        if not self.folder_names:
            messagebox.showwarning("警告", "没有可创建的文件夹名称，请检查参数并刷新预览")
            return

        # 二次确认
        if not messagebox.askyesno("确认创建",
                                   f"将在以下目录中创建 {len(self.folder_names)} 个文件夹：\n{parent}\n\n是否继续？"):
            return

        # 清空日志，开始创建
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        created = 0
        skipped = 0
        for name in self.folder_names:
            full_path = os.path.join(parent, name)
            try:
                os.mkdir(full_path)
                self.log(f"创建成功: {name}")
                created += 1
            except FileExistsError:
                self.log(f"跳过（已存在）: {name}")
                skipped += 1
            except Exception as e:
                self.log(f"创建失败: {name}，错误: {e}")

        self.log(f"\n操作完成：成功创建 {created} 个，跳过 {skipped} 个。")
        # 刷新预览以更新已存在标记
        self.update_preview()

if __name__ == "__main__":
    root = tk.Tk()
    app = BatchCreateFoldersApp(root)
    root.mainloop()