# -*- coding: utf-8 -*-
"""
Android设备API客户端

封装对Android端内嵌HTTP服务器的所有API调用。
开发者可以直接使用本模块与手机上的RPA服务通信。

使用示例:
    client = DeviceClient("http://192.168.1.100:9527")
    client.send_message("张三", "你好")
    messages = client.read_messages("张三", count=5)
"""
import time
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class DeviceClient:
    """
    Android设备API客户端

    通过HTTP请求与手机上运行的RPA服务通信，
    驱动AccessibilityService执行自动化操作。
    """

    def __init__(self, api_base: str, timeout: int = 60):
        """
        Args:
            api_base: Android设备HTTP服务器地址，如 http://192.168.1.100:9527
            timeout: 任务执行超时时间（秒）
        """
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    # ================================================================
    # 状态查询
    # ================================================================

    def get_status(self) -> dict:
        """获取设备RPA服务状态"""
        resp = self._get("/api/status")
        return resp.get("data", {})

    def is_ready(self) -> bool:
        """检查设备是否就绪"""
        try:
            status = self.get_status()
            return status.get("accessibility_enabled", False)
        except Exception:
            return False

    # ================================================================
    # 消息收发
    # ================================================================

    def send_message(self, contact: str, message: str, wait: bool = True) -> dict:
        """
        发送消息

        Args:
            contact: 联系人或群组名称
            message: 消息内容
            wait: 是否等待执行完成

        Returns:
            执行结果字典
        """
        resp = self._post("/api/send_message", {
            "contact": contact,
            "message": message,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    def read_messages(self, contact: str, count: int = 10, wait: bool = True) -> dict:
        """
        读取指定联系人/群组的最新消息

        Args:
            contact: 联系人或群组名称
            count: 读取条数
            wait: 是否等待执行完成

        Returns:
            包含消息列表的结果字典
        """
        resp = self._post("/api/read_messages", {
            "contact": contact,
            "count": count,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    # ================================================================
    # 群管理
    # ================================================================

    def create_group(self, group_name: str, members: list, wait: bool = True) -> dict:
        """
        创建群聊

        Args:
            group_name: 群名称
            members: 初始成员列表
            wait: 是否等待执行完成
        """
        resp = self._post("/api/create_group", {
            "group_name": group_name,
            "members": members,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    def invite_to_group(self, group_name: str, members: list, wait: bool = True) -> dict:
        """
        邀请成员入群

        Args:
            group_name: 群名称
            members: 要邀请的成员列表
            wait: 是否等待执行完成
        """
        resp = self._post("/api/invite_to_group", {
            "group_name": group_name,
            "members": members,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    def remove_from_group(self, group_name: str, members: list, wait: bool = True) -> dict:
        """
        从群中移除成员

        Args:
            group_name: 群名称
            members: 要移除的成员列表
            wait: 是否等待执行完成
        """
        resp = self._post("/api/remove_from_group", {
            "group_name": group_name,
            "members": members,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    def get_group_members(self, group_name: str, wait: bool = True) -> dict:
        """
        获取群成员列表

        Args:
            group_name: 群名称
            wait: 是否等待执行完成
        """
        resp = self._post("/api/get_group_members", {
            "group_name": group_name,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    # ================================================================
    # 调试工具
    # ================================================================

    def dump_ui_tree(self) -> str:
        """导出当前页面控件树（用于调试和ID校准）"""
        resp = self._get("/api/dump_ui")
        return resp.get("data", "")

    def get_task_result(self, task_id: str) -> dict:
        """查询任务执行结果"""
        return self._get(f"/api/task_result/{task_id}")

    # ================================================================
    # 内部方法
    # ================================================================

    def _get(self, path: str) -> dict:
        """发送GET请求"""
        url = f"{self.api_base}{path}"
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.ConnectionError:
            logger.error(f"无法连接到设备: {url}")
            return {"success": False, "message": f"无法连接到设备: {self.api_base}"}
        except Exception as e:
            logger.error(f"GET请求失败: {url} - {e}")
            return {"success": False, "message": str(e)}

    def _post(self, path: str, data: dict) -> dict:
        """发送POST请求"""
        url = f"{self.api_base}{path}"
        try:
            resp = self.session.post(url, json=data, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.ConnectionError:
            logger.error(f"无法连接到设备: {url}")
            return {"success": False, "message": f"无法连接到设备: {self.api_base}"}
        except Exception as e:
            logger.error(f"POST请求失败: {url} - {e}")
            return {"success": False, "message": str(e)}

    def _wait_for_result(self, task_id: str, poll_interval: float = 2.0) -> dict:
        """轮询等待任务完成"""
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            result = self.get_task_result(task_id)
            data = result.get("data", {})
            if isinstance(data, dict) and data.get("success") is not None:
                return data
            time.sleep(poll_interval)

        return {"success": False, "message": f"任务超时 ({self.timeout}s): {task_id}"}
