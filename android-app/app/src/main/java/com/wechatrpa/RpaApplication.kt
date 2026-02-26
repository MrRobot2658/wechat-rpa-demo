package com.wechatrpa

import android.app.Application
import android.util.Log

/**
 * 应用入口
 */
class RpaApplication : Application() {

    companion object {
        private const val TAG = "RpaApplication"
        lateinit var instance: RpaApplication
            private set
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        Log.i(TAG, "WeChat RPA Application 初始化完成")
    }
}
