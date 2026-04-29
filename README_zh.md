# PyManager - Python 脚本管理器

一个功能强大的 Python 脚本管理工具，专为高效管理和运行 Python 脚本而设计。支持脚本组织、GitHub 脚本市场、AI 分析、自动依赖管理等核心功能。

## 🎯 项目概述

PyManager 是一个现代化的 Python 脚本管理平台，旨在简化 Python 脚本的日常使用和管理。通过直观的图形界面，用户可以轻松组织、运行和管理各种 Python 脚本，同时集成了 GitHub 脚本市场、AI 分析等高级功能。

### 主要特性
- 📁 **智能脚本管理** - 按文件夹分组，支持收藏、置顶、批量操作
- 🌐 **GitHub 脚本市场** - 搜索、预览、下载 GitHub 上的 Python 项目
- 🤖 **AI 智能分析** - 集成多个 AI 平台进行项目分析和翻译
- 🔧 **专业工具集成** - Word 表格格式化、PDF 批处理等实用工具
- ⚙️ **自动化管理** - 依赖检查、自动更新、配置管理

## � 快速开始

### 系统要求
- **操作系统**: Windows 7/10/11（推荐 Windows 10+）
- **Python 版本**: Python 3.7 或更高版本
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 100MB 可用空间

### 安装步骤

1. **下载项目**
   ```bash
   git clone https://github.com/yourusername/pymanager.git
   cd pymanager
   ```

2. **安装依赖包**
   ```bash
   pip install -r requirements.txt
   ```

3. **启动应用程序**
   ```bash
   python main.pyw
   ```
   或者直接双击 `main.pyw` 文件启动

### 首次配置

首次运行时，程序会自动创建必要的配置文件和目录结构。主要配置文件包括：

- `config/app_config.json` - 应用核心配置
- `config/settings.json` - 用户个性化设置
- `data/` - 脚本存储目录

## 📁 核心功能详解

### 1. 脚本管理模块

**脚本组织方式**
- 自动扫描 `data/` 目录结构，按文件夹分组显示
- 支持自定义分组排序和拖拽调整
- 收藏功能：重要脚本可收藏并置顶显示

**操作功能**
- 双击运行：快速执行选中的脚本
- 批量操作：支持多选脚本进行批量删除、移动
- 右键菜单：丰富的上下文操作选项
- 拖拽支持：文件拖拽添加和分组间移动

**运行管理**
- 实时输出：显示脚本执行过程中的输出信息
- 进程控制：支持停止正在运行的脚本
- 历史记录：记录最近运行的脚本历史

### 2. GitHub 脚本市场

**搜索功能**
- 关键词搜索：支持 GitHub 仓库搜索
- 排序选项：按星标、更新时间、语言等排序
- 实时预览：显示仓库基本信息和技术栈

**智能分析**
- AI 分析：集成智谱AI、通义千问、DeepSeek 进行项目分析
- 多语言翻译：支持 README 文档的自动翻译
- 依赖检测：自动识别项目依赖关系

**下载管理**
- 选择性下载：可选择单个或多个文件下载
- 自动归类：下载的脚本自动归类到对应分组
- 依赖安装：自动检测并安装所需 Python 包

### 3. Word 表格格式化工具

项目内置了专业的 Word 文档表格格式化工具，支持多种格式化选项：

**可用工具**
- `format_tables_1.0_gui.py` - 顶线/底线 1.0 磅实线版本
- `format_tables_1.5_gui.py` - 顶线/底线 1.5 磅实线版本
- `报告word表格处理.py` - 专业报告表格处理工具

**格式化特性**
- **边框样式**: 表格内部 0.5 磅虚线，顶线/底线 1.0 或 1.5 磅实线
- **字体设置**: 中文宋体 + Times New Roman，10.5pt 字号
- **对齐方式**: 中文左对齐，数字右对齐，表头居中
- **特殊处理**: 首行底线 0.5 磅实线，支持纵向合并单元格识别

**使用步骤**
1. 运行对应的 GUI 工具
2. 选择要处理的 Word 文档
3. 选择输出目录
4. 点击开始处理，等待进度完成

### 4. 其他实用工具

**文档处理**
- PDF 批处理工具：PDF 文件批量处理
- Excel 合并工具：多文件数据合并到单个 Excel
- 文件重命名：文件夹内文件批量重命名

**系统工具**
- Windows 更新管理：禁用/启用 Windows 自动更新
- GitHub 发布追踪：监控 GitHub 项目发布情况
- 微信消息监控：实时监控微信消息

## 🏗️ 项目架构

