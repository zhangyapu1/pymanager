import os
import sys
from pathlib import Path

def get_base_dir():
    """
    获取项目基础目录。
    如果是冻结应用（如PyInstaller打包），返回可执行文件所在目录；
    否则，返回当前文件所在目录的父目录（假设当前文件位于子目录中）。
    """
    if getattr(sys, 'frozen', False):
        # 冻结应用情况下，sys.executable 是可执行文件路径
        return str(Path(sys.executable).parent)
    
    # 非冻结情况下，__file__ 是当前脚本路径
    # .resolve() 可以解析符号链接，使路径更规范，但原代码使用 abspath
    # 为了严格保持原逻辑行为（abspath 不解析 symlink 的最后一层，但通常足够）
    # 原逻辑: dirname(dirname(abspath(__file__)))
    current_file = Path(__file__).resolve().parent
    # 原代码是两层 dirname，即父目录的父目录
    # Path(__file__).parent 相当于第一层 dirname
    # .parent 再次相当于第二层 dirname
    base_dir = current_file.parent
    return str(base_dir)

# 定义路径相关的常量，便于维护
DATA_DIR_NAME = "data"
CONFIG_FILE_NAME = "scripts.dat"
DEFAULT_GROUP = "默认分组"

# 计算基础目录
BASE_DIR = get_base_dir()

# 构建完整路径
# 使用 Path 进行拼接，然后转换为 str 以保持与原代码类型一致
DATA_DIR = str(Path(BASE_DIR) / DATA_DIR_NAME)
CONFIG_FILE = str(Path(DATA_DIR) / CONFIG_FILE_NAME)

# 确保data目录存在
# 使用 pathlib 的 mkdir 方法，parents=True 对应 makedirs, exist_ok=True 保持不变
try:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
except OSError as e:
    # 在生产环境中，可能需要记录日志而不是直接抛出，或者根据需求处理
    # 这里保持原代码行为：如果创建失败（非存在性错误），允许异常抛出终止程序
    # 但显式捕获可以让调试信息更清晰，或者仅仅为了展示严谨性
    # 鉴于原代码没有 try-except，且 makedirs 失败通常意味着严重配置错误，
    # 我们重新抛出异常，但确保了逻辑的清晰度。
    raise e