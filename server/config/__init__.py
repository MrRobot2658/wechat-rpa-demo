# -*- coding: utf-8 -*-
"""
服务端配置
"""

# Android设备HTTP服务器地址
# 格式: http://<手机IP>:<端口>
# 默认端口为9527，需确保手机和服务器在同一局域网
DEVICE_API_BASE = "http://192.168.8.222:9527"

# ADB 路径（用于实时画面截屏；填本机 adb 绝对路径以保证实时画面可用）
ADB_PATH = "/Users/lei26/Library/Android/sdk/platform-tools/adb"

# 多设备配置（用于多账号托管场景）
# 若需前端实时画面，可配置 adb_serial（adb devices 中的设备序列号），不填则用默认设备
DEVICES = {
    "device_1": {
        "name": "设备1-企业微信",
        "api_base": "http://192.168.8.222:9527",
        "target_app": "wework",
        "adb_serial": "DYGA4PVWKJU8DENJ",  # adb devices 第一列序列号（非 model 名）；单设备可留空
    },
    # "device_2": {
    #     "name": "设备2-企业微信",
    #     "api_base": "http://192.168.1.101:9527",
    #     "target_app": "wework",
    # },
}

# 任务轮询间隔（秒）
TASK_POLL_INTERVAL = 2

# 任务超时时间（秒）
TASK_TIMEOUT = 60

# 服务端API端口
SERVER_PORT = 8080

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "rpa_server.log"
