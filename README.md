# pymanager
一个非专业人员，编写的用于保存、管理py文件的小程序

pymanager/
├── data/                 # 存放脚本文件
├── modules/              # 核心功能模块
│   ├── __init__.py       # 模块导入配置
│   ├── add_script.py     # 添加脚本功能
│   ├── check_deps.py     # 依赖检查功能
│   ├── config.py         # 配置管理
│   ├── delete_selected.py # 删除脚本功能
│   ├── dependencies.py   # 依赖管理
│   ├── drag_drop.py      # 拖拽功能
│   ├── edit_content.py   # 编辑脚本功能
│   ├── group_manager.py  # 分组管理
│   ├── logger.py         # 日志管理
│   ├── rename_selected.py # 重命名脚本功能
│   ├── run_selected.py   # 运行脚本功能
│   ├── storage.py        # 存储管理
│   ├── updater.py        # 自动更新功能
│   └── utils.py          # 工具函数
├── .gitignore            # Git忽略文件
├── README.md             # 项目说明
└── main.py               # 主程序
