# -*- coding: utf-8 -*-
"""
Android RPA Server

多应用、多套 API：每增加一个 app，就多一套相同能力的 API（/api/<app>/*）。
当前支持：微信(wechat)、企业微信(wework)；新增应用时在 APPS 中追加一项并实现设备端即可。
"""
import logging
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, RedirectResponse
from pydantic import BaseModel, Field

from server.core import DeviceClient, DeviceManager
from server.config import DEVICES, SERVER_PORT, ADB_PATH

# Swagger 分组（与根 API 结构一致）
TAG_DEVICES = "设备管理 /api/devices"
TAG_APPS = "应用管理 /api/apps"
TAG_BROADCAST = "广播与调试"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("AndroidRpaServer")

# ================================================================
# Android RPA Server
# ================================================================
app = FastAPI(
    title="Android RPA Server",
    description="多应用 RPA 网关：每增加一个 app 即多一套 API（获取联系人、单聊、创建群、群管理、收发消息）。文档分组与根 API 结构一致。",
    version="2.0.0",
    openapi_tags=[
        {"name": TAG_DEVICES, "description": "设备列表、状态、实时画面、控件树"},
        {"name": TAG_APPS, "description": "已注册应用及对应 /api/<app>/* 前缀"},
        {"name": "微信 /api/wechat", "description": "个人微信：联系人、单聊、群聊与群管理"},
        {"name": "企业微信 /api/wework", "description": "企业微信：联系人、单聊、群聊与群管理"},
        {"name": TAG_BROADCAST, "description": "广播、健康检查"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

device_manager = DeviceManager()
for device_id, device_config in DEVICES.items():
    device_manager.add_device(
        device_id=device_id,
        api_base=device_config["api_base"],
        name=device_config.get("name", device_id),
    )


# ================================================================
# 请求模型（通用，均含 device_id）
# ================================================================

class DeviceIdMixin(BaseModel):
    device_id: str = Field(..., description="设备ID")


class SendMessageRequest(DeviceIdMixin):
    contact: str = Field(..., description="联系人或群组名称")
    message: str = Field(..., description="消息内容")


class ReadMessagesRequest(DeviceIdMixin):
    contact: str = Field(..., description="联系人或群组名称")
    count: int = Field(10, description="读取条数")


class CreateGroupRequest(DeviceIdMixin):
    group_name: str = Field("", description="群名称")
    members: list[str] = Field(..., description="初始成员列表")


class GroupMemberRequest(DeviceIdMixin):
    group_name: str = Field(..., description="群名称")
    members: list[str] = Field(..., description="成员列表")


class GroupQueryRequest(DeviceIdMixin):
    group_name: str = Field(..., description="群名称")


class BroadcastRequest(BaseModel):
    contact: str = Field(..., description="联系人名称")
    message: str = Field(..., description="消息内容")


# ================================================================
# 设备管理 API  /api/devices
# ================================================================

@app.get("/api/devices", summary="获取所有设备列表", tags=[TAG_DEVICES])
async def list_devices():
    return {"success": True, "data": device_manager.get_all_devices()}


@app.get("/api/devices/online", summary="获取在线设备列表", tags=[TAG_DEVICES])
async def list_online_devices():
    online = device_manager.get_online_devices()
    return {"success": True, "data": online, "count": len(online)}


@app.get("/api/devices/{device_id}/status", summary="获取设备状态", tags=[TAG_DEVICES])
async def get_device_status(device_id: str):
    status = device_manager.get_device_status(device_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return {"success": True, "data": status}


# ================================================================
# 按应用注册 API：多一个 app 就多一套 /api/<app>/*
# ================================================================

# 已支持的应用：(路径前缀, app_type 传设备端, 展示名)
APPS: list[tuple[str, str, str]] = [
    ("wechat", "wechat", "微信"),
    ("wework", "wework", "企业微信"),
]


def _get_client(device_id: str) -> DeviceClient:
    client = device_manager.get_device(device_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"设备不存在: {device_id}")
    return client


def _norm_contact_result(result: dict) -> dict:
    if isinstance(result.get("data"), list):
        return {
            "success": result.get("success", True),
            "data": result["data"],
            "message": result.get("message", ""),
        }
    return {"success": True, "data": result}


def _register_app_routes(prefix: str, app_type: str, label: str) -> None:
    """为单个应用注册一套 API（获取联系人、单聊、创建群、群管理）"""
    tag = f"{label} /api/{prefix}"

    @app.post(f"/api/{prefix}/contacts", summary="获取联系人列表", tags=[tag])
    async def _contacts(req: DeviceIdMixin):
        result = _get_client(req.device_id).get_contact_list(app_type=app_type)
        return _norm_contact_result(result)

    @app.post(f"/api/{prefix}/send_message", summary="单聊-发送消息", tags=[tag])
    async def _send_message(req: SendMessageRequest):
        result = _get_client(req.device_id).send_message(
            req.contact, req.message, wait=False, app_type=app_type
        )
        return {"success": True, "data": result}

    @app.post(f"/api/{prefix}/read_messages", summary="单聊-读取消息", tags=[tag])
    async def _read_messages(req: ReadMessagesRequest):
        result = _get_client(req.device_id).read_messages(
            req.contact, req.count, wait=True, app_type=app_type
        )
        return {"success": True, "data": result}

    @app.post(f"/api/{prefix}/create_group", summary="创建群聊", tags=[tag])
    async def _create_group(req: CreateGroupRequest):
        result = _get_client(req.device_id).create_group(
            req.group_name, req.members, wait=False, app_type=app_type
        )
        return {"success": True, "data": result}

    @app.post(f"/api/{prefix}/invite_to_group", summary="群管理-邀请入群", tags=[tag])
    async def _invite_to_group(req: GroupMemberRequest):
        result = _get_client(req.device_id).invite_to_group(
            req.group_name, req.members, wait=False, app_type=app_type
        )
        return {"success": True, "data": result}

    @app.post(f"/api/{prefix}/remove_from_group", summary="群管理-移除成员", tags=[tag])
    async def _remove_from_group(req: GroupMemberRequest):
        result = _get_client(req.device_id).remove_from_group(
            req.group_name, req.members, wait=False, app_type=app_type
        )
        return {"success": True, "data": result}

    @app.post(f"/api/{prefix}/group_members", summary="群管理-获取群成员", tags=[tag])
    async def _group_members(req: GroupQueryRequest):
        result = _get_client(req.device_id).get_group_members(
            req.group_name, wait=False, app_type=app_type
        )
        return {"success": True, "data": result}


for _prefix, _app_type, _label in APPS:
    _register_app_routes(_prefix, _app_type, _label)


# ================================================================
# 广播与调试
# ================================================================

@app.post("/api/broadcast", summary="广播消息（多设备）", tags=[TAG_BROADCAST])
async def broadcast_message(req: BroadcastRequest):
    results = device_manager.broadcast_message(req.contact, req.message)
    return {"success": True, "data": results, "device_count": len(results)}


@app.get("/api/devices/{device_id}/dump_ui", summary="导出控件树", tags=[TAG_DEVICES])
async def dump_ui(device_id: str):
    client = device_manager.get_device(device_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"设备不存在: {device_id}")
    return {"success": True, "data": client.dump_ui_tree()}


@app.get("/api/devices/{device_id}/screen", summary="设备实时画面（截屏）", tags=[TAG_DEVICES])
async def device_screen(device_id: str):
    """返回设备当前屏幕 PNG 图像，用于前端实时展示手机操作界面。需本机已连接 ADB。"""
    if device_id not in DEVICES:
        raise HTTPException(status_code=404, detail=f"设备不存在: {device_id}")
    adb = (ADB_PATH or "adb").strip()
    if adb and not Path(adb).is_file():
        raise HTTPException(
            status_code=503,
            detail=f"ADB_PATH 指向的文件不存在: {adb}，请检查 config 中的 ADB_PATH 是否为本机 adb 实际路径。"
        )
    serial = (DEVICES[device_id].get("adb_serial") or "").strip()
    cmd_with_serial = [adb, "-s", serial, "exec-out", "screencap", "-p"] if serial else None
    cmd_default = [adb, "exec-out", "screencap", "-p"]

    def run_screencap(cmd):
        out = subprocess.run(cmd, capture_output=True, timeout=10)
        err = out.stderr.decode(errors="ignore") if out.stderr else ""
        return out.returncode, out.stdout, err

    try:
        cmd = cmd_with_serial if cmd_with_serial else cmd_default
        returncode, stdout, stderr = run_screencap(cmd)
        if (returncode != 0 or not stdout) and cmd_with_serial and "not found" in stderr.lower():
            returncode, stdout, stderr = run_screencap(cmd_default)
        if returncode != 0 or not stdout:
            raise HTTPException(
                status_code=503,
                detail=f"ADB 截屏失败: {stderr or '无输出'}。请确认手机已 USB 连接并开启调试，或在本机执行 adb devices 核对设备。"
            )
        return Response(content=stdout, media_type="image/png")
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="未找到 adb，请配置 config.ADB_PATH 或确保 adb 在 PATH 中")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="ADB 截屏超时")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/health", summary="健康检查", tags=[TAG_BROADCAST])
async def health_check():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/apps", summary="已注册应用列表", tags=[TAG_APPS])
async def list_apps():
    """返回当前已注册的应用（每应用对应一套 /api/<app>/*）"""
    return {
        "success": True,
        "data": [{"prefix": p, "app_type": a, "label": l} for p, a, l in APPS],
    }


# ================================================================
# 根路径重定向到 Swagger 文档（前端独立运行于 frontend-react）
# ================================================================

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
