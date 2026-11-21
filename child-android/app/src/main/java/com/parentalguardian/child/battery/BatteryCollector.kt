package com.parentalguardian.child.battery

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import org.json.JSONObject
import java.time.Instant

object BatteryCollector {
    fun read(ctx: Context): JSONObject {
        val i = ctx.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val level = i?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = i?.getIntExtra(BatteryManager.EXTRA_SCALE, 100) ?: 100
        val status = i?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        val charging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
            status == BatteryManager.BATTERY_STATUS_FULL
        val pct = if (level >= 0 && scale > 0) (level * 100 / scale).coerceIn(0, 100) else 0
        return JSONObject().put("t", "bat").put("level", pct).put("charging", charging)
            .put("recorded_at", Instant.now().toString())
    }
}
