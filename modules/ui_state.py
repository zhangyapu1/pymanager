"""
UI 状态 - 管理界面控件引用和运行状态，实现 UIStateProtocol 接口。

类 UIState：
    持有主界面所有控件的引用，提供统一的状态查询和更新方法。
    作为 AppContext 的 ui_state 属性被各模块使用。

    控件引用：
        listbox      - 脚本列表控件（tk.Listbox）
        listbox_items - 列表项数据映射（索引 → 脚本字典）
        output_text  - 输出文本控件（tk.Text）
        stop_btn     - 停止按钮控件
        status_var   - 状态栏文本变量（tk.StringVar）
        version_var  - 版本信息文本变量（tk.StringVar）
        group_combo  - 分组下拉框控件
        search_var   - 搜索框文本变量（tk.StringVar）

    选择方法：
        get_selected_item()：
            获取单选模式下的选中脚本项字典
            返回 None 表示无选中

        get_selected_items()：
            获取多选模式下的所有选中脚本项列表
            支持批量操作（批量删除、移动、导出、依赖检查）

    控件设置方法：
        set_listbox / set_output_text / set_stop_button / set_status_var /
        set_version_var / set_group_combo / set_search_var：
            由 ui_builder 创建控件后调用，注入控件引用

    状态更新方法：
        append_output(message)：
            追加输出文本并自动滚动到底部，同时写入日志

        clear_output()：
            清空输出区域

        set_status(message)：
            更新状态栏文字

        set_version_info(message)：
            更新版本信息文字

        set_stop_button_enabled(enabled)：
            启用/禁用停止按钮

        refresh_group_combo(groups, current_group)：
            刷新分组下拉框的选项和当前值

依赖：modules.logger
"""
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
