# 部署指南

## 一、Android 端部署

### 1.1 开发环境

| 工具 | 版本要求 | 说明 |
|------|---------|------|
| Android Studio | Hedgehog (2023.1.1)+ | IDE |
| JDK | 17+ | Java 开发工具包 |
| Gradle | 8.0+ | 构建工具（Android Studio 自带） |
| Kotlin | 1.9+ | 开发语言 |

### 1.2 目标设备要求

| 项目 | 要求 |
|------|------|
| Android 版本 | 7.0 (API 24) 及以上 |
| 企业微信版本 | 4.1.x ~ 5.x |
| 网络 | 与服务端在同一局域网 |
| 存储空间 | 至少 100MB 可用空间 |

### 1.3 编译步骤

```bash
# 1. 克隆项目
git clone https://github.com/MrRobot2658/wechat-rpa-demo.git
cd wechat-rpa-demo

# 2. 用 Android Studio 打开 android-app 目录
#    File -> Open -> 选择 android-app 目录

# 3. 等待 Gradle Sync 完成

# 4. 编译 APK
#    Build -> Build Bundle(s) / APK(s) -> Build APK(s)

# 5. APK 输出路径:
#    android-app/app/build/outputs/apk/debug/app-debug.apk
```

### 1.4 安装与配置

```bash
# 方式一：通过 ADB 安装
adb install app-debug.apk

# 方式二：将 APK 传输到手机，直接安装
```

**手机端配置步骤：**

1. 打开 **WeChat RPA** 应用
2. 点击「**开启无障碍服务**」
3. 在系统无障碍设置中，找到 "WeChat RPA" 并开启
4. 返回应用，确认无障碍服务状态为 "✅ 已开启"
5. 点击「**启动HTTP服务器**」
6. 确认整体状态为 "🟢 系统就绪"

### 1.5 验证

```bash
# 获取手机IP（假设为 192.168.1.100）
# 在电脑上测试连接
curl http://192.168.1.100:9527/api/status

# 预期返回:
# {"code":200,"success":true,"message":"ok","data":{"accessibility_enabled":true,...}}
```

## 二、Python 服务端部署

### 2.1 环境要求

| 工具 | 版本要求 |
|------|---------|
| Python | 3.10+ |
| pip | 最新版 |

### 2.2 安装步骤

```bash
cd server

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate    # Linux/macOS
# venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2.3 配置

编辑 `server/config/__init__.py`：

```python
# 修改为实际的手机IP地址
DEVICE_API_BASE = "http://192.168.1.100:9527"

# 多设备配置
DEVICES = {
    "device_1": {
        "name": "设备1-企业微信",
        "api_base": "http://192.168.1.100:9527",
        "target_app": "wework",
    },
    # 添加更多设备...
}
```

### 2.4 启动

```bash
# 开发模式（自动重载）
python -m uvicorn api.app:app --host 0.0.0.0 --port 8080 --reload

# 生产模式
python -m uvicorn api.app:app --host 0.0.0.0 --port 8080 --workers 4

# 访问 API 文档
# http://localhost:8080/docs
```

### 2.5 使用 systemd 部署为系统服务（Linux）

```ini
# /etc/systemd/system/wechat-rpa.service
[Unit]
Description=WeChat RPA Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/wechat-rpa-demo/server
ExecStart=/path/to/venv/bin/uvicorn api.app:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable wechat-rpa
sudo systemctl start wechat-rpa
```

## 三、云手机集群部署（多账号托管）

### 3.1 架构

```
┌──────────────────────────────────┐
│     Python 服务端 (云服务器)       │
│     FastAPI + DeviceManager      │
└──────┬───────┬───────┬──────────┘
       │       │       │
       ▼       ▼       ▼
   ┌──────┐┌──────┐┌──────┐
   │云手机1││云手机2││云手机N│
   │RPA App││RPA App││RPA App│
   │:9527  ││:9527  ││:9527  │
   └──────┘└──────┘└──────┘
```

### 3.2 云手机平台选择

| 平台 | 特点 |
|------|------|
| 华为云手机 | 稳定，企业级 |
| 阿里云无影 | 性价比高 |
| 红手指 | 操作简单 |
| 多多云 | 价格低 |

### 3.3 批量部署脚本

```python
# batch_deploy.py - 批量注册设备示例
from server.core import DeviceManager

manager = DeviceManager()

# 批量注册云手机
cloud_phones = [
    ("phone_001", "http://10.0.1.1:9527", "企微账号A"),
    ("phone_002", "http://10.0.1.2:9527", "企微账号B"),
    ("phone_003", "http://10.0.1.3:9527", "企微账号C"),
    # ...
]

for device_id, api_base, name in cloud_phones:
    manager.add_device(device_id, api_base, name)

# 检查在线状态
online = manager.get_online_devices()
print(f"在线设备: {len(online)}/{len(cloud_phones)}")

# 向所有在线设备广播消息
manager.broadcast_message("客户群", "今日促销活动开始！")
```

## 四、常见问题

### Q: 无障碍服务被系统自动关闭？

Android 系统可能在电池优化时关闭无障碍服务。解决方案：
- 将 RPA App 加入电池优化白名单
- 开启 "允许后台运行"
- 关闭 "智能省电" 等功能

### Q: HTTP服务器无法连接？

1. 确认手机和电脑在同一局域网
2. 检查手机防火墙设置
3. 确认 9527 端口未被占用
4. 尝试 `ping <手机IP>` 测试网络连通性

### Q: 控件找不到？

企业微信更新后控件ID可能变化：
1. 调用 `/api/dump_ui` 导出控件树
2. 搜索目标控件的新ID
3. 更新 `WeworkOperator.kt` 中的 `WeworkIds`
4. 重新编译安装
