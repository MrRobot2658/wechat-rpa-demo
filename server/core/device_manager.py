# -*- coding: utf-8 -*-
"""
多设备管理器

管理多台Android设备的连接和任务分发，
支持多账号托管场景下的负载均衡和故障转移。
"""
import logging
from typing import Optional
from .device_client import DeviceClient

logger = logging.getLogger(__name__)


class DeviceManager:
    """
    多设备管理器

    使用示例:
        manager = DeviceManager()
        manager.add_device("device_1", "http://192.168.1.100:9527", "企微账号A")
        manager.add_device("device_2", "http://192.168.1.101:9527", "企微账号B")

        # 通过指定设备发送消息
        manager.get_device("device_1").send_message("张三", "你好")

        # 获取所有在线设备
        online = manager.get_online_devices()
    """

    def __init__(self):
        self._devices: dict[str, dict] = {}

    def add_device(self, device_id: str, api_base: str, name: str = "", **kwargs):
        """
        注册设备

        Args:
            device_id: 设备唯一标识
            api_base: 设备HTTP API地址
            name: 设备名称/备注
        """
        client = DeviceClient(api_base)
        self._devices[device_id] = {
            "id": device_id,
            "name": name or device_id,
            "api_base": api_base,
            "client": client,
            **kwargs,
        }
        logger.info(f"设备已注册: {device_id} ({api_base})")

    def remove_device(self, device_id: str):
        """移除设备"""
        if device_id in self._devices:
            del self._devices[device_id]
            logger.info(f"设备已移除: {device_id}")

    def get_device(self, device_id: str) -> Optional[DeviceClient]:
        """获取指定设备的客户端"""
        device = self._devices.get(device_id)
        return device["client"] if device else None

    def get_all_devices(self) -> dict:
        """获取所有已注册设备"""
        return {
            did: {
                "id": d["id"],
                "name": d["name"],
                "api_base": d["api_base"],
            }
            for did, d in self._devices.items()
        }

    def get_online_devices(self) -> list[str]:
        """获取所有在线（可连接）的设备ID"""
        online = []
        for device_id, device in self._devices.items():
            client: DeviceClient = device["client"]
            if client.is_ready():
                online.append(device_id)
        return online

    def get_device_status(self, device_id: str) -> dict:
        """获取指定设备的详细状态"""
        client = self.get_device(device_id)
        if client is None:
            return {"error": f"设备不存在: {device_id}"}
        try:
            return client.get_status()
        except Exception as e:
            return {"error": str(e)}

    def broadcast_message(self, contact: str, message: str) -> dict:
        """
        向所有在线设备广播消息（每个设备都发送相同消息给指定联系人）

        Args:
            contact: 联系人名称
            message: 消息内容

        Returns:
            各设备的执行结果
        """
        results = {}
        for device_id in self.get_online_devices():
            client = self.get_device(device_id)
            if client:
                results[device_id] = client.send_message(contact, message, wait=False)
        return results
