import tkinter as tk
from tkinter import messagebox
import threading
import os
import tempfile
import shutil
from modules.dependencies import check_script_deps_and_install

def edit_content(manager):
    item = manager.get_selected_item()
    if not item:
        return

    script_rel_path = item["storage_path"]
    script_path = manager._resolve_path(script_rel_path)

    if not os.path.isfile(script_path):
        msg = "脚本文件不存在"
        manager.append_output(f"[错误] {msg}")
        messagebox.showerror("错误", msg)
        return

    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        msg = "文件编码不是 UTF-8，无法编辑"
        manager.append_output(f"[错误] {msg}")
        messagebox.showerror("读取错误", msg)
        return
    except OSError as e:
        msg = f"无法读取脚本内容：{e}"
        manager.append_output(f"[错误] {msg}")
        messagebox.showerror("读取错误", msg)
        return

    win = tk.Toplevel(manager.root)
    win.title(f"编辑脚本 - {item['display']}")
    win.geometry("800x600")

    text = tk.Text(win, wrap=tk.NONE, font=("Consolas", 10))
    sb_y = tk.Scrollbar(win, orient=tk.VERTICAL, command=text.yview)
    sb_x = tk.Scrollbar(win, orient=tk.HORIZONTAL, command=text.xview)

    text.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

    text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    sb_y.grid(row=0, column=1, sticky="ns")
    sb_x.grid(row=1, column=0, sticky="ew")

    win.grid_rowconfigure(0, weight=1)
    win.grid_columnconfigure(0, weight=1)

    text.insert("1.0", content)

    btn_frame = tk.Frame(win)
    btn_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="e")

    save_btn = tk.Button(btn_frame, text="保存", state=tk.NORMAL)
    save_btn.pack(side=tk.RIGHT, padx=5)

    cancel_btn = tk.Button(btn_frame, text="取消", command=win.destroy)
    cancel_btn.pack(side=tk.RIGHT, padx=5)

    def save():
        save_btn.config(state=tk.DISABLED)
        cancel_btn.config(state=tk.DISABLED)
        manager.status_var.set("正在保存并检查依赖...")
        win.config(cursor="watch")

        new_content = text.get("1.0", "end-1c")

        def background_check():
            error_msg = None
            save_success = False

            try:
                dir_name = os.path.dirname(script_path)
                fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    shutil.move(temp_path, script_path)
                    save_success = True
                except:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise
            except Exception as e:
                error_msg = f"文件保存失败：{e}"

            if save_success and not error_msg:
                try:
                    check_script_deps_and_install(script_path, item['display'], manager.root)
                except Exception as e:
                    error_msg = f"依赖检查或安装失败：{str(e)}"

            manager.root.after(0, lambda: on_check_complete(error_msg))

        def on_check_complete(error_msg):
            win.config(cursor="")

            if not win.winfo_exists():
                return

            save_btn.config(state=tk.NORMAL)
            cancel_btn.config(state=tk.NORMAL)

            if error_msg:
                manager.append_output(f"[错误] {error_msg}")
                messagebox.showerror("操作错误", error_msg)
                manager.status_var.set("操作失败")
            else:
                msg = f"已保存并更新依赖：{item['display']}"
                manager.append_output(msg)
                manager.status_var.set(msg)
                win.destroy()

        thread = threading.Thread(target=background_check, daemon=True)
        thread.start()

    save_btn.config(command=save)
