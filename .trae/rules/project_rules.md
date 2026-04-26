# pymanager 规则

## 更新
1. 先清空
2. 更新 `updater.py` 的 `CURRENT_VERSION`（bug→第3位，功能→第2位，重大→第1位）
3. 更新 README.md：模块表+更新日志
4. 更新 REQUIREMENTS.md：已实现→已发布，路线图，版本历史
5. `python -m modules.manifest_generator`
6. `python -m pytest tests/ -v --tb=short`
7. `git add -A && git commit -m "release: v版本号 - 摘要"`
8. `git push`
9. `create_github_release(version, changelog)`

## 清空
1. 删所有 `__pycache__/` `.pyc` `.pyo`
2. 清空 `logs/`
3. 清空 `config/`
4. 清空 `backups/`
5. 卸载所有包（保留pip）+ `pip cache purge`
6. 确认结果

## 风格
- 不加注释（除非要求）
- 模块必须有docstring
- 用户可见字符串用中文

## 受保护（更新不删）
`data/` `config/` `logs/` `backups/` `settings.json` `groups_meta.json`

## 测试
`python -m pytest tests/ -v --tb=short`
