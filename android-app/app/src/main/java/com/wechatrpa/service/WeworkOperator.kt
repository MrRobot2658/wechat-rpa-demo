package com.wechatrpa.service

import android.content.Intent
import android.net.Uri
import android.util.Log
import com.wechatrpa.model.*
import com.wechatrpa.utils.NodeHelper

/**
 * 企业微信自动化操作实现
 *
 * 本类封装了对企业微信客户端的所有自动化操作，包括：
 * - 搜索联系人/群组
 * - 发送文本消息
 * - 读取聊天消息
 * - 创建群聊
 * - 邀请/移除群成员
 *
 * 所有操作均通过 RpaAccessibilityService 提供的控件查找和模拟点击能力实现，
 * 不涉及任何协议层面的操作。
 *
 * 注意：控件ID（resource-id）会随企业微信版本更新而变化，
 * 需要通过 dumpUiTree() 方法获取最新ID并更新 WeworkIds 对象。
 */
class WeworkOperator {

    companion object {
        private const val TAG = "WeworkOperator"

        /** 操作间隔（毫秒），模拟人类操作节奏，降低风控风险 */
        private const val DELAY_SHORT = 500L
        private const val DELAY_MEDIUM = 1000L
        private const val DELAY_LONG = 2000L
        private const val DELAY_PAGE_LOAD = 3000L
    }

    private val service: RpaAccessibilityService?
        get() = RpaAccessibilityService.instance

    // ====================================================================
    // 企业微信控件ID配置
    // 重要：这些ID会随版本更新变化，需要通过 dumpUiTree() 校准
    // ====================================================================
    object WeworkIds {
        // --- 主页 ---
        const val TAB_MESSAGE = "com.tencent.wework:id/hn5"      // 底部Tab-消息
        const val TAB_CONTACTS = "com.tencent.wework:id/hn7"     // 底部Tab-通讯录
        const val SEARCH_BTN = "com.tencent.wework:id/hfp"       // 主页搜索按钮
        const val SEARCH_INPUT = "com.tencent.wework:id/cd7"     // 搜索输入框

        // --- 聊天页 ---
        const val CHAT_INPUT = "com.tencent.wework:id/b4o"       // 聊天输入框
        const val CHAT_SEND_BTN = "com.tencent.wework:id/b5d"    // 发送按钮
        const val CHAT_MSG_LIST = "com.tencent.wework:id/auj"    // 消息列表
        const val CHAT_MSG_TEXT = "com.tencent.wework:id/aum"    // 消息文本内容
        const val CHAT_TITLE = "com.tencent.wework:id/ams"       // 聊天标题（联系人名）
        const val CHAT_MORE_BTN = "com.tencent.wework:id/amw"    // 聊天页右上角更多按钮

        // --- 群管理 ---
        const val GROUP_MEMBER_ADD = "com.tencent.wework:id/c0g"  // 群成员添加按钮（+号）
        const val GROUP_MEMBER_DEL = "com.tencent.wework:id/c0h"  // 群成员删除按钮（-号）
        const val GROUP_NAME = "com.tencent.wework:id/bz8"        // 群名称

        // 提示：以上ID基于企业微信 4.1.x 版本，不同版本需要重新校准
        // 使用 dumpUiTree() 方法可以导出当前页面的完整控件树
    }

    // ====================================================================
    // 导航操作
    // ====================================================================

    /**
     * 启动指定应用（微信或企业微信）
     */
    fun launchApp(target: AppTarget): Boolean {
        return try {
            val ctx = service?.applicationContext ?: return false
            val intent = ctx.packageManager.getLaunchIntentForPackage(target.packageName)
            intent?.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            ctx.startActivity(intent)
            Thread.sleep(DELAY_PAGE_LOAD)
            Log.i(TAG, "${target.label}已启动")
            true
        } catch (e: Exception) {
            Log.e(TAG, "启动${target.label}失败: ${e.message}")
            false
        }
    }

    /** 兼容旧调用 */
    fun launchWework(): Boolean = launchApp(AppTarget.WEWORK)

