"""
微信/企业微信 Android RPA 账号托管 - 全局配置
"""

# ============================================================
# 设备连接配置
# ============================================================
# 设备序列号（通过 adb devices 查看）
# 设为 None 表示自动选择第一个已连接设备
DEVICE_SERIAL = None

# 设备连接超时（秒）
CONNECT_TIMEOUT = 10

# ============================================================
# 微信配置
# ============================================================
WECHAT_PACKAGE = "com.tencent.mm"
WECHAT_MAIN_ACTIVITY = ".ui.LauncherUI"

# 微信关键控件 resource-id（需根据实际版本通过 weditor 确认）
# 以下为常见版本的 resource-id，可能随版本更新变化
WECHAT_IDS = {
    # --- 主界面 ---
    "search_btn": "com.tencent.mm:id/icon_search",          # 搜索按钮（放大镜图标）
    "search_input": "com.tencent.mm:id/cd7",                # 搜索输入框
    "search_clear": "com.tencent.mm:id/iv_clear",           # 搜索清除按钮

    # --- 聊天界面 ---
    "chat_input": "com.tencent.mm:id/al_",                  # 聊天输入框
    "chat_send_btn": "com.tencent.mm:id/b8k",               # 发送按钮
    "chat_msg_list": "com.tencent.mm:id/bn1",               # 消息列表 RecyclerView
    "chat_title": "com.tencent.mm:id/obn",                  # 聊天标题（联系人名称）

    # --- 消息气泡 ---
    "msg_text": "com.tencent.mm:id/bkl",                    # 文本消息内容
    "msg_nickname": "com.tencent.mm:id/bk0",                # 消息发送者昵称

    # --- 底部导航 ---
    "tab_chat": "微信",                                      # 底部Tab - 微信
    "tab_contacts": "通讯录",                                 # 底部Tab - 通讯录
    "tab_discover": "发现",                                   # 底部Tab - 发现
    "tab_me": "我",                                          # 底部Tab - 我
}

# ============================================================
# 企业微信配置
# ============================================================
WEWORK_PACKAGE = "com.tencent.wework"
WEWORK_MAIN_ACTIVITY = ".launch.LaunchSplashActivity"

# 企业微信关键控件 resource-id
WEWORK_IDS = {
    # --- 主界面 ---
    "search_btn": "com.tencent.wework:id/gy3",              # 搜索按钮
    "search_input": "com.tencent.wework:id/gy6",            # 搜索输入框

    # --- 聊天界面 ---
    "chat_input": "com.tencent.wework:id/input_et",         # 聊天输入框
    "chat_send_btn": "com.tencent.wework:id/send_btn",      # 发送按钮
    "chat_msg_list": "com.tencent.wework:id/msg_list",      # 消息列表
    "chat_title": "com.tencent.wework:id/title_name",       # 聊天标题

    # --- 消息气泡 ---
    "msg_text": "com.tencent.wework:id/msg_content",        # 文本消息内容
    "msg_nickname": "com.tencent.wework:id/msg_name",       # 消息发送者昵称

    # --- 底部导航 ---
    "tab_msg": "消息",
    "tab_contacts": "通讯录",
    "tab_workbench": "工作台",
    "tab_me": "我",
}

# ============================================================
# RPA 行为参数（模拟人类操作的随机延迟）
# ============================================================
# 操作间隔（秒）- [最小值, 最大值]
DELAY_AFTER_CLICK = [0.5, 1.5]
DELAY_AFTER_INPUT = [0.3, 0.8]
DELAY_AFTER_SEARCH = [1.5, 3.0]
DELAY_AFTER_SEND = [0.5, 1.0]
DELAY_PAGE_LOAD = [2.0, 4.0]

# 消息轮询间隔（秒）
MSG_POLL_INTERVAL = 3

# 最大重试次数
MAX_RETRY = 3

# ============================================================
# 日志配置
# ============================================================
LOG_LEVEL = "INFO"
LOG_FILE = "rpa_bot.log"
