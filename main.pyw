"""PyManager 主入口 - 初始化应用并启动主界面。"""
import sys

sys.dont_write_bytecode = True

from modules.config import BASE_DIR, DATA_DIR
from modules.settings_manager import load_settings
from modules.utils import update_title_mode
from modules.group_manager import GroupManager
from modules.script_manager import scan_data_directory
from modules.ui_builder import create_widgets, on_close as _on_close
from modules.ui_callback import UICallback
from modules.ui_state import UIState
from modules.list_display import update_listbox as _update_listbox
from modules.process_manager import ProcessManager
from modules.script_collection import ScriptCollection
from modules.drag_drop import setup_drag_drop
from modules.deps_init import run_startup_deps_check
from modules.script_selector import on_script_selected as _on_script_selected
import modules.updater as updater


class ScriptManager:
    def __init__(self, root):
        self._root = root
        self.data_dir = DATA_DIR
        self.base_dir = BASE_DIR
        self.scripts = ScriptCollection()
        self.settings = load_settings()
        self.ui = UICallback(root)
        self.ui_state = UIState()
        self.process_manager = ProcessManager()
        self.group_manager = GroupManager(self.data_dir, output_callback=self.append_output, ui_callback=self.ui)

        create_widgets(self)
        run_startup_deps_check(self)
        scan_data_directory(self)
        setup_drag_drop(self)
        update_title_mode(self._root)
        updater.show_version_info(self)

    def append_output(self, message):
        self.ui_state.append_output(message)

    def clear_output(self):
        self.ui_state.clear_output()

    def set_status(self, message):
        self.ui_state.set_status(message)

    def set_version_info(self, message):
        self.ui_state.set_version_info(message)

    def get_selected_item(self):
        return self.ui_state.get_selected_item()

    def get_selected_items(self):
        return self.ui_state.get_selected_items()

    def update_listbox(self):
        keyword = self.ui_state.search_var.get() if self.ui_state.search_var else ""
        _update_listbox(self.ui_state, self.scripts, self.settings, self.group_manager.current_group, keyword)

    def refresh_group_combo(self):
        self.ui_state.refresh_group_combo(list(self.group_manager.groups), self.group_manager.current_group)

    def on_group_changed(self, new_group):
        self.group_manager.current_group = new_group
        self.update_listbox()
        self.append_output(f"当前分组：{new_group}")
        self.set_status(f"当前分组：{new_group}")

    def on_script_selected(self, event):
        _on_script_selected(self, event)

    def on_close(self):
        _on_close(self)

    def schedule_callback(self, callback):
        self._root.after(0, callback)

    def get_root_window(self):
        return self._root


if __name__ == "__main__":
    from modules.app_bootstrap import bootstrap
    bootstrap(ScriptManager)
