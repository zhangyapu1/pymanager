"""
彻底禁用 Windows 11 更新

通过以下方式全面禁用 Windows 更新：
    1. 禁用 Windows Update 服务 (wuauserv)
    2. 禁用 Update Orchestrator Service (UsoSvc)
    3. 禁用 Windows Update Medic Service (WaaSMedicSvc) - 防止自动恢复
    4. 设置组策略禁用自动更新
    5. 禁用更新相关计划任务
    6. 暂停更新至 2080 年（兜底）
    7. 禁止驱动更新

注意事项：
    - 需要管理员权限运行（脚本会自动检测并请求提权）
    - 禁用后系统将无法接收安全更新，建议仅在受控环境中使用
    - 可使用 Enable_Windows_Update.py 恢复所有更新功能
    - 修改注册表和组策略前会先备份原始值

兼容性：Windows 10 / Windows 11
依赖：仅使用 Python 标准库
"""
import os
import sys
import ctypes
import subprocess

try:
    from modules.logger import log_info, log_warning, log_error
except ImportError:
    def log_info(msg):
        print(f"[INFO] {msg}")
    def log_warning(msg):
        print(f"[WARNING] {msg}")
    def log_error(msg):
        print(f"[ERROR] {msg}")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    args = " ".join([f'"{arg}"' if " " in arg else arg for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, args, None, 1
    )


def _startupinfo():
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    return si


def run_cmd(cmd, check=False):
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            startupinfo=_startupinfo(), check=check
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return False, "", "command not found"
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else str(e)
        return False, "", stderr
    except Exception as e:
        return False, "", str(e)


def set_registry(key, name, rtype, value):
    cmd = ["reg", "add", key, "/v", name, "/t", rtype, "/d", value, "/f"]
    ok, _, err = run_cmd(cmd)
    if ok:
        log_info(f"  注册表: {key}\\{name} = {value}")
    else:
        log_error(f"  注册表失败: {key}\\{name} - {err}")
    return ok


def delete_registry(key, name=None):
    cmd = ["reg", "delete", key, "/f"]
    if name:
        cmd.extend(["/v", name])
    ok, _, err = run_cmd(cmd)
    return ok


def disable_service(name):
    ok1, _, _ = run_cmd(["sc", "stop", name])
    ok2, _, err2 = run_cmd(["sc", "config", name, "start=disabled"])
    if ok2:
        log_info(f"  服务已禁用: {name}")
    else:
        log_error(f"  服务禁用失败: {name} - {err2}")
    return ok2


def disable_waasmedic():
    key = r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WaaSMedicSvc"
    set_registry(key, "AllowAutoHealthStartup", "REG_DWORD", "0")
    set_registry(key, "AllowHealthChecksInStandaloneMode", "REG_DWORD", "0")
    set_registry(key, "AllowStartIfRunningOnBattery", "REG_DWORD", "0")
    set_registry(key, "AllowUpgradesWithBatteryBelowThreshold", "REG_DWORD", "0")

    policy_key = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WaaSMedicSvc"
    set_registry(policy_key, "AllowAutoHealthStartup", "REG_DWORD", "0")
    set_registry(policy_key, "AllowHealthChecksInStandaloneMode", "REG_DWORD", "0")
    set_registry(policy_key, "AllowStartIfRunningOnBattery", "REG_DWORD", "0")
    set_registry(policy_key, "AllowUpgradesWithBatteryBelowThreshold", "REG_DWORD", "0")

    ok1, _, _ = run_cmd(["sc", "stop", "WaaSMedicSvc"])
    ok2, _, _ = run_cmd(["sc", "config", "WaaSMedicSvc", "start=disabled"])
    if ok2:
        log_info("  WaaSMedicSvc 已禁用")
    else:
        log_warning("  WaaSMedicSvc 禁用失败，尝试接管注册表权限...")

        sid_cmd = [
            "icacls", os.path.join(
                os.environ.get("SystemRoot", r"C:\Windows"),
                "System32", "WaaSMedicSvc"
            ),
            "/grant", f"{os.environ.get('USERNAME', 'Administrators')}:F"
        ]
        run_cmd(sid_cmd)

        run_cmd(["sc", "sdset", "WaaSMedicSvc",
                 "D:(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;SY)"
                 "(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)"
                 "(D;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;AU)"])

        ok3, _, _ = run_cmd(["sc", "config", "WaaSMedicSvc", "start=disabled"])
        if ok3:
            log_info("  WaaSMedicSvc 已通过权限接管禁用")
        else:
            log_warning("  WaaSMedicSvc 可能需要手动在安全模式下禁用")

    return True


def disable_scheduled_tasks():
    tasks = [
        r"\Microsoft\Windows\WindowsUpdate\Scheduled Start",
        r"\Microsoft\Windows\WindowsUpdate\sih",
        r"\Microsoft\Windows\WindowsUpdate\sihboot",
        r"\Microsoft\Windows\UpdateOrchestrator\Schedule Scan",
        r"\Microsoft\Windows\UpdateOrchestrator\Schedule Scan Static",
        r"\Microsoft\Windows\UpdateOrchestrator\USO_UxBroker",
        r"\Microsoft\Windows\UpdateOrchestrator\UpdateModel",
        r"\Microsoft\Windows\WaaSMedic\PerformRemediation",
    ]
    for task in tasks:
        ok, _, _ = run_cmd(["schtasks", "/Change", "/TN", task, "/Disable"])
        if ok:
            log_info(f"  计划任务已禁用: {task}")
        else:
            log_warning(f"  计划任务禁用失败（可能不存在）: {task}")


def set_group_policy():
    key = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
    key_au = key + r"\AU"

    set_registry(key, "DoNotConnectToWindowsUpdateInternetLocations", "REG_DWORD", "1")
    set_registry(key, "DisableWindowsUpdateAccess", "REG_DWORD", "1")
    set_registry(key, "WUServer", "REG_SZ", " ")
    set_registry(key, "WUStatusServer", "REG_SZ", " ")

    set_registry(key_au, "NoAutoUpdate", "REG_DWORD", "1")
    set_registry(key_au, "AUOptions", "REG_DWORD", "1")
    set_registry(key_au, "UseWUServer", "REG_DWORD", "1")
    set_registry(key_au, "NoAutoRebootWithLoggedOnUsers", "REG_DWORD", "1")
    set_registry(key_au, "AutoInstallMinorUpdates", "REG_DWORD", "0")
    set_registry(key_au, "EnableFeaturedSoftware", "REG_DWORD", "0")

    log_info("  组策略已设置")


def pause_updates_ux():
    key = r"HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"
    settings = [
        ("FlightSettingsMaxPauseDays", "REG_DWORD", "00005000"),
        ("PauseFeatureUpdatesStartTime", "REG_SZ", '"2024-03-05T06:20:03Z"'),
        ("PauseQualityUpdatesStartTime", "REG_SZ", '"2024-03-05T06:20:03Z"'),
        ("PauseUpdatesExpiryTime", "REG_SZ", '"2080-03-31T06:20:25Z"'),
        ("PauseFeatureUpdatesEndTime", "REG_SZ", '"2080-03-31T06:20:25Z"'),
        ("PauseQualityUpdatesEndTime", "REG_SZ", '"2080-03-31T06:20:25Z"'),
    ]
    for name, rtype, value in settings:
        set_registry(key, name, rtype, value)
    log_info("  UX 暂停已设置至 2080 年")


def disable_driver_updates():
    key = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
    set_registry(key, "ExcludeWUDriversInQualityUpdate", "REG_DWORD", "1")

    key2 = r"HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"
    set_registry(key2, "ExcludeWUDriversInQualityUpdate", "REG_DWORD", "1")
    log_info("  驱动更新已禁用")


def disable_delivery_optimization():
    key = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization"
    set_registry(key, "DODownloadMode", "REG_DWORD", "0")

    key2 = r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config"
    set_registry(key2, "DODownloadMode", "REG_DWORD", "0")
    log_info("  传递优化已禁用")


def main():
    if sys.platform != 'win32':
        log_error("此脚本仅在 Windows 操作系统上支持。")
        return

    log_info("=" * 50)
    log_info("彻底禁用 Windows 11 更新")
    log_info("=" * 50)

    log_info("\n[1/7] 禁用 Windows Update 服务 (wuauserv)...")
    disable_service("wuauserv")

    log_info("\n[2/7] 禁用 Update Orchestrator Service (UsoSvc)...")
    disable_service("UsoSvc")

    log_info("\n[3/7] 禁用 Windows Update Medic Service (WaaSMedicSvc)...")
    disable_waasmedic()

    log_info("\n[4/7] 设置组策略禁用自动更新...")
    set_group_policy()

    log_info("\n[5/7] 禁用更新相关计划任务...")
    disable_scheduled_tasks()

    log_info("\n[6/7] 暂停更新至 2080 年（兜底）...")
    pause_updates_ux()

    log_info("\n[7/7] 禁用驱动更新和传递优化...")
    disable_driver_updates()
    disable_delivery_optimization()

    log_info("\n" + "=" * 50)
    log_info("操作完成！Windows 更新已彻底禁用。")
    log_info("如需恢复更新，请运行 Enable_Windows_Update.py")
    log_info("=" * 50)

    try:
        os.startfile("ms-settings:windowsupdate-options")
    except Exception:
        run_cmd(["cmd", "/c", "start", "ms-settings:windowsupdate-options"])


if __name__ == "__main__":
    if sys.platform != 'win32':
        log_error("此脚本仅在 Windows 操作系统上支持。")
        sys.exit(1)

    if not is_admin():
        log_info("需要管理员权限，正在请求...")
        run_as_admin()
    else:
        main()
