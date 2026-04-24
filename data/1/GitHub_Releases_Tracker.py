import os
import sys
import json
import re
import threading
import urllib.request
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
DATA_FILE = os.path.join(CONFIG_DIR, "github_releases.json")
THIS_FILE = os.path.abspath(__file__)

HARDCODED_TOKEN = ""

try:
    from modules.token_crypto import get_api_token as _get_stored_token, save_api_token as _save_token
except ImportError:
    def _get_stored_token():
        return os.environ.get("GITHUB_TOKEN", "")
    def _save_token(token):
        pass


def get_api_token():
    stored = _get_stored_token()
    if stored:
        return stored
    return HARDCODED_TOKEN


def _ensure_token_stored(root=None):
    if _get_stored_token():
        return
    token = simpledialog.askstring(
        "API Token", "首次运行需要设置 GitHub API Token：\n\n（用于提升 API 限额至 5000 次/小时）\n\n留空则使用匿名访问（60 次/小时）",
        parent=root
    )
    if token and token.strip():
        _save_token(token.strip())


def get_download_dir():
    import ctypes.wintypes
    CSIDL_DOWNLOADS = 0x0028
    SHGFP_TYPE_CURRENT = 0
    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_DOWNLOADS, 0, SHGFP_TYPE_CURRENT, buf)
    return buf.value


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"projects": [], "seen_versions": {}}


def save_data(data):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存数据失败: {e}")


def fetch_releases(owner, repo):
    token = get_api_token()
    url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=20"
    headers = {"User-Agent": "PyManager/1.0", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            remaining = resp.headers.get("X-RateLimit-Remaining", "?")
            limit = resp.headers.get("X-RateLimit-Limit", "?")
            reset_ts = resp.headers.get("X-RateLimit-Reset", "")
            print(f"API 限额: {remaining}/{limit} 剩余")
            if reset_ts:
                import time
                reset_time = time.strftime("%H:%M:%S", time.localtime(int(reset_ts)))
                print(f"限额重置时间: {reset_time}")
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            remaining = e.headers.get("X-RateLimit-Remaining", "?")
            limit = e.headers.get("X-RateLimit-Limit", "?")
            reset_ts = e.headers.get("X-RateLimit-Reset", "")
            reset_info = ""
            if reset_ts:
                import time
                reset_time = time.strftime("%H:%M:%S", time.localtime(int(reset_ts)))
                reset_info = f"\n限额将在 {reset_time} 重置"
            raise RuntimeError(f"GitHub API 限流（403）\n\n剩余请求: {remaining}/{limit}{reset_info}")
        if e.code == 404:
            raise RuntimeError(f"项目 {owner}/{repo} 不存在或无 releases（404）")
        raise RuntimeError(f"HTTP 错误 {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络连接失败: {e.reason}")


def parse_repo_url(url_str):
    url_str = url_str.strip().rstrip("/")
    if url_str.endswith(".git"):
        url_str = url_str[:-4]
    if "github.com/" in url_str:
        parts = url_str.split("github.com/")[-1].split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]
    parts = url_str.split("/")
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None


def extract_github_urls(text):
    results = []
    url_pattern = r'https?://github\.com/[\w\-\.]+/[\w\-\.]+'
    for match in re.finditer(url_pattern, text):
        url = match.group(0).rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        owner, repo = parse_repo_url(url)
        if owner and repo:
            results.append((owner, repo))
    short_pattern = r'(?<![/\w])([a-zA-Z0-9][\w\-\.]{1,38})/([a-zA-Z0-9][\w\-\.]{1,38})(?![/\w])'
    skip_words = {"owner", "repo", "user", "name", "path", "dir", "file", "http", "https", "www"}
    for match in re.finditer(short_pattern, text):
        owner = match.group(1)
        repo = match.group(2)
        before = text[max(0, match.start() - 30):match.start()]
        if "github.com/" in before and before.rstrip().endswith("github.com/"):
            continue
        if owner.lower() in skip_words or repo.lower() in skip_words:
            continue
        already = any(o == owner and r == repo for o, r in results)
        if not already:
            results.append((owner, repo))
    return results


def format_release_date(date_str):
    if not date_str:
        return ""
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str[:10] if len(date_str) >= 10 else ""


