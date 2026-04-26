import tkinter as tk
from tkinter import ttk

try:
    import ttkbootstrap as ttkb
    HAS_TTKBOOTSTRAP = True
except ImportError:
    HAS_TTKBOOTSTRAP = False


def _button(parent, text, command, bootstyle="secondary"):
    if HAS_TTKBOOTSTRAP:
        return ttkb.Button(parent, text=text, command=command, bootstyle=bootstyle)
    else:
        return ttk.Button(parent, text=text, command=command)


class EditorWindow:
    def __init__(self, parent, title, content, on_save, on_cancel):
        self._win = tk.Toplevel(parent)
        self._win.title(title)
        self._win.geometry("800x600")
        self._win.configure(bg='#f3f3f3')

        self._text = tk.Text(
            self._win, wrap=tk.NONE, font=("Consolas", 10),
            bg='#ffffff', fg='#1a1a1a',
            insertbackground='#1a1a1a',
            selectbackground='#e0e0e0', selectforeground='#1a1a1a',
            borderwidth=1, relief='solid',
            highlightthickness=1, highlightcolor='#cccccc', highlightbackground='#dcdcdc'
        )
        sb_y = ttk.Scrollbar(self._win, orient=tk.VERTICAL, command=self._text.yview)
        sb_x = ttk.Scrollbar(self._win, orient=tk.HORIZONTAL, command=self._text.xview)

        self._text.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self._text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        self._win.grid_rowconfigure(0, weight=1)
        self._win.grid_columnconfigure(0, weight=1)

        self._text.insert("1.0", content)

        btn_frame = ttk.Frame(self._win)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="e")

        self._save_btn = _button(btn_frame, text="保存", command=lambda: on_save(self), bootstyle="secondary")
        self._save_btn.pack(side=tk.RIGHT, padx=5)

        self._cancel_btn = _button(btn_frame, text="取消", command=lambda: on_cancel(self), bootstyle="secondary")
        self._cancel_btn.pack(side=tk.RIGHT, padx=5)

    def get_content(self):
        return self._text.get("1.0", "end-1c")

    def set_buttons_enabled(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self._save_btn.config(state=state)
        self._cancel_btn.config(state=state)

    def set_cursor(self, cursor):
        self._win.config(cursor=cursor)

    def exists(self):
        return self._win.winfo_exists()

    def destroy(self):
        if self._win.winfo_exists():
            self._win.destroy()