    /**
     * 回到主页（按 target 判断是否在对应应用主页）
     * 若需启动应用，会等待目标应用主页出现（微信加载较慢时多等几秒）
     */
    fun goToMainPage(target: AppTarget = AppTarget.WEWORK): Boolean {
        for (i in 0..5) {
            if (NodeHelper.isInMainPage(target)) {
                Log.i(TAG, "已回到主页")
                return true
            }
            service?.pressBack()
            Thread.sleep(DELAY_SHORT)
        }
        if (!launchApp(target)) return false
        // 微信冷启动较慢，多等一会并轮询直到主页出现
        if (target == AppTarget.WECHAT) {
            for (w in 0..10) {
                Thread.sleep(500)
                if (NodeHelper.isInMainPage(target)) return true
            }
            Thread.sleep(2000)
        }
        return NodeHelper.isInMainPage(target)
    }

    /**
     * 搜索并打开与指定联系人/群组的聊天窗口
     */
    fun openChat(contactName: String, target: AppTarget = AppTarget.WEWORK): Boolean {
        Log.i(TAG, "搜索联系人/群组: $contactName (${target.label})")
        goToMainPage(target)
        Thread.sleep(DELAY_SHORT)

        // 微信无企微的 resource-id，优先用文案点击；企微可先用 ID
        val searchOk = if (target == AppTarget.WECHAT) {
            NodeHelper.clickText("搜索") || NodeHelper.clickId(WeworkIds.SEARCH_BTN)
        } else {
            NodeHelper.clickId(WeworkIds.SEARCH_BTN) || NodeHelper.clickText("搜索")
        }
        if (!searchOk) {
            Log.e(TAG, "无法点击搜索按钮")
            return false
        }
        Thread.sleep(DELAY_MEDIUM)
        val searchInputId = if (target == AppTarget.WEWORK) WeworkIds.SEARCH_INPUT else null
        if (!NodeHelper.inputToField(contactName, searchInputId)) {
            if (!NodeHelper.inputToField(contactName)) {
                Log.e(TAG, "无法输入搜索关键词")
                service?.pressBack()
                return false
            }
        }
        Thread.sleep(DELAY_LONG)

        // 点击搜索结果
        val resultNode = NodeHelper.scrollAndFindText(contactName, maxScrolls = 3)
        if (resultNode != null) {
            service?.clickNode(resultNode)
            Thread.sleep(DELAY_PAGE_LOAD)
            Log.i(TAG, "已打开与 '$contactName' 的聊天窗口")
            return true
        }

        Log.e(TAG, "未找到联系人/群组: $contactName")
        service?.pressBack()
        service?.pressBack()
        return false
    }

    // ====================================================================
    // 消息收发
    // ====================================================================

    /**
     * 发送文本消息
     *
     * @param contactName 联系人或群组名称
     * @param message 消息内容
     * @return 执行结果
     */
    fun sendMessage(contactName: String, message: String, target: AppTarget = AppTarget.WEWORK): TaskResult {
        Log.i(TAG, "发送消息给 '$contactName': ${message.take(50)}... (${target.label})")
        if (!openChat(contactName, target)) {
            return TaskResult("", false, "无法打开与 '$contactName' 的聊天窗口")
        }

        // 微信没有企微的 ID，优先用“第一个输入框 + 发送文案”
        val inputOk = if (target == AppTarget.WECHAT) {
            NodeHelper.inputToField(message) || NodeHelper.inputToField(message, WeworkIds.CHAT_INPUT)
        } else {
            NodeHelper.inputToField(message, WeworkIds.CHAT_INPUT) || NodeHelper.inputToField(message)
        }
        if (!inputOk) {
            return TaskResult("", false, "消息输入失败")
        }
        Thread.sleep(DELAY_SHORT)

        val sendOk = if (target == AppTarget.WECHAT) {
            NodeHelper.clickText("发送") || NodeHelper.clickContentDesc("发送") || NodeHelper.clickId(WeworkIds.CHAT_SEND_BTN)
        } else {
            NodeHelper.clickId(WeworkIds.CHAT_SEND_BTN) || NodeHelper.clickText("发送") || NodeHelper.clickContentDesc("发送")
        }
        if (!sendOk) {
            return TaskResult("", false, "发送按钮点击失败")
        }
        Thread.sleep(DELAY_SHORT)

        Log.i(TAG, "消息已发送给 '$contactName'")
        return TaskResult("", true, "消息发送成功")
    }

