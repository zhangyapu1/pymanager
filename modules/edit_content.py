import tkinter as tk
from tkinter import messagebox
import threading
import os
import tempfile
import shutil
# 1. 直接导入具体函数，避免循环导入
from modules.dependencies import check_script_deps_and_install

def edit_content(manager):
    item = manager.get_selected_item()
    if not item:
        return
    
    script_path = item["storage_path"]
    
    # 验证路径有效性
    if not os.path.isfile(script_path):
        messagebox.showerror("错误", "脚本文件不存在")
        return

    # 1. 读取文件内容
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        messagebox.showerror("读取错误", "文件编码不是 UTF-8，无法编辑")
        return
    except OSError as e:
        messagebox.showerror("读取错误", f"无法读取脚本内容：{e}")
        return

    # 2. 创建编辑窗口
    win = tk.Toplevel(manager.root)
    win.title(f"编辑脚本 - {item['display']}")
    win.geometry("800x600")

    # 3. 创建文本框和滚动条
    text = tk.Text(win, wrap=tk.NONE, font=("Consolas", 10))
    sb_y = tk.Scrollbar(win, orient=tk.VERTICAL, command=text.yview)
    sb_x = tk.Scrollbar(win, orient=tk.HORIZONTAL, command=text.xview)
    
    text.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
    
    # 使用 grid 布局
    text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    sb_y.grid(row=0, column=1, sticky="ns")
    sb_x.grid(row=1, column=0, sticky="ew")
    
    win.grid_rowconfigure(0, weight=1)
    win.grid_columnconfigure(0, weight=1)

    text.insert("1.0", content)

    # 4. 定义保存逻辑
    
    # 提前创建按钮框架和按钮，以便在 save 函数中引用，避免作用域问题
    btn_frame = tk.Frame(win)
    btn_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="e")
    
    save_btn = tk.Button(btn_frame, text="保存", state=tk.NORMAL)
    save_btn.pack(side=tk.RIGHT, padx=5)
    
    cancel_btn = tk.Button(btn_frame, text="取消", command=win.destroy)
    cancel_btn.pack(side=tk.RIGHT, padx=5)

    def save():
        # 禁用保存按钮，防止重复提交
        save_btn.config(state=tk.DISABLED)
        cancel_btn.config(state=tk.DISABLED) # 保存期间也禁用取消，防止状态不一致
        manager.status_var.set("正在保存并检查依赖...")
        win.config(cursor="watch") # 更改光标为加载状态
        
        # 获取内容
        new_content = text.get("1.0", "end-1c")
        
        # 定义后台任务
        def background_check():
            error_msg = None
            save_success = False
            
            # 先同步保存文件（采用原子写入方式以防数据损坏）
            try:
                # 获取原文件所在目录
                dir_name = os.path.dirname(script_path)
                # 创建临时文件
                fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    # 替换原文件
                    shutil.move(temp_path, script_path)
                    save_success = True
                except:
                    # 如果移动失败，尝试清理临时文件
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise
            except Exception as e:
                error_msg = f"文件保存失败：{e}"
            
            # 只有保存成功才进行依赖检查
            if save_success and not error_msg:
                try:
                    # 执行耗时的依赖检查
                    # 注意：确保 check_script_deps_and_install 内部不包含直接的 Tkinter UI 更新操作
                    # 否则会导致线程安全问题。如果它只进行 pip install 等系统调用，则是安全的。
                    check_script_deps_and_install(script_path, item['display'], manager.root)
                except Exception as e:
                    error_msg = f"依赖检查或安装失败：{str(e)}"
            
            # 任务完成后，调度回主线程更新 UI
            manager.root.after(0, lambda: on_check_complete(error_msg))

        def on_check_complete(error_msg):
            """主线程回调：处理检查结果"""
            # 恢复光标
            win.config(cursor="")
            
            # 检查窗口是否仍然有效，防止用户在线程运行期间关闭了窗口
            if not win.winfo_exists():
                return

            save_btn.config(state=tk.NORMAL)
            cancel_btn.config(state=tk.NORMAL)
            
            if error_msg:
                messagebox.showerror("操作错误", error_msg)
                manager.status_var.set("操作失败")
            else:
                manager.status_var.set(f"已保存并更新依赖：{item['display']}")
                win.destroy() # 只有成功才关闭窗口

        # 启动后台线程
        thread = threading.Thread(target=background_check, daemon=True)
        thread.start()

    # 绑定命令到按钮
    save_btn.config(command=save)