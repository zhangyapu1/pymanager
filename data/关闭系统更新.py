import os
import sys
import ctypes
import subprocess

# 检查是否以管理员权限运行
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

# 以管理员权限重新运行脚本
def run_as_admin():
    # 确保参数正确传递，特别是包含空格的情况
    # ShellExecuteW 的第二个参数是操作，第三个是文件，第四个是参数
    # sys.executable 是 python 解释器路径，sys.argv[0] 是脚本路径
    # 通常重新运行脚本需要传递脚本路径作为第一个参数给 python
    args = " ".join([f'"{arg}"' if " " in arg else arg for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, args, None, 1
    )

# 修改注册表项
def set_registry_value(key, value_name, value_type, value):
    try:
        # 使用 reg.exe 命令修改注册表，避免 shell=True 以防止注入
        # reg add <Key> /v <ValueName> /t <Type> /d <Data> /f
        cmd = [
            "reg", "add", key,
            "/v", value_name,
            "/t", value_type,
            "/d", value,
            "/f"
        ]
        # 创建窗口隐藏，避免弹出黑框
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True,
            startupinfo=startupinfo
        )
        print(f"设置注册表: {key}\\{value_name} = {value}")
        return True
    except FileNotFoundError:
        print("错误: 找不到 reg.exe 命令。请确保在 Windows 环境下运行。")
        return False
    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr.decode('gbk', errors='ignore') if e.stderr else str(e)
        print(f"设置注册表失败: {stderr_msg.strip()}")
        return False
    except Exception as e:
        print(f"发生未知错误: {str(e)}")
        return False

# 主函数
def main():
    # 平台检查
    if sys.platform != 'win32':
        print("错误: 此脚本仅在 Windows 操作系统上支持。")
        return

    print("Windows 更新暂停至 2080 年")
    print(f"当前运行路径：{os.getcwd()}")
    
    # 注册表键路径 (使用原始字符串避免转义问题)
    reg_key = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"
    
    # 设置注册表值
    registry_settings = [
        ("ActiveHoursEnd", "REG_DWORD", "00000011"),
        ("ActiveHoursStart", "REG_DWORD", "00000008"),
        ("AllowAutoWindowsUpdateDownloadOverMeteredNetwork", "REG_DWORD", "00000000"),
        ("AutoRebootLimitInDays", "REG_DWORD", "00005000"),
        ("ExcludeWUDriversInQualityUpdate", "REG_DWORD", "00000000"),
        ("FlightCommitted", "REG_DWORD", "00000000"),
        ("IsExpedited", "REG_DWORD", "00000000"),
        ("LastToastAction", "REG_DWORD", "00000000"),
        ("UxOption", "REG_DWORD", "00000000"),
        ("FlightSettingsMaxPauseDays", "REG_DWORD", "00005000"),
        ("PauseFeatureUpdatesStartTime", "REG_SZ", '"2024-03-05T06:20:03Z"'),
        ("PauseQualityUpdatesStartTime", "REG_SZ", '"2024-03-05T06:20:03Z"'),
        ("PauseUpdatesExpiryTime", "REG_SZ", '"2080-03-31T06:20:25Z"'),
        ("PauseFeatureUpdatesEndTime", "REG_SZ", '"2080-03-31T06:20:25Z"'),
        ("PauseQualityUpdatesEndTime", "REG_SZ", '"2080-03-31T06:20:25Z"'),
        ("AllowMUUpdateService", "REG_DWORD", "00000000"),
    ]
    
    # 应用所有注册表设置
    for value_name, value_type, value in registry_settings:
        set_registry_value(reg_key, value_name, value_type, value)
    
    # 打开 Windows 更新设置页面
    print("打开 Windows 更新设置页面...")
    try:
        # 使用 os.startfile 更轻量且无需 shell
        os.startfile("ms-settings:windowsupdate-options")
    except Exception as e:
        print(f"无法打开设置页面: {e}")
        # 降级方案：尝试使用 subprocess
        try:
            subprocess.run(["cmd", "/c", "start", "ms-settings:windowsupdate-options"], check=False)
        except Exception:
            pass
    
    print("操作完成！Windows 更新已暂停至 2080 年。")

if __name__ == "__main__":
    if sys.platform != 'win32':
        print("错误: 此脚本仅在 Windows 操作系统上支持。")
        sys.exit(1)

    if not is_admin():
        print("需要管理员权限，正在请求...")
        run_as_admin()
    else:
        main()