import os

def update_title_mode(root, data_dir, base_dir):
    mode = "便携模式" if data_dir == os.path.join(base_dir, "data") else "本地模式"
    root.title(f"Python 脚本管理器 - {mode}")