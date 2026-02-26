#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChat RPA Demo - Python客户端使用示例

本脚本演示如何通过Python SDK与Android设备上的RPA服务通信，
实现企业微信的自动化操作。

前置条件:
    1. Android设备已安装并启动RPA应用
    2. 已开启无障碍服务
    3. 已启动HTTP服务器
    4. 手机和电脑在同一局域网
    5. 企业微信已登录

使用方法:
    python demo.py
"""
import sys
import time
import logging

# 添加项目根目录到路径
sys.path.insert(0, "..")

from core.device_client import DeviceClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    # ============================================================
    # 配置设备地址（请替换为实际的手机IP）
    # ============================================================
    DEVICE_IP = "192.168.1.100"
    DEVICE_PORT = 9527
    API_BASE = f"http://{DEVICE_IP}:{DEVICE_PORT}"

    print("""
╔══════════════════════════════════════════════════════════════╗
║     WeChat RPA Demo - AccessibilityService 方案             ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  请选择演示功能:                                             ║
║                                                              ║
║  1. 检查设备连接状态                                         ║
║  2. 发送消息                                                 ║
║  3. 读取最新消息                                             ║
║  4. 创建群聊                                                 ║
║  5. 邀请成员入群                                             ║
║  6. 获取群成员列表                                           ║
║  7. 导出控件树（调试）                                       ║
║  0. 退出                                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    client = DeviceClient(API_BASE)

    while True:
        choice = input("\n请输入选项 (0-7): ").strip()

        if choice == "0":
            print("再见！")
            break

        elif choice == "1":
            demo_check_status(client)

        elif choice == "2":
            demo_send_message(client)

        elif choice == "3":
            demo_read_messages(client)

        elif choice == "4":
            demo_create_group(client)

        elif choice == "5":
            demo_invite_to_group(client)

        elif choice == "6":
            demo_get_group_members(client)

        elif choice == "7":
            demo_dump_ui(client)

        else:
            print("无效选项，请重新输入")


def demo_check_status(client: DeviceClient):
    """演示: 检查设备连接状态"""
    print("\n--- 检查设备状态 ---")
    if client.is_ready():
        status = client.get_status()
        print(f"  设备状态: 在线")
        print(f"  无障碍服务: {'已开启' if status.get('accessibility_enabled') else '未开启'}")
        print(f"  当前前台应用: {status.get('current_package', '-')}")
        print(f"  任务队列: {status.get('task_queue_size', 0)} 个任务")
    else:
        print("  设备状态: 离线或不可达")
        print(f"  请检查: 1) 手机是否在同一网络  2) RPA应用是否启动  3) IP地址是否正确")


def demo_send_message(client: DeviceClient):
    """演示: 发送消息"""
    print("\n--- 发送消息 ---")
    contact = input("  联系人/群组名称: ").strip()
    message = input("  消息内容: ").strip()

    if not contact or not message:
        print("  联系人和消息内容不能为空")
        return

    print(f"  正在发送消息给 '{contact}'...")
    result = client.send_message(contact, message, wait=False)
    print(f"  结果: {result}")


def demo_read_messages(client: DeviceClient):
    """演示: 读取消息"""
    print("\n--- 读取消息 ---")
    contact = input("  联系人/群组名称: ").strip()
    count = input("  读取条数 (默认10): ").strip()
    count = int(count) if count.isdigit() else 10

    if not contact:
        print("  联系人名称不能为空")
        return

    print(f"  正在读取 '{contact}' 的最新 {count} 条消息...")
    result = client.read_messages(contact, count, wait=False)
    print(f"  结果: {result}")


def demo_create_group(client: DeviceClient):
    """演示: 创建群聊"""
    print("\n--- 创建群聊 ---")
    group_name = input("  群名称: ").strip()
    members_str = input("  成员列表 (逗号分隔): ").strip()
    members = [m.strip() for m in members_str.split(",") if m.strip()]

    if not members:
        print("  成员列表不能为空")
        return

    print(f"  正在创建群聊 '{group_name}'，成员: {members}...")
    result = client.create_group(group_name, members, wait=False)
    print(f"  结果: {result}")


def demo_invite_to_group(client: DeviceClient):
    """演示: 邀请入群"""
    print("\n--- 邀请入群 ---")
    group_name = input("  群名称: ").strip()
    members_str = input("  要邀请的成员 (逗号分隔): ").strip()
    members = [m.strip() for m in members_str.split(",") if m.strip()]

    if not group_name or not members:
        print("  群名称和成员列表不能为空")
        return

    print(f"  正在邀请 {members} 加入群 '{group_name}'...")
    result = client.invite_to_group(group_name, members, wait=False)
    print(f"  结果: {result}")


def demo_get_group_members(client: DeviceClient):
    """演示: 获取群成员"""
    print("\n--- 获取群成员 ---")
    group_name = input("  群名称: ").strip()

    if not group_name:
        print("  群名称不能为空")
        return

    print(f"  正在获取群 '{group_name}' 的成员列表...")
    result = client.get_group_members(group_name, wait=False)
    print(f"  结果: {result}")


def demo_dump_ui(client: DeviceClient):
    """演示: 导出控件树"""
    print("\n--- 导出控件树 ---")
    print("  正在导出当前页面的控件树...")
    tree = client.dump_ui_tree()
    if tree:
        # 保存到文件
        filename = f"ui_tree_{int(time.time())}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(tree)
        print(f"  控件树已保存到: {filename}")
        # 显示前20行
        lines = tree.split("\n")[:20]
        print("  前20行预览:")
        for line in lines:
            print(f"    {line}")
    else:
        print("  导出失败，请检查无障碍服务是否已开启")


if __name__ == "__main__":
    main()
