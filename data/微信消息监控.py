#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信消息监控 - 监控微信数据库并发送 Windows 通知

使用方式：
    python 微信消息监控.py

依赖：
    pip install plyer

微信数据库路径（自动检测）：
    %APPDATA%\Tencent\WeChat\<随机>\MicroMsg.db

也可以手动指定路径：
    python 微信消息监控.py "C:\path\to\MicroMsg.db"

通知内容：
    - 发送者昵称
    - 消息内容
    - 通知时间
"""

import os
import sys
import time
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from collections import deque

try:
    from plyer import notification
    HAS_NOTIFIER = True
except ImportError:
    HAS_NOTIFIER = False
    print("[警告] 未安装 plyer，正在安装...")
    os.system(f"{sys.executable} -m pip install plyer")
    try:
        from plyer import notification
        HAS_NOTIFIER = True
    except ImportError:
        print("[错误] plyer 安装失败，请手动安装：pip install plyer")
        sys.exit(1)


def get_wechat_db_path():
    """获取微信数据库路径"""
    appdata = os.environ.get('APPDATA', '')
    wechat_base = Path(appdata) / 'Tencent' / 'WeChat'

    if not wechat_base.exists():
        return None

    for folder in wechat_base.iterdir():
        if folder.is_dir() and len(folder.name) == 32:
            db_path = folder / 'MicroMsg.db'
            if db_path.exists():
                return str(db_path)

    return None


def init_database(db_path):
    """初始化数据库连接"""
    try:
        conn = sqlite3.connect(db_path, timeout=1.0)
        conn.set_trace_callback(None)
        return conn
    except sqlite3.Error as e:
        print(f"[错误] 数据库连接失败: {e}")
        return None


def get_latest_messages(conn, last_id=0, limit=10):
    """获取最新消息"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.msgId, m.msgServerId, c.nickname, m.strContent, m.CreateTime
            FROM MSG m
            LEFT JOIN Contact c ON m.strTalker = c.strUsrName
            WHERE m.msgId > ?
            ORDER BY m.msgId DESC
            LIMIT ?
        """, (last_id, limit))

        messages = []
        for row in cursor.fetchall():
            msg_id, server_id, nickname, content, create_time = row
            if content and nickname:
                messages.append({
                    'id': msg_id,
                    'server_id': server_id or 0,
                    'nickname': nickname or '未知',
                    'content': content,
                    'time': create_time
                })

        return messages
    except sqlite3.Error as e:
        print(f"[错误] 查询消息失败: {e}")
        return []


def parse_timestamp(timestamp):
    """解析时间戳"""
    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime('%H:%M:%S')
    except:
        return ''


def send_notification(sender, content, timestamp=''):
    """发送 Windows 通知"""
    if not HAS_NOTIFIER:
        print(f"[通知] {sender} ({timestamp}): {content}")
        return

    try:
        title = f"💬 微信消息 - {sender}"
        message = content[:100] + ('...' if len(content) > 100 else '')

        notification.notify(
            title=title,
            message=message,
            app_name='PyManager',
            timeout=10
        )
        print(f"[通知已发送] {sender}: {content[:50]}...")
    except Exception as e:
        print(f"[错误] 通知发送失败: {e}")


def is_group_message(nickname):
    """判断是否为群消息"""
    return nickname.endswith('（群）') or '群' in nickname


def is_self_message(content, nickname):
    """判断是否为自己的消息（排除自己发的）"""
    return False


class WeChatMonitor:
    def __init__(self, db_path=None):
        self.db_path = db_path or get_wechat_db_path()
        self.conn = None
        self.last_msg_id = 0
        self.running = False
        self.message_history = deque(maxlen=100)
        self.check_interval = 2.0

        if not self.db_path:
            print("[错误] 未找到微信数据库，请确保微信已安装并登录过")
            sys.exit(1)

        print(f"[信息] 微信数据库: {self.db_path}")

    def connect(self):
        """连接到数据库"""
        self.conn = init_database(self.db_path)
        if self.conn:
            messages = get_latest_messages(self.conn, 0, 1)
            if messages:
                self.last_msg_id = messages[0]['id']
                print(f"[信息] 已同步最新消息 ID: {self.last_msg_id}")
            return True
        return False

    def check_new_messages(self):
        """检查新消息"""
        if not self.conn:
            return

        messages = get_latest_messages(self.conn, self.last_msg_id, 20)

        new_messages = []
        for msg in reversed(messages):
            if msg['id'] > self.last_msg_id:
                new_messages.append(msg)
                self.last_msg_id = max(self.last_msg_id, msg['id'])

        return new_messages

    def handle_message(self, msg):
        """处理单条消息"""
        sender = msg['nickname']
        content = msg['content']
        timestamp = parse_timestamp(msg['time'])

        msg_key = f"{msg['server_id']}_{content}"
        if msg_key in self.message_history:
            return

        self.message_history.add(msg_key)

        if not is_self_message(content, sender):
            print(f"[新消息] {sender} ({timestamp}): {content}")
            send_notification(sender, content, timestamp)

    def monitor_loop(self):
        """监控循环"""
        print("[信息] 开始监控微信消息...")
        print("[提示] 按 Ctrl+C 停止监控")

        while self.running:
            try:
                new_messages = self.check_new_messages()
                if new_messages:
                    for msg in new_messages:
                        self.handle_message(msg)

                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\n[信息] 收到停止信号，正在关闭...")
                self.stop()
                break
            except Exception as e:
                print(f"[错误] 监控异常: {e}")
                time.sleep(5)

                self.conn = init_database(self.db_path)
                if not self.conn:
                    print("[错误] 数据库重连失败，退出")
                    break

    def start(self):
        """启动监控"""
        if not self.connect():
            sys.exit(1)

        self.running = True
        self.monitor_loop()

    def stop(self):
        """停止监控"""
        self.running = False
        if self.conn:
            self.conn.close()
            self.conn = None
        print("[信息] 监控已停止")


def main():
    print("=" * 60)
    print("  微信消息监控工具")
    print("=" * 60)

    db_path = get_wechat_db_path()
    if not db_path:
        print("[错误] 无法找到微信数据库")
        print("[提示] 请确保：")
        print("  1. 微信已安装")
        print("  2. 微信已登录过")
        print("  3. 微信数据库文件存在")
        sys.exit(1)

    monitor = WeChatMonitor(db_path)

    try:
        monitor.start()
    except KeyboardInterrupt:
        monitor.stop()
        print("[信息] 程序已退出")


if __name__ == "__main__":
    main()
