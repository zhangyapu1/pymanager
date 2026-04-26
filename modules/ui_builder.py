import tkinter as tk
from tkinter import ttk

try:
    import ttkbootstrap as ttkb
    HAS_TTKBOOTSTRAP = True
except ImportError:
    HAS_TTKBOOTSTRAP = False

from modules.logger import log_error
from modules.run_selected import run_selected, stop_running
from modules.context_menu import show_context_menu
from modules.app_context import AppContext


def _button(parent, text, command, bootstyle="secondary"):
    if HAS_TTKBOOTSTRAP:
        return ttkb.Button(parent, text=text, command=command, bootstyle=bootstyle)
    else:
        return ttk.Button(parent, text=text, command=command)


def _combobox(parent, **kwargs):
    if HAS_TTKBOOTSTRAP:
        return ttkb.Combobox(parent, **kwargs)
    else:
        return ttk.Combobox(parent, **kwargs)


def _label(parent, **kwargs):
    if HAS_TTKBOOTSTRAP:
        return ttkb.Label(parent, **kwargs)
    else:
        kwargs.pop('bootstyle', None)
        return ttk.Label(parent, **kwargs)


def create_widgets(ctx: AppContext):
    try:
        root = ctx.get_root_window()

        top_frame = ttk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        _create_group_widgets(ctx, top_frame)

        buttons = [
            ("\u2795 添加脚本", lambda: _add_script(ctx), "secondary"),
            ("\U0001f50d 检查依赖", lambda: _check_deps(ctx), "secondary"),
            ("\U0001f504 检查更新", lambda: _check_updates(ctx), "secondary"),
            ("\U0001f511 删除Token", lambda: ctx.delete_token(), "secondary"),
            ("\U0001f4c1 打开程序目录", lambda: ctx.open_program_dir(), "secondary"),
        ]
        for text, cmd, bootstyle in buttons:
            btn = _button(top_frame, text=text, command=lambda c=cmd: c(), bootstyle=bootstyle)
            btn.pack(side=tk.LEFT, padx=4, pady=2)

        content_frame = ttk.Frame(root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

        left_label = ttk.Label(left_frame, text="已加载脚本:")
        left_label.pack(anchor=tk.W)

        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        listbox = tk.Listbox(
            list_frame, selectmode=tk.SINGLE,
            font=('Consolas', 10), width=25,
            bg='#ffffff', fg='#1a1a1a',
            selectbackground='#e0e0e0', selectforeground='#1a1a1a',
            highlightthickness=1, highlightcolor='#cccccc', highlightbackground='#dcdcdc',
            borderwidth=1, relief='solid', activestyle='none'
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        listbox.bind('<Double-Button-1>', lambda e: run_selected(ctx))
        listbox.bind("<Button-3>", lambda e: show_context_menu(ctx, e))
        listbox.bind("<<ListboxSelect>>", ctx.on_script_selected)
        ctx.set_listbox(listbox)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)

        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        output_header = ttk.Frame(right_frame)
        output_header.pack(fill=tk.X)

        output_label = ttk.Label(output_header, text="运行输出:")
        output_label.pack(side=tk.LEFT)

        stop_btn = _button(output_header, text="\u23f9 停止运行", command=lambda: stop_running(ctx), bootstyle="secondary")
        stop_btn.pack(side=tk.RIGHT, padx=5)
        stop_btn.config(state=tk.DISABLED)
        ctx.set_stop_button(stop_btn)

        output_text = tk.Text(
            right_frame, font=('Consolas', 10),
            bg='#ffffff', fg='#1a1a1a',
            insertbackground='#1a1a1a',
            selectbackground='#e0e0e0', selectforeground='#1a1a1a',
            borderwidth=1, relief='solid',
            highlightthickness=1, highlightcolor='#cccccc', highlightbackground='#dcdcdc'
        )
        output_text.pack(fill=tk.BOTH, expand=True)
        ctx.set_output_text(output_text)

        output_scrollbar = ttk.Scrollbar(output_text, orient=tk.VERTICAL, command=output_text.yview)
        output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=output_scrollbar.set)

        _apply_window_geometry(ctx)

        root.protocol("WM_DELETE_WINDOW", ctx.on_close)

        status_var = tk.StringVar()
        status_var.set("就绪 | 拖拽 .py 文件自动复制存储，并检查依赖")
        ctx.set_status_var(status_var)

        status_bar = _label(root, textvariable=status_var, anchor=tk.W, bootstyle="secondary")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        version_var = tk.StringVar()
        version_var.set("版本信息加载中...")
        ctx.set_version_var(version_var)

        version_bar = _label(root, textvariable=version_var, anchor=tk.E, font=('Microsoft YaHei UI', 8), bootstyle="secondary")
        version_bar.pack(side=tk.BOTTOM, fill=tk.X)

    except (tk.TclError, OSError) as e:
        log_error(f"创建界面失败：{e}")
        ctx.append_output(f"[错误] 无法创建界面：{e}")
        ctx.ui.show_error("界面错误", f"无法创建界面：{e}\n\n详细信息已写入 logs/error_log.txt")
        import sys
        sys.exit(1)


def _apply_window_geometry(ctx: AppContext):
    root = ctx.get_root_window()
    root.geometry("950x600")

    win_cfg = ctx.settings.get("window", {})
    win_w = win_cfg.get("width", 950)
    win_h = win_cfg.get("height", 600)
    win_x = win_cfg.get("x")
    win_y = win_cfg.get("y")
    if win_x is not None and win_y is not None:
        root.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")
    else:
        root.geometry(f"{win_w}x{win_h}")


def _add_script(ctx: AppContext):
    from modules.add_script import add_script
    add_script(ctx)


def _check_deps(ctx: AppContext):
    from modules.check_deps import check_deps
    check_deps(ctx)


def _check_updates(ctx: AppContext):
    import modules.updater as updater
    updater.check_for_updates(ctx.get_root_window(), ui_callback=ctx.ui, show_no_update_msg=True, output_callback=ctx.append_output)


def _create_group_widgets(ctx: AppContext, parent_frame):
    ttk.Label(parent_frame, text="分组：").pack(side=tk.LEFT, padx=5)

    combo = _combobox(parent_frame, state="readonly", width=20)
    combo.pack(side=tk.LEFT, padx=5)
    combo['values'] = ctx.get_groups()
    combo.set(ctx.get_current_group())
    ctx.set_group_combo(combo)

    def on_select(event):
        selected = combo.get()
        groups = ctx.get_groups()
        if selected in groups:
            ctx.group_manager.set_current_group(selected)
            ctx.on_group_changed(selected)
            ctx.refresh_group_combo()
        else:
            combo.set(ctx.get_current_group())

    combo.bind("<<ComboboxSelected>>", on_select)

    new_btn = _button(parent_frame, text="新建分组", command=lambda: _new_group_ui(ctx), bootstyle="secondary")
    new_btn.pack(side=tk.LEFT, padx=4)

    del_btn = _button(parent_frame, text="删除分组", command=lambda: _delete_group_ui(ctx), bootstyle="secondary")
    del_btn.pack(side=tk.LEFT, padx=4)


def _new_group_ui(ctx: AppContext):
    new_name = ctx.group_manager.new_group(parent=ctx.get_root_window())
    if new_name:
        ctx.on_group_changed(ctx.get_current_group())
        ctx.refresh_group_combo()


def _delete_group_ui(ctx: AppContext):
    result = ctx.group_manager.delete_group(parent=ctx.get_root_window())
    if result:
        ctx.on_group_changed(ctx.get_current_group())
        ctx.refresh_group_combo()
