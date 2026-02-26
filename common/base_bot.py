"""
RPA 机器人基类
封装 uiautomator2 的通用操作，提供统一的控件查找、点击、输入等接口。
"""
import time
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

from .utils import human_delay, setup_logger

logger = setup_logger("BaseBot")


@dataclass
class Message:
    """消息数据模型"""
    sender: str = ""              # 发送者名称
    content: str = ""             # 消息文本内容
    timestamp: str = ""           # 时间戳
    is_self: bool = False         # 是否为自己发送的消息
    msg_type: str = "text"        # 消息类型: text / image / file / voice


class BaseBot:
    """
    RPA 机器人基类。
    封装 uiautomator2 的通用操作逻辑，微信和企业微信的 Bot 均继承此类。
    """

    def __init__(self, device_serial: Optional[str] = None):
        """
        初始化 Bot 并连接设备。

        Args:
            device_serial: 设备序列号，None 表示自动选择
        """
        # 延迟导入，方便在没有真机的环境下查看代码
        try:
            import uiautomator2 as u2
            self._u2 = u2
        except ImportError:
            logger.warning(
                "uiautomator2 未安装。请运行: pip install uiautomator2\n"
                "当前以模拟模式运行（仅打印操作日志，不实际执行）。"
            )
            self._u2 = None

        self.device_serial = device_serial
        self.device = None
        self.connected = False
        self.package_name = ""
        self.ids = {}

    # ============================================================
    # 设备连接
    # ============================================================

    def connect(self) -> bool:
        """连接到 Android 设备"""
        if self._u2 is None:
            logger.info("[模拟模式] 跳过设备连接")
            self.connected = True
            return True

        try:
            if self.device_serial:
                self.device = self._u2.connect(self.device_serial)
                logger.info(f"已连接到设备: {self.device_serial}")
            else:
                self.device = self._u2.connect()
                logger.info("已连接到默认设备")

            # 打印设备信息
            info = self.device.info
            logger.info(
                f"设备信息: {info.get('productName', 'N/A')} | "
                f"屏幕: {info.get('displayWidth', '?')}x{info.get('displayHeight', '?')} | "
                f"SDK: {info.get('sdkInt', '?')}"
            )
            self.connected = True
            return True

        except Exception as e:
            logger.error(f"连接设备失败: {e}")
            self.connected = False
            return False

    # ============================================================
    # 应用管理
    # ============================================================

    def launch_app(self) -> bool:
        """启动目标应用"""
        logger.info(f"启动应用: {self.package_name}")
        if self._u2 is None:
            logger.info(f"[模拟模式] app_start('{self.package_name}')")
            return True

        try:
            self.device.app_start(self.package_name, stop=False)
            human_delay([2.0, 4.0])

            # 确认应用已启动
            current = self.device.app_current()
            if current.get("package") == self.package_name:
                logger.info(f"应用已启动: {self.package_name}")
                return True
            else:
                logger.warning(f"当前前台应用: {current.get('package')}，非目标应用")
                return False
        except Exception as e:
            logger.error(f"启动应用失败: {e}")
            return False

    def is_app_running(self) -> bool:
        """检查目标应用是否在前台运行"""
        if self._u2 is None:
            return True
        try:
            current = self.device.app_current()
            return current.get("package") == self.package_name
        except Exception:
            return False

    # ============================================================
    # 通用控件操作
    # ============================================================

    def find_and_click(
        self,
        resource_id: Optional[str] = None,
        text: Optional[str] = None,
        description: Optional[str] = None,
        class_name: Optional[str] = None,
        xpath: Optional[str] = None,
        timeout: float = 10,
        delay_after: list = None,
    ) -> bool:
        """
        查找控件并点击。

        支持多种定位方式：resource_id、text、description、className、xpath。
        """
        if delay_after is None:
            delay_after = [0.5, 1.5]

        locator_desc = (
            resource_id or text or description or class_name or xpath or "unknown"
        )
        logger.debug(f"查找并点击: {locator_desc}")

        if self._u2 is None:
            logger.info(f"[模拟模式] click({locator_desc})")
            human_delay(delay_after)
            return True

        try:
            element = None

            if xpath:
                element = self.device.xpath(xpath)
                if element.wait(timeout=timeout):
                    element.click()
                    human_delay(delay_after)
                    return True
                else:
                    logger.warning(f"XPath 未找到元素: {xpath}")
                    return False

            # 构建 selector
            selector_kwargs = {}
            if resource_id:
                selector_kwargs["resourceId"] = resource_id
            if text:
                selector_kwargs["text"] = text
            if description:
                selector_kwargs["description"] = description
            if class_name:
                selector_kwargs["className"] = class_name

            element = self.device(**selector_kwargs)

            if element.wait(timeout=timeout):
                element.click()
                human_delay(delay_after)
                return True
            else:
                logger.warning(f"未找到元素: {selector_kwargs}")
                return False

        except Exception as e:
            logger.error(f"点击操作失败: {e}")
            return False

    def find_and_input(
        self,
        text_to_input: str,
        resource_id: Optional[str] = None,
        text: Optional[str] = None,
        class_name: Optional[str] = None,
        xpath: Optional[str] = None,
        timeout: float = 10,
        clear_first: bool = True,
    ) -> bool:
        """
        查找输入框并输入文本。
        """
        locator_desc = resource_id or text or class_name or xpath or "unknown"
        logger.debug(f"查找并输入: {locator_desc} -> '{text_to_input}'")

        if self._u2 is None:
            logger.info(f"[模拟模式] input({locator_desc}, '{text_to_input}')")
            human_delay([0.3, 0.8])
            return True

        try:
            if xpath:
                el = self.device.xpath(xpath)
                if el.wait(timeout=timeout):
                    el.click()
                    human_delay([0.2, 0.5])
                    if clear_first:
                        self.device.clear_text()
                    self.device.send_keys(text_to_input)
                    human_delay([0.3, 0.8])
                    return True
                return False

            selector_kwargs = {}
            if resource_id:
                selector_kwargs["resourceId"] = resource_id
            if text:
                selector_kwargs["text"] = text
            if class_name:
                selector_kwargs["className"] = class_name

            element = self.device(**selector_kwargs)

            if element.wait(timeout=timeout):
                element.click()
                human_delay([0.2, 0.5])
                if clear_first:
                    element.clear_text()
                element.set_text(text_to_input)
                human_delay([0.3, 0.8])
                return True
            else:
                logger.warning(f"未找到输入框: {selector_kwargs}")
                return False

        except Exception as e:
            logger.error(f"输入操作失败: {e}")
            return False

    def get_element_text(
        self,
        resource_id: Optional[str] = None,
        text: Optional[str] = None,
        xpath: Optional[str] = None,
        timeout: float = 5,
    ) -> Optional[str]:
        """获取控件的文本内容"""
        if self._u2 is None:
            return "[模拟模式] 文本内容"

        try:
            if xpath:
                el = self.device.xpath(xpath)
                if el.wait(timeout=timeout):
                    return el.get_text()
                return None

            selector_kwargs = {}
            if resource_id:
                selector_kwargs["resourceId"] = resource_id
            if text:
                selector_kwargs["text"] = text

            element = self.device(**selector_kwargs)
            if element.wait(timeout=timeout):
                return element.get_text()
            return None

        except Exception as e:
            logger.error(f"获取文本失败: {e}")
            return None

    def element_exists(
        self,
        resource_id: Optional[str] = None,
        text: Optional[str] = None,
        timeout: float = 3,
    ) -> bool:
        """检查控件是否存在"""
        if self._u2 is None:
            return True

        selector_kwargs = {}
        if resource_id:
            selector_kwargs["resourceId"] = resource_id
        if text:
            selector_kwargs["text"] = text

        return self.device(**selector_kwargs).wait(timeout=timeout)

    def press_back(self):
        """按返回键"""
        if self._u2 is None:
            logger.info("[模拟模式] press('back')")
            return
        self.device.press("back")
        human_delay([0.3, 0.8])

    def press_enter(self):
        """按回车键"""
        if self._u2 is None:
            logger.info("[模拟模式] press('enter')")
            return
        self.device.press("enter")
        human_delay([0.3, 0.5])

    def swipe_up(self, duration: float = 0.5):
        """向上滑动（查看更多内容）"""
        if self._u2 is None:
            logger.info("[模拟模式] swipe_up()")
            return
        w, h = self.device.window_size()
        self.device.swipe(w // 2, h * 3 // 4, w // 2, h // 4, duration=duration)
        human_delay([0.5, 1.0])

    def swipe_down(self, duration: float = 0.5):
        """向下滑动（刷新或查看历史）"""
        if self._u2 is None:
            logger.info("[模拟模式] swipe_down()")
            return
        w, h = self.device.window_size()
        self.device.swipe(w // 2, h // 4, w // 2, h * 3 // 4, duration=duration)
        human_delay([0.5, 1.0])

    def take_screenshot(self, save_path: str = "screenshot.png") -> bool:
        """截取当前屏幕"""
        if self._u2 is None:
            logger.info(f"[模拟模式] screenshot('{save_path}')")
            return True
        try:
            self.device.screenshot(save_path)
            logger.info(f"截图已保存: {save_path}")
            return True
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return False

    def dump_hierarchy(self, save_path: str = "hierarchy.xml") -> bool:
        """导出当前页面的 UI 控件树（用于调试）"""
        if self._u2 is None:
            logger.info(f"[模拟模式] dump_hierarchy('{save_path}')")
            return True
        try:
            xml = self.device.dump_hierarchy()
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(xml)
            logger.info(f"控件树已保存: {save_path}")
            return True
        except Exception as e:
            logger.error(f"导出控件树失败: {e}")
            return False
