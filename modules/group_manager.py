import os
import pickle
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from modules.config import DEFAULT_GROUP
from modules.logger import log_error

class GroupManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.groups_file = os.path.join(data_dir, "groups.dat")
        self.groups = []
        self.current_group = DEFAULT_GROUP
        self.combo = None          # 保存 Combobox 引用，用于自动刷新
        self.load_groups()

    def load_groups(self):
        # 根据data目录下的子文件夹确定分组
        self.groups = [DEFAULT_GROUP]
        
        # 遍历data目录下的子文件夹
        if os.path.exists(self.data_dir):
            for item in os.listdir(self.data_dir):
                item_path = os.path.join(self.data_dir, item)
                if os.path.isdir(item_path) and item != DEFAULT_GROUP:
                    self.groups.append(item)
        
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
        if new_name in self.groups:
            messagebox.showwarning("提示", "分组已存在", parent=parent)
            return None
        
        # 创建对应的子文件夹
        group_dir = os.path.join(self.data_dir, new_name)
        try:
            os.makedirs(group_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("错误", f"创建分组文件夹失败：{str(e)}", parent=parent)
            return None
        
        self.groups.append(new_name)
        self.save_groups()
        self.current_group = new_name
        if self.combo:
            self.refresh_combo()
        return new_name

    def delete_group(self, parent=None):
        if self.current_group == DEFAULT_GROUP:
            messagebox.showwarning("提示", "默认分组不能删除", parent=parent)
            return False
        if not messagebox.askyesno("确认删除", f"确定删除分组「{self.current_group}」吗？\n该分组下的所有脚本将移动到「{DEFAULT_GROUP}」。", parent=parent):
            return False
        deleted = self.current_group
        
        # 移动分组文件夹中的文件到默认分组
        group_dir = os.path.join(self.data_dir, deleted)
        if os.path.exists(group_dir):
            try:
                for file_name in os.listdir(group_dir):
                    if file_name.endswith('.py'):
                        old_path = os.path.join(group_dir, file_name)
                        new_path = os.path.join(self.data_dir, file_name)
                        
                        # 处理文件名冲突
                        counter = 1
                        name_without_ext, ext = os.path.splitext(file_name)
                        while os.path.exists(new_path):
                            new_file_name = f"{name_without_ext}_{counter}{ext}"
                            new_path = os.path.join(self.data_dir, new_file_name)
                            counter += 1
                        
                        # 移动文件
                        import shutil
                        shutil.move(old_path, new_path)
                
                # 删除空的分组文件夹
                if len(os.listdir(group_dir)) == 0:
                    os.rmdir(group_dir)
            except Exception as e:
                messagebox.showerror("错误", f"移动文件失败：{str(e)}", parent=parent)
        
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
            self.current_group = combo.get()
            if on_group_changed_callback:
                on_group_changed_callback(self.current_group)

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