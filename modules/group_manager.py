"""
分组管理 - 脚本分组的创建、删除、重命名和脚本移动。

类 GroupManager：
    管理脚本分组的完整生命周期，每个分组对应 data/ 下的一个子目录。

    初始化参数：
        data_dir         - 数据目录路径
        output_callback  - 输出回调函数（可选）
        ui_callback      - UI 交互回调（可选）

    核心属性：
        groups          - 分组名称列表，默认分组始终在首位
        groups_meta     - 分组元数据字典，包含排序信息
        current_group   - 当前激活的分组名

    方法：
        load_groups()：
            从文件系统加载分组列表
            - 扫描 data/ 下的子目录作为分组
            - 合并 groups_meta.json 中的元数据
            - 清理不存在的分组元数据
            - 默认分组始终排在第一位

        save_groups()：
            保存分组元数据到 groups_meta.json

        new_group(parent=None)：
            创建新分组
            - 弹出输入对话框获取分组名
            - 验证名称格式（字母、数字、中文、下划线、连字符、空格）
            - 检查名称是否已存在
            - 创建对应子目录

        delete_group(parent=None)：
            删除当前分组
            - 默认分组不可删除
            - 确认后将脚本移动到默认分组
            - 处理文件名冲突（自动添加序号后缀）
            - 删除分组目录

        set_current_group(group_name)：
            切换当前分组

    名称验证规则：
        - 长度不超过 50 字符
        - 不包含 / \\ .. 等路径分隔符
        - 匹配正则 ^[\\w\\u4e00-\\u9fa5\\s\\-]+$

依赖：modules.config, modules.logger, modules.settings_manager
"""
import os
import shutil
import re
from modules.config import DEFAULT_GROUP
from modules.logger import log_error
from modules.settings_manager import load_groups_meta, save_groups_meta

class GroupManager:
    VALID_GROUP_NAME_PATTERN = re.compile(r'^[\w\u4e00-\u9fa5\s\-]+$')

    def __init__(self, data_dir, output_callback=None, ui_callback=None):
        self.data_dir = data_dir
        self.groups = []
        self.groups_meta = {}
        self.current_group = DEFAULT_GROUP
        self._output = output_callback
        self._ui = ui_callback
        self.load_groups()

    def _is_valid_group_name(self, name):
        if not name:
            return False
        if len(name) > 50:
            return False
        if '/' in name or '\\' in name or '..' in name:
            return False
        if not self.VALID_GROUP_NAME_PATTERN.match(name):
            return False
        return True

    def load_groups(self):
        self.groups = [DEFAULT_GROUP]

        if os.path.exists(self.data_dir):
            try:
                for item in os.listdir(self.data_dir):
                    item_path = os.path.join(self.data_dir, item)
                    if os.path.isdir(item_path) and item != DEFAULT_GROUP:
                        self.groups.append(item)
            except OSError as e:
                log_error(f"加载分组列表失败: {e}")
                if self._output:
                    self._output(f"[错误] 无法读取数据目录：{e}")
                if self._ui:
                    self._ui.show_error("错误", f"无法读取数据目录：{e}")

        self.groups_meta = load_groups_meta()

        for g in self.groups:
            if g not in self.groups_meta:
                self.groups_meta[g] = {"order": len(self.groups_meta)}

        stale = [g for g in self.groups_meta if g not in self.groups]
        for g in stale:
            del self.groups_meta[g]

        self.groups.sort(key=lambda g: self.groups_meta.get(g, {}).get("order", 999))
        default_idx = self.groups.index(DEFAULT_GROUP) if DEFAULT_GROUP in self.groups else 0
        self.groups.pop(default_idx)
        self.groups.insert(0, DEFAULT_GROUP)

        self.save_groups()
        self.current_group = DEFAULT_GROUP

    def save_groups(self):
        save_groups_meta(self.groups_meta)

    def new_group(self, parent=None):
        if not self._ui:
            return None

        new_name = self._ui.ask_string("新建分组", "请输入分组名称：", parent=parent)
        if not new_name or not new_name.strip():
            return None

        new_name = new_name.strip()

        if not self._is_valid_group_name(new_name):
            if self._output:
                self._output("[警告] 分组名称包含非法字符或格式不正确")
            self._ui.show_warning("提示", "分组名称包含非法字符或格式不正确。\n仅支持字母、数字、中文、下划线、连字符和空格。", parent=parent)
            return None

        if new_name in self.groups:
            if self._output:
                self._output(f"[警告] 分组「{new_name}」已存在")
            self._ui.show_warning("提示", "分组已存在", parent=parent)
            return None

        group_dir = os.path.join(self.data_dir, new_name)
        try:
            os.makedirs(group_dir, exist_ok=True)
        except PermissionError as e:
            error_msg = f"权限不足，无法创建分组文件夹：{e}"
            log_error(error_msg)
            if self._output:
                self._output(f"[错误] {error_msg}")
            self._ui.show_error("错误", error_msg, parent=parent)
            return None
        except OSError as e:
            error_msg = f"创建分组文件夹失败：{e}"
            log_error(error_msg)
            if self._output:
                self._output(f"[错误] {error_msg}")
            self._ui.show_error("错误", error_msg, parent=parent)
            return None

        self.groups.append(new_name)
        self.save_groups()
        self.current_group = new_name
        return new_name

    def delete_group(self, parent=None):
        if self.current_group == DEFAULT_GROUP:
            if self._output:
                self._output("[提示] 默认分组不能删除")
            if self._ui:
                self._ui.show_warning("提示", "默认分组不能删除", parent=parent)
            return False

        if not self._ui:
            return False

        if not self._ui.ask_yes_no("确认删除", f"确定删除分组「{self.current_group}」吗？\n该分组下的所有脚本将移动到「{DEFAULT_GROUP}」。", parent=parent):
            return False

        deleted = self.current_group

        group_dir = os.path.join(self.data_dir, deleted)
        default_dir = self.data_dir

        if os.path.exists(group_dir):
            try:
                files_to_move = []
                try:
                    for file_name in os.listdir(group_dir):
                        if file_name.endswith('.py'):
                            files_to_move.append(file_name)
                except OSError as e:
                    raise OSError(f"读取分组目录失败: {e}")

                for file_name in files_to_move:
                    old_path = os.path.join(group_dir, file_name)
                    new_path = os.path.join(default_dir, file_name)

                    if os.path.exists(new_path):
                        counter = 1
                        name_without_ext, ext = os.path.splitext(file_name)
                        while True:
                            new_file_name = f"{name_without_ext}_{counter}{ext}"
                            new_path_candidate = os.path.join(default_dir, new_file_name)
                            if not os.path.exists(new_path_candidate):
                                new_path = new_path_candidate
                                break
                            counter += 1

                    shutil.move(old_path, new_path)

                try:
                    if not os.listdir(group_dir):
                        os.rmdir(group_dir)
                except OSError:
                    pass

            except OSError as e:
                error_msg = f"移动文件失败：{e}"
                log_error(error_msg)
                if self._output:
                    self._output(f"[错误] {error_msg}")
                self._ui.show_error("错误", error_msg, parent=parent)
                return False

        if deleted in self.groups:
            self.groups.remove(deleted)

        self.save_groups()
        self.current_group = DEFAULT_GROUP
        return deleted

    def add_group(self, group_name):
        if group_name not in self.groups:
            self.groups.append(group_name)

    def set_current_group(self, group_name):
        if group_name in self.groups:
            self.current_group = group_name
        else:
            self.current_group = DEFAULT_GROUP
