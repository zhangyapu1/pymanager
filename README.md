# pymanager
一个非专业人员，编写的用于保存、管理py文件的小程序

# 项目目录结构图

```
pymanager/
├── data/
│   ├── 1/
│   │   └── 关闭系统更新.py
│   ├── 合并多个文件到一个excel.py
│   ├── 合并多个文件的数据表到一页.py
│   ├── 批量新建文件夹.py
│   └── 文件夹内批量重命名.py
├── modules/
│   ├── __init__.py
│   ├── add_script.py
│   ├── check_deps.py
│   ├── config.py
│   ├── delete_selected.py
│   ├── dependencies.py
│   ├── drag_drop.py
│   ├── edit_content.py
│   ├── group_manager.py
│   ├── logger.py
│   ├── rename_selected.py
│   ├── run_selected.py
│   ├── storage.py
│   ├── updater.py
│   └── utils.py
├── .gitignore
├── README.md
└── main.py
```

## 结构分析

1. **data 文件夹**：
   - 包含各种Python脚本，主要是一些实用工具脚本
   - 有一个子文件夹 `1/`，其中包含 "关闭系统更新.py"
   - 其他脚本包括文件合并、批量操作等功能

2. **modules 文件夹**：
   - 包含多个功能模块，每个模块负责不同的功能
   - 包括脚本管理、依赖检查、拖放功能、内容编辑等
   - 是项目的核心功能实现部分

3. **根目录文件**：
   - `main.py`：项目的主入口文件
   - `README.md`：项目说明文件
   - `.gitignore`：Git忽略文件配置

项目结构清晰，模块化设计良好，便于维护和扩展。
