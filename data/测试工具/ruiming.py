# -*- coding: UTF-8 -*-
"""
锐明数据处理功能模块

提供图像标注相关的数据处理功能，包括：
- screen_unmarked_image: 筛选未标注的图片
- change_label_in_xml: 修改XML标注文件中的标签
- screen_without_label_json_file: 筛选无标注的JSON文件

使用方式：python ruiming.py <功能名> [参数...]
示例：python ruiming.py screen_unmarked_image ./data_dir
"""

try:
    from office.core.TestTypes.RuimingType import MainRuiming
    ruiming = MainRuiming()
except ImportError:
    try:
        import poruiming
        ruiming = poruiming
    except ImportError:
        ruiming = None


def _check_dependency():
    if ruiming is None:
        raise ImportError(
            "无法导入锐明数据处理模块，请安装依赖：\n"
            "  pip install python-office\n"
            "或：pip install poruiming"
        )


def screen_unmarked_image(dir_path):
    """筛选未标注的图片。

    Args:
        dir_path: 包含图片和标注文件的目录路径

    Returns:
        None
    """
    _check_dependency()
    if hasattr(ruiming, 'screen_unmarked_image'):
        ruiming.screen_unmarked_image(dir_path)
    else:
        print(f"筛选未标注图片：{dir_path}")


def change_label_in_xml(dir_path, old_label, new_label):
    """修改XML标注文件中的标签。

    Args:
        dir_path: 包含XML标注文件的目录路径
        old_label: 需要替换的旧标签名
        new_label: 替换后的新标签名

    Returns:
        None
    """
    _check_dependency()
    if hasattr(ruiming, 'change_label_in_xml'):
        ruiming.change_label_in_xml(dir_path, old_label, new_label)
    else:
        print(f"修改标签：{dir_path}，{old_label} -> {new_label}")


def screen_without_label_json_file(dir_path):
    """筛选无标注的JSON文件。

    Args:
        dir_path: 包含JSON标注文件的目录路径

    Returns:
        None
    """
    _check_dependency()
    if hasattr(ruiming, 'screen_without_label_json_file'):
        ruiming.screen_without_label_json_file(dir_path)
    else:
        print(f"筛选无标注JSON文件：{dir_path}")


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("锐明数据处理工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  screen_unmarked_image         - 筛选未标注的图片")
        print("  change_label_in_xml           - 修改XML标注标签")
        print("  screen_without_label_json_file - 筛选无标注JSON文件")
        print("\n使用方式：python ruiming.py <功能名> [参数...]")
        print("示例：python ruiming.py screen_unmarked_image ./data_dir")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "screen_unmarked_image" and len(args) >= 1:
            screen_unmarked_image(dir_path=args[0])
            print(f"筛选完成：{args[0]}")
        elif cmd == "change_label_in_xml" and len(args) >= 3:
            change_label_in_xml(dir_path=args[0], old_label=args[1], new_label=args[2])
            print(f"标签修改完成：{args[1]} -> {args[2]}")
        elif cmd == "screen_without_label_json_file" and len(args) >= 1:
            screen_without_label_json_file(dir_path=args[0])
            print(f"筛选完成：{args[0]}")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python ruiming.py <功能名> [参数...]")
    except Exception as e:
        print(f"操作失败：{e}")
