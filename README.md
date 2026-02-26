# Android 微信/企业微信 RPA 账号托管技术栈与Demo

本项目旨在提供一个基于 Android 客户端的微信和企业微信 RPA（机器人流程自动化）账号托管解决方案。方案使用 Python 和 `uiautomator2` 库，通过模拟人类在屏幕上的操作来实现自动化，不涉及任何协议破解，但强依赖于客户端的 UI 布局。

**免责声明：** 本项目仅用于技术研究和学习目的。自动化操作微信/企业微信可能违反其用户协议，存在被限制功能甚至封号的风险。使用者必须自行承担所有风险和后果。**强烈不建议将此方案用于任何商业或关键业务场景。**

## 项目结构

```
wechat-rpa-demo/
├── config/                  # 配置文件
│   ├── __init__.py
│   └── settings.py          # 核心配置，包括设备序列号、包名、控件ID等
├── common/                  # 通用基础模块
│   ├── __init__.py
│   ├── base_bot.py          # RPA机器人基类，封装通用UI操作
│   ├── device_manager.py    # 设备管理器，封装ADB命令
│   └── utils.py             # 工具函数（日志、延迟等）
├── wechat/                  # 微信Bot模块
│   ├── __init__.py
│   └── wechat_bot.py        # 微信RPA核心逻辑
├── wework/                  # 企业微信Bot模块
│   ├── __init__.py
│   └── wework_bot.py        # 企业微信RPA核心逻辑
├── docs/                    # 文档目录
│   └── ...
├── demo_wechat.py           # 微信收发消息演示脚本
├── demo_wework.py           # 企业微信收发消息演示脚本
├── tool_calibrate_ids.py    # UI控件ID校准工具
├── requirements.txt         # Python依赖
└── README.md                # 本文档
```

## 技术栈核心

| 技术点 | 工具/库 | 作用 |
| :--- | :--- | :--- |
| **核心自动化框架** | `uiautomator2` | Google官方UI测试框架的Python封装，稳定、强大，用于驱动Android设备。 |
| **设备连接与管理** | `adbutils` | `uiautomator2`的依赖库，封装了ADB（Android调试桥）命令，用于设备发现、应用安装、文件传输等。 |
| **UI元素定位** | `weditor` / `uiautodev` | 基于Web的UI查看器，可以实时查看手机屏幕，并获取UI控件的`resource-id`、`text`、`xpath`等属性，是RPA脚本编写的关键辅助工具。 |
| **编程语言** | Python 3 | 简单易学，拥有强大的生态系统，是自动化脚本编写的首选语言。 |
| **运行环境** | 物理Android手机 / Android模拟器 | 脚本需要在一个真实的Android环境中运行，模拟器（如MuMu、雷电）或云手机均可。 |

## 环境准备与部署指南

### 1. 软件依赖

- **Python 3.8+**
- **ADB (Android Debug Bridge)**: 确保已安装并配置到系统环境变量。可以从 [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools) 下载。

### 2. 安装Python库

在项目根目录下，运行以下命令安装所有必要的Python库：

```bash
# 建议在虚拟环境中安装
# python -m venv venv
# source venv/bin/activate  (Linux/macOS)
# venv\Scripts\activate  (Windows)

pip install -r requirements.txt
```

### 3. 准备Android设备

- **开启开发者选项**：通常在“设置” -> “关于手机”中连续点击“版本号”7次。
- **开启USB调试**：在“开发者选项”中找到并启用“USB调试”和“USB调试（安全设置）”。
- **连接设备**：使用USB数据线将手机连接到电脑，并在手机弹出的授权窗口中选择“允许”。
- **验证连接**：在电脑终端运行 `adb devices`，如果看到你的设备序列号和 `device` 状态，说明连接成功。

### 4. 初始化 `uiautomator2`

`uiautomator2` 需要在手机上安装一个名为 `atx-agent` 的守护进程来接收和执行指令。运行以下命令进行自动安装：

```bash
python -m uiautomator2 init
```

此过程会自动下载并安装所需服务到手机。如果安装失败，请检查网络连接和手机权限。

### 5. 校准UI控件ID（**非常重要**）

微信和企业微信的UI `resource-id` 会随着版本更新而频繁变化，直接运行Demo很可能会因为ID不匹配而失败。**在运行Demo前，必须先校准ID**。

1.  在手机上，手动打开微信或企业微信，并导航到你想要自动化的页面（例如，与“文件传输助手”的聊天界面）。
2.  运行校准工具：

    ```bash
    python tool_calibrate_ids.py
    ```

3.  脚本会截取当前屏幕，并打印出所有带有 `resource-id` 的控件信息。
4.  根据打印出的ID，**手动更新 `config/settings.py` 文件中 `WECHAT_IDS` 或 `WEWORK_IDS` 字典里的值**。

    > **专业提示**：使用 `weditor` (通过 `python -m weditor` 启动) 可以更直观地在浏览器中实时查看和定位控件，强烈推荐在开发和调试时使用。

## 运行Demo

项目提供了两个独立的Demo脚本，分别用于演示微信和企业微信的收发消息。

### 微信Demo

运行以下命令启动微信演示脚本：

```bash
python demo_wechat.py
```

脚本会提供菜单选项：
- **发送消息**：自动打开微信，找到“文件传输助手”，并发送一条测试消息。
- **读取最新消息**：打开与“文件传输助手”的聊天窗口，并读取最新的几条消息。
- **监听消息并自动回复**：持续监听“文件传输助手”的新消息，并根据预设规则进行自动回复（按 `Ctrl+C` 停止）。

### 企业微信Demo

运行以下命令启动企业微信演示脚本：

```bash
python demo_wework.py
```

功能与微信Demo类似，操作对象同样是“文件传输助手”。

## 核心风险与注意事项

1.  **UI易变性**：RPA方案的**最大弱点**。微信/企业微信的任何UI更新都可能导致`resource-id`或控件结构变化，从而使脚本失效。需要持续维护和更新ID配置。
2.  **风控与封号**：模拟器、root设备、以及过于快速和规律的自动化操作都可能触发平台的风控策略，导致功能限制甚至封号。代码中的 `human_delay` 函数试图通过随机延迟模拟人类行为，但不能完全规避风险。
3.  **异常处理**：健壮的RPA系统需要处理各种异常，如网络中断、应用崩溃、系统弹窗（权限申请、低电量提醒等）。本Demo仅为基础演示，未包含复杂的异常处理逻辑。
4.  **多账号托管**：在单台PC上实现多账号托管通常需要借助**虚拟机**或**应用多开工具**来创建隔离的环境。在服务器端，则普遍采用“**云手机集群**”方案，通过在大量虚拟手机实例上运行RPA脚本来实现规模化托管，但这同样面临严峻的风控挑战。

## 结论

基于 `uiautomator2` 的RPA方案为微信和企业微信的自动化提供了一条技术上可行的路径。然而，由于其固有的脆弱性和合规风险，该方案仅适用于个人自动化探索或非关键性任务。对于任何需要高可靠性和安全性的企业级应用，**强烈建议优先使用官方提供的API接口**（如企业微信API、微信开放平台、公众号/小程序API）进行开发。
