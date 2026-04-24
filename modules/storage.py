import os
import pickle
from modules.logger import log_error
from modules.config import DEFAULT_GROUP

def save_scripts(scripts, config_file):
    try:
        with open(config_file, 'wb') as f:
            pickle.dump(scripts, f)
        return True
    except Exception as e:
        log_error(f"保存配置失败：{str(e)}")
        return False

def load_scripts(config_file, groups):
    if not os.path.exists(config_file):
        return [], set()
    try:
        with open(config_file, 'rb') as f:
            scripts = pickle.load(f)
        groups_set = set(groups)
        valid = []
        for item in scripts:
            if os.path.exists(item["storage_path"]):
                # 根据文件实际位置重新确定分组
                relative_path = os.path.relpath(item["storage_path"], os.path.dirname(config_file))
                relative_dir = os.path.dirname(relative_path)
                if relative_dir == '.' or relative_dir == '':
                    item["group"] = DEFAULT_GROUP
                else:
                    # 取第一级子目录作为分组
                    item["group"] = relative_dir.split(os.sep)[0]
                groups_set.add(item["group"])
                valid.append(item)
            else:
                print(f"警告：脚本 {item['display']} 内部文件丢失，已忽略")
        return valid, groups_set
    except Exception as e:
        log_error(f"加载配置失败：{str(e)}")
        return [], set()