    /**
     * 在当前聊天窗口发送消息（不切换聊天窗口）
     */
    fun sendInCurrentChat(message: String): Boolean {
        if (!NodeHelper.inputToField(message, WeworkIds.CHAT_INPUT)) {
            if (!NodeHelper.inputToField(message)) return false
        }
        Thread.sleep(DELAY_SHORT)

        if (!NodeHelper.clickId(WeworkIds.CHAT_SEND_BTN)) {
            if (!NodeHelper.clickText("发送")) return false
        }
        return true
    }

    /**
     * 读取当前聊天窗口的最新消息
     *
     * @param count 读取条数
     */
    fun readMessages(count: Int = 10): List<ChatMessage> {
        val messages = mutableListOf<ChatMessage>()

        // 方式一：通过resource-id获取消息文本
        val msgNodes = service?.findById(WeworkIds.CHAT_MSG_TEXT) ?: emptyList()
        for (node in msgNodes.takeLast(count)) {
            val text = node.text?.toString() ?: continue
            if (text.isNotBlank()) {
                messages.add(ChatMessage(content = text, msgType = "text"))
            }
        }

        // 方式二：如果resource-id方式无结果，遍历所有TextView
        if (messages.isEmpty()) {
            val textViews = NodeHelper.findByClassName("android.widget.TextView")
            val excludeTexts = setOf("发送", "消息", "通讯录", "工作台", "我", "按住 说话", "更多", "返回")
            for (tv in textViews.takeLast(count * 2)) {
                val text = tv.text?.toString() ?: continue
                if (text.isNotBlank() && text.length > 1 && text !in excludeTexts) {
                    messages.add(ChatMessage(content = text, msgType = "text"))
                }
            }
        }

        Log.i(TAG, "读取到 ${messages.size} 条消息")
        return messages.takeLast(count)
    }

    /**
     * 读取指定联系人/群组的最新消息
     */
    fun readMessagesFrom(contactName: String, count: Int = 10, target: AppTarget = AppTarget.WEWORK): TaskResult {
        if (!openChat(contactName, target)) {
            return TaskResult("", false, "无法打开聊天窗口")
        }
        val messages = readMessages(count)
        return TaskResult("", true, "读取成功", messages)
    }

    // ====================================================================
    // 群管理操作
    // ====================================================================

    /**
     * 创建群聊
     *
     * @param groupName 群名称
     * @param members 初始成员列表
     */
    fun createGroup(groupName: String, members: List<String>, target: AppTarget = AppTarget.WEWORK): TaskResult {
        Log.i(TAG, "创建群聊: $groupName, 成员: $members")
        goToMainPage(target)
        Thread.sleep(DELAY_SHORT)
        // 点击右上角 "+" 按钮
        if (!NodeHelper.clickText("+") && !NodeHelper.clickId("com.tencent.wework:id/hfq")) {
            return TaskResult("", false, "无法点击创建按钮")
        }
        Thread.sleep(DELAY_MEDIUM)

        // 点击 "发起群聊"
        if (!NodeHelper.clickText("发起群聊")) {
            return TaskResult("", false, "无法找到'发起群聊'选项")
        }
        Thread.sleep(DELAY_PAGE_LOAD)

        // 逐个搜索并选择成员
        for (member in members) {
            // 在搜索框输入成员名称
            val searchInput = NodeHelper.findEditTexts().firstOrNull()
            if (searchInput != null) {
                service?.inputText(searchInput, member)
                Thread.sleep(DELAY_LONG)

                // 点击搜索结果中的成员
                val memberNode = NodeHelper.findByExactText(member)
                if (memberNode != null) {
                    service?.clickNode(memberNode)
                    Thread.sleep(DELAY_SHORT)
                    // 清空搜索框
                    service?.clearText(searchInput)
                    Thread.sleep(DELAY_SHORT)
                } else {
                    Log.w(TAG, "未找到成员: $member")
                }
            }
        }

        // 点击确定/完成
        if (!NodeHelper.clickText("确定") && !NodeHelper.clickText("完成")) {
            return TaskResult("", false, "无法点击确定按钮")
        }
        Thread.sleep(DELAY_PAGE_LOAD)

        // 如果需要设置群名
        if (groupName.isNotBlank()) {
            // 进入群设置修改群名
            modifyGroupName(groupName)
        }

        return TaskResult("", true, "群聊创建成功")
    }

