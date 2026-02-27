# WeChat RPA - 基于 AccessibilityService 的企业微信自动化方案

> 一个基于 Android 官方无障碍服务（AccessibilityService）的企业微信/微信自动化框架，支持收发消息、自动拉群、群管理等功能。采用经过社区验证的最佳实践架构。

**免责声明：** 本项目仅用于技术研究和学习目的。自动化操作微信/企业微信可能违反其用户协议，存在被限制功能甚至封号的风险。使用者必须自行承担所有风险和后果。

## 为什么选择 AccessibilityService？

本项目从 `uiautomator2` 方案升级为 **AccessibilityService** 方案，这是经过 [WorkTool](https://github.com/gallonyin/worktool)（3k+ Stars）等多个成功开源项目验证的最佳实践。

| 对比维度 | AccessibilityService（本方案） | uiautomator2（旧方案） |
|---------|-------------------------------|----------------------|
| **稳定性** | 高，系统级常驻服务，长时间运行稳定 | 低，atx-agent 守护进程易断连 |
| **部署方式** | 独立 APK，安装即用，无需电脑持续连接 | 需要 PC 端 Python 通过 ADB 持续驱动 |
| **响应速度** | 快，进程内直接调用系统 API | 慢，跨进程 HTTP + ADB 多层通信 |
| **兼容性** | 99%+ Android 7.0+ 设备 | 依赖 ADB 连接和 atx-agent 版本 |
| **合规性** | 基于官方无障碍 SDK | 基于测试框架，非设计用途 |
| **多设备扩展** | 每台设备独立运行，天然支持集群 | 每台设备需一个 PC 端进程驱动 |

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    外部系统 / 开发者                       │
│              (CRM、客服系统、自定义脚本)                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP API (端口 8080)
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Python 服务端 (FastAPI)                      │
│         多设备管理 · 任务调度 · 统一API网关                 │
│         Swagger文档: http://localhost:8080/docs           │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP API (局域网, 端口 9527)
                       ▼
┌─────────────────────────────────────────────────────────┐
│           Android 设备 (手机/云手机)                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │         RPA App (本项目 Android 端)               │    │
│  │                                                   │    │
│  │  HttpServerService ──→ TaskController             │    │
│  │  (NanoHTTPD:9527)      (任务队列,串行执行)          │    │
│  │                             │                     │    │
│  │                             ▼                     │    │
│  │                      WeworkOperator               │    │
│  │                      (业务逻辑封装)                 │    │
│  │                             │                     │    │
│  │                             ▼                     │    │
│  │                 RpaAccessibilityService            │    │
│  │                 (控件查找 · 模拟点击 · 手势)         │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │            企业微信 / 微信 客户端                  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## 项目结构

```
wechat-rpa-demo/
│
├── android-app/                              # ===== Android 端应用 =====
│   └── app/
│       ├── build.gradle                      # Gradle 构建配置
│       └── src/main/
│           ├── AndroidManifest.xml            # 应用清单
│           ├── java/com/wechatrpa/
│           │   ├── RpaApplication.kt          # Application 入口
│           │   ├── activity/
│           │   │   └── MainActivity.kt        # 主界面（状态展示、服务控制）
│           │   ├── service/
│           │   │   ├── RpaAccessibilityService.kt  # [核心] 无障碍服务
│           │   │   ├── WeworkOperator.kt            # [核心] 企微操作封装
│           │   │   ├── TaskController.kt            # 任务队列控制器
│           │   │   └── HttpServerService.kt         # 内嵌HTTP服务器
│           │   ├── model/
│           │   │   └── Models.kt              # 数据模型定义
│           │   └── utils/
│           │       └── NodeHelper.kt          # 控件查找工具类
│           └── res/
│               ├── xml/accessibility_service_config.xml
│               └── values/strings.xml
│
├── server/                                   # ===== Python 服务端 =====
│   ├── api/
│   │   └── app.py                            # FastAPI 应用（统一API网关）
│   ├── core/
│   │   ├── device_client.py                  # 设备API客户端（Python SDK）
│   │   └── device_manager.py                 # 多设备管理器
│   ├── config/
│   │   └── __init__.py                       # 服务端配置
│   ├── demo.py                               # 交互式使用示例
│   └── requirements.txt                      # Python 依赖
│
└── README.md                                 # 本文档
```

## 快速开始

### 第一步：编译安装 Android 端

**环境要求：**
- Android Studio Hedgehog+
- JDK 17
- Android 7.0+ 设备（物理手机或云手机）
- 企业微信 4.1.x ~ 5.x

```bash
# 1. 克隆项目
git clone https://github.com/MrRobot2658/wechat-rpa-demo.git

# 2. 用 Android Studio 打开 android-app 目录
# 3. Sync Gradle，然后 Build -> Build APK(s)
# 4. 安装 APK 到手机
```

**手机端操作：**
1. 打开 **WeChat RPA** 应用
2. 点击「**开启无障碍服务**」→ 在系统设置中找到并启用 "WeChat RPA"
3. 返回本应用后，**HTTP 服务会自动启动**（也可手动点击「启动HTTP服务器」）
4. 确认状态显示为 "🟢 系统就绪"；**之后可切到微信或后台，服务会持续运行，连接不断**
5. 记录手机的 IP 地址（设置 → WLAN → 查看IP），并在 `server/config/__init__.py` 的 `DEVICES` 中配置 `api_base`

### 第二步：部署 Python 服务端

```bash
cd server

# 安装依赖
pip install -r requirements.txt

# 修改配置：将 DEVICE_API_BASE 改为手机的实际IP
# 编辑 server/config/__init__.py

# 启动服务端
python -m uvicorn api.app:app --host 0.0.0.0 --port 8080

# 访问 Swagger API 文档（分组与根 API 结构一致）
# http://localhost:8080/docs
# 根路径 / 会重定向到 /docs
```

**Swagger 文档分组**：与根 API 结构一致，分为「设备管理 /api/devices」「应用管理 /api/apps」「微信 /api/wechat」「企业微信 /api/wework」「广播与调试」。

**前端（React，独立启动）：**
```bash
cd frontend-react
cp .env.example .env   # 编辑 .env 中的 VITE_API_BASE 为后端地址，如 http://localhost:8080
npm install
npm run dev
# 浏览器打开 http://localhost:5173
```
前端提供：设备管理、应用管理、实时画面（需本机配置 ADB，见「前端与实时画面」一节）。

### 第三步：测试微信通讯录与发消息（联调脚本）

确保手机已登录微信、RPA 应用已开启无障碍并已启动 HTTP 服务（见上方手机端操作），且 PC 已启动 RPA 服务端（见第二步）。

```bash
# 仅测试获取微信通讯录
python scripts/test_wechat_rpa.py

# 获取通讯录并给指定联系人发一条消息
python scripts/test_wechat_rpa.py --send "联系人昵称" "你好，这是测试消息"
```

可选环境变量：`RPA_SERVER_URL`（默认 `http://127.0.0.1:8080`）、`RPA_DEVICE_ID`（默认 `device_1`）。脚本会先拉取通讯录并打印前 50 个名称，若传 `--send` 则再发送一条消息。

### 第四步：使用 Python SDK 或 Demo

**方式一：交互式 Demo**

```bash
cd server
python demo.py
```

**方式二：直接使用 SDK**

```python
from server.core import DeviceClient

# 连接设备
client = DeviceClient("http://192.168.1.100:9527")

# 检查设备状态
print(client.is_ready())        # True
print(client.get_status())      # {'accessibility_enabled': True, ...}

# 发送消息
client.send_message("张三", "你好，这是自动发送的消息")

# 读取最新消息
result = client.read_messages("张三", count=5)

# 创建群聊
client.create_group("项目讨论群", ["张三", "李四", "王五"])

# 邀请入群
client.invite_to_group("项目讨论群", ["赵六", "钱七"])

# 获取群成员列表
members = client.get_group_members("项目讨论群")

# 移除群成员
client.remove_from_group("项目讨论群", ["钱七"])

# 导出控件树（调试用）
ui_tree = client.dump_ui_tree()
```

**方式三：直接调用 Android 端 HTTP API**

```bash
# 发送消息
curl -X POST http://192.168.1.100:9527/api/send_message \
  -H "Content-Type: application/json" \
  -d '{"contact": "张三", "message": "你好"}'

# 读取消息
curl -X POST http://192.168.1.100:9527/api/read_messages \
  -H "Content-Type: application/json" \
  -d '{"contact": "张三", "count": 10}'

# 创建群聊
curl -X POST http://192.168.1.100:9527/api/create_group \
  -H "Content-Type: application/json" \
  -d '{"group_name": "测试群", "members": ["张三", "李四"]}'

# 邀请入群
curl -X POST http://192.168.1.100:9527/api/invite_to_group \
  -H "Content-Type: application/json" \
  -d '{"group_name": "测试群", "members": ["王五"]}'

# 获取群成员
curl -X POST http://192.168.1.100:9527/api/get_group_members \
  -H "Content-Type: application/json" \
  -d '{"group_name": "测试群"}'

# 查看设备状态
curl http://192.168.1.100:9527/api/status

# 导出控件树
curl http://192.168.1.100:9527/api/dump_ui
```

## API 结构说明（Android RPA Server）

服务端名称为 **Android RPA Server**。规则：**多一个 app，就多一套 API**。  
每套 API 路径为 `/api/<app>/*`，能力一致（获取联系人、单聊、创建群、群管理、收发消息）。

| 应用 | 路径前缀 | 说明 |
|------|----------|------|
| **微信** | `/api/wechat/*` | 个人微信 |
| **企业微信** | `/api/wework/*` | 企业微信 |

新增应用时，在服务端 `APPS` 中追加一项并在设备端实现对应 `app_type` 即可自动多出一套接口。

每套均提供（请求体均含 `device_id`）：

| 能力 | 微信 | 企业微信 | 说明 |
|------|------|----------|------|
| 获取联系人 | `POST /api/wechat/contacts` | `POST /api/wework/contacts` | 通讯录列表（当前页） |
| 单聊-发消息 | `POST /api/wechat/send_message` | `POST /api/wework/send_message` | `contact`, `message` |
| 单聊-收消息 | `POST /api/wechat/read_messages` | `POST /api/wework/read_messages` | `contact`, `count` |
| 创建群 | `POST /api/wechat/create_group` | `POST /api/wework/create_group` | `group_name`, `members[]` |
| 群管理-邀请 | `POST /api/wechat/invite_to_group` | `POST /api/wework/invite_to_group` | `group_name`, `members[]` |
| 群管理-移除 | `POST /api/wechat/remove_from_group` | `POST /api/wework/remove_from_group` | `group_name`, `members[]` |
| 群管理-成员列表 | `POST /api/wechat/group_members` | `POST /api/wework/group_members` | `group_name` |

示例（企业微信）：

```bash
# 获取联系人
curl -X POST http://localhost:8080/api/wework/contacts -H "Content-Type: application/json" -d '{"device_id":"device_1"}'

# 发消息
curl -X POST http://localhost:8080/api/wework/send_message -H "Content-Type: application/json" \
  -d '{"device_id":"device_1","contact":"张三","message":"你好"}'
```

微信只需将路径改为 `/api/wechat/*`，请求体格式相同。

### 微信（个人微信）操作说明与排查

本方案**同时支持企业微信和微信**，但实现方式不同：

| 项目 | 企业微信 | 微信（个人） |
|------|----------|--------------|
| 控件定位 | 使用 `resource-id`（WeworkIds） | **无**企微 ID，依赖文案、`contentDescription`、首个 EditText |
| 通讯录 | 点击「通讯录」Tab | 同上，进入通讯录后采集列表 |
| 发消息 | 输入框/发送按钮用 ID | 首个输入框 + 文案「发送」或 contentDescription「发送」 |

**若微信无法操作，请按下面排查：**

1. **无障碍已声明目标应用**  
   在 `RpaAccessibilityService.onServiceConnected()` 中已设置 `packageNames = ["com.tencent.mm", "com.tencent.wework"]`。  
   **若未生效**：在系统设置中关闭本 RPA 的无障碍后再重新打开，确保已勾选「微信」。

2. **操作前必须处于微信前台**  
   获取通讯录/发消息前，会先 `goToMainPage(WECHAT)` 启动或回到微信主页。  
   **若手机在别的应用**：RPA 会先尝试返回再启动微信，请确保手机已安装并登录微信。

3. **微信版本/界面变化**  
   若微信改版导致「搜索」「发送」等文案或结构变化，需用 `dump_ui` 导出当前页面控件树，按需在 `WeworkOperator` 中增加文案或 `contentDescription` 的 fallback。

4. **测试顺序**  
   先用 `python scripts/test_wechat_rpa.py` 只测通讯录；成功后再测 `--send "昵称" "内容"`。  
   若通讯录能拉取、发消息失败，多为聊天页输入框或发送按钮未匹配到，可用 `dump_ui` 查看当前聊天页节点。

## API 完整参考

### Android 端 API（端口 9527）

请求体可带 `app_type`: `"wechat"` | `"wework"`，默认 `"wework"`。

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| GET | `/api/status` | - | 获取服务状态 |
| POST | `/api/send_message` | `contact`, `message`, `app_type?` | 发送文本消息 |
| POST | `/api/read_messages` | `contact`, `count`, `app_type?` | 读取最新消息 |
| POST | `/api/create_group` | `group_name`, `members[]`, `app_type?` | 创建群聊 |
| POST | `/api/invite_to_group` | `group_name`, `members[]` | 邀请入群 |
| POST | `/api/remove_from_group` | `group_name`, `members[]` | 移除群成员 |
| POST | `/api/get_group_members` | `group_name` | 获取群成员列表 |
| GET | `/api/dump_ui` | - | 导出控件树（调试） |
| GET | `/api/task_result/{id}` | - | 查询异步任务结果 |

### Python 服务端 API（端口 8080）

启动后访问 `http://localhost:8080/docs` 查看完整的 Swagger 交互文档。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/devices` | 获取所有设备列表 |
| GET | `/api/devices/online` | 获取在线设备 |
| GET | `/api/devices/{id}/status` | 获取设备详细状态 |
| POST | `/api/send_message` | 发送消息（指定设备） |
| POST | `/api/read_messages` | 读取消息（指定设备） |
| POST | `/api/create_group` | 创建群聊 |
| POST | `/api/invite_to_group` | 邀请入群 |
| POST | `/api/remove_from_group` | 移除群成员 |
| POST | `/api/get_group_members` | 获取群成员 |
| POST | `/api/broadcast` | 向所有在线设备广播消息 |
| GET | `/api/devices/{id}/dump_ui` | 导出控件树 |

## 控件ID校准指南

企业微信每次版本更新都可能导致控件的 `resource-id` 发生变化，这是 UI 自动化方案的固有挑战。

**校准步骤：**

```bash
# 1. 在手机上打开企业微信，进入目标页面（如聊天页面）

# 2. 调用导出控件树API
curl http://192.168.1.100:9527/api/dump_ui | python -m json.tool

# 3. 在输出的控件树中搜索目标元素
#    例如搜索 "发送" 按钮、"搜索" 输入框等

# 4. 更新 WeworkOperator.kt 中 WeworkIds 对象的常量值
#    例如: const val CHAT_SEND_BTN = "com.tencent.wework:id/新ID"

# 5. 重新编译安装 APK
```

**推荐工具：** 使用 Android Studio 的 **Layout Inspector** 或 `uiautomatorviewer` 可以更直观地查看控件层级。

## 核心技术原理

### AccessibilityService 工作机制

```
                    ┌──────────────────┐
                    │   Android 系统    │
                    │  AccessibilityManager
                    └────────┬─────────┘
                             │ 注册/回调
                             ▼
┌────────────────────────────────────────────────┐
│         RpaAccessibilityService                 │
│                                                  │
│  onServiceConnected()                            │
│    → 服务启动，获取系统级权限                       │
│                                                  │
│  onAccessibilityEvent(event)                     │
│    → 监听窗口变化、内容变化等事件                   │
│    → 记录当前前台应用包名和Activity                 │
│                                                  │
│  rootInActiveWindow                              │
│    → 获取当前窗口的完整控件树                       │
│    → 遍历树查找目标控件                            │
│                                                  │
│  performAction()                                 │
│    → ACTION_CLICK: 模拟点击                       │
│    → ACTION_SET_TEXT: 输入文本                     │
│    → ACTION_SCROLL_FORWARD: 滚动                  │
│                                                  │
│  dispatchGesture()                               │
│    → 模拟复杂手势（滑动、长按等）                   │
│    → 当 performAction 失效时的兜底方案              │
└────────────────────────────────────────────────┘
```

### 关键类职责

| 类 | 层级 | 职责 |
|----|------|------|
| `RpaAccessibilityService` | 系统层 | Android无障碍服务，提供控件查找和模拟操作的底层能力 |
| `NodeHelper` | 工具层 | 封装常用的控件查找方法（按ID/文本/类名/滚动查找等） |
| `WeworkOperator` | 业务层 | 封装企业微信的具体操作流程（搜索、发消息、拉群、群管理等） |
| `TaskController` | 调度层 | 任务队列管理，确保UI操作串行执行，避免冲突 |
| `HttpServerService` | 接口层 | 基于NanoHTTPD的HTTP服务器，将操作能力暴露为REST API |
| `DeviceClient` | SDK层 | Python客户端，封装HTTP调用，提供简洁的Python API |
| `DeviceManager` | 管理层 | 多设备管理，支持设备注册、状态监控、任务分发 |

### 多账号托管架构

```
┌──────────────────────────────────────────┐
│           Python 服务端 (FastAPI)          │
│          DeviceManager 多设备管理          │
└──┬──────────┬──────────┬────────────────┘
   │          │          │
   ▼          ▼          ▼
┌──────┐  ┌──────┐  ┌──────┐
│设备 1 │  │设备 2 │  │设备 N │    ← 物理手机 / 云手机
│企微A  │  │企微B  │  │企微N  │
│:9527  │  │:9527  │  │:9527  │
└──────┘  └──────┘  └──────┘
```

每台设备独立运行 RPA App，Python 服务端通过 HTTP API 统一管理和调度。

## 前端与实时画面

项目自带前端控制台，启动服务端后访问 **http://localhost:8080/** 即可使用：

| 功能 | 说明 |
|------|------|
| **设备管理** | 展示已配置设备及在线状态（来自 `/api/devices`、`/api/devices/online`） |
| **应用管理** | 展示已注册应用及 API 前缀（来自 `/api/apps`） |
| **实时画面** | 在浏览器中查看手机当前界面，便于观察 RPA 操作流程 |

**启用实时画面**（可选）：

1. 本机已安装 Android SDK Platform-Tools，且手机已通过 USB 连接并开启 USB 调试。
2. 在 `server/config/__init__.py` 中配置：
   - **ADB_PATH**：adb 可执行文件路径，如 `"/Users/xxx/Library/Android/sdk/platform-tools/adb"`；留空则使用系统 PATH 中的 `adb`。
   - **DEVICES\["device_1"\]\["adb_serial"\]**：该设备对应的 adb 序列号（运行 `adb devices` 可见）；多台设备时必填，单台可留空使用默认设备。

未配置或未连接时，前端「实时画面」会提示 ADB 未配置或设备未连接，不影响设备管理与应用管理。

## 调试与日志

用 adb 查看日志时，系统/ROM 会打印大量无关信息。**只看本应用**可过滤包名或 TAG：

```bash
# 仅 WeChat RPA 相关（推荐）
adb logcat -v time | grep -E "wechatrpa|HttpServerService|RpaHttpServer"

# 含崩溃堆栈
adb logcat -v time | grep -E "wechatrpa|HttpServerService|RpaHttpServer|AndroidRuntime|FATAL"
```

未出现上述 TAG 的 Exception 一般来自系统或其它应用，可忽略。

## 风险提示

1. **封号风险**：自动化操作企业微信存在违反其用户协议的风险，可能导致账号被限制或封禁。
2. **版本兼容**：企业微信版本更新会导致控件ID变化，需要定期校准 `WeworkIds`。
3. **操作节奏**：代码中已内置随机延迟模拟人类操作节奏，但不能完全规避风控。
4. **异常处理**：生产环境需要补充更完善的异常处理逻辑（弹窗处理、网络异常、应用崩溃恢复等）。
5. **合规使用**：请遵守相关法律法规和平台规则，仅用于合法合规的场景。

## 参考项目

- [WorkTool](https://github.com/gallonyin/worktool) - 企微无障碍服务机器人（3k+ Stars，本项目架构参考）
- [openatx/uiautomator2](https://github.com/openatx/uiautomator2) - Android UI自动化框架（旧方案参考）
- [NanoHTTPD](https://github.com/NanoHttpd/nanohttpd) - 轻量级Java HTTP服务器

## License

Apache License 2.0
