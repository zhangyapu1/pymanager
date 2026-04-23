import tkinter as tk
from tkinter import messagebox

def edit_content(manager):
    item = manager.get_selected_item()
    if not item:
        return
    script_path = item["storage_path"]
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        messagebox.showerror("读取错误", f"无法读取脚本内容：{e}")
        return

    win = tk.Toplevel(manager.root)
    win.title(f"编辑脚本 - {item['display']}")
    win.geometry("800x600")

    text = tk.Text(win, wrap=tk.NONE, font=("Consolas", 10))
    text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    text.insert("1.0", content)

    sb_y = tk.Scrollbar(text, orient=tk.VERTICAL, command=text.yview)
    sb_x = tk.Scrollbar(text, orient=tk.HORIZONTAL, command=text.xview)
    text.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
    sb_y.pack(side=tk.RIGHT, fill=tk.Y)
    sb_x.pack(side=tk.BOTTOM, fill=tk.X)

    def save():
        new_content = text.get("1.0", tk.END)
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            manager.status_var.set(f"已保存：{item['display']}")
            win.destroy()
            # 重新检查依赖
            import modules as actions
            actions.check_script_deps_and_install(script_path, item['display'], manager.root)
        except Exception as e:
            messagebox.showerror("保存错误", f"保存失败：{e}")

    btn_frame = tk.Frame(win)
    btn_frame.pack(fill=tk.X, pady=5)
    tk.Button(btn_frame, text="保存", command=save).pack(side=tk.RIGHT, padx=5)
    tk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=5)