# pymanager

一个用于保存、管理 Python 脚本的小工具。

## 目录结构

```
pymanager/
├── config/                  # JSON 配置文件目录
│   ├── settings.json        # 窗口、日志等全局设置
│   ├── groups_meta.json     # 分组排序元数据
│   └── pdf_tool.json        # PDF 工具配置
├── data/                    # 脚本存放目录（按分组组织子目录）
│   └── 系统工具/            # 分组子目录
│       ├── Disable_Windows_Update.py
│       └── GitHub_Releases_Tracker.py
├── modules/                 # 功能模块
│   ├── __init__.py
│   ├── add_script.py        # 添加脚本
│   ├── ai_analyzer.py       # AI 项目分析（智谱/通义/DeepSeek）
│   ├── app_bootstrap.py     # 应用启动工厂
│   ├── app_context.py       # AppContext / UICallbackProtocol / GroupManagerInterface
│   ├── backup_manager.py    # 备份创建与清理
│   ├── batch_ops.py         # 批量操作（多选删除/移动/导出）
│   ├── check_deps.py        # 依赖检查
│   ├── config.py            # 版本号、路径与配置常量
│   ├── context_menu.py      # 右键菜单
│   ├── delete_selected.py   # 删除脚本
│   ├── dependencies.py      # 依赖解析与安装
│   ├── deps_init.py         # 依赖初始化
│   ├── drag_drop.py         # 拖拽支持
│   ├── edit_content.py      # 编辑脚本内容
│   ├── encrypt_utils.py     # API Key 加密存储
│   ├── favorites.py         # 脚本收藏/置顶
│   ├── github_api.py        # GitHub API 通信
│   ├── github_repo.py       # GitHub 仓库 API（搜索/文件/README）
│   ├── group_manager.py     # 分组管理
│   ├── list_display.py      # 列表显示与排序
│   ├── logger.py            # 日志记录
│   ├── manifest_cleanup.py  # 清单加载与过时文件清理
│   ├── manifest_generator.py # 清单生成器
│   ├── markdown_renderer.py # Markdown/HTML 渲染
│   ├── process_manager.py   # 进程管理
│   ├── py2_compat.py        # Python 2 兼容垫片
│   ├── recent_runs.py       # 最近运行记录
│   ├── rename_selected.py   # 重命名脚本
│   ├── run_selected.py      # 运行与停止脚本
│   ├── script_collection.py # 脚本集合管理
│   ├── script_icons.py      # 脚本图标
│   ├── script_manager.py    # 脚本数据 CRUD
│   ├── script_market.py     # 脚本市场 UI
│   ├── script_selector.py   # 脚本选择器
│   ├── settings_manager.py  # JSON 配置管理
│   ├── token_crypto.py      # Token 加密存储
│   ├── translate_service.py # 翻译服务（Google/百度/腾讯）
│   ├── ui_builder.py        # UI 组件构建
│   ├── ui_callback.py       # UI 操作抽象层（messagebox/filedialog）
│   ├── ui_editor.py         # 编辑器窗口 UI（EditorWindow）
│   ├── ui_state.py          # UI 状态管理
│   ├── updater.py           # 自动更新
│   └── utils.py             # 通用工具
├── tests/                   # 单元测试
├── main.pyw                 # 程序入口
├── REQUIREMENTS.md          # 需求文档
├── README.md
└── .gitignore
```

## 模块说明

