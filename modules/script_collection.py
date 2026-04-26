"""
脚本集合 - 脚本列表的数据容器，实现 AppContext 的 ScriptCollectionProtocol。

类 ScriptCollection：
    管理脚本元数据列表，每个脚本项为字典格式：
    {
        "display": "显示名称.py",
        "storage_path": "分组名/文件名.py",
        "group": "分组名"
    }

    方法：
        add(script)：
            添加脚本项到集合末尾

        remove(script)：
            从集合中移除脚本项（ValueError 时静默跳过）

        find_by_path(storage_path)：
            按 storage_path 查找脚本索引
            返回索引或 None

        update(index, display, group)：
            更新指定索引脚本的显示名和分组

    协议实现：
        __iter__()  - 返回迭代器，支持 for item in collection
        __len__()   - 返回脚本数量
        __getitem__(index) - 支持索引访问 collection[i]

依赖：typing
"""
from typing import List, Dict, Any, Optional, Iterator


class ScriptCollection:
    def __init__(self):
        self._scripts: List[Dict[str, Any]] = []

    def add(self, script: Dict[str, Any]) -> None:
        self._scripts.append(script)

    def remove(self, script: Dict[str, Any]) -> None:
        try:
            self._scripts.remove(script)
        except ValueError:
            pass

    def find_by_path(self, storage_path: str) -> Optional[int]:
        for i, script in enumerate(self._scripts):
            if script['storage_path'] == storage_path:
                return i
        return None

    def update(self, index: int, display: str, group: str) -> None:
        self._scripts[index]["display"] = display
        self._scripts[index]["group"] = group

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(self._scripts)

    def __len__(self) -> int:
        return len(self._scripts)

    def __getitem__(self, index):
        return self._scripts[index]
