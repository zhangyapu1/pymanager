def check_deps(manager):
    """检查选中脚本的依赖，并给出明确的状态反馈"""
    item = manager.get_selected_item()
    if not item:
        manager.status_var.set("未选中任何脚本，无法检查依赖")
        return

    manager.status_var.set(f"正在检查脚本「{item['display']}」的依赖...")
    manager.root.update_idletasks()  # 强制刷新状态栏

    import modules as actions
    result = actions.check_script_deps_and_install(
        item["storage_path"],
        item["display"],
        manager.root
    )

    if result is None:
        manager.status_var.set(f"已取消依赖安装：{item['display']}")
    elif result is True:
        manager.status_var.set(f"依赖检查完成：{item['display']} 所有依赖已满足")
    else:
        manager.status_var.set(f"依赖检查完成：{item['display']} 仍缺少部分依赖")