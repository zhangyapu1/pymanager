"""
脚本市场 - 浏览和下载 GitHub 上的 Python 脚本资源。

UI 组件：
    - 三栏可调布局：仓库列表、文件列表、README 预览（PanedWindow）
    - 下载进度条：显示文件下载进度
    - AI 分析面板：包含 AI 选择、Key 管理和分析按钮
    - 翻译服务选择：可切换不同翻译服务

类 ScriptMarketWindow：
    主窗口类，管理所有 UI 组件和交互逻辑

    核心方法：
        _search_repos()          - 搜索 GitHub 仓库
        _load_repo_contents()    - 加载仓库文件列表
        _load_readme()           - 加载并渲染 README
        _translate_readme()      - 分段翻译 README
        _analyze_project()       - AI 分析项目
        _download_selected()     - 下载选中项目/文件
        _save_api_key()          - 保存加密的 API Key
        _delete_api_key()        - 删除指定 AI 的 Key

依赖：modules.translate_service, modules.ai_analyzer, modules.github_repo, modules.markdown_renderer
"""
import json
import os
import re
import threading
import tkinter as tk
from tkinter import ttk
from urllib.error import URLError, HTTPError

try:
    import ttkbootstrap as ttkb
    HAS_TTKBOOTSTRAP = True
except ImportError:
    HAS_TTKBOOTSTRAP = False

from modules.logger import log_info, log_error
from modules.config import DATA_DIR
from modules.encrypt_utils import get_default_key
from modules.translate_service import (
    TRANSLATE_PROVIDERS,
    load_translate_config,
    save_translate_config,
    translate_chunk,
)
from modules.ai_analyzer import (
    AI_PROVIDERS,
    load_ai_config,
    save_ai_config,
    ai_query,
)
from modules.github_repo import (
    search_repos,
    get_repo_contents,
    get_raw_file,
    get_repo_readme,
    is_english,
)
from modules.markdown_renderer import render_markdown


def create_button(parent, text, command, bootstyle="primary", **kwargs):
    if HAS_TTKBOOTSTRAP:
        return ttkb.Button(parent, text=text, command=command, bootstyle=bootstyle, **kwargs)
    return ttk.Button(parent, text=text, command=command, **kwargs)