    /**
     * 邀请成员入群
     *
     * @param groupName 群名称
     * @param members 要邀请的成员列表
     */
    fun inviteToGroup(groupName: String, members: List<String>, target: AppTarget = AppTarget.WEWORK): TaskResult {
        Log.i(TAG, "邀请入群: $groupName, 成员: $members")

        if (!openChat(groupName, target)) {
            return TaskResult("", false, "无法打开群聊: $groupName")
        }
        // 点击右上角群设置按钮
        if (!NodeHelper.clickId(WeworkIds.CHAT_MORE_BTN)) {
            return TaskResult("", false, "无法打开群设置")
        }
        Thread.sleep(DELAY_PAGE_LOAD)

        // 点击添加成员按钮（+号）
        if (!NodeHelper.clickId(WeworkIds.GROUP_MEMBER_ADD)) {
            // 备选：查找带有"+"描述的控件
            val addBtn = service?.findNode { it.contentDescription?.toString()?.contains("添加") == true }
            if (addBtn != null) {
                service?.clickNode(addBtn)
            } else {
                return TaskResult("", false, "无法找到添加成员按钮")
            }
        }
        Thread.sleep(DELAY_PAGE_LOAD)

        // 逐个搜索并选择成员
        val successList = mutableListOf<String>()
        val failList = mutableListOf<String>()

        for (member in members) {
            val searchInput = NodeHelper.findEditTexts().firstOrNull()
            if (searchInput != null) {
                service?.inputText(searchInput, member)
                Thread.sleep(DELAY_LONG)

                val memberNode = NodeHelper.findByExactText(member)
                if (memberNode != null) {
                    service?.clickNode(memberNode)
                    successList.add(member)
                    Thread.sleep(DELAY_SHORT)
                    service?.clearText(searchInput)
                    Thread.sleep(DELAY_SHORT)
                } else {
                    failList.add(member)
                    Log.w(TAG, "未找到成员: $member")
                    service?.clearText(searchInput)
                    Thread.sleep(DELAY_SHORT)
                }
            }
        }

        // 点击确认邀请
        if (successList.isNotEmpty()) {
            NodeHelper.clickText("确定") || NodeHelper.clickText("邀请")
            Thread.sleep(DELAY_PAGE_LOAD)
        }

        val result = mapOf("success" to successList, "failed" to failList)
        return TaskResult("", true, "邀请完成: 成功${successList.size}人, 失败${failList.size}人", result)
    }

    /**
     * 从群中移除成员
     */
    fun removeFromGroup(groupName: String, members: List<String>, target: AppTarget = AppTarget.WEWORK): TaskResult {
        Log.i(TAG, "移除群成员: $groupName, 成员: $members")

        if (!openChat(groupName, target)) {
            return TaskResult("", false, "无法打开群聊")
        }
        NodeHelper.clickId(WeworkIds.CHAT_MORE_BTN)
        Thread.sleep(DELAY_PAGE_LOAD)
        // 点击删除成员按钮（-号）
        if (!NodeHelper.clickId(WeworkIds.GROUP_MEMBER_DEL)) {
            return TaskResult("", false, "无法找到删除成员按钮")
        }
        Thread.sleep(DELAY_PAGE_LOAD)

        val removedList = mutableListOf<String>()
        for (member in members) {
            val searchInput = NodeHelper.findEditTexts().firstOrNull()
            if (searchInput != null) {
                service?.inputText(searchInput, member)
                Thread.sleep(DELAY_LONG)

                val memberNode = NodeHelper.findByExactText(member)
                if (memberNode != null) {
                    service?.clickNode(memberNode)
                    removedList.add(member)
                    Thread.sleep(DELAY_SHORT)
                    service?.clearText(searchInput)
                }
            }
        }

        if (removedList.isNotEmpty()) {
            NodeHelper.clickText("确定") || NodeHelper.clickText("删除")
            // 确认弹窗
            Thread.sleep(DELAY_MEDIUM)
            NodeHelper.clickText("确认") || NodeHelper.clickText("确定")
            Thread.sleep(DELAY_PAGE_LOAD)
        }

        return TaskResult("", true, "移除完成: ${removedList.size}人", removedList)
    }