| 模块 | 功能 |
|------|------|
| `add_script` | 添加新脚本到管理库 |
| `ai_analyzer` | AI 项目分析（智谱AI / 通义千问 / DeepSeek） |
| `app_bootstrap` | 应用启动工厂（延迟导入避免循环依赖） |
| `app_context` | 模块间接口协议（AppContext / UICallbackProtocol / GroupManagerInterface） |
| `backup_manager` | 更新前创建项目备份，自动清理过期备份 |
| `batch_ops` | 批量操作（Ctrl/Shift 多选，批量删除/移动/导出） |
| `check_deps` | 检查脚本依赖 |
| `config` | 版本号、路径与配置常量（CURRENT_VERSION 唯一定义处） |
| `context_menu` | 右键菜单 |
| `delete_selected` | 删除选中的脚本 |
| `dependencies` | 依赖解析和处理 |
| `deps_init` | 依赖初始化 |
| `drag_drop` | 拖拽功能支持 |
| `edit_content` | 编辑脚本内容 |
| `encrypt_utils` | API Key 加密存储（XOR + Base64，内置默认密钥） |
| `favorites` | 脚本收藏/置顶管理 |
| `github_api` | GitHub API 通信（版本查询、文件下载、Release 发布） |
| `github_repo` | GitHub 仓库 API（搜索/文件列表/README 获取） |
| `group_manager` | 脚本分组管理 |
| `list_display` | 列表显示与排序（收藏→最近运行→其他） |
| `logger` | 日志记录 |
| `manifest_cleanup` | 更新时对比新旧 manifest.json，清理废弃文件和空目录 |
| `manifest_generator` | 清单生成器（扫描项目文件生成 manifest.json） |
| `markdown_renderer` | Markdown/HTML 转纯文本渲染 |
| `process_manager` | 运行进程管理（启动/停止/状态） |
| `py2_compat` | Python 2 兼容垫片（自动创建 site-packages 垫片） |
| `recent_runs` | 最近运行时间戳记录与查询 |
| `rename_selected` | 重命名选中脚本 |
| `run_selected` | 运行选中脚本 |
| `script_collection` | 脚本集合封装（add/remove/find/update） |
| `script_icons` | 脚本图标管理（20 个内置 emoji） |
| `script_manager` | 脚本数据 CRUD |
| `script_market` | 脚本市场 UI（GitHub 仓库浏览/搜索、项目下载） |
| `script_selector` | 脚本选择器 |
| `settings_manager` | JSON 配置管理 |
| `token_crypto` | API Token 加密 |
| `translate_service` | 翻译服务（Google / 百度 / 腾讯，分段翻译） |
| `ui_builder` | UI 组件构建（主界面布局、搜索框） |
| `ui_callback` | UI 操作抽象层（messagebox / filedialog / simpledialog） |
| `ui_editor` | 编辑器窗口 UI（EditorWindow 类） |
| `ui_state` | UI 状态管理（选择、搜索、按钮状态） |
| `updater` | 自动更新检查 |
| `utils` | 通用工具函数 |

## 主要功能

- **脚本管理**：添加、删除、重命名脚本，收藏/置顶，自定义图标
- **搜索过滤**：列表上方搜索框，实时模糊匹配脚本名称和路径
- **智能排序**：收藏置顶 → 最近运行 → 其他脚本，最近运行按时间倒序
- **分组管理**：按类别组织脚本
- **快速运行**：直接运行 Python 脚本
- **批量操作**：Ctrl/Shift 多选，批量删除/移动/导出
- **脚本市场**：浏览 GitHub 仓库，搜索项目，下载项目/文件，README 翻译，AI 项目分析
- **多翻译服务**：有道翻译、百度翻译、腾讯翻译君，支持分段翻译逐段显示
- **AI 分析**：智谱AI / 通义千问 项目分析，API Key 加密存储
- **依赖检查**：自动检测和安装依赖，运行前自动检查，详细状态输出，Python 2 兼容性自动修复，包冲突自动替换
- **自动更新**：检查并更新到最新版本
- **统一输出**：所有模块通过 `append_output` 统一输出到"运行输出"窗口和日志文件
- **日志管理**：自动清理过期日志（7天过期，单文件1MB截断）

## 更新日志

### v1.8.2

**🔧 版本号统一管理**
- 版本号统一到 `config.py` 管理，所有模块从 `config.CURRENT_VERSION` 引用
- 以后更新版本号只需修改 `config.py` 一处

**📦 模块拆分解耦**
- `updater.py`（883→305行）拆分为：`github_api.py`（GitHub API 通信）、`backup_manager.py`（备份创建与清理）、`manifest_cleanup.py`（清单加载与过时文件清理）
- `script_market.py`（1374→963行）拆分为：`translate_service.py`（翻译服务）、`ai_analyzer.py`（AI 分析）、`github_repo.py`（GitHub 仓库 API）、`markdown_renderer.py`（Markdown 渲染）
- `dependencies.py`（458→333行）拆分为：`py2_compat.py`（Python 2 兼容垫片）

**🗑 冗余代码移除**
- 移除 `PDF批处理工具.py` 中的自动依赖安装代码（由主程序统一管理）
- 修正 `合并多个文件的数据表到一页.py` 过时的依赖描述

**🐛 Bug 修复**
- 修复 `group_manager.py` 中正则转义序列 SyntaxWarning

