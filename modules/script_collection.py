"""脚本集合 - 脚本列表的数据容器，支持按组过滤和搜索。"""
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
