#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信 RPA 联调脚本：测试「获取通讯录」和「发消息」

前置条件：
  1. 手机已安装 RPA 应用，并已开启无障碍 + 启动 HTTP 服务（或打开应用后自动启动）
  2. PC 已启动本仓库的 API 服务：在项目根目录执行
     cd server && uvicorn api.app:app --host 0.0.0.0 --port 8080
  3. server/config/__init__.py 中 DEVICES 的 api_base 指向手机 IP:9527
  4. 手机已登录微信

用法示例：
  # 仅测试获取微信通讯录
  python scripts/test_wechat_rpa.py

  # 获取通讯录并给指定联系人发一条消息
  python scripts/test_wechat_rpa.py --send "联系人昵称" "你好，这是测试消息"
"""
import argparse
import os
import sys
import threading

# 抑制 urllib3/LibreSSL 版本告警，避免刷屏
import warnings
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL.*", category=UserWarning)

try:
    import requests
except ImportError:
    print("请先安装: pip install requests")
    sys.exit(1)

# 通讯录接口超时（秒），略大于服务端请求设备的 95s，避免一直卡住
CONTACTS_TIMEOUT = 100

# 默认使用本机启动的 RPA 服务
BASE_URL = os.environ.get("RPA_SERVER_URL", "http://127.0.0.1:8080")
DEVICE_ID = os.environ.get("RPA_DEVICE_ID", "device_1")


def get_wechat_contacts():
    """获取微信通讯录列表（超时 CONTACTS_TIMEOUT 秒）"""
    url = f"{BASE_URL}/api/wechat/contacts"
    payload = {"device_id": DEVICE_ID}
    r = requests.post(url, json=payload, timeout=CONTACTS_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(data.get("message", "获取通讯录失败"))
    raw = data.get("data")
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return list(raw.values()) if raw else []
    return []


def send_wechat_message(contact: str, message: str):
    """发送微信消息"""
    url = f"{BASE_URL}/api/wechat/send_message"
    payload = {"device_id": DEVICE_ID, "contact": contact, "message": message}
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("success", False), data.get("message", "")


def main():
    global BASE_URL, DEVICE_ID
    parser = argparse.ArgumentParser(description="测试微信 RPA：通讯录 + 发消息")
    parser.add_argument("--base", default=BASE_URL, help="RPA 服务地址（默认 http://127.0.0.1:8080）")
    parser.add_argument("--device", default=DEVICE_ID, help="设备 ID（默认 device_1）")
    parser.add_argument("--send", nargs=2, metavar=("CONTACT", "MESSAGE"), help="发送消息：联系人昵称 消息内容")
    args = parser.parse_args()

    BASE_URL = args.base.rstrip("/")
    DEVICE_ID = args.device

    print(f"服务地址: {BASE_URL}  设备: {DEVICE_ID}\n")

    # 1. 获取通讯录（最多等 CONTACTS_TIMEOUT 秒，超时即报错不再卡住）
    print(f"正在获取微信通讯录…（最多等待 {CONTACTS_TIMEOUT} 秒，请确保手机 RPA 已启动、网络可达）")
    progress_stop = threading.Event()
    def _progress():
        n = 0
        while not progress_stop.wait(15):
            n += 15
            if n < CONTACTS_TIMEOUT:
                print(f"  仍在等待设备响应… ({n}s)")
    t = threading.Thread(target=_progress, daemon=True)
    t.start()
    try:
        contacts = get_wechat_contacts()
    except requests.exceptions.ConnectionError:
        print("连接失败，请确认：1) 已启动 RPA 服务（uvicorn）；2) 手机 RPA 已启动 HTTP 服务且与 PC 同网段")
        sys.exit(2)
    except requests.exceptions.Timeout:
        print("请求超时。请确认：手机已亮屏/解锁、已打开过微信、RPA 应用已启动 HTTP 服务且与 PC 同网段。")
        sys.exit(3)
    except Exception as e:
        print(f"获取通讯录失败: {e}")
        sys.exit(4)
    finally:
        progress_stop.set()

    print(f"共获取到 {len(contacts)} 个联系人/入口:")
    for i, name in enumerate(contacts[:50], 1):
        print(f"  {i}. {name}")
    if len(contacts) > 50:
        print(f"  ... 等共 {len(contacts)} 个")

    # 2. 可选：发消息
    if args.send:
        contact, message = args.send
        print(f"\n正在向「{contact}」发送: {message}")
        ok, msg = send_wechat_message(contact, message)
        if ok:
            print("发送请求已提交成功。")
        else:
            print(f"发送失败: {msg}")
            sys.exit(5)

    print("\n测试完成。")


if __name__ == "__main__":
    main()
