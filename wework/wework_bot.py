"""
企业微信 Android RPA Bot
基于 uiautomator2 实现企业微信的自动化收发消息。
"""
import time
from typing import Optional
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.base_bot import BaseBot, Message
from common.utils import human_delay, setup_logger
from config.settings import (
    WEWORK_PACKAGE,
    WEWORK_IDS,
    DELAY_AFTER_CLICK,
    DELAY_AFTER_INPUT,
    DELAY_AFTER_SEARCH,
    DELAY_AFTER_SEND,
    DELAY_PAGE_LOAD,
    MSG_POLL_INTERVAL,
    MAX_RETRY,
)

logger = setup_logger("WeWorkBot")


class WeWorkBot(BaseBot):
    """
    企业微信 RPA 机器人。

    功能：
    - 搜索并打开与指定联系人/群组的聊天窗口
    - 发送文本消息
    - 读取聊天窗口中的最新消息
    - 消息轮询监听
    """

    def __init__(self, device_serial: Optional[str] = None):
        super().__init__(device_serial)
        self.package_name = WEWORK_PACKAGE
        self.ids = WEWORK_IDS
        self._last_messages: list[str] = []

    # ============================================================
    # 启动与初始化
    # ============================================================

    def start(self) -> bool:
        """启动企业微信 Bot"""
        logger.info("=" * 50)
        logger.info("企业微信 RPA Bot 启动中...")
        logger.info("=" * 50)

        if not self.connect():
            return False

        if not self.launch_app():
            return False

        # 等待主界面加载
        logger.info("等待企业微信主界面加载...")
        if self.element_exists(text=self.ids["tab_msg"], timeout=15):
            logger.info("企业微信主界面已加载完成")
            return True
        else:
            logger.warning("企业微信主界面加载超时，尝试继续...")
            return True

    # ============================================================
    # 导航操作
    # ============================================================

    def go_to_msg_tab(self) -> bool:
        """切换到"消息"Tab"""
        logger.info("切换到消息列表Tab")
        return self.find_and_click(text=self.ids["tab_msg"], delay_after=DELAY_AFTER_CLICK)

    def search_contact(self, contact_name: str) -> bool:
        """
        搜索联系人/群组并打开聊天窗口。

        Args:
            contact_name: 联系人或群组名称

        Returns:
            是否成功打开聊天窗口
        """
        logger.info(f"搜索联系人/群组: {contact_name}")

        for attempt in range(MAX_RETRY):
            try:
                if not self.is_app_running():
                    self.launch_app()

                # 点击搜索按钮
                search_clicked = self.find_and_click(
                    resource_id=self.ids["search_btn"],
                    timeout=5,
                    delay_after=DELAY_AFTER_CLICK,
                )

                if not search_clicked:
                    search_clicked = self.find_and_click(
                        description="搜索",
                        timeout=5,
                        delay_after=DELAY_AFTER_CLICK,
                    )

                if not search_clicked:
                    logger.warning(f"搜索按钮点击失败 (尝试 {attempt + 1}/{MAX_RETRY})")
                    self.press_back()
                    human_delay([1.0, 2.0])
                    continue

                # 输入搜索关键词
                input_success = self.find_and_input(
                    text_to_input=contact_name,
                    resource_id=self.ids["search_input"],
                    timeout=5,
                )

                if not input_success:
                    input_success = self.find_and_input(
                        text_to_input=contact_name,
                        class_name="android.widget.EditText",
                        timeout=5,
                    )

                if not input_success:
                    logger.warning("搜索输入失败")
                    self.press_back()
                    continue

                human_delay(DELAY_AFTER_SEARCH)

                # 点击搜索结果
                contact_clicked = self.find_and_click(
                    text=contact_name,
                    timeout=8,
                    delay_after=DELAY_PAGE_LOAD,
                )

                if contact_clicked:
                    logger.info(f"已打开与 '{contact_name}' 的聊天窗口")
                    return True
                else:
                    logger.warning(f"未找到联系人/群组: {contact_name}")
                    self.press_back()
                    self.press_back()
                    continue

            except Exception as e:
                logger.error(f"搜索联系人异常: {e}")
                self.press_back()

        logger.error(f"搜索联系人失败: {contact_name}")
        return False

    # ============================================================
    # 发送消息
    # ============================================================

    def send_message(self, contact_name: str, message: str) -> bool:
        """向指定联系人/群组发送文本消息"""
        logger.info(f"准备发送消息给 '{contact_name}': {message[:50]}...")

        if not self.search_contact(contact_name):
            return False

        # 输入消息
        input_success = self.find_and_input(
            text_to_input=message,
            resource_id=self.ids["chat_input"],
            timeout=8,
        )

        if not input_success:
            input_success = self.find_and_input(
                text_to_input=message,
                class_name="android.widget.EditText",
                timeout=5,
            )

        if not input_success:
            logger.error("消息输入失败")
            return False

        human_delay(DELAY_AFTER_INPUT)

        # 点击发送
        send_success = self.find_and_click(
            resource_id=self.ids["chat_send_btn"],
            timeout=5,
            delay_after=DELAY_AFTER_SEND,
        )

        if not send_success:
            send_success = self.find_and_click(
                text="发送",
                timeout=5,
                delay_after=DELAY_AFTER_SEND,
            )

        if send_success:
            logger.info(f"消息已发送给 '{contact_name}'")
            return True
        else:
            logger.error("发送按钮点击失败")
            return False

    # ============================================================
    # 接收消息
    # ============================================================

    def read_latest_messages(self, count: int = 10) -> list[Message]:
        """读取当前聊天窗口中的最新消息"""
        logger.info(f"读取最新 {count} 条消息...")
        messages = []

        if self._u2 is None:
            for i in range(min(count, 3)):
                messages.append(Message(
                    sender="模拟同事",
                    content=f"[模拟模式] 企业微信消息 {i + 1}",
                    timestamp=datetime.now().strftime("%H:%M"),
                    is_self=False,
                    msg_type="text",
                ))
            return messages

        try:
            # 通过 resource-id 获取消息
            msg_nodes = self.device.xpath(
                f'//*[@resource-id="{self.ids["msg_text"]}"]'
            ).all()

            for node in msg_nodes[-count:]:
                text = node.text or ""
                if text.strip():
                    msg = Message(
                        content=text.strip(),
                        timestamp=datetime.now().strftime("%H:%M"),
                        msg_type="text",
                    )
                    messages.append(msg)

            # 备选方案
            if not messages:
                text_views = self.device.xpath('//android.widget.TextView').all()
                for tv in text_views[-count * 2:]:
                    text = tv.text or ""
                    if (text.strip()
                        and len(text) > 1
                        and text not in ["发送", "消息", "通讯录", "工作台", "我",
                                        "按住 说话", "更多"]):
                        msg = Message(
                            content=text.strip(),
                            timestamp=datetime.now().strftime("%H:%M"),
                            msg_type="text",
                        )
                        messages.append(msg)

            logger.info(f"读取到 {len(messages)} 条消息")

        except Exception as e:
            logger.error(f"读取消息失败: {e}")

        return messages[-count:]

    def check_new_messages(self) -> list[Message]:
        """检测新消息"""
        current_messages = self.read_latest_messages(count=20)
        current_texts = [m.content for m in current_messages]

        new_messages = [
            msg for msg in current_messages
            if msg.content not in self._last_messages
        ]

        self._last_messages = current_texts

        if new_messages:
            logger.info(f"检测到 {len(new_messages)} 条新消息")
        return new_messages

    def listen_and_reply(
        self,
        contact_name: str,
        reply_handler=None,
        poll_interval: float = None,
    ):
        """监听指定联系人的消息并自动回复"""
        if poll_interval is None:
            poll_interval = MSG_POLL_INTERVAL

        logger.info(f"开始监听 '{contact_name}' 的消息 (间隔: {poll_interval}s)")

        if not self.search_contact(contact_name):
            logger.error(f"无法打开与 '{contact_name}' 的聊天窗口")
            return

        self._last_messages = [m.content for m in self.read_latest_messages(20)]

        try:
            while True:
                time.sleep(poll_interval)
                new_messages = self.check_new_messages()

                for msg in new_messages:
                    logger.info(f"收到新消息: {msg.content}")
                    if reply_handler:
                        reply_text = reply_handler(msg)
                        if reply_text:
                            self._send_in_current_chat(reply_text)

        except KeyboardInterrupt:
            logger.info("监听已停止")

    def _send_in_current_chat(self, message: str) -> bool:
        """在当前聊天窗口发送消息"""
        input_success = self.find_and_input(
            text_to_input=message,
            resource_id=self.ids["chat_input"],
            timeout=5,
        )
        if not input_success:
            input_success = self.find_and_input(
                text_to_input=message,
                class_name="android.widget.EditText",
                timeout=5,
            )

        if not input_success:
            return False

        send_success = self.find_and_click(
            resource_id=self.ids["chat_send_btn"],
            timeout=5,
            delay_after=DELAY_AFTER_SEND,
        )
        if not send_success:
            send_success = self.find_and_click(
                text="发送",
                timeout=5,
                delay_after=DELAY_AFTER_SEND,
            )

        return send_success

    def debug_dump_chat_ui(self, save_path: str = "wework_chat_ui.xml"):
        """导出当前聊天界面的控件树"""
        logger.info("导出企业微信聊天界面控件树...")
        self.dump_hierarchy(save_path)
        self.take_screenshot("wework_chat_screenshot.png")