### v1.7.0

**🚀 更新机制重构**
- manifest.json 移入 `modules/` 目录（解决 `config/` 被排除导致发布包缺少 manifest 的问题）
- 发布 Release 不再单独打包 zip，使用 GitHub zipball 自动生成源码包
- 修复 `_load_manifest` 在强制删除 manifest 后无法读取旧版 manifest 导致对比清理跳过的问题
- 更新时强制清理 `config/manifest.json`（旧版遗留）

### v1.6.4

**🐛 更新清理修复**
- 修复更新时强制清理（`.trae/`、`tests/`、`.gitignore`、`REQUIREMENTS.md`、`manifest.json`）未执行的问题
- 原因：强制清理逻辑位于 manifest 缺失检查之后，旧版无 manifest 时直接 return 导致跳过
- 修复：将强制清理逻辑提前到函数开头，确保无论有无 manifest 都会执行

### v1.6.3

**🔧 更新机制修复**
- 修复下载更新后空目录未清理的问题：循环清理嵌套空目录，直到无新空目录产生
- 修复下载更新后未自动重启的问题：重启脚本添加 `taskkill /f /pid` 强制终止旧进程（支持 .pyw 入口）
- .exe 更新增加文件复制重试机制（最多5次），防止进程未完全退出导致文件被占用
- manifest.json 移入 config/ 目录，不再放在项目根目录
- 更新时强制清理 `.trae/`、`tests/`、`.gitignore`、`REQUIREMENTS.md`、根目录 `manifest.json`
- manifest 生成排除 `.trae/`、`tests/`、`.gitignore`、`REQUIREMENTS.md`，不纳入发布包

### v1.6.2

**📝 文档改进**
- 为全部 34 个模块添加详细 docstring：功能描述、函数签名、参数说明、数据结构、实现细节、依赖关系
- 修复 `utils.py` docstring 中三单引号导致语法错误的问题

### v1.6.1

**📦 更新机制增强**
- 清单对比清理：新增 `manifest.json` 和 `manifest_generator.py`，更新时自动对比新旧清单，删除废弃文件，清理空目录
- GitHub Release 自动发布：新增 `create_github_release()` 函数，通过 GitHub API 自动创建 Release
- 白名单保护：`data/`、`config/`、`logs/`、`backups/` 等用户数据目录更新时永不删除

**🐛 Bug 修复**
- 修复 `scan_data_directory` 返回 None 导致 TypeError（不再赋值给 `ctx.scripts`）
- 修复 AI 面板按钮不可见（改用 grid 布局，去掉 `pack_propagate(False)`）

### v1.6.0

**脚本市场**
- GitHub 仓库浏览与搜索：浏览热门 Python 仓库，支持关键词搜索
- 项目下载：支持下载整个项目到 `data/` 目录，或下载单个文件/文件夹
- 下载进度条：实时显示下载进度
- 三栏可调布局：仓库列表、文件列表、README 预览宽度可手动拖拽调节（PanedWindow）

**README 翻译**
- 多翻译服务：有道翻译、百度翻译、腾讯翻译君，可手动切换
- 分段翻译逐段显示：长文本分段翻译，翻译一段显示一段，无需等待全文完成
- 翻译滚动条不自动跟随：翻译时不强制滚动到底部，方便阅读已翻译部分

**AI 项目分析**
- 双 AI 引擎：智谱AI / 通义千问，默认通义千问
- API Key 加密存储：XOR + Base64 加密，内置默认 Key，失败时弹窗让用户输入
- Key 管理：保存/删除 Key 按钮，支持切换 AI 时自动加载对应 Key
- 手动选择 AI 自动设为默认

**UI 改进**
- 统一按钮配色：所有按钮使用 ttkbootstrap primary 样式
- 统一窗口底色：所有窗口和组件背景色一致
- 窗口闪烁修复：翻译进度节流（500ms 间隔），减少 UI 重绘
- AI 面板 grid 布局：确保所有按钮完整显示

**Bug 修复**
- 修复 `scan_data_directory` 返回 None 导致 TypeError
- 修复 GitHub API 403 错误（集成主程序 GitHub Token）
- 修复翻译卡在"正在翻译中"（增加超时、文本分段、错误日志）
- 修复窗口关闭后 TclError（添加窗口存活检查）
- 修复 README 预览显示源代码而非渲染内容

### v1.5.0

