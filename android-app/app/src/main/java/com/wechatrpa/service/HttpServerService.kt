package com.wechatrpa.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import com.wechatrpa.model.AppTarget
import com.wechatrpa.model.TaskRequest
import com.wechatrpa.model.TaskResult
import com.wechatrpa.model.TaskType
import fi.iki.elonen.NanoHTTPD
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

/**
 * 内嵌HTTP服务（前台服务）
 *
 * 在Android设备上运行一个轻量级HTTP服务器（基于NanoHTTPD），
 * 对外暴露REST API，供Python服务端或其他客户端调用。
 *
 * 默认监听端口：9527
 *
 * API列表：
 *   GET  /api/status              - 获取服务状态
 *   POST /api/send_message        - 发送消息
 *   POST /api/read_messages       - 读取消息
 *   POST /api/create_group        - 创建群聊
 *   POST /api/invite_to_group     - 邀请入群
 *   POST /api/remove_from_group   - 移除群成员
 *   POST /api/get_group_members   - 获取群成员列表
 *   GET  /api/dump_ui             - 导出控件树（调试）
 *   GET  /api/task_result/{id}    - 查询任务结果
 */
class HttpServerService : Service() {

    companion object {
        private const val TAG = "HttpServerService"
        private const val PORT = 9527
        private const val CHANNEL_ID = "rpa_http_server"
        private const val NOTIFICATION_ID = 1001
    }

