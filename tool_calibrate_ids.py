#!/usr/bin/env python3
"""
UI 控件 ID 校准工具

微信和企业微信的 resource-id 会随版本更新而变化。
本工具帮助你快速获取当前版本的控件 ID，用于更新 config/settings.py。

使用方法:
    1. 在手机上打开微信/企业微信，手动导航到目标页面
    2. 运行本脚本
    3. 查看生成的 XML 文件和截图
    4. 根据 XML 中的 resource-id 更新 config/settings.py
"""
import sys
import os
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def dump_current_page(device_serial=None):
    """导出当前页面的控件树和截图"""
    try:
        import uiautomator2 as u2
    except ImportError:
        print("错误: 请先安装 uiautomator2: pip install uiautomator2")
        return

    # 连接设备
    if device_serial:
        d = u2.connect(device_serial)
    else:
        d = u2.connect()

    print(f"已连接设备: {d.device_info}")

    # 获取当前应用信息
    current = d.app_current()
    package = current.get("package", "unknown")
    activity = current.get("activity", "unknown")
    print(f"当前应用: {package}")
    print(f"当前Activity: {activity}")

    # 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"calibrate_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # 导出控件树
    xml_path = os.path.join(output_dir, "hierarchy.xml")
    xml_content = d.dump_hierarchy()
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"控件树已保存: {xml_path}")

    # 截图
    screenshot_path = os.path.join(output_dir, "screenshot.png")
    d.screenshot(screenshot_path)
    print(f"截图已保存: {screenshot_path}")

    # 解析并列出所有有 resource-id 的控件
    print(f"\n{'=' * 60}")
    print("当前页面的关键控件:")
    print(f"{'=' * 60}")

    # 简单解析 XML 提取 resource-id
    id_pattern = re.compile(r'resource-id="([^"]+)"')
    text_pattern = re.compile(r'\btext="([^"]*)"')
    class_pattern = re.compile(r'class="([^"]+)"')

    seen_ids = set()
    for line in xml_content.split(">"):
        id_match = id_pattern.search(line)
        text_match = text_pattern.search(line)
        class_match = class_pattern.search(line)

        if id_match:
            rid = id_match.group(1)
            if rid not in seen_ids:
                seen_ids.add(rid)
                text = text_match.group(1) if text_match else ""
                cls = class_match.group(1).split(".")[-1] if class_match else ""
                print(f"  ID: {rid:<50} Text: {text:<20} Class: {cls}")

    print(f"\n共发现 {len(seen_ids)} 个不同的 resource-id")
    print(f"\n提示: 使用 weditor 或 uiautodev 可以更直观地查看控件属性")
    print(f"  启动 weditor: python -m weditor")
    print(f"  启动 uiautodev: python -m uiautodev")

    # 保存汇总信息
    summary_path = os.path.join(output_dir, "summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"校准时间: {timestamp}\n")
        f.write(f"应用包名: {package}\n")
        f.write(f"Activity: {activity}\n")
        f.write(f"设备信息: {d.device_info}\n\n")
        f.write("Resource IDs:\n")
        for rid in sorted(seen_ids):
            f.write(f"  {rid}\n")

    print(f"\n汇总信息已保存: {summary_path}")


if __name__ == "__main__":
    serial = sys.argv[1] if len(sys.argv) > 1 else None
    dump_current_page(serial)
