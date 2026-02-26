# -*- coding: utf-8 -*-
"""
服务端配置
"""

# Android设备HTTP服务器地址
# 格式: http://<手机IP>:<端口>
# 默认端口为9527，需确保手机和服务器在同一局域网
DEVICE_API_BASE = "http://192.168.1.100:9527"

# 多设备配置（用于多账号托管场景）
DEVICES = {
    "device_1": {
        "name": "设备1-企业微信",
        "api_base": "http://192.168.1.100:9527",
        "target_app": "wework",
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
