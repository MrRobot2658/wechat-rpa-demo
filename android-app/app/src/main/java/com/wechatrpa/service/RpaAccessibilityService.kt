package com.wechatrpa.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.graphics.Path
import android.graphics.Rect
import android.os.Bundle
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.wechatrpa.model.AppTarget
import com.wechatrpa.model.TaskResult
import com.wechatrpa.utils.NodeHelper

/**
 * 核心无障碍服务
 *
 * 本服务是整个RPA系统的基石。它通过Android官方的AccessibilityService框架，
 * 获取企业微信/微信的UI控件树（AccessibilityNodeInfo），并在其上执行模拟操作
 * （点击、输入、滚动等），从而实现对目标应用的自动化控制。
 *
 * 架构角色：
 *   [Python服务端] --HTTP API--> [Android端HttpServer] --调用--> [本服务]
 *
 * 核心原理：
 *   1. 系统授权后，本服务可通过 rootInActiveWindow 获取当前屏幕的完整控件树
 *   2. 通过 resource-id / text / className 等属性定位目标控件
 *   3. 通过 performAction() 在控件上执行点击、输入等操作
 *   4. 通过 performGlobalAction() 执行返回、回到主页等全局操作
 */
class RpaAccessibilityService : AccessibilityService() {

    companion object {
        private const val TAG = "RpaAccessibility"

        /** 单例引用，供外部（如HttpServer）调用 */
        @Volatile
        var instance: RpaAccessibilityService? = null
            private set
    }

    // ====================================================================
    // 当前页面状态追踪
    // ====================================================================
    var currentPackage: String = ""
        private set
    var currentClassName: String = ""
        private set

    // ====================================================================
    // 生命周期
    // ====================================================================

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        // 隐藏软键盘，防止遮挡控件
        softKeyboardController.showMode = SHOW_MODE_HIDDEN
        Log.i(TAG, "无障碍服务已连接，RPA引擎就绪")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        event ?: return
        val pkg = event.packageName?.toString() ?: return
        val cls = event.className?.toString() ?: ""

