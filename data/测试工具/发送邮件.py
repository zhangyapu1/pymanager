# -*- coding: utf-8 -*-
"""
邮件发送功能演示模块

提供邮件发送功能演示，展示如何使用python-office发送邮件。

使用方式：python 发送邮件.py
注意：此脚本为演示脚本，需要配置真实邮箱信息后才能发送邮件。
"""

import poemail
from poemail.lib.Const import Mail_Type


def send_email(key, msg_from, msg_to, msg_subject='', content='', host=Mail_Type['qq'], port=465):
    """发送邮件。

    Args:
        key: 邮箱授权码（非登录密码）
        msg_from: 发件人邮箱地址
        msg_to: 收件人邮箱地址
        msg_subject: 邮件主题，默认为空
        content: 邮件内容，默认为空
        host: 邮箱服务器地址，默认为QQ邮箱
        port: 邮箱服务器端口号，默认为465

    Returns:
        None
    """
    poemail.send.send_email(
        key=key,
        msg_from=msg_from,
        msg_to=msg_to,
        msg_subject=msg_subject,
        content=content,
        host=host,
        port=port
    )


if __name__ == "__main__":
    print("=" * 50)
    print("邮件发送功能演示")
    print("=" * 50)

    print("\n使用说明：")
    print("1. 需要先配置邮箱的SMTP服务")
    print("2. 获取邮箱授权码（非登录密码）")
    print("3. 使用 email.py 脚本发送邮件：")
    print("   python email.py send_email <授权码> <发件人> <收件人> <主题> <内容>")
    print("\n示例配置：")
    print("   授权码：your_email_password")
    print("   发件人：your_email@qq.com")
    print("   收件人：recipient@example.com")
    print("   主题：测试邮件")
    print("   内容：这是一封测试邮件")

    print("\n相关资源：")
    print("  项目官网：https://www.python-office.com")
    print("  交流群：https://www.python4office.cn/wechat-group")
