import os
import shutil
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from modules.config import DEFAULT_GROUP
from modules.logger import log_error

class GroupManager:
    # 预编译正则表达式，用于验证分组名称：只允许字母、数字、中文、下划线、连字符、空格
    # 禁止路径分隔符和点号开头，防止路径遍历和隐藏文件问题
    VALID_GROUP_NAME_PATTERN = re.compile(r'^[\w\u4e00-\u9fa5\s\-]+$')

    def __init__(self, data_dir, output_callback=None):
        self.data_dir = data_dir
        self.groups_file = os.path.join(data_dir, "groups.dat")
        self.groups = []
        self.current_group = DEFAULT_GROUP
        self.combo = None
        self._output = output_callback
        self.load_groups()

    def _is_valid_group_name(self, name):
        """验证分组名称是否合法"""
        if not name:
            return False
        # 检查长度限制，避免过长文件名
        if len(name) > 50:
            return False
        # 检查是否包含非法字符（如路径分隔符）
        if '/' in name or '\\' in name or '..' in name:
            return False
        # 使用正则匹配允许的字符集
        if not self.VALID_GROUP_NAME_PATTERN.match(name):
            return False
        return True

    def load_groups(self):
        # 根据data目录下的子文件夹确定分组
        self.groups = [DEFAULT_GROUP]
        
        # 遍历data目录下的子文件夹
        if os.path.exists(self.data_dir):
            try:
                for item in os.listdir(self.data_dir):
                    item_path = os.path.join(self.data_dir, item)
                    # 确保是目录且不是默认分组（默认分组可能不存在物理文件夹，或者作为根目录存在）
                    # 注意：如果 DEFAULT_GROUP 对应一个物理文件夹，这里排除它意味着它不会出现在下拉菜单的“额外”选项中，
                    # 但它在 self.groups 初始化时已经存在。
                    if os.path.isdir(item_path) and item != DEFAULT_GROUP:
                        self.groups.append(item)
            except OSError as e:
                log_error(f"加载分组列表失败: {str(e)}")
                if self._output:
                    self._output(f"[错误] 无法读取数据目录：{str(e)}")
                messagebox.showerror("错误", f"无法读取数据目录：{str(e)}")
        
        # 保存分组信息（可选，用于向后兼容）
        # self.save_groups()
        
        self.current_group = DEFAULT_GROUP

    def save_groups(self):
        # 分组信息现在根据文件夹结构动态生成，不需要保存到文件中
        # 保留此方法以保持向后兼容
        pass

    def new_group(self, parent=None):
        new_name = simpledialog.askstring("新建分组", "请输入分组名称：", parent=parent)
        if not new_name or not new_name.strip():
            return None
        
        new_name = new_name.strip()
        
        # 安全性检查：验证分组名称
        if not self._is_valid_group_name(new_name):
            if self._output:
                self._output("[警告] 分组名称包含非法字符或格式不正确")
            messagebox.showwarning("提示", "分组名称包含非法字符或格式不正确。\n仅支持字母、数字、中文、下划线、连字符和空格。", parent=parent)
            return None

        if new_name in self.groups:
            if self._output:
                self._output(f"[警告] 分组「{new_name}」已存在")
            messagebox.showwarning("提示", "分组已存在", parent=parent)
            return None
        
        # 创建对应的子文件夹
        group_dir = os.path.join(self.data_dir, new_name)
        try:
            os.makedirs(group_dir, exist_ok=True)
        except Exception as e:
            error_msg = f"创建分组文件夹失败：{str(e)}"
            log_error(error_msg)
            if self._output:
                self._output(f"[错误] {error_msg}")
            messagebox.showerror("错误", error_msg, parent=parent)
            return None
        
        self.groups.append(new_name)
        self.save_groups()
        self.current_group = new_name
        if self.combo:
            self.refresh_combo()
        return new_name

    def delete_group(self, parent=None):
        if self.current_group == DEFAULT_GROUP:
            if self._output:
                self._output("[提示] 默认分组不能删除")
            messagebox.showwarning("提示", "默认分组不能删除", parent=parent)
            return False
        
        if not messagebox.askyesno("确认删除", f"确定删除分组「{self.current_group}」吗？\n该分组下的所有脚本将移动到「{DEFAULT_GROUP}」。", parent=parent):
            return False
        
        deleted = self.current_group
        
        # 移动分组文件夹中的文件到默认分组
        group_dir = os.path.join(self.data_dir, deleted)
        default_dir = self.data_dir # 默认分组对应根数据目录
        
        if os.path.exists(group_dir):
            try:
                # 获取所有需要移动的文件
                files_to_move = []
                try:
                    for file_name in os.listdir(group_dir):
                        if file_name.endswith('.py'):
                            files_to_move.append(file_name)
                except OSError as e:
                    raise IOError(f"读取分组目录失败: {str(e)}")

                for file_name in files_to_move:
                    old_path = os.path.join(group_dir, file_name)
                    new_path = os.path.join(default_dir, file_name)
                    
                    # 处理文件名冲突
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
                    
                    # 移动文件
                    shutil.move(old_path, new_path)
                
                # 删除空的分组文件夹
                # 再次检查目录是否为空，因为可能有些非 .py 文件留在那里
                try:
                    if not os.listdir(group_dir):
                        os.rmdir(group_dir)
                    else:
                        # 如果有非 .py 文件残留，可以选择保留目录或警告用户
                        # 这里选择保留目录以避免误删其他数据，但从 groups 列表中移除
                        pass
                except OSError:
                    pass # 忽略删除目录失败，可能已被删除或非空

            except Exception as e:
                error_msg = f"移动文件失败：{str(e)}"
                log_error(error_msg)
                if self._output:
                    self._output(f"[错误] {error_msg}")
                messagebox.showerror("错误", error_msg, parent=parent)
                # 如果移动失败，不应该从列表中移除分组，以免数据丢失且无法访问
                return False
        
        # 只有成功移动后才从内存列表中移除
        if deleted in self.groups:
            self.groups.remove(deleted)
            
        self.save_groups()
        self.current_group = DEFAULT_GROUP
        if self.combo:
            self.refresh_combo()
        return deleted

    def set_current_group(self, group_name):
        if group_name in self.groups:
            self.current_group = group_name
        else:
            self.current_group = DEFAULT_GROUP
        if self.combo:
            self.combo.set(self.current_group)

    def refresh_combo(self):
        """刷新关联的 Combobox 的值和显示"""
        if self.combo:
            self.combo['values'] = self.groups
            self.combo.set(self.current_group)

    def create_group_widgets(self, parent_frame, on_group_changed_callback):
        tk.Label(parent_frame, text="分组：").pack(side=tk.LEFT, padx=5)
        combo = ttk.Combobox(parent_frame, state="readonly", width=20)
        combo.pack(side=tk.LEFT, padx=5)
        combo['values'] = self.groups
        combo.set(self.current_group)
        self.combo = combo   # 保存引用

        def on_select(event):
            selected = combo.get()
            # 防止设置无效值
            if selected in self.groups:
                self.current_group = selected
                if on_group_changed_callback:
                    on_group_changed_callback(self.current_group)
            else:
                # 如果选中的值不在列表中（理论上不会发生，因为是 readonly），重置
                combo.set(self.current_group)

        combo.bind("<<ComboboxSelected>>", on_select)

        new_btn = tk.Button(parent_frame, text="新建分组", command=lambda: self._new_group_ui(parent_frame, on_group_changed_callback))
        new_btn.pack(side=tk.LEFT, padx=5)

        del_btn = tk.Button(parent_frame, text="删除分组", command=lambda: self._delete_group_ui(parent_frame, on_group_changed_callback))
        del_btn.pack(side=tk.LEFT, padx=5)

        return combo, new_btn, del_btn

    def _new_group_ui(self, parent, callback):
        new_name = self.new_group(parent)
        if new_name and callback:
            callback(self.current_group)

    def _delete_group_ui(self, parent, callback):
        result = self.delete_group(parent)
        if result and callback:
            callback(self.current_group)