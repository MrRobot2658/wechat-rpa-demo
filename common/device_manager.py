"""
Android 设备管理器
负责设备连接、状态检测和基础设备操作。
"""
import subprocess
from typing import Optional
from .utils import setup_logger

logger = setup_logger("DeviceManager")


class DeviceManager:
    """
    Android 设备管理器。
    封装 ADB 命令，提供设备发现、连接和状态管理功能。
    """

    @staticmethod
    def list_devices() -> list[dict]:
        """
        列出所有已连接的 Android 设备。

        Returns:
            设备信息列表，每个元素包含 serial 和 status
        """
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True, text=True, timeout=10
            )
            devices = []
            for line in result.stdout.strip().split("\n")[1:]:
                if line.strip() and "device" in line:
                    parts = line.split()
                    serial = parts[0]
                    status = parts[1]
                    model = ""
                    for part in parts[2:]:
                        if part.startswith("model:"):
                            model = part.split(":")[1]
                    devices.append({
                        "serial": serial,
                        "status": status,
                        "model": model,
                    })
            return devices
        except Exception as e:
            logger.error(f"列出设备失败: {e}")
            return []

    @staticmethod
    def is_device_online(serial: str) -> bool:
        """检查指定设备是否在线"""
        devices = DeviceManager.list_devices()
        return any(d["serial"] == serial and d["status"] == "device" for d in devices)

    @staticmethod
    def get_device_info(serial: Optional[str] = None) -> dict:
        """
        获取设备详细信息。

        Args:
            serial: 设备序列号，None 表示使用默认设备

        Returns:
            设备信息字典
        """
        cmd_prefix = ["adb"]
        if serial:
            cmd_prefix += ["-s", serial]

        info = {}
        props = {
            "brand": "ro.product.brand",
            "model": "ro.product.model",
            "sdk_version": "ro.build.version.sdk",
            "android_version": "ro.build.version.release",
            "screen_density": "ro.sf.lcd_density",
        }

        for key, prop in props.items():
            try:
                result = subprocess.run(
                    cmd_prefix + ["shell", "getprop", prop],
                    capture_output=True, text=True, timeout=5
                )
                info[key] = result.stdout.strip()
            except Exception:
                info[key] = "unknown"

        # 获取屏幕分辨率
        try:
            result = subprocess.run(
                cmd_prefix + ["shell", "wm", "size"],
                capture_output=True, text=True, timeout=5
            )
            size_str = result.stdout.strip().split(":")[-1].strip()
            w, h = size_str.split("x")
            info["screen_width"] = int(w)
            info["screen_height"] = int(h)
        except Exception:
            info["screen_width"] = 0
            info["screen_height"] = 0

        return info

    @staticmethod
    def install_apk(apk_path: str, serial: Optional[str] = None) -> bool:
        """安装 APK 到设备"""
        cmd = ["adb"]
        if serial:
            cmd += ["-s", serial]
        cmd += ["install", "-r", apk_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return "Success" in result.stdout
        except Exception as e:
            logger.error(f"安装 APK 失败: {e}")
            return False

    @staticmethod
    def screenshot(save_path: str, serial: Optional[str] = None) -> bool:
        """截取设备屏幕"""
        cmd = ["adb"]
        if serial:
            cmd += ["-s", serial]

        try:
            # 在设备上截图
            subprocess.run(
                cmd + ["shell", "screencap", "-p", "/sdcard/screenshot.png"],
                capture_output=True, timeout=10
            )
            # 拉取到本地
            subprocess.run(
                cmd + ["pull", "/sdcard/screenshot.png", save_path],
                capture_output=True, timeout=10
            )
            return True
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return False
