package com.wechatrpa.activity

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.wechatrpa.service.HttpServerService
import com.wechatrpa.service.RpaAccessibilityService
import java.util.Timer
import java.util.TimerTask

/**
 * 主界面
 *
 * 提供以下功能：
 * 1. 引导用户开启无障碍服务
 * 2. 启动/停止内嵌HTTP服务器
 * 3. 显示服务运行状态
 */
class MainActivity : AppCompatActivity() {

    private lateinit var tvStatus: TextView
    private lateinit var tvAccessibility: TextView
    private lateinit var tvHttpServer: TextView
    private lateinit var tvCurrentApp: TextView
    private lateinit var btnAccessibility: Button
    private lateinit var btnHttpServer: Button
    private var statusTimer: Timer? = null
    private var httpServerRunning = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // 使用简单的线性布局（实际项目中应使用XML布局文件）
        setContentView(createLayout())
    }

    override fun onResume() {
        super.onResume()
        startStatusRefresh()
    }

    override fun onPause() {
        super.onPause()
        statusTimer?.cancel()
    }

    /**
     * 创建简单的UI布局
     */
    private fun createLayout(): android.view.View {
        val context = this
        return android.widget.LinearLayout(context).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(48, 48, 48, 48)

            // 标题
            addView(TextView(context).apply {
                text = "WeChat RPA 控制台"
                textSize = 24f
                setTypeface(null, android.graphics.Typeface.BOLD)
                setPadding(0, 0, 0, 32)
            })

            // 无障碍服务状态
            tvAccessibility = TextView(context).apply {
                text = "无障碍服务: 未开启"
                textSize = 16f
                setPadding(0, 16, 0, 8)
            }
            addView(tvAccessibility)

            // 开启无障碍服务按钮
            btnAccessibility = Button(context).apply {
                text = "开启无障碍服务"
                setOnClickListener {
                    val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                    startActivity(intent)
                }
            }
            addView(btnAccessibility)

            // HTTP服务器状态
            tvHttpServer = TextView(context).apply {
                text = "HTTP服务器: 未启动"
                textSize = 16f
                setPadding(0, 24, 0, 8)
            }
            addView(tvHttpServer)

            // 启动HTTP服务器按钮
            btnHttpServer = Button(context).apply {
                text = "启动HTTP服务器"
                setOnClickListener { toggleHttpServer() }
            }
            addView(btnHttpServer)

            // 当前应用状态
            tvCurrentApp = TextView(context).apply {
                text = "当前前台应用: -"
                textSize = 14f
                setPadding(0, 24, 0, 8)
            }
            addView(tvCurrentApp)

            // 总体状态
            tvStatus = TextView(context).apply {
                text = "就绪"
                textSize = 14f
                setPadding(0, 24, 0, 0)
                setTextColor(android.graphics.Color.GRAY)
            }
            addView(tvStatus)

            // 使用说明
            addView(TextView(context).apply {
                text = "\n使用步骤:\n" +
                    "1. 点击「开启无障碍服务」并在设置中启用\n" +
                    "2. 点击「启动HTTP服务器」\n" +
                    "3. 通过 http://<手机IP>:9527/api/ 调用API\n" +
                    "\n提示: 确保手机和调用端在同一局域网内"
                textSize = 13f
                setPadding(0, 32, 0, 0)
                setTextColor(android.graphics.Color.DKGRAY)
            })
        }
    }

    /**
     * 切换HTTP服务器状态
     */
    private fun toggleHttpServer() {
        if (httpServerRunning) {
            stopService(Intent(this, HttpServerService::class.java))
            httpServerRunning = false
            btnHttpServer.text = "启动HTTP服务器"
        } else {
            val intent = Intent(this, HttpServerService::class.java)
            startForegroundService(intent)
            httpServerRunning = true
            btnHttpServer.text = "停止HTTP服务器"
        }
    }

    /**
     * 定时刷新状态
     */
    private fun startStatusRefresh() {
        statusTimer = Timer().apply {
            scheduleAtFixedRate(object : TimerTask() {
                override fun run() {
                    runOnUiThread { updateStatus() }
                }
            }, 0, 2000)
        }
    }

    private fun updateStatus() {
        val service = RpaAccessibilityService.instance
        val isAccessibilityOn = service != null

        tvAccessibility.text = if (isAccessibilityOn) {
            "无障碍服务: ✅ 已开启"
        } else {
            "无障碍服务: ❌ 未开启"
        }

        tvHttpServer.text = if (httpServerRunning) {
            "HTTP服务器: ✅ 运行中 (端口 9527)"
        } else {
            "HTTP服务器: ⏹ 未启动"
        }

        tvCurrentApp.text = "当前前台应用: ${service?.currentPackage ?: "-"}"

        tvStatus.text = if (isAccessibilityOn && httpServerRunning) {
            "🟢 系统就绪，可以接收API指令"
        } else {
            "🔴 请先开启无障碍服务并启动HTTP服务器"
        }
    }
}