    /**
     * 获取群成员列表
     */
    fun getGroupMembers(groupName: String, target: AppTarget = AppTarget.WEWORK): TaskResult {
        if (!openChat(groupName, target)) {
            return TaskResult("", false, "无法打开群聊")
        }
        NodeHelper.clickId(WeworkIds.CHAT_MORE_BTN)
        Thread.sleep(DELAY_PAGE_LOAD)
        // 收集所有成员名称
        val members = mutableListOf<String>()
        val textViews = NodeHelper.findByClassName("android.widget.TextView")
        val excludeTexts = setOf("群聊名称", "群公告", "群管理", "投诉", "添加", "删除",
            "全部群成员", "查看全部", "群成员", "消息免打扰", "置顶聊天", "保存到通讯录")

        for (tv in textViews) {
            val text = tv.text?.toString() ?: continue
            if (text.isNotBlank() && text.length in 2..20 && text !in excludeTexts) {
                members.add(text)
            }
        }

        service?.pressBack()
        return TaskResult("", true, "获取群成员成功", members.distinct())
    }

    // ====================================================================
    // 辅助方法
    // ====================================================================

    /**
     * 修改群名称
     */
    private fun modifyGroupName(newName: String): Boolean {
        // 点击群名称区域
        val nameNode = NodeHelper.findFirstById(WeworkIds.GROUP_NAME)
            ?: NodeHelper.findByExactText("群聊")
        if (nameNode != null) {
            service?.clickNode(nameNode)
            Thread.sleep(DELAY_MEDIUM)

            val editText = NodeHelper.findEditTexts().firstOrNull()
            if (editText != null) {
                service?.inputText(editText, newName)
                Thread.sleep(DELAY_SHORT)
                NodeHelper.clickText("确定") || NodeHelper.clickText("保存")
                Thread.sleep(DELAY_MEDIUM)
                return true
            }
        }
        return false
    }

    /** 通讯录页加载后等待时间（毫秒），列表渲染与网络可能较慢 */
    private val DELAY_CONTACTS_LOAD = 5000L

    /**
     * 获取联系人列表（通讯录）
     * 支持企业微信/微信：先进入通讯录 Tab，等待页面加载，可滚动多屏采集更多联系人
     */
    fun getContactList(target: AppTarget = AppTarget.WEWORK): TaskResult {
        Log.i(TAG, "获取联系人列表 (${target.label})")
        goToMainPage(target)
        Thread.sleep(DELAY_MEDIUM)
        // 优先用“等待出现再点击”，避免页面未就绪时点击失败（尤其后台/冷启动）
        val entered = service?.waitAndClickText("通讯录", 15000) == true
            || NodeHelper.clickText("通讯录")
            || NodeHelper.clickId(WeworkIds.TAB_CONTACTS)
        if (!entered) {
            Log.e(TAG, "无法进入通讯录")
            return TaskResult("", false, "无法进入通讯录页")
        }
        Thread.sleep(DELAY_CONTACTS_LOAD)

        // 采集当前页 + 滚动多屏以加载更多（微信/企业微信通讯录多为列表懒加载）
        val exclude = setOf(
            "通讯录", "消息", "工作台", "我", "微信", "发现",
            "搜索", "添加", "新的朋友", "群聊", "标签", "公众号",
            "企业微信", "全部", "组织", "管理员",
            "视频号", "小程序", "朋友圈", "扫一扫", "看一看"
        )
        val names = mutableSetOf<String>()
        val maxScrolls = 5
        for (scrollRound in 0..maxScrolls) {
            val textViews = NodeHelper.findByClassName("android.widget.TextView")
            for (tv in textViews) {
                val text = tv.text?.toString()?.trim() ?: continue
                if (text.length in 1..30 && text !in exclude && !text.all { it.isDigit() }) {
                    names.add(text)
                }
            }
            if (scrollRound < maxScrolls) {
                val scrollable = NodeHelper.findScrollables().firstOrNull()
                if (scrollable != null) {
                    service?.scrollForward(scrollable)
                    Thread.sleep(800)
                } else break
            }
        }

        val list = names.sorted()
        Log.i(TAG, "联系人列表获取成功，共 ${list.size} 条")
        return TaskResult("", true, "共 ${list.size} 个联系人", list)
    }

    /**
     * 导出当前页面控件树（调试用）
     */
    fun dumpUiTree(): String {
        return service?.dumpNodeTree() ?: "AccessibilityService未连接"
    }
}
