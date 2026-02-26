# -*- coding: utf-8 -*-
"""
Python服务端 - FastAPI应用

提供统一的REST API，作为多设备管理和任务调度的中枢。
外部系统（如CRM、客服系统）通过本API间接控制Android设备上的企业微信。

架构：
    外部系统 --HTTP--> [本服务端] --HTTP--> [Android设备HTTP服务] --Accessibility--> [企业微信]
"""
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from server.core import DeviceClient, DeviceManager
from server.config import DEVICES, SERVER_PORT

# ================================================================
# 日志配置
# ================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("RpaServer")

# ================================================================
# 初始化
# ================================================================
app = FastAPI(
    title="WeChat RPA Server",
    description="基于AccessibilityService的企业微信/微信自动化管理平台",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化设备管理器
device_manager = DeviceManager()
for device_id, device_config in DEVICES.items():
    device_manager.add_device(
        device_id=device_id,
        api_base=device_config["api_base"],
        name=device_config.get("name", device_id),
    )


# ================================================================
# 请求模型
# ================================================================

class SendMessageRequest(BaseModel):
    device_id: str = Field(..., description="设备ID")
    contact: str = Field(..., description="联系人或群组名称")
    message: str = Field(..., description="消息内容")


class ReadMessagesRequest(BaseModel):
    device_id: str = Field(..., description="设备ID")
    contact: str = Field(..., description="联系人或群组名称")
    count: int = Field(10, description="读取条数")


class CreateGroupRequest(BaseModel):
    device_id: str = Field(..., description="设备ID")
    group_name: str = Field("", description="群名称")
    members: list[str] = Field(..., description="初始成员列表")


class GroupMemberRequest(BaseModel):
    device_id: str = Field(..., description="设备ID")
    group_name: str = Field(..., description="群名称")
    members: list[str] = Field(..., description="成员列表")


class GroupQueryRequest(BaseModel):
    device_id: str = Field(..., description="设备ID")
    group_name: str = Field(..., description="群名称")


class BroadcastRequest(BaseModel):
    contact: str = Field(..., description="联系人名称")
    message: str = Field(..., description="消息内容")


# ================================================================
# 设备管理API
# ================================================================

@app.get("/api/devices", summary="获取所有设备列表")
async def list_devices():
    """返回所有已注册设备的信息"""
    return {
        "success": True,
        "data": device_manager.get_all_devices(),
    }


@app.get("/api/devices/online", summary="获取在线设备列表")
async def list_online_devices():
    """返回所有在线（可连接）的设备ID"""
    online = device_manager.get_online_devices()
    return {
        "success": True,
        "data": online,
        "count": len(online),
    }


@app.get("/api/devices/{device_id}/status", summary="获取设备状态")
async def get_device_status(device_id: str):
    """获取指定设备的详细运行状态"""
    status = device_manager.get_device_status(device_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return {"success": True, "data": status}


# ================================================================
# 消息收发API
# ================================================================

@app.post("/api/send_message", summary="发送消息")
async def send_message(req: SendMessageRequest):
    """向指定联系人/群组发送文本消息"""
    client = device_manager.get_device(req.device_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"设备不存在: {req.device_id}")

    result = client.send_message(req.contact, req.message, wait=False)
    return {"success": True, "data": result}


@app.post("/api/read_messages", summary="读取消息")
async def read_messages(req: ReadMessagesRequest):
    """读取指定联系人/群组的最新消息"""
    client = device_manager.get_device(req.device_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"设备不存在: {req.device_id}")

    result = client.read_messages(req.contact, req.count, wait=False)
    return {"success": True, "data": result}


# ================================================================
# 群管理API
# ================================================================

@app.post("/api/create_group", summary="创建群聊")
async def create_group(req: CreateGroupRequest):
    """创建新的群聊"""
    client = device_manager.get_device(req.device_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"设备不存在: {req.device_id}")

    result = client.create_group(req.group_name, req.members, wait=False)
    return {"success": True, "data": result}


@app.post("/api/invite_to_group", summary="邀请入群")
async def invite_to_group(req: GroupMemberRequest):
    """邀请成员加入群聊"""
    client = device_manager.get_device(req.device_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"设备不存在: {req.device_id}")

    result = client.invite_to_group(req.group_name, req.members, wait=False)
    return {"success": True, "data": result}


@app.post("/api/remove_from_group", summary="移除群成员")
async def remove_from_group(req: GroupMemberRequest):
    """从群聊中移除成员"""
    client = device_manager.get_device(req.device_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"设备不存在: {req.device_id}")

    result = client.remove_from_group(req.group_name, req.members, wait=False)
    return {"success": True, "data": result}


@app.post("/api/get_group_members", summary="获取群成员")
async def get_group_members(req: GroupQueryRequest):
    """获取群聊的成员列表"""
    client = device_manager.get_device(req.device_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"设备不存在: {req.device_id}")

    result = client.get_group_members(req.group_name, wait=False)
    return {"success": True, "data": result}


# ================================================================
# 广播API（多设备）
# ================================================================

@app.post("/api/broadcast", summary="广播消息")
async def broadcast_message(req: BroadcastRequest):
    """向所有在线设备广播消息"""
    results = device_manager.broadcast_message(req.contact, req.message)
    return {
        "success": True,
        "data": results,
        "device_count": len(results),
    }


# ================================================================
# 调试API
# ================================================================

@app.get("/api/devices/{device_id}/dump_ui", summary="导出控件树")
async def dump_ui(device_id: str):
    """导出指定设备当前页面的控件树（用于调试和ID校准）"""
    client = device_manager.get_device(device_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"设备不存在: {device_id}")

    tree = client.dump_ui_tree()
    return {"success": True, "data": tree}


@app.get("/api/health", summary="健康检查")
async def health_check():
    """服务健康检查"""
    return {"status": "ok", "version": "2.0.0"}


# ================================================================
# 启动入口
# ================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
