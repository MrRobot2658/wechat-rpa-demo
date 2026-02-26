package com.wechatrpa.model

/**
 * 目标应用枚举
 */
enum class AppTarget(val packageName: String, val label: String) {
    WECHAT("com.tencent.mm", "微信"),
    WEWORK("com.tencent.wework", "企业微信");

    companion object {
        fun fromPackage(pkg: String): AppTarget? = values().firstOrNull { it.packageName == pkg }
    }
}

/**
 * 任务类型枚举
 */
enum class TaskType {
    SEND_MESSAGE,       // 发送消息
    READ_MESSAGES,      // 读取消息
    CREATE_GROUP,       // 创建群聊
    INVITE_TO_GROUP,    // 邀请入群
    REMOVE_FROM_GROUP,  // 踢出群聊
    GET_GROUP_MEMBERS,  // 获取群成员
    ADD_FRIEND,         // 添加好友
    ACCEPT_FRIEND,      // 通过好友请求
    GET_CONTACT_LIST,   // 获取联系人列表
    DUMP_UI_TREE,       // 导出控件树（调试）
}

/**
 * 任务请求
 */
data class TaskRequest(
    val taskId: String,
    val taskType: TaskType,
    val target: AppTarget = AppTarget.WEWORK,
    val params: Map<String, Any> = emptyMap()
) {
    /** 便捷取参 */
    fun getString(key: String, default: String = ""): String =
        params[key]?.toString() ?: default

    fun getStringList(key: String): List<String> =
        (params[key] as? List<*>)?.mapNotNull { it?.toString() } ?: emptyList()

    fun getInt(key: String, default: Int = 0): Int =
        (params[key] as? Number)?.toInt() ?: default

    fun getBoolean(key: String, default: Boolean = false): Boolean =
        (params[key] as? Boolean) ?: default
}

/**
 * 任务执行结果
 */
data class TaskResult(
    val taskId: String,
    val success: Boolean,
    val message: String = "",
    val data: Any? = null
)

/**
 * 聊天消息
 */
data class ChatMessage(
    val sender: String = "",
    val content: String = "",
    val timestamp: String = "",
    val isSelf: Boolean = false,
    val msgType: String = "text"  // text, image, file, link, etc.
)

/**
 * 联系人/群组信息
 */
data class ContactInfo(
    val name: String,
    val type: String = "person",  // person, group, department
    val avatar: String = "",
    val memberCount: Int = 0
)

/**
 * 服务状态
 */
data class ServiceStatus(
    val accessibilityEnabled: Boolean = false,
    val httpServerRunning: Boolean = false,
    val currentApp: String = "",
    val currentPage: String = "",
    val taskQueueSize: Int = 0
)