def load_embedded_data():
    try:
        with open(THIS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        marker_start = "# @EMBEDDED_DATA_START@"
        marker_end = "# @EMBEDDED_DATA_END@"
        start = content.rfind(marker_start)
        end = content.rfind(marker_end)
        if start != -1 and end != -1 and end > start:
            raw = content[start + len(marker_start):end]
            lines = [l for l in raw.splitlines() if not l.strip().startswith("#")]
            json_str = "\n".join(lines).strip()
            if json_str:
                return json.loads(json_str)
    except Exception:
        pass
    return None


def save_to_source_code(data):
    try:
        with open(THIS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        marker_start = "# @EMBEDDED_DATA_START@"
        marker_end = "# @EMBEDDED_DATA_END@"
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        new_block = f"{marker_start}\n{json_str}\n{marker_end}"
        start = content.rfind(marker_start)
        end = content.rfind(marker_end)
        if start != -1 and end != -1 and end > start:
            content = content[:start] + new_block + content[end + len(marker_end):]
        else:
            content = content.rstrip() + "\n\n" + new_block + "\n"
        with open(THIS_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"保存到源代码失败: {e}")
        return False


class GitHubReleasesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Releases 追踪器")
        self.root.geometry("1050x600")
        self.data = load_data()
        embedded = load_embedded_data()
        if embedded:
            existing = {(p["owner"], p["repo"]) for p in self.data["projects"]}
            for p in embedded.get("projects", []):
                if (p["owner"], p["repo"]) not in existing:
                    self.data["projects"].append(p)
                    existing.add((p["owner"], p["repo"]))
        self.project_widgets = {}
        self.releases_cache = {}
        self.select_vars = {}
        _ensure_token_stored(self.root)
        self.build_ui()
        self.refresh_projects()

    def build_ui(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(toolbar, text="➕ 添加项目", command=self.add_project).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="📋 批量导入", command=self.batch_import).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="🔄 全部刷新", command=self.refresh_all).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="💾 保存到源码", command=self.save_to_code).pack(side=tk.LEFT, padx=3)

        tk.Frame(toolbar, width=20).pack(side=tk.LEFT)

        self.batch_mode = tk.BooleanVar(value=False)
        tk.Checkbutton(toolbar, text="批量删除模式", variable=self.batch_mode, command=self.toggle_batch_mode).pack(
            side=tk.LEFT, padx=3
        )
        tk.Button(toolbar, text="🗑 删除勾选", command=self.delete_selected).pack(side=tk.LEFT, padx=3)

        main_area = tk.Frame(self.root)
        main_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_frame = tk.Frame(main_area)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(left_frame)
        scrollbar = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = canvas
        self.canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        right_frame = tk.Frame(main_area, width=210, bd=1, relief=tk.GROOVE)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)

        tk.Label(right_frame, text="筛选与排序", font=("", 11, "bold")).pack(pady=(10, 5))
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        tk.Label(right_frame, text="按年份筛选：").pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.filter_year_var = tk.StringVar(value="全部")
        self.filter_year_combo = ttk.Combobox(right_frame, textvariable=self.filter_year_var, state="readonly", width=18)
        self.filter_year_combo.pack(padx=10, pady=2)
        self.filter_year_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())

        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        tk.Label(right_frame, text="排序方式：").pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.sort_var = tk.StringVar(value="默认")
        sort_options = ["默认", "最新更新优先", "最旧更新优先"]
        self.sort_combo = ttk.Combobox(right_frame, textvariable=self.sort_var, state="readonly", values=sort_options, width=18)
        self.sort_combo.pack(padx=10, pady=2)
        self.sort_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())

        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        tk.Label(right_frame, text="批量选择：", font=("", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(5, 2))
        tk.Button(right_frame, text="✅ 全选当前筛选结果", command=self.select_all_filtered, width=20).pack(padx=10, pady=3)
        tk.Button(right_frame, text="❌ 取消全选", command=self.deselect_all, width=20).pack(padx=10, pady=3)

        self.filtered_count_var = tk.StringVar(value="筛选结果：0 个项目")
        tk.Label(right_frame, textvariable=self.filtered_count_var, fg="gray").pack(anchor=tk.W, padx=10, pady=(10, 2))

        self.status_var = tk.StringVar(value="就绪")
        tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W).pack(
            side=tk.BOTTOM, fill=tk.X
        )

        self._update_year_options()

    def _get_project_latest_year(self, full_name):
        latest_date = self._get_project_latest_date(full_name)
        if latest_date and len(latest_date) >= 4:
            try:
                return int(latest_date[:4])
            except ValueError:
                pass
        return None

    def _get_project_latest_date(self, full_name):
        releases = self.releases_cache.get(full_name, [])
        if not releases:
            return ""
        latest = ""
        for r in releases:
            d = r.get("published_at", "")
            if d and d > latest:
                latest = d
        return latest

    def _update_year_options(self):
        all_years = set()
        for proj in self.data["projects"]:
            full_name = f"{proj['owner']}/{proj['repo']}"
            year = self._get_project_latest_year(full_name)
            if year is not None:
                all_years.add(year)
        year_list = ["全部"] + sorted(all_years, reverse=True)
        self.filter_year_combo["values"] = year_list
        if self.filter_year_var.get() not in year_list:
            self.filter_year_var.set("全部")

    def _get_filtered_projects(self):
        year_filter = self.filter_year_var.get()
        sort_mode = self.sort_var.get()
        projects = list(self.data["projects"])

        if year_filter != "全部":
            try:
                target_year = int(year_filter)
            except ValueError:
                target_year = None
            if target_year is not None:
                filtered = []
                for proj in projects:
                    full_name = f"{proj['owner']}/{proj['repo']}"
                    latest_year = self._get_project_latest_year(full_name)
                    if latest_year == target_year:
                        filtered.append(proj)
                projects = filtered

        if sort_mode == "最新更新优先":
            projects.sort(key=lambda p: self._get_project_latest_date(f"{p['owner']}/{p['repo']}"), reverse=True)
        elif sort_mode == "最旧更新优先":
            projects.sort(key=lambda p: self._get_project_latest_date(f"{p['owner']}/{p['repo']}"))

        return projects

    def apply_filter(self):
        self.refresh_projects()

    def select_all_filtered(self):
        if not self.batch_mode.get():
            self.batch_mode.set(True)
            self.toggle_batch_mode()
        for full_name, var in self.select_vars.items():
            var.set(True)

    def deselect_all(self):
        for full_name, var in self.select_vars.items():
            var.set(False)

    def toggle_batch_mode(self):
        show = self.batch_mode.get()
        for full_name, widgets in self.project_widgets.items():
            cb = widgets.get("select_cb")
            if cb:
                if show:
                    cb.pack(side=tk.LEFT, padx=2)
                else:
                    cb.pack_forget()

    def refresh_projects(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.project_widgets.clear()
        self.select_vars.clear()

        filtered = self._get_filtered_projects()
        self.filtered_count_var.set(f"筛选结果：{len(filtered)} 个项目")

        for i, proj in enumerate(filtered):
            self._create_project_row(i, proj)

    def _create_project_row(self, index, proj):
        owner = proj.get("owner", "")
        repo = proj.get("repo", "")
        full_name = f"{owner}/{repo}"

        frame = tk.LabelFrame(self.scroll_frame, text=full_name, padx=5, pady=5)
        frame.pack(fill=tk.X, padx=5, pady=3)

        row = tk.Frame(frame)
        row.pack(fill=tk.X)

        select_var = tk.BooleanVar(value=False)
        select_cb = tk.Checkbutton(row, variable=select_var)
        if self.batch_mode.get():
            select_cb.pack(side=tk.LEFT, padx=2)
        self.select_vars[full_name] = select_var

        tk.Button(row, text="🔄", width=3, command=lambda o=owner, r=repo: self.fetch_one(o, r)).pack(
            side=tk.LEFT, padx=2
        )

        release_var = tk.StringVar()
        release_combo = ttk.Combobox(row, textvariable=release_var, state="readonly", width=45)
        release_combo.pack(side=tk.LEFT, padx=5)

        tk.Button(row, text="⬇ 下载", command=lambda o=owner, r=repo, v=release_var: self.download_release(o, r, v)).pack(
            side=tk.LEFT, padx=2
        )

        tk.Button(row, text="🔗 打开", command=lambda o=owner, r=repo: self.open_project_url(o, r)).pack(
            side=tk.LEFT, padx=2
        )

        releases = self.releases_cache.get(full_name, [])
        if releases:
            display_items = []
            for r in releases:
                tag = r.get("tag_name", "")
                date = format_release_date(r.get("published_at", ""))
                if date:
                    display_items.append(f"[{date}] {tag}")
                else:
                    display_items.append(tag)
            release_combo["values"] = display_items
            if display_items:
                release_var.set(display_items[0])

        self.project_widgets[full_name] = {
            "frame": frame,
            "release_var": release_var,
            "release_combo": release_combo,
            "select_cb": select_cb,
        }

    def add_project(self):
        url = simpledialog.askstring("添加项目", "请输入 GitHub 项目地址或 owner/repo：\n\n例如：https://github.com/zhangyapu1/pymanager\n或者：zhangyapu1/pymanager")
        if not url:
            return
        owner, repo = parse_repo_url(url)
        if not owner or not repo:
            messagebox.showerror("错误", "无法解析项目地址，请检查格式。")
            return
        full_name = f"{owner}/{repo}"
        for p in self.data["projects"]:
            if p.get("owner") == owner and p.get("repo") == repo:
                messagebox.showinfo("提示", f"项目 {full_name} 已存在。")
                return
        self.data["projects"].append({"owner": owner, "repo": repo})
        save_data(self.data)
        self._update_year_options()
        self.refresh_projects()
        self.status_var.set(f"已添加项目：{full_name}")

    def batch_import(self):
        win = tk.Toplevel(self.root)
        win.title("批量导入 GitHub 项目")
        win.geometry("600x400")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="粘贴包含 GitHub 地址的文本，程序会自动提取：").pack(anchor=tk.W, padx=10, pady=5)

        text_frame = tk.Frame(win)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        result_label = tk.Label(win, text="", fg="blue")
        result_label.pack(anchor=tk.W, padx=10)

        def do_import():
            content = text_widget.get("1.0", tk.END)
            repos = extract_github_urls(content)
            if not repos:
                result_label.config(text="未找到有效的 GitHub 项目地址", fg="red")
                return
            added = 0
            skipped = 0
            existing = {(p["owner"], p["repo"]) for p in self.data["projects"]}
            for owner, repo in repos:
                if (owner, repo) not in existing:
                    self.data["projects"].append({"owner": owner, "repo": repo})
                    existing.add((owner, repo))
                    added += 1
                else:
                    skipped += 1
            save_data(self.data)
            self._update_year_options()
            self.refresh_projects()
            result_label.config(text=f"导入完成：新增 {added} 个，跳过 {skipped} 个已存在", fg="green")
            self.status_var.set(f"批量导入完成：新增 {added} 个项目")

        btn_frame = tk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_frame, text="导入", command=do_import).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="关闭", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def save_to_code(self):
        export_data = {
            "projects": self.data["projects"],
            "seen_versions": self.data.get("seen_versions", {}),
        }
        if save_to_source_code(export_data):
            save_data(self.data)
            self.status_var.set("已保存到源代码和配置文件")
            messagebox.showinfo("保存成功", "项目信息已写入源代码文件中的 EMBEDDED_DATA 区域。")
        else:
            messagebox.showerror("保存失败", "写入源代码失败，请检查文件权限。")

    def delete_selected(self):
        to_delete = [fn for fn, var in self.select_vars.items() if var.get()]
        if not to_delete:
            messagebox.showinfo("提示", "请先勾选要删除的项目。")
            return
        confirm = messagebox.askyesno("确认删除", f"确定要删除以下 {len(to_delete)} 个项目吗？\n\n" + "\n".join(to_delete))
        if not confirm:
            return
        for full_name in to_delete:
            owner, repo = full_name.split("/", 1)
            for i, p in enumerate(self.data["projects"]):
                if p["owner"] == owner and p["repo"] == repo:
                    del self.data["projects"][i]
                    self.data.get("seen_versions", {}).pop(full_name, None)
                    break
        save_data(self.data)
        self._update_year_options()
        self.refresh_projects()
        self.status_var.set(f"已删除 {len(to_delete)} 个项目")

    def fetch_one(self, owner, repo):
        full_name = f"{owner}/{repo}"
        self.status_var.set(f"正在获取 {full_name} 的版本列表...")

        def worker():
            try:
                releases = fetch_releases(owner, repo)
                self.releases_cache[full_name] = releases
                self.root.after(0, lambda: self._update_project_ui(owner, repo))
                self.root.after(0, lambda: self._update_year_options())
                self.root.after(0, lambda: self.status_var.set(f"已获取 {full_name} 的 {len(releases)} 个版本"))
            except RuntimeError as e:
                self.root.after(0, lambda: messagebox.showerror("获取失败", str(e)))
                self.root.after(0, lambda: self.status_var.set(f"获取失败：{full_name}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("获取失败", f"获取 {full_name} 版本列表失败：\n{e}"))
                self.root.after(0, lambda: self.status_var.set(f"获取 {full_name} 版本列表失败"))

        threading.Thread(target=worker, daemon=True).start()

    def _update_project_ui(self, owner, repo):
        full_name = f"{owner}/{repo}"
        if full_name not in self.project_widgets:
            return
        widgets = self.project_widgets[full_name]
        releases = self.releases_cache.get(full_name, [])

        if releases:
            display_items = []
            for r in releases:
                tag = r.get("tag_name", "")
                date = format_release_date(r.get("published_at", ""))
                if date:
                    display_items.append(f"[{date}] {tag}")
                else:
                    display_items.append(tag)
            widgets["release_combo"]["values"] = display_items
            if display_items:
                widgets["release_var"].set(display_items[0])
        else:
            widgets["release_combo"]["values"] = []
            widgets["release_var"].set("")

    def refresh_all(self):
        for proj in self.data["projects"]:
            self.fetch_one(proj["owner"], proj["repo"])

    def open_project_url(self, owner, repo):
        import webbrowser
        url = f"https://github.com/{owner}/{repo}"
        webbrowser.open(url)

    def _parse_tag_from_display(self, display_text):
        if not display_text:
            return ""
        match = re.search(r'\] (.+)$', display_text)
        if match:
            return match.group(1)
        return display_text

    def download_release(self, owner, repo, release_var):
        full_name = f"{owner}/{repo}"
        display_text = release_var.get()
        if not display_text:
            messagebox.showwarning("提示", "请先选择要下载的版本。")
            return

        tag = self._parse_tag_from_display(display_text)

        releases = self.releases_cache.get(full_name, [])
        target_release = None
        for r in releases:
            if r.get("tag_name") == tag:
                target_release = r
                break

        if not target_release:
            messagebox.showerror("错误", f"未找到版本 {tag} 的信息，请先刷新。")
            return

        assets = target_release.get("assets", [])
        if not assets:
            zipball = target_release.get("zipball_url", "")
            if zipball:
                self._do_download(zipball, f"{repo}-{tag}.zip")
            else:
                messagebox.showinfo("提示", f"版本 {tag} 没有可下载的文件。")
            return

        if len(assets) == 1:
            url = assets[0]["browser_download_url"]
            filename = assets[0]["name"]
            self._do_download(url, filename)
        else:
            asset_names = [a["name"] for a in assets]
            choice = simpledialog.askstring(
                "选择文件",
                f"版本 {tag} 有多个文件，请输入要下载的文件名：\n\n" + "\n".join(asset_names),
            )
            if not choice:
                return
            for a in assets:
                if a["name"] == choice:
                    self._do_download(a["browser_download_url"], a["name"])
                    return
            messagebox.showerror("错误", "未找到所选文件。")

    def _do_download(self, url, filename):
        download_dir = get_download_dir()
        dest_path = os.path.join(download_dir, filename)
        if os.path.exists(dest_path):
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(download_dir, f"{name}_{counter}{ext}")):
                counter += 1
            dest_path = os.path.join(download_dir, f"{name}_{counter}{ext}")

        self.status_var.set(f"正在下载：{filename}...")

        def worker():
            try:
                token = get_api_token()
                headers = {"User-Agent": "PyManager/1.0"}
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=120) as resp:
                    total = int(resp.headers.get("Content-Length", 0))
                    downloaded = 0
                    with open(dest_path, "wb") as f:
                        while True:
                            chunk = resp.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                pct = int(downloaded * 100 / total)
                                self.root.after(0, lambda p=pct: self.status_var.set(f"下载中... {p}%"))
                self.root.after(0, lambda: self.status_var.set(f"下载完成：{dest_path}"))
                self.root.after(0, lambda: messagebox.showinfo("下载完成", f"文件已保存到：\n{dest_path}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("下载失败", f"下载失败：\n{e}"))
                self.root.after(0, lambda: self.status_var.set("下载失败"))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubReleasesApp(root)
    root.mainloop()

# @EMBEDDED_DATA_START@
{
  "projects": [
    {
      "owner": "rumla3434",
      "repo": "Atmosphere-stable"
    },
    {
      "owner": "Atmosphere-NX",
      "repo": "Atmosphere"
    },
    {
      "owner": "zdm65477730",
      "repo": "hekate"
    }
  ],
  "seen_versions": {}
}
# @EMBEDDED_DATA_END@
