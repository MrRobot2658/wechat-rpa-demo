#!/usr/bin/env python3
"""
企业微信 Android RPA Demo - 收发消息演示

使用方法:
    1. 确保 Android 设备已通过 USB 连接并开启 USB 调试
    2. 确保企业微信已登录
    3. 运行: python demo_wework.py

功能演示:
    - 发送消息给指定联系人/群组
    - 读取聊天窗口最新消息
    - 监听消息并自动回复
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wework.wework_bot import WeWorkBot
from common.base_bot import Message
from common.utils import setup_logger

logger = setup_logger("WeWorkDemo")


def simple_reply_handler(msg: Message) -> str:
    """简单的自动回复处理器"""
    content = msg.content.lower()

    rules = {
        "你好": "你好！我是企业微信 RPA 机器人。",
        "hello": "Hello! I'm a WeWork RPA bot.",
        "在吗": "在的，请问有什么事？",
        "时间": f"当前时间是: {msg.timestamp}",
        "帮助": "支持的命令:\n- 你好\n- 时间\n- 帮助",
    }

    for keyword, reply in rules.items():
        if keyword in content:
            return reply

    return f"[自动回复] 已收到: {msg.content[:30]}"


def demo_send_message():
    """演示: 发送消息"""
    logger.info("=" * 60)
    logger.info("Demo 1: 企业微信发送消息")
    logger.info("=" * 60)

    bot = WeWorkBot()

    if not bot.start():
        logger.error("Bot 启动失败")
        return

    # 发送消息（请替换为实际的联系人名称）
    success = bot.send_message(
        contact_name="文件传输助手",  # 企业微信也有文件传输助手
        message="你好，这是来自企业微信 RPA Bot 的测试消息！"
    )

    if success:
        logger.info("✅ 消息发送成功！")
    else:
        logger.error("❌ 消息发送失败")


def demo_read_messages():
    """演示: 读取消息"""
    logger.info("=" * 60)
    logger.info("Demo 2: 企业微信读取最新消息")
    logger.info("=" * 60)

    bot = WeWorkBot()

    if not bot.start():
        logger.error("Bot 启动失败")
        return

    if bot.search_contact("文件传输助手"):
        messages = bot.read_latest_messages(count=5)

        logger.info(f"\n最新 {len(messages)} 条消息:")
        for i, msg in enumerate(messages, 1):
            logger.info(f"  [{i}] {msg.content}")


def demo_listen_and_reply():
    """演示: 监听消息并自动回复"""
    logger.info("=" * 60)
    logger.info("Demo 3: 企业微信监听消息并自动回复")
    logger.info("=" * 60)

    bot = WeWorkBot()

    if not bot.start():
        logger.error("Bot 启动失败")
        return

    bot.listen_and_reply(
        contact_name="文件传输助手",
        reply_handler=simple_reply_handler,
        poll_interval=3,
    )


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════╗
║      企业微信 Android RPA Demo - 收发消息演示       ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  请选择演示功能:                                     ║
║                                                      ║
║  1. 发送消息                                         ║
║  2. 读取最新消息                                     ║
║  3. 监听消息并自动回复 (Ctrl+C 停止)                 ║
║  0. 退出                                             ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
    """)

    choice = input("请输入选项 (0-3): ").strip()

    demos = {
        "1": demo_send_message,
        "2": demo_read_messages,
        "3": demo_listen_and_reply,
    }

    if choice == "0":
        print("再见！")
    elif choice in demos:
        demos[choice]()
    else:
        print("无效选项")
