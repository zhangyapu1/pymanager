# pymanager 项目规则

## 当用户说"更新"时，执行以下完整流程

1. **更新版本号**：修改 `modules/updater.py` 中的 `CURRENT_VERSION`，根据变更程度递增（小修 bug 递增第三位，新功能递增第二位，重大变更递增第一位）
2. **更新 README.md**：
   - 检查目录结构和模块说明表是否需要新增模块
   - 在"更新日志"章节顶部添加新版本的更新条目，包含所有变更
3. **更新 REQUIREMENTS.md**：
   - 将已实现的功能从"待实现"移到已发布
   - 更新路线图版本号和内容
   - 在版本历史表中添加新条目
4. **重新生成 manifest.json**：运行 `python -m modules.manifest_generator`
5. **运行测试**：`python -m pytest tests/ -v --tb=short`
6. **提交代码**：`git add -A && git commit -m "release: v版本号 - 变更摘要"`
7. **推送代码**：`git push`
8. **发布 GitHub Release**：调用 `modules/updater.py` 中的 `create_github_release(version, changelog)` 函数，changelog 从 README.md 的对应版本更新日志中提取

## 代码风格

- 不添加注释，除非用户明确要求
- 所有模块必须有 docstring
- 使用中文编写用户可见的字符串和文档

## 受保护的目录和文件（更新时不可删除）

- `data/` - 用户脚本数据
- `config/` - 用户配置
- `logs/` - 日志文件
- `backups/` - 备份文件
- `settings.json`、`groups_meta.json` - 用户配置文件

## 测试命令

```bash
python -m pytest tests/ -v --tb=short
```

## lint 命令

无专用 lint 命令，使用 pytest 验证