### 目录结构
```
pymanager/
├── config/                  # 配置文件目录
│   ├── app_config.json      # 应用核心配置
│   ├── settings.json        # 用户个性化设置
│   └── groups_meta.json     # 分组元数据
├── data/                    # 脚本存储目录
│   ├── 系统工具/            # 系统管理相关脚本
│   ├── PDF批处理工具/       # PDF 处理脚本
│   └── Word表格处理/        # Word 文档处理脚本
├── modules/                 # 核心功能模块
│   ├── script_manager.py    # 脚本管理核心逻辑
│   ├── github_api.py        # GitHub API 集成
│   ├── ai_analyzer.py       # AI 分析功能
│   ├── dependencies.py      # 依赖管理
│   ├── ui_builder.py        # 界面构建
│   └── ...                  # 其他功能模块
├── tests/                   # 测试代码
├── main.pyw                 # 主程序入口
└── README.md               # 项目说明文档
```

### 核心模块说明

**脚本管理模块** (`script_manager.py`)
- 负责脚本的扫描、分类、运行管理
- 实现脚本收藏、历史记录等功能
- 提供批量操作接口

**GitHub 集成模块** (`github_api.py`)
- GitHub API 的封装和调用
- 仓库搜索、信息获取、文件下载
- 支持 OAuth 认证和令牌管理

**AI 分析模块** (`ai_analyzer.py`)
- 多 AI 平台集成（智谱AI、通义千问、DeepSeek）
- 项目分析和代码理解
- 多语言翻译功能

**界面构建模块** (`ui_builder.py`)
- 基于 tkinter 的现代化界面构建
- 响应式布局和主题支持
- 拖拽操作和右键菜单实现

## ⚙️ 配置说明

### 主要配置文件

**应用配置** (`config/app_config.json`)
```json
{
  "version": "1.0.0",
  "github_token": "加密存储的 GitHub 令牌",
  "ai_api_keys": {
    "zhipu": "智谱AI API 密钥",
    "tongyi": "通义千问 API 密钥", 
    "deepseek": "DeepSeek API 密钥"
  },
  "update_channels": ["webdav", "github"]
}
```

**用户设置** (`config/settings.json`)
```json
{
  "window_size": [1200, 800],
  "theme": "dark",
  "auto_update": true,
  "backup_enabled": true,
  "default_group": "未分类"
}
```

### API 密钥配置

如需使用完整功能，需要配置相应的 API 密钥：

1. **GitHub Token**
   - 访问 https://github.com/settings/tokens
   - 创建具有 repo 权限的 personal access token

2. **智谱AI**
   - 访问 https://open.bigmodel.cn/
   - 注册账号并获取 API 密钥

3. **通义千问**
   - 访问 https://dashscope.aliyun.com/
   - 创建应用并获取 API 密钥

4. **DeepSeek**
   - 访问 https://platform.deepseek.com/
   - 注册账号并获取 API 密钥

密钥会自动加密存储，确保安全性。

##  更新与维护

### 自动更新机制

程序支持多种更新方式：

**WebDAV 更新**（推荐）
- 支持坚果云、Dropbox 等 WebDAV 服务
- 配置简单，更新速度快
- 支持增量更新

**GitHub Releases 更新**
- 作为备用更新源
- 自动检测新版本
- 支持版本回滚

**更新保护机制**
- 更新前自动创建程序备份
- 更新失败时可自动恢复
- 版本兼容性检查

### 手动更新方式

如需手动更新，可运行以下脚本：

```bash
# 检查本地发布状态
python release.py

# WebDAV 发布
python release_webdav.py

# 自动发布检查
python release_auto.py
```

## 🐛 故障排除

### 常见问题

**1. 脚本无法运行**
- 检查 Python 环境是否正确安装
- 确认依赖包已全部安装：`pip install -r requirements.txt`
- 查看脚本输出信息获取详细错误

**2. GitHub 搜索失败**
- 检查网络连接是否正常
- 确认 GitHub Token 配置正确
- 查看 API 使用限额是否超限

**3. Word 文档处理报错**
- 确保 Word 文档格式正确
- 检查文档是否被其他程序占用
- 确认 python-docx 库版本兼容性

**4. 界面显示异常**
- 尝试重启应用程序
- 检查屏幕分辨率设置
- 删除配置文件后重新启动

### 日志查看

程序运行日志位于：
- Windows: `%APPDATA%\pymanager\logs\`
- 其他系统: `~/.pymanager/logs/`

## 🤝 贡献指南

### 开发环境搭建

1. **克隆项目**
   ```bash
   git clone https://github.com/yourusername/pymanager.git
   cd pymanager
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **安装开发依赖**
   ```bash
   pip install -r requirements-dev.txt
   ```

### 代码规范

- 遵循 PEP 8 代码风格
- 使用类型注解提高代码可读性
- 添加适当的文档字符串
- 编写单元测试覆盖核心功能

### 提交规范

- 提交信息使用英文描述
- 功能提交：`feat: 描述新功能`
- 修复提交：`fix: 描述修复的问题`
- 文档提交：`docs: 更新文档`

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## � 技术支持

如有问题或建议，可通过以下方式联系：

- GitHub Issues: https://github.com/yourusername/pymanager/issues
- 邮箱: your-email@example.com
- 文档: 查看本项目 Wiki 页面

---

**版本信息**: v1.0.0  
**最后更新**: 2025年4月29日  
**维护者**: Your Name