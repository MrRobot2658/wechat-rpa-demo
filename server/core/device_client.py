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
from typing import Optional, Literal
import requests

AppType = Literal["wechat", "wework"]

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
            timeout: 单次请求与任务轮询的超时时间（秒），建议 ≥30，避免 get_contact_list 等耗时接口读超时
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

    def send_message(
        self,
        contact: str,
        message: str,
        wait: bool = True,
        app_type: AppType = "wework",
    ) -> dict:
        """
        发送消息

        Args:
            contact: 联系人或群组名称
            message: 消息内容
            wait: 是否等待执行完成
            app_type: 目标应用 "wechat" | "wework"
        """
        resp = self._post("/api/send_message", {
            "contact": contact,
            "message": message,
            "app_type": app_type,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    def read_messages(
        self,
        contact: str,
        count: int = 10,
        wait: bool = True,
        app_type: AppType = "wework",
    ) -> dict:
        """读取指定联系人/群组的最新消息。app_type: "wechat" | "wework" """
        resp = self._post("/api/read_messages", {
            "contact": contact,
            "count": count,
            "app_type": app_type,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    # ================================================================
    # 群管理
    # ================================================================

    def create_group(
        self,
        group_name: str,
        members: list,
        wait: bool = True,
        app_type: AppType = "wework",
    ) -> dict:
        """创建群聊。app_type: "wechat" | "wework" """
        resp = self._post("/api/create_group", {
            "group_name": group_name,
            "members": members,
            "app_type": app_type,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    def invite_to_group(
        self,
        group_name: str,
        members: list,
        wait: bool = True,
        app_type: AppType = "wework",
    ) -> dict:
        """邀请成员入群。app_type: "wechat" | "wework" """
        resp = self._post("/api/invite_to_group", {
            "group_name": group_name,
            "members": members,
            "app_type": app_type,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    def remove_from_group(
        self,
        group_name: str,
        members: list,
        wait: bool = True,
        app_type: AppType = "wework",
    ) -> dict:
        """从群中移除成员。app_type: "wechat" | "wework" """
        resp = self._post("/api/remove_from_group", {
            "group_name": group_name,
            "members": members,
            "app_type": app_type,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    def get_group_members(
        self,
        group_name: str,
        wait: bool = True,
        app_type: AppType = "wework",
    ) -> dict:
        """获取群成员列表。app_type: "wechat" | "wework" """
        resp = self._post("/api/get_group_members", {
            "group_name": group_name,
            "app_type": app_type,
        })

        if wait and resp.get("success"):
            task_id = resp.get("data", {}).get("task_id", "")
            if task_id:
                return self._wait_for_result(task_id)
        return resp

    def get_contact_list(self, app_type: AppType = "wework") -> dict:
        """
        获取联系人列表（通讯录当前页可见项）
        超时 95s、不重试，避免设备无响应时脚本长时间卡住；设备端内部已有约 90s 轮询。
        app_type: "wechat" | "wework"
        """
        return self._post(
            "/api/get_contact_list",
            {"app_type": app_type},
            timeout=95,
            retries=1,
        )

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

    def _get(self, path: str, timeout: Optional[int] = None) -> dict:
        """发送GET请求（使用 self.timeout，避免设备端耗时操作读超时）"""
        return self._request("get", path, None, timeout=timeout)

    def _post(
        self,
        path: str,
        data: dict,
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
    ) -> dict:
        """发送POST请求（使用 self.timeout）"""
        return self._request("post", path, data, timeout=timeout, retries=retries)

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[dict],
        retries: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> dict:
        """发送 HTTP 请求，超时或连接失败时自动重试，减轻偶发断线影响"""
        url = f"{self.api_base}{path}"
        last_error = None
        _timeout = timeout if timeout is not None else self.timeout
        _retries = retries if retries is not None else 2
        for attempt in range(_retries):
            try:
                if method == "get":
                    resp = self.session.get(url, timeout=_timeout)
                else:
                    resp = self.session.post(url, json=data, timeout=_timeout)
                resp.raise_for_status()
                return resp.json()
            except requests.ConnectionError as e:
                last_error = e
                if attempt < _retries - 1:
                    logger.warning(f"连接失败，重试 {attempt + 2}/{_retries}: {url}")
                    time.sleep(1)
                else:
                    logger.error(f"无法连接到设备: {url}")
                    return {"success": False, "message": f"无法连接到设备: {self.api_base}"}
            except (requests.Timeout, requests.ReadTimeout) as e:
                last_error = e
                if attempt < _retries - 1:
                    logger.warning(f"请求超时，重试 {attempt + 2}/{_retries}: {url}")
                    time.sleep(1)
                else:
                    logger.error(f"请求失败(超时): {url} - {e}")
                    return {"success": False, "message": str(e)}
            except Exception as e:
                logger.error(f"{method.upper()}请求失败: {url} - {e}")
                return {"success": False, "message": str(e)}
        return {"success": False, "message": str(last_error)}

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
