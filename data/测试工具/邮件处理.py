# -*- coding:utf-8 -*-
"""
Email functionality module.

邮件功能模块。

This module provides email sending and receiving capabilities.

该模块提供了邮件发送和接收功能。

Author:
    程序员晚枫

Project:
    https://www.python-office.com
"""

import poemail
from poemail.lib.Const import Mail_Type


def send_email(key, msg_from, msg_to, msg_cc=None, attach_files=[], msg_subject='', content='', host=Mail_Type['qq'],
               port=465):
    """
    自动发送邮件

    参数:
    key (str): 邮箱账户密钥
    msg_from (str): 发件人邮箱地址
    msg_to (str): 收件人邮箱地址
    msg_cc (str, 可选): 抄送人邮箱地址
    attach_files (list, 可选): 邮件附件路径列表，默认为空列表
    msg_subject (str, 可选): 邮件主题，默认为空字符串
    content (str, 可选): 邮件内容，默认为空字符串
    host (str, 可选): 邮箱服务器地址，默认为'qq'
    port (int, 可选): 邮箱服务器端口号，默认为465

    返回:
    无

    """
    poemail.send.send_email(key=key,
                            msg_from=msg_from,
                            msg_to=msg_to,
                            msg_cc=msg_cc,
                            msg_subject=msg_subject,
                            host=host,
                            port=port)


def receive_email(key, msg_from, msg_to, output_path=r'./', status="UNSEEN", msg_subject='', content='',
                  host=Mail_Type['qq'], port=465):
    """
    自动接收邮件

    参数:
    key (str): 邮箱账户密钥
    msg_from (str): 发件人邮箱地址
    msg_to (str): 收件人邮箱地址
    output_path (str, 可选): 附件保存路径，默认为当前目录
    status (str, 可选): 邮件状态筛选，默认为"UNSEEN"（未读）
    msg_subject (str, 可选): 邮件主题筛选，默认为空
    content (str, 可选): 邮件内容筛选，默认为空
    host (str, 可选): 邮箱服务器地址，默认为'qq'
    port (int, 可选): 邮箱服务器端口号，默认为465

    返回:
    无

    """
    poemail.receive.receive_email(key=key,
                                  msg_from=msg_from,
                                  msg_to=msg_to,
                                  msg_subject=msg_subject,
                                  host=host,
                                  port=port, output_path=output_path, status=status)


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("邮件处理工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n可用功能：")
        print("  send_email    - 发送邮件")
        print("  receive_email - 接收邮件")
        print("\n使用方式：python email.py <功能名> [参数...]")
        print("示例：python email.py send_email <授权码> <发件人> <收件人> <主题> <内容>")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "send_email" and len(args) >= 5:
            send_email(
                key=args[0],
                msg_from=args[1],
                msg_to=args[2],
                msg_subject=args[3],
                content=args[4]
            )
            print(f"邮件已发送给：{args[2]}")
        elif cmd == "receive_email" and len(args) >= 3:
            output_path = args[3] if len(args) > 3 else './'
            receive_email(
                key=args[0],
                msg_from=args[1],
                msg_to=args[2],
                output_path=output_path
            )
            print("邮件接收完成")
        else:
            print(f"未知功能或参数不足：{cmd}")
            print("使用方式：python email.py <功能名> [参数...]")
    except Exception as e:
        print(f"操作失败：{e}")
