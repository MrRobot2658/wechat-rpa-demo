package com.wechatrpa.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import com.wechatrpa.model.*
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

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification())

        // 启动任务控制器
        taskController.start()

        // 启动HTTP服务器
        try {
            httpServer = RpaHttpServer(PORT, taskController)
            httpServer?.start()
            Log.i(TAG, "HTTP服务器已启动，端口: $PORT")
        } catch (e: Exception) {
            Log.e(TAG, "HTTP服务器启动失败: ${e.message}")
        }
    }

    override fun onDestroy() {
        super.onDestroy()
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
        port: Int,
        private val taskController: TaskController
    ) : NanoHTTPD(port) {

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

            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.SEND_MESSAGE,
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

            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.READ_MESSAGES,
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

            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.CREATE_GROUP,
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

            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.INVITE_TO_GROUP,
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

            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.REMOVE_FROM_GROUP,
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

            val taskId = UUID.randomUUID().toString().take(8)
            val task = TaskRequest(
                taskId = taskId,
                taskType = TaskType.GET_GROUP_MEMBERS,
                params = mapOf("group_name" to groupName)
            )
            taskController.submitTask(task)

            return jsonResponse(200, true, "任务已提交", JSONObject().put("task_id", taskId))
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
