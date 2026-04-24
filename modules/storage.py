import os
import pickle
from modules.logger import log_error
from modules.config import DEFAULT_GROUP

# 假设 modules.logger 中可能有 log_warning，如果没有，暂时使用 log_error 或 print 的替代方案
# 为了严格遵守“不改变函数输入输出”且“不引入未定义的依赖”，这里我们尽量复用现有 log_error
# 但在实际生产中，强烈建议添加 log_warning

def save_scripts(scripts, config_file):
    """
    保存脚本配置到文件。
    """
    try:
        # 确保目录存在，防止因目录不存在导致保存失败
        config_dir = os.path.dirname(config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            
        with open(config_file, 'wb') as f:
            pickle.dump(scripts, f)
        return True
    except Exception as e:
        log_error(f"保存配置失败：{str(e)}")
        return False

def load_scripts(config_file, groups):
    """
    从文件加载脚本配置，并验证文件存在性及重新计算分组。
    """
    if not os.path.exists(config_file):
        return [], set()
    
    scripts = []
    groups_set = set(groups)
    
    try:
        with open(config_file, 'rb') as f:
            raw_scripts = pickle.load(f)
        
        # 确保加载的是列表类型，防止数据结构错误导致后续遍历崩溃
        if not isinstance(raw_scripts, list):
            log_error("加载配置失败：配置文件格式错误，期望列表类型")
            return [], set()

        for item in raw_scripts:
            try:
                # 1. 基本数据结构校验
                if not isinstance(item, dict):
                    continue
                
                # 获取必要字段，如果缺失则跳过该项，避免 KeyError 导致整体失败
                storage_path = item.get("storage_path")
                display_name = item.get("display", "未知脚本")
                
                if not storage_path:
                    continue

                # 2. 文件存在性检查
                if not os.path.exists(storage_path):
                    # 使用日志代替 print，保持一致性
                    log_error(f"警告：脚本 {display_name} 内部文件丢失，已忽略: {storage_path}")
                    continue

                # 3. 计算分组
                # 根据文件实际位置重新确定分组
                # 注意：os.path.relpath 如果路径在不同驱动器上（Windows）可能抛出 ValueError
                try:
                    relative_path = os.path.relpath(storage_path, os.path.dirname(config_file))
                except ValueError:
                    # 如果路径无法相对化（例如不同盘符），回退到绝对路径的目录名或其他策略
                    # 这里为了稳健性，将其归为默认组
                    item["group"] = DEFAULT_GROUP
                    groups_set.add(DEFAULT_GROUP)
                    scripts.append(item)
                    continue

                relative_dir = os.path.dirname(relative_path)
                
                if relative_dir == '.' or relative_dir == '':
                    item["group"] = DEFAULT_GROUP
                else:
                    # 取第一级子目录作为分组
                    # 使用 os.sep 分割是安全的，因为 relative_path 是由 os.path 生成的
                    first_level_dir = relative_dir.split(os.sep)[0]
                    item["group"] = first_level_dir
                
                groups_set.add(item["group"])
                scripts.append(item)
                
            except Exception as item_err:
                # 捕获单个项目处理中的任何意外错误，防止整个加载过程中断
                log_error(f"处理单个脚本项时出错，已跳过: {str(item_err)}")
                continue

        return scripts, groups_set

    except (pickle.UnpicklingError, EOFError, FileNotFoundError, PermissionError) as e:
        # 捕获特定的已知异常，提供更清晰的错误处理
        log_error(f"加载配置失败：{str(e)}")
        return [], set()
    except Exception as e:
        # 捕获其他未预见的异常
        log_error(f"加载配置发生未知错误：{str(e)}")
        return [], set()