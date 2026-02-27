package com.wechatrpa.service

import android.util.Log
import com.wechatrpa.model.AppTarget
import com.wechatrpa.model.TaskRequest
import com.wechatrpa.model.TaskResult
import com.wechatrpa.model.TaskType
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.concurrent.thread

/**
 * 任务控制器
 *
 * 负责接收来自HTTP API的任务请求，放入队列中顺序执行。
 * 采用单线程串行执行模型，确保UI操作不会互相冲突。
 *
 * 架构角色：
 *   HttpServer --> TaskController --> WeworkOperator --> RpaAccessibilityService
 */
class TaskController {

    companion object {
        private const val TAG = "TaskController"
    }

    private val taskQueue = ConcurrentLinkedQueue<TaskRequest>()
    private val isRunning = AtomicBoolean(false)
    private val weworkOperator = WeworkOperator()
    private val resultMap = mutableMapOf<String, TaskResult>()

    /**
     * 启动任务执行循环
     */
    fun start() {
        if (isRunning.getAndSet(true)) {
            Log.w(TAG, "任务控制器已在运行中")
            return
        }
        Log.i(TAG, "任务控制器启动")
        thread(name = "TaskExecutor", isDaemon = true) {
            while (isRunning.get()) {
                val task = taskQueue.poll()
                if (task != null) {
                    executeTask(task)
                } else {
                    Thread.sleep(200) // 队列为空时短暂休眠
                }
            }
            Log.i(TAG, "任务控制器已停止")
        }
    }

    /**
     * 停止任务执行
     */
    fun stop() {
        isRunning.set(false)
        Log.i(TAG, "任务控制器停止中...")
    }

    /**
     * 提交任务到队列
     */
    fun submitTask(task: TaskRequest): String {
        taskQueue.offer(task)
        Log.i(TAG, "任务已入队: ${task.taskId} (${task.taskType}), 队列大小: ${taskQueue.size}")
        return task.taskId
    }

    /**
     * 查询任务结果
     */
    fun getResult(taskId: String): TaskResult? {
        return resultMap[taskId]
    }

    /**
     * 获取队列大小
     */
    fun getQueueSize(): Int = taskQueue.size

    /**
     * 执行单个任务
     */
    private fun executeTask(task: TaskRequest) {
        Log.i(TAG, "开始执行任务: ${task.taskId} (${task.taskType})")
        val startTime = System.currentTimeMillis()

        val result = try {
            when (task.taskType) {
                TaskType.SEND_MESSAGE -> {
                    val contact = task.getString("contact")
                    val message = task.getString("message")
                    if (contact.isBlank() || message.isBlank()) {
                        TaskResult(task.taskId, false, "缺少参数: contact 或 message")
                    } else {
                        val r = weworkOperator.sendMessage(contact, message, task.target)
                        r.copy(taskId = task.taskId)
                    }
                }

                TaskType.READ_MESSAGES -> {
                    val contact = task.getString("contact")
                    val count = task.getInt("count", 10)
                    if (contact.isBlank()) {
                        TaskResult(task.taskId, false, "缺少参数: contact")
                    } else {
                        val r = weworkOperator.readMessagesFrom(contact, count, task.target)
                        r.copy(taskId = task.taskId)
                    }
                }

                TaskType.CREATE_GROUP -> {
                    val groupName = task.getString("group_name")
                    val members = task.getStringList("members")
                    if (members.isEmpty()) {
                        TaskResult(task.taskId, false, "缺少参数: members")
                    } else {
                        val r = weworkOperator.createGroup(groupName, members, task.target)
                        r.copy(taskId = task.taskId)
                    }
                }

                TaskType.INVITE_TO_GROUP -> {
                    val groupName = task.getString("group_name")
                    val members = task.getStringList("members")
                    if (groupName.isBlank() || members.isEmpty()) {
                        TaskResult(task.taskId, false, "缺少参数: group_name 或 members")
                    } else {
                        val r = weworkOperator.inviteToGroup(groupName, members, task.target)
                        r.copy(taskId = task.taskId)
                    }
                }

                TaskType.REMOVE_FROM_GROUP -> {
                    val groupName = task.getString("group_name")
                    val members = task.getStringList("members")
                    if (groupName.isBlank() || members.isEmpty()) {
                        TaskResult(task.taskId, false, "缺少参数: group_name 或 members")
                    } else {
                        val r = weworkOperator.removeFromGroup(groupName, members, task.target)
                        r.copy(taskId = task.taskId)
                    }
                }

                TaskType.GET_GROUP_MEMBERS -> {
                    val groupName = task.getString("group_name")
                    if (groupName.isBlank()) {
                        TaskResult(task.taskId, false, "缺少参数: group_name")
                    } else {
                        val r = weworkOperator.getGroupMembers(groupName, task.target)
                        r.copy(taskId = task.taskId)
                    }
                }

                TaskType.GET_CONTACT_LIST -> {
                    val r = weworkOperator.getContactList(task.target)
                    r.copy(taskId = task.taskId)
                }

                TaskType.DUMP_UI_TREE -> {
                    val tree = weworkOperator.dumpUiTree()
                    TaskResult(task.taskId, true, "控件树导出成功", tree)
                }

                else -> {
                    TaskResult(task.taskId, false, "不支持的任务类型: ${task.taskType}")
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "任务执行异常: ${e.message}", e)
            TaskResult(task.taskId, false, "执行异常: ${e.message}")
        }

        val elapsed = System.currentTimeMillis() - startTime
        Log.i(TAG, "任务完成: ${task.taskId} (${result.success}) 耗时: ${elapsed}ms")

        // 保存结果（最多保留1000条）
        resultMap[task.taskId] = result
        if (resultMap.size > 1000) {
            val oldest = resultMap.keys.firstOrNull()
            if (oldest != null) resultMap.remove(oldest)
        }
    }
}
