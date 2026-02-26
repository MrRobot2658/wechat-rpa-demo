"""
微信 Android RPA Bot
基于 uiautomator2 实现微信的自动化收发消息。
"""
import time
from typing import Optional
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.base_bot import BaseBot, Message
from common.utils import human_delay, setup_logger
from config.settings import (
    WECHAT_PACKAGE,
    WECHAT_IDS,
    DELAY_AFTER_CLICK,
    DELAY_AFTER_INPUT,
    DELAY_AFTER_SEARCH,
    DELAY_AFTER_SEND,
    DELAY_PAGE_LOAD,
    MSG_POLL_INTERVAL,
    MAX_RETRY,
)

logger = setup_logger("WeChatBot")


class WeChatBot(BaseBot):
    """
    微信 RPA 机器人。

    功能：
    - 搜索并打开与指定联系人的聊天窗口
    - 发送文本消息
    - 读取聊天窗口中的最新消息
    - 消息轮询监听（简单的新消息检测）
    """

    def __init__(self, device_serial: Optional[str] = None):
        super().__init__(device_serial)
        self.package_name = WECHAT_PACKAGE
        self.ids = WECHAT_IDS
        self._last_messages: list[str] = []  # 缓存上次读取的消息，用于检测新消息

    # ============================================================
    # 启动与初始化
    # ============================================================

    def start(self) -> bool:
        """
        启动微信 Bot：连接设备 -> 启动微信 -> 确认进入主界面。

        Returns:
            是否成功启动
        """
        logger.info("=" * 50)
        logger.info("微信 RPA Bot 启动中...")
        logger.info("=" * 50)

        # 1. 连接设备
        if not self.connect():
            return False

        # 2. 启动微信
        if not self.launch_app():
            return False

        # 3. 等待主界面加载（检查底部Tab是否出现）
        logger.info("等待微信主界面加载...")
        if self.element_exists(text=self.ids["tab_chat"], timeout=10):
            logger.info("微信主界面已加载完成")
            return True
        else:
            logger.warning("微信主界面加载超时，尝试继续...")
            return True

    # ============================================================
    # 导航操作
    # ============================================================

    def go_to_chat_tab(self) -> bool:
        """切换到"微信"（聊天列表）Tab"""
        logger.info("切换到聊天列表Tab")
        return self.find_and_click(text=self.ids["tab_chat"], delay_after=DELAY_AFTER_CLICK)

    def search_contact(self, contact_name: str) -> bool:
        """
        搜索联系人并打开聊天窗口。

        Args:
            contact_name: 联系人名称（必须与微信中显示的完全一致）

        Returns:
            是否成功打开聊天窗口
        """
        logger.info(f"搜索联系人: {contact_name}")

        for attempt in range(MAX_RETRY):
            try:
                # 确保在主界面
                if not self.is_app_running():
                    self.launch_app()

                # 方式1: 通过 resource-id 点击搜索按钮
                search_clicked = self.find_and_click(
                    resource_id=self.ids["search_btn"],
                    timeout=5,
                    delay_after=DELAY_AFTER_CLICK,
                )

                # 方式2: 如果 resource-id 失效，尝试通过 description 定位
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

                # 在搜索框中输入联系人名称
                input_success = self.find_and_input(
                    text_to_input=contact_name,
                    resource_id=self.ids["search_input"],
                    timeout=5,
                )

                # 备选方案：通过 className 定位输入框
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

                # 点击搜索结果中的联系人
                contact_clicked = self.find_and_click(
                    text=contact_name,
                    timeout=8,
                    delay_after=DELAY_PAGE_LOAD,
                )

                if contact_clicked:
                    logger.info(f"已打开与 '{contact_name}' 的聊天窗口")
                    return True
                else:
                    logger.warning(f"未找到联系人: {contact_name}")
                    self.press_back()
                    self.press_back()
                    continue

            except Exception as e:
                logger.error(f"搜索联系人异常: {e}")
                self.press_back()

        logger.error(f"搜索联系人失败，已重试 {MAX_RETRY} 次: {contact_name}")
        return False

    # ============================================================
    # 发送消息
    # ============================================================

    def send_message(self, contact_name: str, message: str) -> bool:
        """
        向指定联系人发送文本消息。

        Args:
            contact_name: 联系人名称
            message: 要发送的消息文本

        Returns:
            是否发送成功
        """
        logger.info(f"准备发送消息给 '{contact_name}': {message[:50]}...")

        # 1. 搜索并打开聊天窗口
        if not self.search_contact(contact_name):
            return False

        # 2. 定位输入框并输入消息
        input_success = self.find_and_input(
            text_to_input=message,
            resource_id=self.ids["chat_input"],
            timeout=8,
        )

        # 备选：通过 className 定位
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

        # 3. 点击发送按钮
        send_success = self.find_and_click(
            resource_id=self.ids["chat_send_btn"],
            timeout=5,
            delay_after=DELAY_AFTER_SEND,
        )

        # 备选：通过 text 定位发送按钮
        if not send_success:
            send_success = self.find_and_click(
                text="发送",
                timeout=5,
                delay_after=DELAY_AFTER_SEND,
            )

        if send_success:
            logger.info(f"消息已发送给 '{contact_name}': {message[:50]}...")
            return True
        else:
            logger.error("发送按钮点击失败")
            return False

    # ============================================================
    # 接收消息
    # ============================================================

    def read_latest_messages(self, count: int = 10) -> list[Message]:
        """
        读取当前聊天窗口中的最新消息。

        注意：此方法要求已经打开了聊天窗口。

        Args:
            count: 最多读取的消息条数

        Returns:
            消息列表
        """
        logger.info(f"读取最新 {count} 条消息...")
        messages = []

        if self._u2 is None:
            # 模拟模式：返回模拟数据
            for i in range(min(count, 3)):
                messages.append(Message(
                    sender="模拟联系人",
                    content=f"[模拟模式] 这是第 {i + 1} 条模拟消息",
                    timestamp=datetime.now().strftime("%H:%M"),
                    is_self=False,
                    msg_type="text",
                ))
            return messages

        try:
            # 方式1: 通过 resource-id 获取消息文本
            msg_elements = self.device(resourceId=self.ids["msg_text"])

            if msg_elements.exists:
                elements_info = msg_elements.info if hasattr(msg_elements, 'info') else []

                # 使用 XPath 获取所有消息文本节点
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

            # 方式2: 如果 resource-id 失效，尝试通过 className 获取
            if not messages:
                text_views = self.device.xpath(
                    '//android.widget.TextView'
                ).all()

                for tv in text_views[-count * 2:]:
                    text = tv.text or ""
                    # 过滤系统文本（时间、按钮文字等）
                    if (text.strip()
                        and len(text) > 1
                        and text not in ["发送", "微信", "通讯录", "发现", "我",
                                        "按住 说话", "切换到键盘", "更多功能"]):
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
        """
        检测是否有新消息（与上次读取对比）。

        Returns:
            新消息列表
        """
        current_messages = self.read_latest_messages(count=20)
        current_texts = [m.content for m in current_messages]

        new_messages = []
        for msg in current_messages:
            if msg.content not in self._last_messages:
                new_messages.append(msg)

        self._last_messages = current_texts

        if new_messages:
            logger.info(f"检测到 {len(new_messages)} 条新消息")
        return new_messages

    # ============================================================
    # 消息监听循环
    # ============================================================

    def listen_and_reply(
        self,
        contact_name: str,
        reply_handler=None,
        poll_interval: float = None,
    ):
        """
        监听指定联系人的消息并自动回复。

        Args:
            contact_name: 要监听的联系人名称
            reply_handler: 回复处理函数，接收 Message 返回回复文本（或 None 不回复）
            poll_interval: 轮询间隔（秒）
        """
        if poll_interval is None:
            poll_interval = MSG_POLL_INTERVAL

        logger.info(f"开始监听 '{contact_name}' 的消息 (间隔: {poll_interval}s)")
        logger.info("按 Ctrl+C 停止监听")

        # 打开聊天窗口
        if not self.search_contact(contact_name):
            logger.error(f"无法打开与 '{contact_name}' 的聊天窗口")
            return

        # 初始化消息缓存
        self._last_messages = [m.content for m in self.read_latest_messages(20)]

        try:
            while True:
                time.sleep(poll_interval)

                # 检查新消息
                new_messages = self.check_new_messages()

                for msg in new_messages:
                    logger.info(f"收到新消息: {msg.content}")

                    # 调用回复处理器
                    if reply_handler:
                        reply_text = reply_handler(msg)
                        if reply_text:
                            # 在当前聊天窗口直接发送回复
                            self._send_in_current_chat(reply_text)

        except KeyboardInterrupt:
            logger.info("监听已停止")

    def _send_in_current_chat(self, message: str) -> bool:
        """
        在当前已打开的聊天窗口中发送消息（无需重新搜索联系人）。

        Args:
            message: 要发送的消息文本

        Returns:
            是否发送成功
        """
        # 输入消息
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
            logger.error("在当前聊天窗口输入消息失败")
            return False

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

        return send_success

    # ============================================================
    # 调试辅助
    # ============================================================

    def debug_dump_chat_ui(self, save_path: str = "wechat_chat_ui.xml"):
        """导出当前聊天界面的控件树，用于调试和确认 resource-id"""
        logger.info("导出微信聊天界面控件树...")
        self.dump_hierarchy(save_path)
        self.take_screenshot("wechat_chat_screenshot.png")
        logger.info(f"控件树: {save_path} | 截图: wechat_chat_screenshot.png")
        logger.info("请使用 weditor 或查看 XML 文件确认控件的 resource-id")