class ScriptMarketWindow:
    def __init__(self, ctx):
        self.ctx = ctx
        self.root = ctx.get_root_window()
        self.window = None
        self.search_entry = None
        self.results_listbox = None
        self.files_listbox = None
        self.preview_text = None
        self.repos = []
        self.files = []
        self.current_repo = None
        self.current_path = []
        self.status_var = None
        self.original_readme = ""
        self.translated_readme = ""
        self.showing_translated = False
        self.translate_btn = None
        self.ai_config = load_ai_config()
        self.ai_text = None
        self.ai_provider_var = None
        self.ai_key_entry = None
        self._skip_file_select = False
        self._translating = False
        self._translate_buffer = []
        self._translate_progress = (0, 0)
        self._translate_flush_id = None

    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.root)
        self.window.title("脚本市场 - 从 GitHub 搜索脚本")
        self.window.geometry("950x750")
        self.window.minsize(800, 600)
        self.window.configure(bg="#f0f0f0")

        self._build_ui()
        self._load_featured()

    def _alive(self):
        return self.window is not None and self.window.winfo_exists()

    def _safe_after(self, ms, callback):
        if self._alive():
            self.window.after(ms, callback)

    def _build_ui(self):
        w = self.window

        search_frame = ttk.Frame(w)
        search_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(search_frame, text="搜索：").pack(side=tk.LEFT)

        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        create_button(search_frame, text="搜索", command=self._do_search).pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="输入关键词搜索 GitHub 上的 Python 脚本仓库")
        ttk.Label(search_frame, textvariable=self.status_var).pack(side=tk.RIGHT, padx=5)

        content_frame = ttk.Frame(w)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        paned = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(paned, text="仓库列表")
        paned.add(left_frame, weight=1)

        left_toolbar = ttk.Frame(left_frame)
        left_toolbar.pack(fill=tk.X, padx=5, pady=(3, 0))
        create_button(left_toolbar, text="⬇ 下载项目", command=self._download_repo).pack(side=tk.LEFT)

        self.results_listbox = tk.Listbox(
            left_frame, font=('Consolas', 10),
            bg='#ffffff', fg='#1a1a1a',
            selectbackground='#e0e0e0', selectforeground='#1a1a1a',
            borderwidth=1, relief='solid', activestyle='none'
        )
        self.results_listbox.bind("<<ListboxSelect>>", self._on_repo_selected)

        left_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        self.results_listbox.config(yscrollcommand=left_scroll.set)

        mid_frame = ttk.LabelFrame(paned, text="文件列表")
        paned.add(mid_frame, weight=1)

        mid_toolbar = ttk.Frame(mid_frame)
        mid_toolbar.pack(fill=tk.X, padx=5, pady=(3, 0))
        create_button(mid_toolbar, text="⬇ 下载选中", command=self._download_selected).pack(side=tk.LEFT, padx=(0, 3))
        create_button(mid_toolbar, text="⬆ 返回上级", command=self._go_up).pack(side=tk.LEFT)

        self.files_listbox = tk.Listbox(
            mid_frame, font=('Consolas', 10),
            bg='#ffffff', fg='#1a1a1a',
            selectbackground='#e0e0e0', selectforeground='#1a1a1a',
            borderwidth=1, relief='solid', activestyle='none'
        )
        self.files_listbox.bind("<<ListboxSelect>>", self._on_file_selected)
        self.files_listbox.bind("<Double-Button-1>", self._on_file_double_click)

        mid_scroll = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        mid_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        self.files_listbox.config(yscrollcommand=mid_scroll.set)

        right_frame = ttk.LabelFrame(paned, text="README 预览")
        paned.add(right_frame, weight=2)

        readme_toolbar = ttk.Frame(right_frame)
        readme_toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))

        self.readme_lang_var = tk.StringVar(value="")
        ttk.Label(readme_toolbar, textvariable=self.readme_lang_var, foreground="gray").pack(side=tk.LEFT)

        self.translate_config = load_translate_config()
        translate_names = list(TRANSLATE_PROVIDERS.keys())
        self.translate_provider_var = tk.StringVar(value=self.translate_config.get("provider", translate_names[0]))
        translate_combo = ttk.Combobox(readme_toolbar, textvariable=self.translate_provider_var, values=translate_names, state="readonly", width=10)
        translate_combo.pack(side=tk.RIGHT, padx=(3, 0))
        translate_combo.bind("<<ComboboxSelected>>", self._on_translate_provider_changed)
        ttk.Label(readme_toolbar, text="翻译：").pack(side=tk.RIGHT)

        self.translate_btn = create_button(readme_toolbar, text="查看原文", command=self._toggle_translation)
        self.translate_btn.pack(side=tk.RIGHT, padx=2)
        self.translate_btn.config(state=tk.DISABLED)

        self.translate_status_var = tk.StringVar(value="")

        self.preview_text = tk.Text(
            right_frame, font=('Consolas', 9),
            bg='#ffffff', fg='#1a1a1a',
            borderwidth=1, relief='solid',
            wrap=tk.WORD, state=tk.DISABLED
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        right_scroll_y = ttk.Scrollbar(self.preview_text, orient=tk.VERTICAL, command=self.preview_text.yview)
        right_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.config(yscrollcommand=right_scroll_y.set)

        self._build_ai_panel(w)

        progress_frame = ttk.Frame(w)
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 2))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="", foreground="gray", width=20)
        self.progress_label.pack(side=tk.RIGHT)

        bottom_frame = ttk.Frame(w)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.info_var = tk.StringVar(value="")
        ttk.Label(bottom_frame, textvariable=self.info_var, foreground="gray").pack(side=tk.RIGHT, padx=5)

    def _build_ai_panel(self, parent):
        ai_frame = ttk.LabelFrame(parent, text="AI 项目分析")
        ai_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        ai_content = ttk.Frame(ai_frame)
        ai_content.pack(fill=tk.X, padx=5, pady=5)
        ai_content.columnconfigure(0, weight=1)
        ai_content.columnconfigure(1, weight=0)

        ai_left = ttk.Frame(ai_content)
        ai_left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.ai_text = tk.Text(
            ai_left, font=('Microsoft YaHei UI', 9),
            bg='#ffffff', fg='#1a1a1a',
            borderwidth=1, relief='solid',
            wrap=tk.WORD, state=tk.DISABLED,
            height=6
        )
        self.ai_text.pack(fill=tk.BOTH, expand=True)

        ai_scroll = ttk.Scrollbar(self.ai_text, orient=tk.VERTICAL, command=self.ai_text.yview)
        ai_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.ai_text.config(yscrollcommand=ai_scroll.set)

        ai_right = ttk.Frame(ai_content)
        ai_right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        provider_names = list(AI_PROVIDERS.keys())
        self.ai_provider_var = tk.StringVar(value=self.ai_config.get("provider", provider_names[0]))

        row0 = ttk.Frame(ai_right)
        row0.pack(fill=tk.X, pady=(0, 3))
        ttk.Label(row0, text="AI：").pack(side=tk.LEFT)
        provider_combo = ttk.Combobox(row0, textvariable=self.ai_provider_var, values=provider_names, state="readonly", width=18)
        provider_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)

        key_row = ttk.Frame(ai_right)
        key_row.pack(fill=tk.X, pady=(0, 3))
        ttk.Label(key_row, text="Key：").pack(side=tk.LEFT)
        current_key = self._get_display_key(self.ai_provider_var.get())
        self.ai_key_entry = ttk.Entry(key_row, width=16, show="*")
        self.ai_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ai_key_entry.insert(0, current_key)

        key_btn_frame = ttk.Frame(ai_right)
        key_btn_frame.pack(fill=tk.X, pady=(0, 3))
        create_button(key_btn_frame, text="保存Key", command=self._save_ai_key, width=9).pack(side=tk.LEFT, padx=(0, 2))
        create_button(key_btn_frame, text="删除Key", command=self._delete_ai_key, width=9).pack(side=tk.LEFT, padx=(2, 0))
        create_button(ai_right, text="🔄 重新分析", command=self._re_analyze).pack(fill=tk.X, pady=(0, 3))

        self.ai_status_var = tk.StringVar(value="选择仓库后自动分析")
        ttk.Label(ai_right, textvariable=self.ai_status_var, foreground="gray", wraplength=200).pack(anchor=tk.W)

    def _on_translate_provider_changed(self, event=None):
        self.translate_config["provider"] = self.translate_provider_var.get()
        provider = self.translate_provider_var.get()
        cfg = TRANSLATE_PROVIDERS.get(provider, {})
        if cfg.get("needs_key", False):
            saved_keys = self.translate_config.get("keys", {})
            has_all = all(saved_keys.get(f"{provider}_{f}", "") for f in cfg.get("fields", []))
            if not has_all:
                self._prompt_translate_key(provider)
        save_translate_config(self.translate_config)
        self.translate_status_var.set(f"已切换到{provider}")

    def _prompt_translate_key(self, provider):
        cfg = TRANSLATE_PROVIDERS.get(provider, {})
        fields = cfg.get("fields", [])
        if not fields:
            return
        dialog = tk.Toplevel(self.window)
        dialog.title(f"配置 {provider} API Key")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        content = ttk.Frame(dialog)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        ttk.Label(content, text=f"配置 {provider} 的 API 凭证（留空使用默认Key）", foreground="gray").pack(anchor=tk.W, pady=(0, 8))

        entries = {}
        for field in fields:
            key_name = f"{provider}_{field}"
            frame = ttk.Frame(content)
            frame.pack(fill=tk.X, pady=3)
            ttk.Label(frame, text=f"{field}：", width=8).pack(side=tk.LEFT)
            entry = ttk.Entry(frame, width=28, show="*")
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            saved_val = self.translate_config.get("keys", {}).get(key_name, "")
            if saved_val:
                entry.insert(0, saved_val)
            entries[key_name] = entry

        def _save():
            if "keys" not in self.translate_config:
                self.translate_config["keys"] = {}
            has_value = False
            for key_name, entry in entries.items():
                val = entry.get().strip()
                if val:
                    self.translate_config["keys"][key_name] = val
                    has_value = True
                else:
                    self.translate_config["keys"].pop(key_name, None)
            save_translate_config(self.translate_config)
            if has_value:
                self.translate_status_var.set(f"✅ {provider} Key 已保存")
                self.ctx.append_output(f"[脚本市场] 翻译 Key 已保存：{provider}")
            else:
                self.translate_status_var.set(f"⚠ {provider} 未输入 Key")
            dialog.destroy()

        def _delete():
            if "keys" not in self.translate_config:
                self.translate_config["keys"] = {}
            for field in fields:
                key_name = f"{provider}_{field}"
                self.translate_config["keys"].pop(key_name, None)
            save_translate_config(self.translate_config)
            self.translate_status_var.set(f"✅ {provider} Key 已删除")
            self.ctx.append_output(f"[脚本市场] 翻译 Key 已删除：{provider}")
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=15, pady=10)
        create_button(btn_frame, text="保存", command=_save).pack(side=tk.LEFT, padx=(0, 5))
        create_button(btn_frame, text="删除Key", command=_delete).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT)

    def _on_provider_changed(self, event=None):
        provider = self.ai_provider_var.get()
        display_key = self._get_display_key(provider)
        self.ai_key_entry.delete(0, tk.END)
        self.ai_key_entry.insert(0, display_key)
        self.ai_config["provider"] = provider
        save_ai_config(self.ai_config)

    def _get_display_key(self, provider):
        custom = self.ai_config.get("custom_keys", {}).get(provider, "")
        if custom:
            return custom
        return ""

    def _get_effective_key(self, provider):
        custom = self.ai_config.get("custom_keys", {}).get(provider, "")
        if custom:
            return custom
        return get_default_key(provider)

    def _save_ai_key(self):
        provider = self.ai_provider_var.get()
        key = self.ai_key_entry.get().strip()
        if not key:
            self.ai_status_var.set("请输入 API Key")
            return
        if "custom_keys" not in self.ai_config:
            self.ai_config["custom_keys"] = {}
        self.ai_config["custom_keys"][provider] = key
        self.ai_config["provider"] = provider
        save_ai_config(self.ai_config)
        self.ai_status_var.set("✅ 自定义 Key 已保存（加密存储）")
        self.ctx.append_output(f"[脚本市场] API Key 已保存：{provider}")

    def _delete_ai_key(self):
        provider = self.ai_provider_var.get()
        if "custom_keys" not in self.ai_config:
            self.ai_config["custom_keys"] = {}
        if provider in self.ai_config["custom_keys"]:
            del self.ai_config["custom_keys"][provider]
        save_ai_config(self.ai_config)
        self.ai_key_entry.delete(0, tk.END)
        self.ai_status_var.set("✅ 自定义 Key 已删除，将使用默认 Key")
        self.ctx.append_output(f"[脚本市场] API Key 已删除：{provider}")

    def _re_analyze(self):
        if self.current_repo:
            self._ai_analyze(self.current_repo)

    def _ai_analyze(self, repo_info):
        provider = self.ai_provider_var.get()
        api_key = self._get_effective_key(provider)

        if not api_key:
            self._show_ai_result("⚠️ 无可用 API Key\n\n"
                                 "请在右侧输入自定义 API Key 并保存，或切换到智谱AI/通义千问（内置默认Key）\n\n"
                                 "获取免费 API Key：\n"
                                 "• DeepSeek: https://platform.deepseek.com\n"
                                 "• 智谱AI: https://open.bigmodel.cn\n"
                                 "• 通义千问: https://dashscope.console.aliyun.com")
            return

        self._show_ai_result("正在分析中...")
        self.ai_status_var.set("AI 分析中...")

        def _query():
            try:
                result = ai_query(provider, api_key, repo_info)
                self._safe_after(0, lambda: self._show_ai_result(result))
                self._safe_after(0, lambda: self.ai_status_var.set("分析完成"))
                self.ctx.append_output(f"[脚本市场] AI 分析完成：{repo_info.get('full_name', '')}")
            except HTTPError as e:
                err_msg = f"HTTP {e.code}"
                try:
                    err_body = e.read().decode("utf-8")
                    err_data = json.loads(err_body)
                    err_msg = err_data.get("error", {}).get("message", err_msg)
                except Exception:
                    pass
                self._safe_after(0, lambda: self._on_ai_key_failed(provider, err_msg, repo_info))
            except URLError as e:
                reason = str(e.reason)
                self._safe_after(0, lambda: self._show_ai_result(f"❌ 网络错误：{reason}\n\n请检查网络连接"))
                self._safe_after(0, lambda: self.ai_status_var.set("网络错误"))
                self.ctx.append_output(f"[脚本市场] AI 网络错误：{reason}")
            except Exception as e:
                msg = str(e)
                self._safe_after(0, lambda: self._show_ai_result(f"❌ 分析失败：{msg}"))
                self._safe_after(0, lambda: self.ai_status_var.set("分析失败"))
                self.ctx.append_output(f"[脚本市场] AI 分析异常：{msg}")

        threading.Thread(target=_query, daemon=True).start()

    def _on_ai_key_failed(self, provider, err_msg, repo_info):
        is_default = not self.ai_config.get("custom_keys", {}).get(provider, "")
        if is_default:
            self._show_ai_result(f"❌ 默认 Key 请求失败：{err_msg}\n\n请输入您自己的 API Key")
            self.ai_status_var.set("默认 Key 失败，请输入自定义 Key")
            self.ctx.append_output(f"[脚本市场] AI 默认 Key 失败：{err_msg}")
            self._prompt_custom_key(provider, repo_info)
        else:
            self._show_ai_result(f"❌ 请求失败：{err_msg}\n\n请检查 API Key 是否正确")
            self.ai_status_var.set("分析失败")
            self.ctx.append_output(f"[脚本市场] AI 分析失败：{err_msg}")

    def _prompt_custom_key(self, provider, repo_info):
        from tkinter import simpledialog
        key = simpledialog.askstring(
            "API Key 无效",
            f"「{provider}」默认 Key 已失效。\n\n请输入您自己的 API Key：\n"
            f"（可在 {provider} 官网免费获取）",
            parent=self.window,
            show="*"
        )
        if key and key.strip():
            key = key.strip()
            if "custom_keys" not in self.ai_config:
                self.ai_config["custom_keys"] = {}
            self.ai_config["custom_keys"][provider] = key
            self.ai_config["provider"] = provider
            save_ai_config(self.ai_config)
            self.ai_key_entry.delete(0, tk.END)
            self.ai_key_entry.insert(0, key)
            self.ai_status_var.set("自定义 Key 已保存，重新分析中...")
            self.ctx.append_output(f"[脚本市场] 用户输入了自定义 Key：{provider}")
            self._ai_analyze(repo_info)

    def _show_ai_result(self, text):
        self.ai_text.config(state=tk.NORMAL)
        self.ai_text.delete("1.0", tk.END)
        self.ai_text.insert("1.0", text)
        self.ai_text.config(state=tk.DISABLED)

    def _load_featured(self):
        self._search_thread("python script tool", featured=True)

    def _do_search(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            return
        self._search_thread(keyword)

    def _search_thread(self, keyword, featured=False):
        self.status_var.set("搜索中...")
        self.repos = []
        self.ctx.append_output(f"[脚本市场] 搜索：{keyword}")

        def _search():
            try:
                data = search_repos(keyword)
                items = data.get("items", [])
                self.repos = items
                total = data.get("total_count", 0)
                self._safe_after(0, lambda: self._display_repos(total, featured))
                self.ctx.append_output(f"[脚本市场] 找到 {total} 个仓库")
            except (URLError, HTTPError) as e:
                msg = str(e)
                self._safe_after(0, lambda: self.status_var.set(f"搜索失败：{msg}"))
                self.ctx.append_output(f"[脚本市场] 搜索失败：{msg}")
            except Exception as e:
                msg = str(e)
                self._safe_after(0, lambda: self.status_var.set(f"网络错误：{msg}"))
                self.ctx.append_output(f"[脚本市场] 网络错误：{msg}")

        threading.Thread(target=_search, daemon=True).start()

    def _display_repos(self, total, featured=False):
        self.results_listbox.delete(0, tk.END)
        if featured:
            self.status_var.set("推荐仓库（按 Star 排序）")
        else:
            self.status_var.set(f"找到 {total} 个仓库")

        for repo in self.repos:
            name = repo.get("full_name", "")
            stars = repo.get("stargazers_count", 0)
            display = f"{'★' * min(stars // 100 + 1, 5)} {name}"
            self.results_listbox.insert(tk.END, display)

    def _on_repo_selected(self, event):
        sel = self.results_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self.repos):
            return
        repo = self.repos[idx]
        self.current_repo = repo
        self.current_path = []
        repo_name = repo.get("full_name", "")
        repo_desc = repo.get("description", "") or "无描述"
        self.ctx.append_output(f"[脚本市场] 选中仓库：{repo_name} - {repo_desc}")
        self._load_repo_contents(repo_name, "")
        self._load_readme(repo_name)
        self._ai_analyze(repo)

    def _load_readme(self, repo_full_name):
        self.status_var.set(f"加载 README...")
        self.original_readme = ""
        self.translated_readme = ""
        self.showing_translated = False
        self.readme_lang_var.set("")
        self.translate_btn.config(state=tk.DISABLED, text="查看原文")
        self._show_preview("加载中...", is_markdown=False)

        def _load():
            try:
                owner, repo = repo_full_name.split("/", 1)
                content = get_repo_readme(owner, repo)
                self.original_readme = content
                is_en = is_english(content)
                if is_en:
                    self._safe_after(0, lambda: self._show_preview(content))
                    self._safe_after(0, lambda: self.readme_lang_var.set("英文 | 自动翻译中..."))
                    self._safe_after(0, lambda: self.status_var.set("检测到英文 README，正在翻译..."))
                    self.ctx.append_output(f"[脚本市场] README 为英文，自动翻译中...")
                    self._auto_translate(content)
                else:
                    self._safe_after(0, lambda: self._show_preview(content))
                    self._safe_after(0, lambda: self.readme_lang_var.set("中文"))
                    self._safe_after(0, lambda: self.status_var.set("README 已加载"))
                    self.ctx.append_output(f"[脚本市场] README 已加载（中文）")
            except HTTPError as e:
                ecode = e.code
                if ecode == 404:
                    self._safe_after(0, lambda: self._show_preview("（该仓库没有 README 文件）", is_markdown=False))
                    self._safe_after(0, lambda: self.readme_lang_var.set("无 README"))
                    self._safe_after(0, lambda: self.status_var.set("该仓库没有 README"))
                    self.ctx.append_output(f"[脚本市场] 该仓库没有 README 文件")
                else:
                    self._safe_after(0, lambda: self._show_preview(f"加载失败：HTTP {ecode}", is_markdown=False))
                    self._safe_after(0, lambda: self.status_var.set(f"加载失败：{ecode}"))
                    self.ctx.append_output(f"[脚本市场] README 加载失败：HTTP {ecode}")
            except Exception as e:
                msg = str(e)
                self._safe_after(0, lambda: self._show_preview(f"加载失败：{msg}", is_markdown=False))
                self._safe_after(0, lambda: self.status_var.set(f"加载失败：{msg}"))
                self.ctx.append_output(f"[脚本市场] README 加载失败：{msg}")

        threading.Thread(target=_load, daemon=True).start()

    def _auto_translate(self, content):
        self._translating = True
        self._translate_buffer = []
        self._translate_progress = (0, 0)
        self._translate_flush_id = None
        self._safe_after(0, self._begin_translate_preview)
        self._schedule_translate_flush()

        def _translate():
            try:
                cfg = load_translate_config()
                provider = cfg.get("provider", "Google翻译")
                providers_order = [provider]
                for p in TRANSLATE_PROVIDERS:
                    if p not in providers_order:
                        providers_order.append(p)

                segments = re.split(r'(\n{2,})', content)
                translated_parts = []
                total = len(segments)
                any_translated = False

                for i, seg in enumerate(segments):
                    if not self._alive() or not self._translating:
                        break

                    if re.match(r'^\s*$', seg):
                        translated_parts.append(seg)
                        self._translate_progress = (i + 1, total)
                        continue

                    if len(seg) > 480:
                        lines = seg.split('\n')
                        chunk = []
                        for line in lines:
                            chunk.append(line)
                            chunk_text = '\n'.join(chunk)
                            if len(chunk_text) > 450:
                                result = translate_chunk(chunk_text, "en", "zh", providers_order)
                                translated_parts.append(result)
                                if result != chunk_text:
                                    any_translated = True
                                self._translate_buffer.append(result)
                                self._translate_progress = (i + 1, total)
                                chunk = []
                        if chunk:
                            result = translate_chunk('\n'.join(chunk), "en", "zh", providers_order)
                            translated_parts.append(result)
                            if result != '\n'.join(chunk):
                                any_translated = True
                            self._translate_buffer.append(result)
                            self._translate_progress = (i + 1, total)
                    else:
                        result = translate_chunk(seg, "en", "zh", providers_order)
                        translated_parts.append(result)
                        if result != seg:
                            any_translated = True
                        self._translate_buffer.append(result)
                        self._translate_progress = (i + 1, total)

                if not self._alive():
                    return

                translated = ''.join(translated_parts)

                if not any_translated or translated == content:
                    self._safe_after(0, lambda: self.readme_lang_var.set("英文（翻译未生效）"))
                    self._safe_after(0, lambda: self.translate_btn.config(state=tk.NORMAL, text="查看翻译"))
                    self._safe_after(0, lambda: self.status_var.set("翻译服务未返回有效结果，可切换翻译服务重试"))
                    self.ctx.append_output(f"[脚本市场] README 翻译未生效，所有翻译服务均失败")
                    return

                self.translated_readme = translated
                self._safe_after(0, lambda: self.readme_lang_var.set("中文（自动翻译）"))
                self._safe_after(0, lambda: self.translate_btn.config(state=tk.NORMAL, text="查看原文"))
                self._safe_after(0, lambda: self.status_var.set("README 已翻译"))
                self.ctx.append_output(f"[脚本市场] README 翻译完成")
                self.showing_translated = True
            except Exception as e:
                msg = str(e) if str(e) else "未知错误"
                self._safe_after(0, lambda: self.readme_lang_var.set("英文（翻译失败）"))
                self._safe_after(0, lambda: self.translate_btn.config(state=tk.NORMAL, text="查看翻译"))
                self._safe_after(0, lambda: self.status_var.set(f"翻译失败：{msg}"))
                self.ctx.append_output(f"[脚本市场] README 翻译失败：{msg}")
                log_error(f"README 翻译异常：{msg}")
            finally:
                self._translating = False

        threading.Thread(target=_translate, daemon=True).start()

    def _schedule_translate_flush(self):
        if not self._alive() or not self._translating:
            self._flush_translate_buffer()
            return
        self._flush_translate_buffer()
        self._translate_flush_id = self.window.after(500, self._schedule_translate_flush)

    def _flush_translate_buffer(self):
        if not self._alive():
            return
        buf = self._translate_buffer
        self._translate_buffer = []
        if not buf:
            cur, tot = self._translate_progress
            if cur < tot:
                self.readme_lang_var.set(f"翻译中... ({cur}/{tot})")
            return
        combined = ''.join(buf)
        rendered = render_markdown(combined)
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.insert(tk.END, rendered)
        self.preview_text.config(state=tk.DISABLED)
        cur, tot = self._translate_progress
        if cur < tot:
            self.readme_lang_var.set(f"翻译中... ({cur}/{tot})")
            self.translate_btn.config(state=tk.NORMAL, text="查看原文")

    def _begin_translate_preview(self):
        if self._alive():
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.config(state=tk.DISABLED)

    def _toggle_translation(self):
        if self.showing_translated:
            self._show_preview(self.original_readme)
            self.translate_btn.config(text="查看翻译")
            self.readme_lang_var.set("英文原文")
            self.showing_translated = False
        else:
            if self.translated_readme:
                self._show_preview(self.translated_readme)
                self.translate_btn.config(text="查看原文")
                self.readme_lang_var.set("中文（自动翻译）")
                self.showing_translated = True

    def _load_repo_contents(self, repo_full_name, path):
        self.status_var.set(f"加载 {repo_full_name}/{path}...")
        self.files = []

        def _load():
            try:
                owner, repo = repo_full_name.split("/", 1)
                contents = get_repo_contents(owner, repo, path)
                if isinstance(contents, dict):
                    contents = [contents]
                self.files = contents
                self._safe_after(0, self._display_files)
            except HTTPError as e:
                ecode = e.code
                self._safe_after(0, lambda: self.status_var.set(f"访问失败：{ecode}"))
            except Exception as e:
                msg = str(e)
                self._safe_after(0, lambda: self.status_var.set(f"加载失败：{msg}"))

        threading.Thread(target=_load, daemon=True).start()

    def _display_files(self):
        self._skip_file_select = True
        self.files_listbox.delete(0, tk.END)
        for item in self.files:
            name = item.get("name", "")
            ftype = item.get("type", "")
            if ftype == "dir":
                self.files_listbox.insert(tk.END, f"📁 {name}/")
            elif name.endswith(".py"):
                self.files_listbox.insert(tk.END, f"🐍 {name}")
            else:
                self.files_listbox.insert(tk.END, f"   {name}")
        self.files_listbox.selection_clear(0, tk.END)
        self._skip_file_select = False
        self.status_var.set(f"已加载 {len(self.files)} 个项目")

    def _on_file_selected(self, event):
        if self._skip_file_select:
            return
        sel = self.files_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self.files):
            return
        item = self.files[idx]
        if item.get("type") != "file":
            return
        filename = item.get("name", "")
        download_url = item.get("download_url")
        if not download_url:
            return
        if filename.endswith(".md"):
            self._preview_markdown(download_url, filename)
        elif filename.endswith(".py"):
            self._preview_python(download_url)
        else:
            self._show_preview("（不支持预览此类型文件）", is_markdown=False)
            self.readme_lang_var.set("")
            self.translate_btn.config(state=tk.DISABLED)

    def _preview_markdown(self, download_url, filename):
        self.status_var.set(f"加载 {filename}...")
        self.original_readme = ""
        self.translated_readme = ""
        self.showing_translated = False
        self.translate_btn.config(state=tk.DISABLED, text="查看原文")
        self._show_preview("加载中...", is_markdown=False)

        def _load():
            try:
                content = get_raw_file(download_url)
                self.original_readme = content
                is_en = is_english(content)
                if is_en:
                    self._safe_after(0, lambda: self._show_preview(content))
                    self._safe_after(0, lambda: self.readme_lang_var.set("英文 | 自动翻译中..."))
                    self._safe_after(0, lambda: self.status_var.set("检测到英文，正在翻译..."))
                    self._auto_translate(content)
                else:
                    self._safe_after(0, lambda: self._show_preview(content))
                    self._safe_after(0, lambda: self.readme_lang_var.set("中文"))
                    self._safe_after(0, lambda: self.status_var.set("已加载"))
            except Exception as e:
                msg = str(e)
                self._safe_after(0, lambda: self._show_preview(f"加载失败：{msg}", is_markdown=False))
                self._safe_after(0, lambda: self.status_var.set(f"加载失败：{msg}"))

        threading.Thread(target=_load, daemon=True).start()

    def _preview_python(self, download_url):
        self.status_var.set("加载源码...")

        def _load():
            try:
                content = get_raw_file(download_url)
                self._safe_after(0, lambda: self._show_preview(content, is_markdown=False))
                self._safe_after(0, lambda: self.readme_lang_var.set("Python 源码"))
                self._safe_after(0, lambda: self.translate_btn.config(state=tk.DISABLED))
                self.status_var.set("源码已加载")
            except Exception as e:
                msg = str(e)
                self._safe_after(0, lambda: self._show_preview(f"加载失败：{msg}", is_markdown=False))
                self.status_var.set(f"加载失败：{msg}")

        threading.Thread(target=_load, daemon=True).start()

    def _on_file_double_click(self, event):
        sel = self.files_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self.files):
            return
        item = self.files[idx]
        if item.get("type") == "dir":
            name = item.get("name", "")
            self.current_path.append(name)
            self._load_repo_contents(self.current_repo["full_name"], "/".join(self.current_path))

    def _show_preview(self, content, is_markdown=True):
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        if is_markdown:
            display = render_markdown(content)
        else:
            display = content
        self.preview_text.insert("1.0", display)
        self.preview_text.config(state=tk.DISABLED)

    def _go_up(self):
        if self.current_path:
            self.current_path.pop()
            self._load_repo_contents(self.current_repo["full_name"], "/".join(self.current_path))

    def _download_repo(self):
        sel = self.results_listbox.curselection()
        if not sel:
            self.ctx.ui.show_warning("提示", "请先在仓库列表中选择一个项目")
            return
        idx = sel[0]
        if idx >= len(self.repos):
            return
        repo = self.repos[idx]
        full_name = repo.get("full_name", "")
        if not full_name:
            return
        repo_name = full_name.split("/")[-1]
        dest_dir = os.path.join(DATA_DIR, "测试项目", repo_name)

        if os.path.exists(dest_dir):
            if not self.ctx.ui.ask_yes_no("项目已存在", f"项目 {repo_name} 已存在于测试项目目录，是否覆盖？"):
                return
            import shutil
            shutil.rmtree(dest_dir, ignore_errors=True)

        self.status_var.set(f"下载项目：{full_name}...")
        self._safe_after(0, lambda: self._update_progress(0, f"扫描 {repo_name}..."))

        def _download():
            try:
                os.makedirs(dest_dir, exist_ok=True)
                file_list = []
                self._collect_repo_files(full_name, "", file_list)
                total = len(file_list)
                if total == 0:
                    self._safe_after(0, lambda: self._on_repo_download_done(repo_name))
                    return
                for i, (fpath, furl, fdest_dir) in enumerate(file_list):
                    if furl:
                        try:
                            content = get_raw_file(furl)
                            fname = fpath.split("/")[-1]
                            file_path = os.path.join(fdest_dir, fname)
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(content)
                        except Exception as e:
                            log_error(f"下载文件 {fpath} 失败：{e}")
                    pct = int((i + 1) / total * 100)
                    self._safe_after(0, lambda p=pct, n=i+1, t=total: self._update_progress(p, f"{n}/{t} 文件"))
                self._safe_after(0, lambda: self._on_repo_download_done(repo_name))
            except Exception as e:
                msg = str(e)
                self._safe_after(0, lambda: self.status_var.set(f"下载失败：{msg}"))
                self._safe_after(0, lambda: self.ctx.ui.show_error("下载失败", msg))
                self._safe_after(0, lambda: self._update_progress(0, "下载失败"))

        threading.Thread(target=_download, daemon=True).start()

    def _collect_repo_files(self, repo_full_name, path, file_list):
        owner, repo = repo_full_name.split("/", 1)
        items = get_repo_contents(owner, repo, path)
        if not isinstance(items, list):
            return
        for item in items:
            name = item.get("name", "")
            ftype = item.get("type", "")
            if ftype == "dir":
                sub_path = f"{path}/{name}" if path else name
                repo_name = repo_full_name.split("/")[-1]
                sub_dir = os.path.join(DATA_DIR, "测试项目", repo_name, sub_path.replace("/", os.sep))
                os.makedirs(sub_dir, exist_ok=True)
                self._collect_repo_files(repo_full_name, sub_path, file_list)
            elif ftype == "file":
                download_url = item.get("download_url", "")
                repo_name = repo_full_name.split("/")[-1]
                fpath = f"{path}/{name}" if path else name
                fdest_dir = os.path.join(DATA_DIR, "测试项目", repo_name, path.replace("/", os.sep)) if path else os.path.join(DATA_DIR, "测试项目", repo_name)
                file_list.append((fpath, download_url, fdest_dir))

    def _on_repo_download_done(self, repo_name):
        self.status_var.set(f"已下载项目：{repo_name}")
        self.info_var.set(f"✅ {repo_name} → 测试项目")
        self.ctx.append_output(f"[脚本市场] 已下载项目 {repo_name} 到「测试项目」目录")
        self._update_progress(100, f"✅ {repo_name} 完成")

        from modules.script_manager import scan_data_directory
        from modules.settings_manager import save_settings
        scan_data_directory(self.ctx)
        self.ctx.update_listbox()
        save_settings(self.ctx.settings)

    def _download_selected(self):
        sel = self.files_listbox.curselection()
        if not sel:
            self.ctx.ui.show_warning("提示", "请先在文件列表中选择要下载的文件或文件夹")
            return
        idx = sel[0]
        if idx >= len(self.files):
            return
        item = self.files[idx]
        ftype = item.get("type", "")
        name = item.get("name", "")

        if ftype == "dir":
            self._download_folder(item)
        else:
            self._download_file(item)

    def _download_file(self, item):
        filename = item.get("name", "script.py")
        download_url = item.get("download_url")
        if not download_url:
            self.ctx.ui.show_error("错误", "无法获取下载链接")
            return

        group = self.ctx.group_manager.current_group
        group_dir = os.path.join(DATA_DIR, group)
        os.makedirs(group_dir, exist_ok=True)
        dest_path = os.path.join(group_dir, filename)

        if os.path.exists(dest_path):
            if not self.ctx.ui.ask_yes_no("文件已存在", f"{filename} 已存在，是否覆盖？"):
                return

        self.status_var.set(f"下载中：{filename}...")
        self._update_progress(50, f"下载 {filename}")

        def _download():
            try:
                content = get_raw_file(download_url)
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self._safe_after(0, lambda: self._on_download_done(filename, group))
            except Exception as e:
                msg = str(e)
                self._safe_after(0, lambda: self.status_var.set(f"下载失败：{msg}"))
                self._safe_after(0, lambda: self.ctx.ui.show_error("下载失败", msg))
                self._safe_after(0, lambda: self._update_progress(0, "下载失败"))

        threading.Thread(target=_download, daemon=True).start()

    def _download_folder(self, item):
        folder_name = item.get("name", "")
        if not self.current_repo:
            self.ctx.ui.show_error("错误", "未选择仓库")
            return

        full_name = self.current_repo.get("full_name", "")
        folder_path = "/".join(self.current_path + [folder_name])
        dest_dir = os.path.join(DATA_DIR, self.ctx.group_manager.current_group, folder_name)

        if os.path.exists(dest_dir):
            if not self.ctx.ui.ask_yes_no("文件夹已存在", f"{folder_name} 已存在，是否覆盖？"):
                return
            import shutil
            shutil.rmtree(dest_dir, ignore_errors=True)

        self.status_var.set(f"下载文件夹：{folder_name}...")
        self._update_progress(0, f"扫描 {folder_name}...")

        def _download():
            try:
                os.makedirs(dest_dir, exist_ok=True)
                file_list = []
                self._collect_folder_files(full_name, folder_path, dest_dir, file_list)
                total = len(file_list)
                if total == 0:
                    group = self.ctx.group_manager.current_group
                    self._safe_after(0, lambda: self._on_download_done(folder_name, group))
                    return
                for i, (fpath, furl, fdest_dir) in enumerate(file_list):
                    if furl:
                        try:
                            content = get_raw_file(furl)
                            fname = fpath.split("/")[-1]
                            file_path = os.path.join(fdest_dir, fname)
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(content)
                        except Exception as e:
                            log_error(f"下载文件 {fpath} 失败：{e}")
                    pct = int((i + 1) / total * 100)
                    self._safe_after(0, lambda p=pct, n=i+1, t=total: self._update_progress(p, f"{n}/{t} 文件"))
                group = self.ctx.group_manager.current_group
                self._safe_after(0, lambda: self._on_download_done(folder_name, group))
            except Exception as e:
                msg = str(e)
                self._safe_after(0, lambda: self.status_var.set(f"下载失败：{msg}"))
                self._safe_after(0, lambda: self.ctx.ui.show_error("下载失败", msg))
                self._safe_after(0, lambda: self._update_progress(0, "下载失败"))

        threading.Thread(target=_download, daemon=True).start()

    def _collect_folder_files(self, repo_full_name, path, dest_dir, file_list):
        owner, repo = repo_full_name.split("/", 1)
        items = get_repo_contents(owner, repo, path)
        if not isinstance(items, list):
            return
        for item in items:
            name = item.get("name", "")
            ftype = item.get("type", "")
            if ftype == "dir":
                sub_dir = os.path.join(dest_dir, name)
                os.makedirs(sub_dir, exist_ok=True)
                sub_path = f"{path}/{name}" if path else name
                self._collect_folder_files(repo_full_name, sub_path, sub_dir, file_list)
            elif ftype == "file":
                download_url = item.get("download_url", "")
                fpath = f"{path}/{name}" if path else name
                file_list.append((fpath, download_url, dest_dir))

    def _on_download_done(self, filename, group):
        self.status_var.set(f"已下载：{filename}")
        self.info_var.set(f"✅ {filename} → {group}")
        self.ctx.append_output(f"[脚本市场] 已下载 {filename} 到分组「{group}」")
        self._update_progress(100, f"✅ {filename} 完成")

        from modules.script_manager import scan_data_directory
        from modules.settings_manager import save_settings
        scan_data_directory(self.ctx)
        self.ctx.update_listbox()
        save_settings(self.ctx.settings)

    def _update_progress(self, value, label=""):
        self.progress_var.set(value)
        self.progress_label.config(text=label)
        if value >= 100:
            self.window.after(3000, lambda: self._reset_progress())

    def _reset_progress(self):
        if self._alive():
            self.progress_var.set(0)
            self.progress_label.config(text="")


def open_script_market(ctx):
    market = ScriptMarketWindow(ctx)
    market.show()
