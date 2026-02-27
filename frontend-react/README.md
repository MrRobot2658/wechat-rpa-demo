# Android RPA Server 前端

React + Vite，独立启动，通过环境变量连接后端 API。

## 环境

- Node 18+
- 后端已启动（默认 `http://localhost:8080`）

## 配置

复制 `.env.example` 为 `.env`，并设置后端地址：

```bash
cp .env.example .env
# 编辑 .env：VITE_API_BASE=http://localhost:8080
```

## 启动

```bash
npm install
npm run dev
```

浏览器打开 **http://localhost:5173**。

## 功能

- **设备管理**：设备列表与在线状态（调用 `/api/devices`、`/api/devices/online`）
- **应用管理**：已注册应用与 API 前缀（调用 `/api/apps`）
- **实时画面**：选择设备后点击「开始」轮询 `/api/devices/{id}/screen` 展示手机画面（需后端配置 ADB）

## 构建

```bash
npm run build
```

产物在 `dist/`，可部署到任意静态托管或与后端同域。
