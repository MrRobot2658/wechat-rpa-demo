# API 参考文档

## 一、Android 端 HTTP API

**Base URL:** `http://<手机IP>:9527`

所有 POST 请求的 Content-Type 均为 `application/json`。

### 1.1 获取服务状态

```
GET /api/status
```

**响应示例：**
```json
{
  "code": 200,
  "success": true,
  "message": "ok",
  "data": {
    "accessibility_enabled": true,
    "current_package": "com.tencent.wework",
    "current_class": "com.tencent.wework.launch.LaunchSplashActivity",
    "task_queue_size": 0,
    "http_server": true
  }
}
```

### 1.2 发送消息

```
POST /api/send_message
```

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| contact | string | 是 | 联系人或群组名称 |
| message | string | 是 | 消息内容 |

**请求示例：**
```json
{
  "contact": "张三",
  "message": "你好，这是一条测试消息"
}
```

**响应示例：**
```json
{
  "code": 200,
  "success": true,
  "message": "任务已提交",
  "data": {
    "task_id": "a1b2c3d4"
  }
}
```

### 1.3 读取消息

```
POST /api/read_messages
```

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| contact | string | 是 | 联系人或群组名称 |
| count | int | 否 | 读取条数，默认10 |

**请求示例：**
```json
{
  "contact": "张三",
  "count": 5
}
```

### 1.4 创建群聊

```
POST /api/create_group
```

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| group_name | string | 否 | 群名称（创建后设置） |
| members | string[] | 是 | 初始成员列表 |

**请求示例：**
```json
{
  "group_name": "项目讨论群",
  "members": ["张三", "李四", "王五"]
}
```

### 1.5 邀请入群

```
POST /api/invite_to_group
```

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| group_name | string | 是 | 群名称 |
| members | string[] | 是 | 要邀请的成员列表 |

**请求示例：**
```json
{
  "group_name": "项目讨论群",
  "members": ["赵六", "钱七"]
}
```

### 1.6 移除群成员

```
POST /api/remove_from_group
```

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| group_name | string | 是 | 群名称 |
| members | string[] | 是 | 要移除的成员列表 |

### 1.7 获取群成员列表

```
POST /api/get_group_members
```

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| group_name | string | 是 | 群名称 |

### 1.8 导出控件树

```
GET /api/dump_ui
```

用于调试和控件ID校准，返回当前页面的完整控件树。

### 1.9 查询任务结果

```
GET /api/task_result/{task_id}
```

所有 POST 操作均为异步执行，返回 `task_id`。通过此接口查询执行结果。

**响应示例：**
```json
{
  "code": 200,
  "success": true,
  "message": "ok",
  "data": {
    "task_id": "a1b2c3d4",
    "success": true,
    "message": "消息发送成功",
    "data": null
  }
}
```

## 二、Python 服务端 API

**Base URL:** `http://<服务器IP>:8080`

启动后访问 `http://localhost:8080/docs` 查看 Swagger 交互文档。

### 2.1 设备管理

#### 获取所有设备

```
GET /api/devices
```

#### 获取在线设备

```
GET /api/devices/online
```

#### 获取设备状态

```
GET /api/devices/{device_id}/status
```

### 2.2 消息操作

#### 发送消息

```
POST /api/send_message
```

```json
{
  "device_id": "device_1",
  "contact": "张三",
  "message": "你好"
}
```

#### 读取消息

```
POST /api/read_messages
```

```json
{
  "device_id": "device_1",
  "contact": "张三",
  "count": 10
}
```

### 2.3 群管理

#### 创建群聊

```
POST /api/create_group
```

```json
{
  "device_id": "device_1",
  "group_name": "测试群",
  "members": ["张三", "李四"]
}
```

#### 邀请入群

```
POST /api/invite_to_group
```

```json
{
  "device_id": "device_1",
  "group_name": "测试群",
  "members": ["王五"]
}
```

#### 移除群成员

```
POST /api/remove_from_group
```

```json
{
  "device_id": "device_1",
  "group_name": "测试群",
  "members": ["王五"]
}
```

#### 获取群成员

```
POST /api/get_group_members
```

```json
{
  "device_id": "device_1",
  "group_name": "测试群"
}
```

### 2.4 广播

```
POST /api/broadcast
```

向所有在线设备广播消息：

```json
{
  "contact": "客户群",
  "message": "今日促销活动开始！"
}
```

### 2.5 调试

#### 导出控件树

```
GET /api/devices/{device_id}/dump_ui
```

#### 健康检查

```
GET /api/health
```

## 三、Python SDK 使用

### DeviceClient

```python
from server.core import DeviceClient

client = DeviceClient("http://192.168.1.100:9527", timeout=60)

# 同步调用（等待结果）
result = client.send_message("张三", "你好", wait=True)

# 异步调用（立即返回task_id）
result = client.send_message("张三", "你好", wait=False)
task_id = result["data"]["task_id"]

# 手动查询结果
result = client.get_task_result(task_id)
```

### DeviceManager

```python
from server.core import DeviceManager

manager = DeviceManager()
manager.add_device("d1", "http://192.168.1.100:9527", "设备1")
manager.add_device("d2", "http://192.168.1.101:9527", "设备2")

# 获取在线设备
online = manager.get_online_devices()

# 通过指定设备操作
client = manager.get_device("d1")
client.send_message("张三", "你好")

# 广播消息
manager.broadcast_message("客户群", "通知内容")
```
