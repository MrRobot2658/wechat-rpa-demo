#!/usr/bin/env python3
"""
微信 Android RPA Demo - 收发消息演示

使用方法:
    1. 确保 Android 设备已通过 USB 连接并开启 USB 调试
    2. 确保微信已登录
    3. 运行: python demo_wechat.py

功能演示:
    - 发送消息给指定联系人
    - 读取聊天窗口最新消息
    - 监听消息并自动回复
"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wechat.wechat_bot import WeChatBot
from common.base_bot import Message
from common.utils import setup_logger

logger = setup_logger("WeChatDemo")


def simple_reply_handler(msg: Message) -> str:
    """
    简单的自动回复处理器。
    收到消息后，根据关键词返回回复内容。

    Args:
        msg: 收到的消息

    Returns:
        回复文本，返回 None 表示不回复
    """
    content = msg.content.lower()

    # 关键词回复规则
    rules = {
        "你好": "你好！我是 RPA 机器人，有什么可以帮你的吗？",
        "hello": "Hello! I'm an RPA bot. How can I help you?",
        "在吗": "在的，请问有什么事？",
        "时间": f"当前时间是: {msg.timestamp}",
        "帮助": "支持的命令:\n- 你好: 打招呼\n- 时间: 查看当前时间\n- 帮助: 查看帮助",
    }

    for keyword, reply in rules.items():
        if keyword in content:
            return reply

    # 默认回复（可以设为 None 不回复）
    return f"[自动回复] 已收到你的消息: {msg.content[:30]}"


def demo_send_message():
    """演示: 发送消息"""
    logger.info("=" * 60)
    logger.info("Demo 1: 发送消息")
    logger.info("=" * 60)

    bot = WeChatBot()

    # 启动 Bot
    if not bot.start():
        logger.error("Bot 启动失败")
        return

    # 发送消息给"文件传输助手"（安全的测试对象）
    success = bot.send_message(
        contact_name="文件传输助手",
        message="你好，这是来自 RPA Bot 的测试消息！🤖"
    )

    if success:
        logger.info("✅ 消息发送成功！")
    else:
        logger.error("❌ 消息发送失败")


def demo_read_messages():
    """演示: 读取消息"""
    logger.info("=" * 60)
    logger.info("Demo 2: 读取最新消息")
    logger.info("=" * 60)

    bot = WeChatBot()

    if not bot.start():
        logger.error("Bot 启动失败")
        return

    # 打开与"文件传输助手"的聊天窗口
    if bot.search_contact("文件传输助手"):
        # 读取最新消息
        messages = bot.read_latest_messages(count=5)

        logger.info(f"\n{'=' * 40}")
        logger.info(f"最新 {len(messages)} 条消息:")
        logger.info(f"{'=' * 40}")

        for i, msg in enumerate(messages, 1):
            logger.info(f"  [{i}] {msg.sender or '未知'}: {msg.content}")

        logger.info(f"{'=' * 40}")


def demo_listen_and_reply():
    """演示: 监听消息并自动回复"""
    logger.info("=" * 60)
    logger.info("Demo 3: 监听消息并自动回复")
    logger.info("=" * 60)

    bot = WeChatBot()

    if not bot.start():
        logger.error("Bot 启动失败")
        return

    # 监听"文件传输助手"的消息（按 Ctrl+C 停止）
    bot.listen_and_reply(
        contact_name="文件传输助手",
        reply_handler=simple_reply_handler,
        poll_interval=3,
    )


def demo_debug_ui():
    """演示: 调试 - 导出UI控件树"""
    logger.info("=" * 60)
    logger.info("Demo 4: 导出UI控件树（调试用）")
    logger.info("=" * 60)

    bot = WeChatBot()

    if not bot.start():
        logger.error("Bot 启动失败")
        return

    if bot.search_contact("文件传输助手"):
        bot.debug_dump_chat_ui()
        logger.info("请查看生成的 XML 和截图文件来确认控件 resource-id")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════╗
║        微信 Android RPA Demo - 收发消息演示         ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  请选择演示功能:                                     ║
║                                                      ║
║  1. 发送消息 (给文件传输助手)                        ║
║  2. 读取最新消息                                     ║
║  3. 监听消息并自动回复 (Ctrl+C 停止)                 ║
║  4. 导出UI控件树 (调试用)                            ║
║  0. 退出                                             ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
    """)

    choice = input("请输入选项 (0-4): ").strip()

    demos = {
        "1": demo_send_message,
        "2": demo_read_messages,
        "3": demo_listen_and_reply,
        "4": demo_debug_ui,
    }

    if choice == "0":
        print("再见！")
    elif choice in demos:
        demos[choice]()
    else:
        print("无效选项，请重新运行")
