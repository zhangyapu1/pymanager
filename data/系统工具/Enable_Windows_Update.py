"""
恢复 Windows 11 更新

恢复被 Disable_Windows_Update.py 禁用的所有更新功能：
1. 启用 Windows Update 服务 (wuauserv)
2. 启用 Update Orchestrator Service (UsoSvc)
3. 启用 Windows Update Medic Service (WaaSMedicSvc)
4. 清除组策略禁用更新设置
5. 启用更新相关计划任务
6. 清除暂停更新设置
7. 恢复驱动更新和传递优化

需要管理员权限运行。
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


def enable_service(name, start_type="demand"):
    ok1, _, _ = run_cmd(["sc", "config", name, f"start={start_type}"])
    ok2, _, _ = run_cmd(["sc", "start", name])
    if ok1:
        log_info(f"  服务已启用: {name} (启动类型: {start_type})")
    else:
        log_error(f"  服务启用失败: {name}")
    return ok1


def enable_waasmedic():
    key = r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WaaSMedicSvc"
    set_registry(key, "AllowAutoHealthStartup", "REG_DWORD", "1")
    set_registry(key, "AllowHealthChecksInStandaloneMode", "REG_DWORD", "1")
    set_registry(key, "AllowStartIfRunningOnBattery", "REG_DWORD", "1")
    set_registry(key, "AllowUpgradesWithBatteryBelowThreshold", "REG_DWORD", "1")

    policy_key = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WaaSMedicSvc"
    delete_registry(policy_key, "AllowAutoHealthStartup")
    delete_registry(policy_key, "AllowHealthChecksInStandaloneMode")
    delete_registry(policy_key, "AllowStartIfRunningOnBattery")
    delete_registry(policy_key, "AllowUpgradesWithBatteryBelowThreshold")

    run_cmd(["sc", "config", "WaaSMedicSvc", "start=demand"])
    ok, _, _ = run_cmd(["sc", "start", "WaaSMedicSvc"])
    if ok:
        log_info("  WaaSMedicSvc 已启用")
    else:
        log_warning("  WaaSMedicSvc 启用失败，可能需要重启后生效")

    return True


def enable_scheduled_tasks():
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
        ok, _, _ = run_cmd(["schtasks", "/Change", "/TN", task, "/Enable"])
        if ok:
            log_info(f"  计划任务已启用: {task}")
        else:
            log_warning(f"  计划任务启用失败（可能不存在）: {task}")


def clear_group_policy():
    key = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
    key_au = key + r"\AU"

    delete_registry(key, "DoNotConnectToWindowsUpdateInternetLocations")
    delete_registry(key, "DisableWindowsUpdateAccess")
    delete_registry(key, "WUServer")
    delete_registry(key, "WUStatusServer")
    delete_registry(key, "ExcludeWUDriversInQualityUpdate")

    delete_registry(key_au, "NoAutoUpdate")
    delete_registry(key_au, "AUOptions")
    delete_registry(key_au, "UseWUServer")
    delete_registry(key_au, "NoAutoRebootWithLoggedOnUsers")
    delete_registry(key_au, "AutoInstallMinorUpdates")
    delete_registry(key_au, "EnableFeaturedSoftware")

    log_info("  组策略已清除")


def clear_pause_ux():
    key = r"HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"
    delete_registry(key, "FlightSettingsMaxPauseDays")
    delete_registry(key, "PauseFeatureUpdatesStartTime")
    delete_registry(key, "PauseQualityUpdatesStartTime")
    delete_registry(key, "PauseUpdatesExpiryTime")
    delete_registry(key, "PauseFeatureUpdatesEndTime")
    delete_registry(key, "PauseQualityUpdatesEndTime")
    log_info("  暂停更新设置已清除")


def enable_driver_updates():
    key = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
    delete_registry(key, "ExcludeWUDriversInQualityUpdate")

    key2 = r"HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"
    delete_registry(key2, "ExcludeWUDriversInQualityUpdate")
    log_info("  驱动更新已恢复")


def enable_delivery_optimization():
    key = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization"
    delete_registry(key, "DODownloadMode")

    key2 = r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config"
    set_registry(key2, "DODownloadMode", "REG_DWORD", "3")
    log_info("  传递优化已恢复")


def trigger_update_check():
    ok, _, _ = run_cmd(["usoclient", "StartScan"])
    if ok:
        log_info("  已触发更新扫描")
    else:
        log_warning("  更新扫描触发失败，请手动检查更新")


def main():
    if sys.platform != 'win32':
        log_error("此脚本仅在 Windows 操作系统上支持。")
        return

    log_info("=" * 50)
    log_info("恢复 Windows 11 更新")
    log_info("=" * 50)

    log_info("\n[1/7] 启用 Windows Update 服务 (wuauserv)...")
    enable_service("wuauserv", "demand")

    log_info("\n[2/7] 启用 Update Orchestrator Service (UsoSvc)...")
    enable_service("UsoSvc", "demand")

    log_info("\n[3/7] 启用 Windows Update Medic Service (WaaSMedicSvc)...")
    enable_waasmedic()

    log_info("\n[4/7] 清除组策略禁用更新设置...")
    clear_group_policy()

    log_info("\n[5/7] 启用更新相关计划任务...")
    enable_scheduled_tasks()

    log_info("\n[6/7] 清除暂停更新设置...")
    clear_pause_ux()

    log_info("\n[7/7] 恢复驱动更新和传递优化...")
    enable_driver_updates()
    enable_delivery_optimization()

    log_info("\n[额外] 触发更新扫描...")
    trigger_update_check()

    log_info("\n" + "=" * 50)
    log_info("操作完成！Windows 更新已恢复。")
    log_info("建议重启计算机以确保所有更改生效。")
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
