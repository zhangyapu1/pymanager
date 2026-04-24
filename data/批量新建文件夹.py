#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
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

        # 定义非法文件名字符 (Windows 主要限制，Linux/macOS 较宽松，但为了跨平台兼容性，去除常见非法字符)
        # \ / : * ? " < > |
        self.invalid_chars_pattern = re.compile(r'[<>:"/\\|?*]')

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
        self.frame_params = tk.LabelFrame(self.root, text="3. 设置参数", padx=5, pady=5)
        self.frame_params.pack(fill=tk.X, padx=10, pady=5)

        # --- 序号模式参数 ---
        self.seq_frame = tk.Frame(self.frame_params)
        self.seq_base_label = tk.Label(self.seq_frame, text="基础名称:")
        self.seq_base_entry = tk.Entry(self.seq_frame, width=20)
        self.seq_base_entry.insert(0, "folder")
        self.seq_start_label = tk.Label(self.seq_frame, text="起始编号:")
        self.seq_start_entry = tk.Entry(self.seq_frame, width=10)
        self.seq_start_entry.insert(0, "1")
        self.seq_digits_label = tk.Label(self.seq_frame, text="编号位数:")
        self.seq_digits_entry = tk.Entry(self.seq_frame, width=10)
        self.seq_digits_entry.insert(0, "3")
        self.seq_count_label = tk.Label(self.seq_frame, text="创建数量:")
        self.seq_count_entry = tk.Entry(self.seq_frame, width=10)
        self.seq_count_entry.insert(0, "5")

        # 布局序号控件
        self.seq_base_label.pack(side=tk.LEFT, padx=5)
        self.seq_base_entry.pack(side=tk.LEFT, padx=5)
        self.seq_start_label.pack(side=tk.LEFT, padx=5)
        self.seq_start_entry.pack(side=tk.LEFT, padx=5)
        self.seq_digits_label.pack(side=tk.LEFT, padx=5)
        self.seq_digits_entry.pack(side=tk.LEFT, padx=5)
        self.seq_count_label.pack(side=tk.LEFT, padx=5)
        self.seq_count_entry.pack(side=tk.LEFT, padx=5)

        # --- 前缀/后缀模式参数 ---
        self.prefix_suffix_frame = tk.Frame(self.frame_params)
        self.prefix_suffix_label = tk.Label(self.prefix_suffix_frame, text="基础名称（每行一个）:")
        self.prefix_suffix_text = tk.Text(self.prefix_suffix_frame, height=6, width=40)
        self.prefix_suffix_scroll = tk.Scrollbar(self.prefix_suffix_frame, command=self.prefix_suffix_text.yview)
        self.prefix_suffix_text.configure(yscrollcommand=self.prefix_suffix_scroll.set)
        self.affix_label = tk.Label(self.prefix_suffix_frame, text="要添加的前缀/后缀:")
        self.affix_entry = tk.Entry(self.prefix_suffix_frame, width=30)

        # 布局前缀/后缀控件
        self.prefix_suffix_label.pack(anchor=tk.W, pady=2)
        self.prefix_suffix_text.pack(fill=tk.BOTH, expand=True, pady=2)
        self.prefix_suffix_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.affix_label.pack(anchor=tk.W, pady=2)
        self.affix_entry.pack(fill=tk.X, pady=2)

        # --- 自定义模式参数 ---
        self.custom_frame = tk.Frame(self.frame_params)
        self.custom_label = tk.Label(self.custom_frame, text="文件夹名称列表（每行一个）:")
        self.custom_text = tk.Text(self.custom_frame, height=10, width=50)
        self.custom_scroll = tk.Scrollbar(self.custom_frame, command=self.custom_text.yview)
        self.custom_text.configure(yscrollcommand=self.custom_scroll.set)

        # 布局自定义控件
        self.custom_label.pack(anchor=tk.W, pady=2)
        self.custom_text.pack(fill=tk.BOTH, expand=True, pady=2)
        self.custom_scroll.pack(side=tk.RIGHT, fill=tk.Y)

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

    def sanitize_filename(self, name):
        """
        清理文件名中的非法字符，防止创建失败。
        将非法字符替换为下划线 '_'。
        """
        if not name:
            return ""
        # 替换非法字符
        clean_name = self.invalid_chars_pattern.sub('_', name)
        # 去除首尾空格和点（Windows 不允许以空格或点结尾）
        clean_name = clean_name.strip().rstrip('.')
        # 如果处理后为空，返回默认名
        if not clean_name:
            clean_name = "unnamed_folder"
        return clean_name

    def log(self, message):
        """在日志区域追加消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        # 强制刷新UI，让用户看到实时日志
        self.root.update_idletasks()

    def select_parent_dir(self):
        """选择父目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.parent_path.set(directory)
            self.update_preview()

    def on_mode_changed(self):
        """根据选择的模式显示/隐藏对应的参数输入框"""
        mode = self.create_mode.get()

        # 隐藏所有参数框架
        self.seq_frame.pack_forget()
        self.prefix_suffix_frame.pack_forget()
        self.custom_frame.pack_forget()

        if mode == "sequential":
            self.seq_frame.pack(fill=tk.X, padx=5, pady=5)
        elif mode in ("prefix", "suffix"):
            self.prefix_suffix_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        elif mode == "custom":
            self.custom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.update_preview()

    def generate_folder_names(self):
        """根据当前模式和参数生成文件夹名称列表"""
        mode = self.create_mode.get()
        names = []

        if mode == "sequential":
            try:
                base_raw = self.seq_base_entry.get().strip()
                base = self.sanitize_filename(base_raw)
                
                start_str = self.seq_start_entry.get().strip()
                digits_str = self.seq_digits_entry.get().strip()
                count_str = self.seq_count_entry.get().strip()

                if not start_str or not digits_str or not count_str:
                    raise ValueError("参数不能为空")

                start = int(start_str)
                digits = int(digits_str)
                count = int(count_str)

                if count <= 0:
                    raise ValueError("创建数量必须大于0")
                if digits <= 0:
                    raise ValueError("编号位数必须大于0")
                
                # 限制最大数量以防内存溢出或UI卡死
                if count > 10000:
                    if not messagebox.askyesno("警告", f"您打算创建 {count} 个文件夹，这可能需要较长时间。是否继续？"):
                        return []

                for i in range(start, start + count):
                    # 确保基础名称不为空，如果为空则只用数字
                    prefix_part = base if base else "folder"
                    names.append(f"{prefix_part}{str(i).zfill(digits)}")
            except ValueError as e:
                self.log(f"序号参数无效: {e}")
                return []
        
        elif mode == "prefix":
            base_text = self.prefix_suffix_text.get("1.0", tk.END).strip()
            if not base_text:
                # 不直接log，因为可能是用户还没输入，仅在生成时为空才提示
                pass 
            else:
                raw_lines = [line.strip() for line in base_text.splitlines() if line.strip()]
                prefix_raw = self.affix_entry.get()
                prefix = self.sanitize_filename(prefix_raw)
                
                for name in raw_lines:
                    clean_name = self.sanitize_filename(name)
                    if clean_name:
                        names.append(f"{prefix}{clean_name}")

        elif mode == "suffix":
            base_text = self.prefix_suffix_text.get("1.0", tk.END).strip()
            if not base_text:
                pass
            else:
                raw_lines = [line.strip() for line in base_text.splitlines() if line.strip()]
                suffix_raw = self.affix_entry.get()
                suffix = self.sanitize_filename(suffix_raw)
                
                for name in raw_lines:
                    clean_name = self.sanitize_filename(name)
                    if clean_name:
                        names.append(f"{clean_name}{suffix}")

        elif mode == "custom":
            text = self.custom_text.get("1.0", tk.END).strip()
            if not text:
                pass
            else:
                raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
                for name in raw_lines:
                    clean_name = self.sanitize_filename(name)
                    if clean_name:
                        names.append(clean_name)
        
        else:
            self.log("未知模式")
            return []

        # 再次过滤空字符串（虽然 sanitize 应该处理了，但双重保险）
        names = [n for n in names if n]
        return names

    def update_preview(self):
        """刷新预览列表"""
        # 安全检查：确保预览控件已创建
        if not hasattr(self, 'preview_listbox'):
            return

        self.preview_listbox.delete(0, tk.END)
        self.folder_names = self.generate_folder_names()
        
        if not self.folder_names:
            self.preview_listbox.insert(tk.END, "(无有效名称，请检查参数)")
            # 如果是因为输入为空导致的，不记录错误日志，以免打扰用户
            return

        parent = self.parent_path.get()
        # 为了防止UI卡顿，如果数量过多，只检查前100个是否存在，或者不做存在性检查（可选优化）
        # 这里保持原有逻辑，但注意性能
        check_limit = 500 
        items_to_check = self.folder_names[:check_limit]
        
        for name in items_to_check:
            full_path = os.path.join(parent, name) if parent else name
            exists = False
            if parent and os.path.isdir(parent):
                exists = os.path.exists(full_path)
            display = f"{name}  {'(已存在！)' if exists else ''}"
            self.preview_listbox.insert(tk.END, display)
            
        if len(self.folder_names) > check_limit:
            self.preview_listbox.insert(tk.END, f"... 还有 {len(self.folder_names) - check_limit} 个文件未显示")

        self.log(f"预览已更新，共 {len(self.folder_names)} 个文件夹待创建")

    def execute_create(self):
        """执行创建文件夹操作"""
        parent = self.parent_path.get()
        if not parent or not os.path.isdir(parent):
            messagebox.showerror("错误", "请先选择一个有效的父目录")
            return

        # 重新生成一次名称，确保数据最新
        current_names = self.generate_folder_names()
        if not current_names:
            messagebox.showwarning("警告", "没有可创建的文件夹名称，请检查参数并刷新预览")
            return

        # 二次确认
        confirm_msg = f"将在以下目录中创建 {len(current_names)} 个文件夹：\n{parent}\n\n是否继续？"
        if not messagebox.askyesno("确认创建", confirm_msg):
            return

        # 清空日志，开始创建
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log("开始创建文件夹...")

        created = 0
        skipped = 0
        failed = 0
        
        # 禁用按钮防止重复点击
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        for name in current_names:
            full_path = os.path.join(parent, name)
            try:
                # 检查是否已存在，避免异常开销（可选，os.mkdir 本身也会检查）
                if os.path.exists(full_path):
                    self.log(f"跳过（已存在）: {name}")
                    skipped += 1
                else:
                    os.mkdir(full_path)
                    self.log(f"创建成功: {name}")
                    created += 1
            except FileExistsError:
                self.log(f"跳过（已存在）: {name}")
                skipped += 1
            except OSError as e:
                self.log(f"创建失败: {name}，错误: {e}")
                failed += 1
            except Exception as e:
                self.log(f"未知错误: {name}，错误: {e}")
                failed += 1
            
            # 每创建10个刷新一次UI，避免假死
            if (created + skipped + failed) % 10 == 0:
                self.root.update_idletasks()

        self.root.config(cursor="")
        self.log(f"\n操作完成：成功 {created} 个，跳过 {skipped} 个，失败 {failed} 个。")
        
        # 刷新预览以更新已存在标记
        self.update_preview()

if __name__ == "__main__":
    root = tk.Tk()
    # 尝试设置高DPI支持 (Windows)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    app = BatchCreateFoldersApp(root)
    root.mainloop()