**搜索与排序**
- 脚本搜索/过滤：列表上方搜索框，实时模糊匹配，支持按名称和路径过滤
- 最近运行排序：脚本列表按 收藏→最近运行→其他 排序，最近运行脚本按时间倒序（🕒 标记）
- 运行时间戳记录：`recent_runs` 模块，自动清理超过 50 条的旧记录

### v1.4.0

**脚本管理增强**
- 脚本收藏/置顶：右键收藏脚本，收藏脚本自动置顶显示（⭐ 标记）
- 脚本图标：右键设置图标（20 个内置 emoji 图标），显示在脚本名前
- 批量操作：Ctrl/Shift 多选脚本，右键批量删除/移动/导出

**依赖管理系统增强**
- Python 2 兼容性自动修复：检测到 Python 2 遗留模块（如 `exceptions`、`Queue`、`ConfigParser` 等 20+ 个）时，自动在 site-packages 创建兼容垫片
- 包冲突自动替换：检测到旧版 `docx` 包与 `python-docx` 冲突时，自动卸载旧版并安装正确版本
- 传递依赖检测增强：`verify_imports` 支持三层自动修复（Python 2 垫片 → 包冲突替换 → 模块缓存清理后重试）
- 依赖检查日志记录：`check_deps.py` 和 `run_selected.py` 中的依赖检查操作写入日志文件

**性能优化**
- 禁用 `__pycache__` 字节码缓存（`sys.dont_write_bytecode = True`），减少磁盘写入

### v1.3.1

- 代码解耦深化：定义 `AppContext Protocol`、`UICallbackProtocol`、`GroupManagerInterface` 三个接口协议，模块间依赖接口而非具体实现
- `dependencies.py` / `updater.py` 移除所有直接 `tkinter` 调用，通过 `ui_callback` 参数注入 UI 操作
- `updater.py` 移除 `Toplevel` 进度窗口，改用 `progress_callback` 回调
- `scripts` 列表封装：新增 `add_script()`/`remove_script()`/`find_script_by_path()`/`update_script()` 方法，消除外部直接修改
- `self.root` 改为 `self._root` 私有属性，通过 `get_root_window()` 访问
- `add_script.py` 通过 `UICallback.ask_open_filename()` 替代直接 `filedialog` 调用
- `group_manager.py` 移除未使用的 `messagebox`/`simpledialog` 导入
- `edit_content.py` 编辑器 UI 提取到独立 `ui_editor.py`（`EditorWindow` 类），业务模块不再导入 tkinter
- `group_manager.py` 移除 `self.combo` 和 `create_group_widgets()`，分组 UI 移至 `ui_builder.py`
- 引入 `ttkbootstrap`（cosmo 主题），所有按钮/标签/组合框使用 `bootstyle` 样式，界面风格适配 Windows 11

### v1.3.0

- 代码解耦：拆分 `script_manager.py`（脚本数据 CRUD）、`context_menu.py`（右键菜单）、`settings_manager.py`（JSON 配置管理）
- JSON 配置系统：所有配置统一存放在 `config/` 目录，支持 `settings.json`、`groups_meta.json`、`pdf_tool.json`
- 异常处理细化：modules/ 下 40 处 `except Exception` 全部替换为具体异常类型，避免吞掉未预料的 bug
- 窗口位置记忆：关闭时保存窗口大小和位置，下次启动恢复
- 单元测试：新增 55 个测试用例覆盖核心模块

### v1.2.1

- 统一输出系统：所有模块通过 `append_output` 写入窗口和日志文件
- 依赖检查增强：运行前自动检查，详细状态输出，pip 进度实时显示
- 线程安全修复：耗时操作移至后台线程，messagebox 线程安全调用
- 日志自动清理：启动时自动删除 7 天前日志，超过 1MB 自动截断
- 修复 data 脚本 messagebox 无限递归 bug

### v1.2.0

- 废弃代码清理：删除 `storage.py`，移除 pickle 相关代码
- 线程安全：UI 更新统一通过 `root.after` 调度，修复竞态条件
- 运行控制：新增停止运行按钮，防止重复启动
- 路径重构：`storage_path` 统一为相对路径，新增 `_resolve_path` 方法
- 统一输出与日志：新增 `_append_output` 方法，日志迁移至 `logs/` 目录
- 脚本自描述：单击显示脚本头注释（docstring / # 注释）

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
