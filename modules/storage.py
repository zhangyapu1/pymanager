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
        for script in scripts:
            if "group" not in script:
                script["group"] = DEFAULT_GROUP
            groups_set.add(script["group"])
        valid = []
        for item in scripts:
            if os.path.exists(item["storage_path"]):
                valid.append(item)
            else:
                print(f"警告：脚本 {item['display']} 内部文件丢失，已忽略")
        return valid, groups_set
    except Exception as e:
        log_error(f"加载配置失败：{str(e)}")
        return [], set()