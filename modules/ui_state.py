"""UI 状态 - 管理界面控件引用和运行状态。"""
import tkinter as tk

from modules.logger import log_output


class UIState:
    def __init__(self):
        self.listbox = None
        self.listbox_items = []
        self.output_text = None
        self.stop_btn = None
        self.status_var = None
        self.version_var = None
        self.group_combo = None
        self.search_var = None

    def get_selected_item(self):
        if not self.listbox:
            return None
        sel = self.listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        if 0 <= idx < len(self.listbox_items):
            return self.listbox_items[idx]
        return None

    def get_selected_items(self):
        if not self.listbox:
            return []
        sel = self.listbox.curselection()
        if not sel:
            return []
        items = []
        for idx in sel:
            if 0 <= idx < len(self.listbox_items):
                items.append(self.listbox_items[idx])
        return items

    def set_listbox(self, listbox):
        self.listbox = listbox

    def set_output_text(self, text_widget):
        self.output_text = text_widget

    def set_stop_button(self, button):
        self.stop_btn = button

    def set_status_var(self, var):
        self.status_var = var

    def set_version_var(self, var):
        self.version_var = var

    def set_group_combo(self, combo):
        self.group_combo = combo

    def set_search_var(self, var):
        self.search_var = var

    def set_stop_button_enabled(self, enabled):
        if self.stop_btn:
            self.stop_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def append_output(self, message):
        log_output(message)
        if self.output_text:
            self.output_text.insert(tk.END, message + '\n')
            self.output_text.see(tk.END)

    def clear_output(self):
        if self.output_text:
            self.output_text.delete(1.0, 'end')

    def set_status(self, message):
        if self.status_var:
            self.status_var.set(message)

    def set_version_info(self, message):
        if self.version_var:
            self.version_var.set(message)

    def refresh_group_combo(self, groups, current_group):
        if self.group_combo:
            self.group_combo['values'] = groups
            self.group_combo.set(current_group)