        // 记录当前前台页面信息（仅记录Activity级别的切换）
        if (event.eventType == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
            currentPackage = pkg
            if (cls.contains(".")) {
                currentClassName = cls
            }
            Log.d(TAG, "页面切换 -> pkg=$pkg, cls=$cls")
        }
    }

    override fun onInterrupt() {
        Log.w(TAG, "无障碍服务被中断")
    }

    override fun onDestroy() {
        super.onDestroy()
        instance = null
        softKeyboardController.showMode = SHOW_MODE_AUTO
        Log.i(TAG, "无障碍服务已销毁")
    }

    // ====================================================================
    // 控件查找（核心能力）
    // ====================================================================

    /**
     * 获取当前屏幕的根控件节点
     */
    fun getRootNode(): AccessibilityNodeInfo? {
        return try {
            rootInActiveWindow
        } catch (e: Exception) {
            Log.e(TAG, "获取rootInActiveWindow失败: ${e.message}")
            null
        }
    }

    /**
     * 通过 resource-id 查找控件
     */
    fun findById(resourceId: String): List<AccessibilityNodeInfo> {
        val root = getRootNode() ?: return emptyList()
        return root.findAccessibilityNodeInfosByViewId(resourceId) ?: emptyList()
    }

    /**
     * 通过文本内容查找控件
     */
    fun findByText(text: String): List<AccessibilityNodeInfo> {
        val root = getRootNode() ?: return emptyList()
        return root.findAccessibilityNodeInfosByText(text) ?: emptyList()
    }

    /**
     * 通过文本精确匹配查找控件（findByText是模糊匹配，此方法为精确匹配）
     */
    fun findByExactText(text: String): AccessibilityNodeInfo? {
        val candidates = findByText(text)
        return candidates.firstOrNull { it.text?.toString() == text }
    }

    /**
     * 递归遍历控件树，通过自定义条件查找
     */
    fun findNode(
        root: AccessibilityNodeInfo? = getRootNode(),
        predicate: (AccessibilityNodeInfo) -> Boolean
    ): AccessibilityNodeInfo? {
        root ?: return null
        if (predicate(root)) return root
        for (i in 0 until root.childCount) {
            val child = root.getChild(i) ?: continue
            val result = findNode(child, predicate)
            if (result != null) return result
        }
        return null
    }

    /**
     * 递归遍历控件树，收集所有满足条件的控件
     */
    fun findAllNodes(
        root: AccessibilityNodeInfo? = getRootNode(),
        predicate: (AccessibilityNodeInfo) -> Boolean
    ): List<AccessibilityNodeInfo> {
        val results = mutableListOf<AccessibilityNodeInfo>()
        fun traverse(node: AccessibilityNodeInfo?) {
            node ?: return
            if (predicate(node)) results.add(node)
            for (i in 0 until node.childCount) {
                traverse(node.getChild(i))
            }
        }
        traverse(root)
        return results
    }

    // ====================================================================
    // 模拟操作（核心能力）
    // ====================================================================

    /**
     * 点击指定控件
     */
    fun clickNode(node: AccessibilityNodeInfo): Boolean {
        // 优先尝试直接点击
        if (node.isClickable) {
            return node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
        }
        // 如果控件本身不可点击，向上查找可点击的父节点
        var parent = node.parent
        while (parent != null) {
            if (parent.isClickable) {
                return parent.performAction(AccessibilityNodeInfo.ACTION_CLICK)
            }
            parent = parent.parent
        }
        // 兜底方案：通过坐标点击
        val rect = Rect()
        node.getBoundsInScreen(rect)
        return clickByCoordinate(rect.centerX().toFloat(), rect.centerY().toFloat())
    }

    /**
     * 通过屏幕坐标点击（GestureDescription API，Android 7.0+）
     */
    fun clickByCoordinate(x: Float, y: Float, duration: Long = 100): Boolean {
        val path = Path().apply { moveTo(x, y) }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, duration))
            .build()
        return dispatchGesture(gesture, null, null)
    }

    /**
     * 长按指定控件
     */
    fun longClickNode(node: AccessibilityNodeInfo): Boolean {
        if (node.isLongClickable) {
            return node.performAction(AccessibilityNodeInfo.ACTION_LONG_CLICK)
        }
        val rect = Rect()
        node.getBoundsInScreen(rect)
        return longPressByCoordinate(rect.centerX().toFloat(), rect.centerY().toFloat())
    }

    /**
     * 通过坐标长按
     */
    fun longPressByCoordinate(x: Float, y: Float, duration: Long = 1000): Boolean {
        val path = Path().apply { moveTo(x, y) }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, duration))
            .build()
        return dispatchGesture(gesture, null, null)
    }

    /**
     * 向输入框填入文本（通过剪贴板粘贴，兼容中文）
     */
    fun inputText(node: AccessibilityNodeInfo, text: String): Boolean {
        // 方式一：直接通过 ACTION_SET_TEXT（Android 5.0+）
        val args = Bundle().apply {
            putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
        }
        val result = node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
        if (result) return true

        // 方式二：通过剪贴板粘贴（兜底方案，更兼容）
        return try {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            clipboard.setPrimaryClip(ClipData.newPlainText("rpa_input", text))
            // 先聚焦
            node.performAction(AccessibilityNodeInfo.ACTION_FOCUS)
            // 全选已有内容（ACTION_SELECT_ALL = 0x20000，部分 SDK 中无此常量）
            node.performAction(0x20000)
            // 粘贴
            node.performAction(AccessibilityNodeInfo.ACTION_PASTE)
        } catch (e: Exception) {
            Log.e(TAG, "inputText失败: ${e.message}")
            false
        }
    }

    /**
     * 清空输入框
     */
    fun clearText(node: AccessibilityNodeInfo): Boolean {
        return inputText(node, "")
    }

    /**
     * 滚动控件（向前/向后）
     */
    fun scrollForward(node: AccessibilityNodeInfo): Boolean {
        return node.performAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD)
    }

    fun scrollBackward(node: AccessibilityNodeInfo): Boolean {
        return node.performAction(AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD)
    }

    /**
     * 通过坐标滑动（模拟手指滑动手势）
     */
    fun swipe(
        startX: Float, startY: Float,
        endX: Float, endY: Float,
        duration: Long = 500
    ): Boolean {
        val path = Path().apply {
            moveTo(startX, startY)
            lineTo(endX, endY)
        }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, duration))
            .build()
        return dispatchGesture(gesture, null, null)
    }

    // ====================================================================
    // 全局操作
    // ====================================================================

    /** 按返回键 */
    fun pressBack(): Boolean = performGlobalAction(GLOBAL_ACTION_BACK)

    /** 回到主页 */
    fun pressHome(): Boolean = performGlobalAction(GLOBAL_ACTION_HOME)

    /** 打开最近任务 */
    fun pressRecents(): Boolean = performGlobalAction(GLOBAL_ACTION_RECENTS)

    /** 打开通知栏 */
    fun openNotifications(): Boolean = performGlobalAction(GLOBAL_ACTION_NOTIFICATIONS)

    // ====================================================================
    // 高级辅助方法
    // ====================================================================

    /**
     * 等待指定控件出现
     */
    fun waitForNode(
        timeoutMs: Long = 10000,
        intervalMs: Long = 500,
        predicate: (AccessibilityNodeInfo) -> Boolean
    ): AccessibilityNodeInfo? {
        val startTime = System.currentTimeMillis()
        while (System.currentTimeMillis() - startTime < timeoutMs) {
            val node = findNode(predicate = predicate)
            if (node != null) return node
            Thread.sleep(intervalMs)
        }
        Log.w(TAG, "等待控件超时 (${timeoutMs}ms)")
        return null
    }

    /**
     * 等待指定文本出现并点击
     */
    fun waitAndClickText(text: String, timeoutMs: Long = 10000): Boolean {
        val node = waitForNode(timeoutMs) { it.text?.toString() == text }
        return if (node != null) clickNode(node) else false
    }

    /**
     * 等待指定resource-id出现并点击
     */
    fun waitAndClickId(resourceId: String, timeoutMs: Long = 10000): Boolean {
        val node = waitForNode(timeoutMs) { it.viewIdResourceName == resourceId }
        return if (node != null) clickNode(node) else false
    }

    /**
     * 检查当前是否在指定应用的前台
     */
    fun isAppForeground(packageName: String): Boolean {
        return currentPackage == packageName
    }

    /**
     * 导出当前页面的控件树（用于调试和ID校准）
     */
    fun dumpNodeTree(): String {
        val sb = StringBuilder()
        fun dump(node: AccessibilityNodeInfo?, depth: Int) {
            node ?: return
            val indent = "  ".repeat(depth)
            sb.appendLine(
                "${indent}[${node.className}] " +
                "id=${node.viewIdResourceName ?: "null"} " +
                "text=\"${node.text ?: ""}\" " +
                "desc=\"${node.contentDescription ?: ""}\" " +
                "clickable=${node.isClickable} " +
                "bounds=${Rect().also { node.getBoundsInScreen(it) }}"
            )
            for (i in 0 until node.childCount) {
                dump(node.getChild(i), depth + 1)
            }
        }
        dump(getRootNode(), 0)
        return sb.toString()
    }
}
