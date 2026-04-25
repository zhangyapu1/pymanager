# pymanager

一个用于保存、管理 Python 脚本的小工具。

## 目录结构

```
pymanager/
├── data/                    # 脚本存放目录（按分组组织子目录）
│   └── 系统工具/            # 分组子目录
│       ├── Disable_Windows_Update.py
│       └── GitHub_Releases_Tracker.py
├── modules/                 # 功能模块
│   ├── __init__.py
│   ├── add_script.py        # 添加脚本
│   ├── check_deps.py        # 依赖检查
│   ├── config.py            # 路径与配置常量
│   ├── delete_selected.py   # 删除脚本
│   ├── dependencies.py      # 依赖解析与安装
│   ├── drag_drop.py         # 拖拽支持
│   ├── edit_content.py      # 编辑脚本内容
│   ├── group_manager.py     # 分组管理
│   ├── logger.py            # 日志记录
│   ├── rename_selected.py   # 重命名脚本
│   ├── run_selected.py      # 运行与停止脚本
│   ├── token_crypto.py      # Token 加密存储
│   ├── updater.py           # 自动更新
│   └── utils.py             # 通用工具
├── main.pyw                 # 程序入口
├── REQUIREMENTS.md          # 需求文档
├── README.md
└── .gitignore
```

## 模块说明

| 模块 | 功能 |
|------|------|
| `add_script` | 添加新脚本到管理库 |
| `check_deps` | 检查脚本依赖 |
| `config` | 配置管理 |
| `delete_selected` | 删除选中的脚本 |
| `dependencies` | 依赖解析和处理 |
| `drag_drop` | 拖拽功能支持 |
| `edit_content` | 编辑脚本内容 |
| `group_manager` | 脚本分组管理 |
| `logger` | 日志记录 |
| `rename_selected` | 重命名选中脚本 |
| `run_selected` | 运行选中脚本 |
| `token_crypto` | API Token 加密 |
| `updater` | 自动更新检查 |
| `utils` | 通用工具函数 |

## 主要功能

- **脚本管理**：添加、删除、重命名脚本
- **分组管理**：按类别组织脚本
- **快速运行**：直接运行 Python 脚本
- **依赖检查**：自动检测和安装依赖
- **自动更新**：检查并更新到最新版本

## 更新日志

### v1.2.0

**废弃代码清理**
- 删除 `storage.py` 模块（主流程已改用目录扫描，pickle 序列化不再使用）
- 清理 `config.py` 中与 pickle 存储相关的 `CONFIG_FILE`、`CONFIG_FILE_NAME` 常量
- 移除 README 模块说明表中已删除的 `storage` 条目

**线程安全修复**
- 所有耗时操作的 UI 更新统一通过 `root.after(0, callback)` 调度，杜绝跨线程直接操作 Tkinter 控件
  - `run_selected.py`：后台线程的输出插入、状态栏更新、按钮状态变更全部改为 `root.after` 调度
  - `check_deps.py`：后台线程中所有 `status_var.set` 和输出回调改为 `root.after` 调度
  - `main.pyw`：`output_to_console` 回调统一使用 `root.after`，新增 `_append_output()` 线程安全入口
- 修复 `stop_running()` 直接操作 UI 控件的线程安全问题，提取 `_on_stopped()` 函数通过 `root.after` 调度
- 修复 `_on_stopped` 与 `_on_run_complete` 竞态条件：用户停止脚本后，后台线程仍会调度"运行完成"回调，导致输出窗口同时出现"已停止"和"运行完成"两条消息。新增 `_process_stopped` 标志，`_on_run_complete` 检测到该标志后跳过执行

**运行控制增强**
- 保存 `subprocess.Popen` 引用到 `manager.running_process`
- 新增 **⏹ 停止运行** 按钮，调用 `process.terminate()` 终止正在运行的脚本
- 运行时自动启用停止按钮，运行完成后自动禁用
- 运行前检查是否已有进程在执行，防止重复启动

**路径系统重构**
- `storage_path` 字段统一改为相对路径（基于 `data_dir`），如 `"脚本.py"` 或 `"工具组/脚本.py"`
- 新增 `manager._resolve_path(rel_path)` 方法，在需要绝对路径时统一解析
- 所有模块（`add_script`、`delete_selected`、`rename_selected`、`edit_content`、`check_deps`、`run_selected`）均已适配相对路径
- 路径分隔符统一使用 `/`，确保跨平台一致性
- 修复 `run_selected.py` 路径解析不一致问题：内联的 `os.path.join` + `os.path.isabs` 替换为 `manager._resolve_path()`，与其他模块保持统一入口

**代码质量修复**
- 修复 `add_script.py` 重复路径生成逻辑：`_get_unique_path()` 已返回唯一路径，但 28-38 行又自行实现了一套冲突检测 while 循环，逻辑重复且不支持子目录，已删除
- 修复 `run_selected.py` 缺少 `import tkinter as tk`：使用了 `tk.NORMAL`/`tk.DISABLED` 但未导入 tkinter

**统一输出与日志系统**
- 新增 `manager._append_output(msg)` 统一输出方法，所有模块写入"运行输出"窗口的内容均通过此方法
- `_append_output` 同时写入 GUI 窗口和 `logs/output_log.txt` 日志文件，确保运行记录持久化
- `run_selected.py`：所有 `output_text.insert` 替换为 `manager._append_output()`，子进程输出、运行完成/停止消息统一走此入口
- `main.pyw`：脚本头注释显示、依赖检查输出等均改用 `_append_output()`
- `updater.py`：34 处 `print()` 全部替换为 `logger.info()` / `logger.error()`，`traceback.print_exc()` 替换为 `logger.error(..., exc_info=True)`
- `token_crypto.py`：`print()` 替换为 `log_error()`
- `logger.py` 重构：日志文件从项目根目录 `error_log.txt` 迁移至 `logs/` 目录（`logs/error_log.txt` + `logs/output_log.txt`），新增 `log_output()` 函数专门记录运行输出
- `.gitignore` 新增 `logs/` 忽略规则

**脚本自描述**
- 单击脚本列表中的文件时，自动在运行输出窗口显示脚本头注释
- 支持 Python 三引号 docstring（`"""` / `'''`）和 `#` 注释行两种格式
- 无头注释的脚本显示"该脚本无头注释"提示

### v1.1.0

**依赖管理系统升级**
- 优化依赖检查功能，支持多国内镜像源自动切换
- 实现依赖安装详细进度显示（下载速度、进度百分比）
- 10秒超时自动切换到下一个镜像源
- 统一所有输出到运行输出窗口
- 清理并更新国内镜像源列表（保留3个可用源）

**PDF批处理工具增强**
- 添加输出目录记忆功能
- 支持拖放文件到列表
- 水印功能优化（斜45度，最上层）
- 窗口大小调整，确保所有按钮正确显示

**代码质量改进**
- 统一所有脚本的日志输出格式
- 修复各种bug和异常处理
- 提升代码可维护性

### v1.0.9

**updater.py 重构**
- 引入日志系统替代 print 语句
- 拆分 `fetch_latest_version` 为多个单一职责函数
- 提升代码可维护性和可测试性