    private var httpServer: RpaHttpServer? = null
    private val taskController = TaskController()
    private var wakeLock: PowerManager.WakeLock? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        // 持有一个 PARTIAL_WAKE_LOCK，避免后台/熄屏时系统休眠导致 HTTP 连接被断
        val pm = getSystemService(Context.POWER_SERVICE) as? PowerManager
        wakeLock = pm?.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "$packageName:HttpServer")?.apply {
            setReferenceCounted(false)
            acquire(10 * 60 * 60 * 1000L) // 最长 10 小时，onDestroy 时 release
        }
        if (wakeLock != null) Log.i(TAG, "WakeLock 已持有，减少后台断连")

        // Android 14+ 必须传入前台服务类型，否则会抛异常导致服务无法启动
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(NOTIFICATION_ID, buildNotification(), ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(NOTIFICATION_ID, buildNotification())
        }

        // 启动任务控制器
        taskController.start()

        // 启动HTTP服务器（在后台线程避免阻塞，并显式绑定 0.0.0.0 以接受局域网连接）
        Thread {
            try {
                httpServer = RpaHttpServer("0.0.0.0", PORT, taskController)
                httpServer?.start()
                Log.i(TAG, "HTTP服务器已启动，端口: $PORT，监听 0.0.0.0")
            } catch (e: Exception) {
                Log.e(TAG, "HTTP服务器启动失败: ${e.message}", e)
            }
        }.start()
    }

    override fun onDestroy() {
        super.onDestroy()
        wakeLock?.let {
            if (it.isHeld) it.release()
            wakeLock = null
        }
        httpServer?.stop()
        taskController.stop()
        Log.i(TAG, "HTTP服务器已停止")
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID, "RPA服务", NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "保持RPA自动化服务在后台运行"
            }
            getSystemService(NotificationManager::class.java)?.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(): Notification {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
                .setContentTitle("WeChat RPA 服务运行中")
                .setContentText("HTTP API 端口: $PORT")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .build()
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
                .setContentTitle("WeChat RPA 服务运行中")
                .setContentText("HTTP API 端口: $PORT")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .build()
        }
    }

    // ====================================================================
    // 内嵌HTTP服务器实现
    // ====================================================================

    /**
     * 基于NanoHTTPD的轻量级HTTP服务器
     *
     * NanoHTTPD是一个单文件的Java HTTP服务器库，非常适合嵌入到Android应用中。
     * 依赖：implementation 'org.nanohttpd:nanohttpd:2.3.1'
     */
    class RpaHttpServer(
        hostname: String,
        port: Int,
        private val taskController: TaskController
    ) : NanoHTTPD(hostname, port) {

        override fun serve(session: IHTTPSession): Response {
            val uri = session.uri
            val method = session.method

            Log.d("RpaHttpServer", "$method $uri")

            return try {
                when {
                    // 状态查询
                    uri == "/api/status" && method == Method.GET -> handleStatus()

                    // 发送消息
                    uri == "/api/send_message" && method == Method.POST -> {
                        val body = parseBody(session)
                        handleSendMessage(body)
                    }

                    // 读取消息
                    uri == "/api/read_messages" && method == Method.POST -> {
                        val body = parseBody(session)
                        handleReadMessages(body)
                    }

                    // 创建群聊
                    uri == "/api/create_group" && method == Method.POST -> {
                        val body = parseBody(session)
                        handleCreateGroup(body)
                    }

                    // 邀请入群
                    uri == "/api/invite_to_group" && method == Method.POST -> {
                        val body = parseBody(session)
                        handleInviteToGroup(body)
                    }

                    // 移除群成员
                    uri == "/api/remove_from_group" && method == Method.POST -> {
                        val body = parseBody(session)
                        handleRemoveFromGroup(body)
                    }

                    // 获取群成员
                    uri == "/api/get_group_members" && method == Method.POST -> {
                        val body = parseBody(session)
                        handleGetGroupMembers(body)
                    }

                    // 获取联系人列表
                    uri == "/api/get_contact_list" && (method == Method.GET || method == Method.POST) -> {
                        val body = if (method == Method.POST) parseBody(session) else JSONObject()
                        handleGetContactList(body)
                    }

                    // 导出控件树
                    uri == "/api/dump_ui" && method == Method.GET -> handleDumpUi()

                    // 查询任务结果
                    uri.startsWith("/api/task_result/") && method == Method.GET -> {
                        val taskId = uri.removePrefix("/api/task_result/")
                        handleTaskResult(taskId)
                    }

                    else -> jsonResponse(404, false, "API not found: $uri")
                }
            } catch (e: Exception) {
                Log.e("RpaHttpServer", "请求处理异常: ${e.message}", e)
                jsonResponse(500, false, "Internal error: ${e.message}")
            }
        }

        // --- 辅助：从 body 解析目标应用 ---
        private fun appTargetFromBody(body: JSONObject): AppTarget {
            return if (body.optString("app_type", "wework").equals("wechat", ignoreCase = true)) {
                AppTarget.WECHAT
            } else {
                AppTarget.WEWORK
            }
        }

        // --- API处理方法 ---

        private fun handleStatus(): Response {
            val service = RpaAccessibilityService.instance
            val status = JSONObject().apply {
                put("accessibility_enabled", service != null)
                put("current_package", service?.currentPackage ?: "")
                put("current_class", service?.currentClassName ?: "")
                put("task_queue_size", taskController.getQueueSize())
                put("http_server", true)
            }
            return jsonResponse(200, true, "ok", status)
        }

        private fun handleSendMessage(body: JSONObject): Response {
            val contact = body.optString("contact", "")
            val message = body.optString("message", "")
            if (contact.isBlank() || message.isBlank()) {
                return jsonResponse(400, false, "缺少参数: contact, message")
            }
            val target = appTargetFromBody(body)
            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.SEND_MESSAGE,
                target = target,
                params = mapOf("contact" to contact, "message" to message)
            )
            taskController.submitTask(task)

            return jsonResponse(200, true, "任务已提交", JSONObject().put("task_id", taskId))
        }

        private fun handleReadMessages(body: JSONObject): Response {
            val contact = body.optString("contact", "")
            val count = body.optInt("count", 10)
            if (contact.isBlank()) {
                return jsonResponse(400, false, "缺少参数: contact")
            }
            val target = appTargetFromBody(body)
            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.READ_MESSAGES,
                target = target,
                params = mapOf("contact" to contact, "count" to count)
            )
            taskController.submitTask(task)

            return jsonResponse(200, true, "任务已提交", JSONObject().put("task_id", taskId))
        }

        private fun handleCreateGroup(body: JSONObject): Response {
            val groupName = body.optString("group_name", "")
            val membersArray = body.optJSONArray("members") ?: JSONArray()
            val members = (0 until membersArray.length()).map { membersArray.getString(it) }

            if (members.isEmpty()) {
                return jsonResponse(400, false, "缺少参数: members")
            }
            val target = appTargetFromBody(body)
            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.CREATE_GROUP,
                target = target,
                params = mapOf("group_name" to groupName, "members" to members)
            )
            taskController.submitTask(task)

            return jsonResponse(200, true, "任务已提交", JSONObject().put("task_id", taskId))
        }

        private fun handleInviteToGroup(body: JSONObject): Response {
            val groupName = body.optString("group_name", "")
            val membersArray = body.optJSONArray("members") ?: JSONArray()
            val members = (0 until membersArray.length()).map { membersArray.getString(it) }

            if (groupName.isBlank() || members.isEmpty()) {
                return jsonResponse(400, false, "缺少参数: group_name, members")
            }
            val target = appTargetFromBody(body)
            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.INVITE_TO_GROUP,
                target = target,
                params = mapOf("group_name" to groupName, "members" to members)
            )
            taskController.submitTask(task)

            return jsonResponse(200, true, "任务已提交", JSONObject().put("task_id", taskId))
        }

        private fun handleRemoveFromGroup(body: JSONObject): Response {
            val groupName = body.optString("group_name", "")
            val membersArray = body.optJSONArray("members") ?: JSONArray()
            val members = (0 until membersArray.length()).map { membersArray.getString(it) }

            if (groupName.isBlank() || members.isEmpty()) {
                return jsonResponse(400, false, "缺少参数: group_name, members")
            }
            val target = appTargetFromBody(body)
            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.REMOVE_FROM_GROUP,
                target = target,
                params = mapOf("group_name" to groupName, "members" to members)
            )
            taskController.submitTask(task)

            return jsonResponse(200, true, "任务已提交", JSONObject().put("task_id", taskId))
        }

        private fun handleGetGroupMembers(body: JSONObject): Response {
            val groupName = body.optString("group_name", "")
            if (groupName.isBlank()) {
                return jsonResponse(400, false, "缺少参数: group_name")
            }
            val target = appTargetFromBody(body)
            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.GET_GROUP_MEMBERS,
                target = target,
                params = mapOf("group_name" to groupName)
            )
            taskController.submitTask(task)

            return jsonResponse(200, true, "任务已提交", JSONObject().put("task_id", taskId))
        }

        private fun handleGetContactList(body: JSONObject): Response {
            val target = appTargetFromBody(body)
            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.GET_CONTACT_LIST,
                target = target
            )
            taskController.submitTask(task)
            // 轮询等待执行完成（通讯录页加载+滚动采集可能需 30s～90s，尤其后台/冷启动）
            val pollIntervalMs = 1000L
            val timeoutMs = 90_000L
            var result: TaskResult? = null
            val start = System.currentTimeMillis()
            while (System.currentTimeMillis() - start < timeoutMs) {
                result = taskController.getResult(taskId)
                if (result != null) break
                Thread.sleep(pollIntervalMs)
            }
            if (result == null) result = taskController.getResult(taskId)
            val data = when (val d = result?.data) {
                is List<*> -> JSONArray(d.map { it.toString() })
                else -> d
            }
            return if (result != null && result.success) {
                jsonResponse(200, true, result.message, data)
            } else {
                jsonResponse(200, result?.success == true, result?.message ?: "获取联系人列表失败", data)
            }
        }

        private fun handleDumpUi(): Response {
            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(taskId = taskId, taskType = TaskType.DUMP_UI_TREE)
            taskController.submitTask(task)

            // 同步等待结果（调试接口，可以等待）
            Thread.sleep(2000)
            val result = taskController.getResult(taskId)
            return if (result != null) {
                jsonResponse(200, result.success, result.message, result.data?.toString() ?: "")
            } else {
                jsonResponse(200, true, "任务已提交，请通过 /api/task_result/$taskId 查询结果",
                    JSONObject().put("task_id", taskId))
            }
        }

        private fun handleTaskResult(taskId: String): Response {
            val result = taskController.getResult(taskId)
            return if (result != null) {
                val data = JSONObject().apply {
                    put("task_id", result.taskId)
                    put("success", result.success)
                    put("message", result.message)
                    put("data", result.data?.toString() ?: "")
                }
                jsonResponse(200, true, "ok", data)
            } else {
                jsonResponse(200, false, "任务结果未找到或仍在执行中")
            }
        }

        // --- 工具方法 ---

        private fun parseBody(session: IHTTPSession): JSONObject {
            val files = mutableMapOf<String, String>()
            session.parseBody(files)
            val bodyStr = files["postData"] ?: ""
            return if (bodyStr.isNotBlank()) JSONObject(bodyStr) else JSONObject()
        }

        private fun jsonResponse(
            code: Int,
            success: Boolean,
            message: String,
            data: Any? = null
        ): Response {
            val json = JSONObject().apply {
                put("code", code)
                put("success", success)
                put("message", message)
                if (data != null) put("data", data)
            }
            return newFixedLengthResponse(
                Response.Status.lookup(code) ?: Response.Status.OK,
                "application/json",
                json.toString()
            )
        }
    }
}
