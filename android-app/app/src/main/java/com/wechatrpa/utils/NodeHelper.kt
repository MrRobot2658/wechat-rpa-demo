package com.wechatrpa.utils

import android.util.Log
import android.view.accessibility.AccessibilityNodeInfo
import com.wechatrpa.model.AppTarget
import com.wechatrpa.service.RpaAccessibilityService

/**
 * 控件查找辅助工具
 *
 * 封装了在企业微信/微信UI控件树中定位和操作控件的常用方法。
 * 所有方法均基于 AccessibilityNodeInfo 的标准API，不涉及任何Hook或逆向。
 */
object NodeHelper {

    private const val TAG = "NodeHelper"

    private val service: RpaAccessibilityService?
        get() = RpaAccessibilityService.instance

    // ====================================================================
    // 查找方法
    // ====================================================================

    /**
     * 通过resource-id查找第一个匹配的控件
     */
    fun findFirstById(resourceId: String): AccessibilityNodeInfo? {
        return service?.findById(resourceId)?.firstOrNull()
    }

    /**
     * 通过文本精确匹配查找控件
     */
    fun findByExactText(text: String): AccessibilityNodeInfo? {
        return service?.findByExactText(text)
    }

    /**
     * 通过文本模糊匹配查找控件
     */
    fun findByContainsText(text: String): List<AccessibilityNodeInfo> {
        return service?.findByText(text) ?: emptyList()
    }

    /**
     * 通过className查找所有匹配的控件
     */
    fun findByClassName(className: String): List<AccessibilityNodeInfo> {
        return service?.findAllNodes { it.className?.toString() == className } ?: emptyList()
    }

    /**
     * 查找所有EditText输入框
     */
    fun findEditTexts(): List<AccessibilityNodeInfo> {
        return findByClassName("android.widget.EditText")
    }

    /**
     * 查找所有可点击的控件
     */
    fun findClickables(): List<AccessibilityNodeInfo> {
        return service?.findAllNodes { it.isClickable } ?: emptyList()
    }

    /**
     * 查找所有可滚动的控件（如ListView、RecyclerView）
     */
    fun findScrollables(): List<AccessibilityNodeInfo> {
        return service?.findAllNodes { it.isScrollable } ?: emptyList()
    }

    // ====================================================================
    // 操作方法
    // ====================================================================

    /**
     * 查找并点击包含指定文本的控件
     * @return 是否成功
     */
    fun clickText(text: String, exact: Boolean = true): Boolean {
        val node = if (exact) findByExactText(text) else findByContainsText(text).firstOrNull()
        if (node == null) {
            Log.w(TAG, "clickText: 未找到文本 '$text'")
            return false
        }
        return service?.clickNode(node) ?: false
    }

    /**
     * 查找并点击指定resource-id的控件
     */
    fun clickId(resourceId: String): Boolean {
        val node = findFirstById(resourceId)
        if (node == null) {
            Log.w(TAG, "clickId: 未找到ID '$resourceId'")
            return false
        }
        return service?.clickNode(node) ?: false
    }

    /**
     * 按 contentDescription 包含指定文案查找并点击（微信等发送按钮可能只有图标无文字）
     */
    fun clickContentDesc(desc: String): Boolean {
        val node = service?.findAllNodes { it.contentDescription?.toString()?.contains(desc) == true }?.firstOrNull()
        if (node == null) {
            Log.w(TAG, "clickContentDesc: 未找到 contentDescription 包含 '$desc'")
            return false
        }
        return service?.clickNode(node) ?: false
    }

    /**
     * 查找输入框并输入文本
     * @param resourceId 输入框的resource-id（可选，为空则查找第一个EditText）
     * @param text 要输入的文本
     */
    fun inputToField(text: String, resourceId: String? = null): Boolean {
        val node = if (resourceId != null) {
            findFirstById(resourceId)
        } else {
            findEditTexts().firstOrNull()
        }
        if (node == null) {
            Log.w(TAG, "inputToField: 未找到输入框")
            return false
        }
        return service?.inputText(node, text) ?: false
    }

    /**
     * 在可滚动列表中查找指定文本（自动滚动查找）
     * @param text 要查找的文本
     * @param maxScrolls 最大滚动次数
     */
    fun scrollAndFindText(text: String, maxScrolls: Int = 10): AccessibilityNodeInfo? {
        for (i in 0..maxScrolls) {
            val node = findByExactText(text)
            if (node != null) return node

            // 查找可滚动的列表并向下滚动
            val scrollable = findScrollables().firstOrNull() ?: break
            service?.scrollForward(scrollable) ?: break
            Thread.sleep(800) // 等待滚动动画完成
        }
        return null
    }

    /**
     * 等待并点击（带重试）
     */
    fun waitAndClick(
        text: String? = null,
        resourceId: String? = null,
        timeoutMs: Long = 10000,
        intervalMs: Long = 500
    ): Boolean {
        val s = service ?: return false
        val startTime = System.currentTimeMillis()
        while (System.currentTimeMillis() - startTime < timeoutMs) {
            val node = when {
                text != null -> s.findByExactText(text)
                resourceId != null -> s.findById(resourceId).firstOrNull()
                else -> null
            }
            if (node != null) {
                return s.clickNode(node)
            }
            Thread.sleep(intervalMs)
        }
        Log.w(TAG, "waitAndClick超时: text=$text, id=$resourceId")
        return false
    }

    // ====================================================================
    // 页面判断
    // ====================================================================

    /**
     * 判断当前页面是否包含指定文本
     */
    fun pageContainsText(text: String): Boolean {
        return findByContainsText(text).isNotEmpty()
    }

    /**
     * 判断当前是否在聊天页面（企业微信）
     */
    fun isInChatPage(): Boolean {
        // 企业微信聊天页面通常包含发送按钮和输入框
        return findByContainsText("发送").isNotEmpty() ||
               findEditTexts().isNotEmpty()
    }

    /**
     * 判断当前是否在主页
     * @param target 微信：通讯录+发现/我；企业微信：消息+通讯录
     */
    fun isInMainPage(target: AppTarget = AppTarget.WEWORK): Boolean {
        return when (target) {
            AppTarget.WECHAT ->
                findByExactText("通讯录") != null &&
                    (findByExactText("发现") != null || findByExactText("我") != null)
            AppTarget.WEWORK ->
                findByExactText("消息") != null && findByExactText("通讯录") != null
        }
    }
}
