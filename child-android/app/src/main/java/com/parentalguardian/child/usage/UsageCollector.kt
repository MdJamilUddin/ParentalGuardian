package com.parentalguardian.child.usage

import android.app.usage.UsageStatsManager
import android.content.Context
import com.parentalguardian.child.permissions.PermissionHelper
import org.json.JSONArray
import org.json.JSONObject
import java.time.LocalDate
import java.time.ZoneId

object UsageCollector {
    /** Today's foreground time per launchable app (daily totals; the server keeps the latest value). */
    fun today(ctx: Context): JSONArray {
        val out = JSONArray()
        if (!PermissionHelper.hasUsageAccess(ctx)) return out
        val usm = ctx.getSystemService(UsageStatsManager::class.java)
        val pm = ctx.packageManager
        val today = LocalDate.now()
        val start = today.atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli()
        val stats = usm.queryAndAggregateUsageStats(start, System.currentTimeMillis())
        stats.values
            .filter { it.totalTimeInForeground >= 1000 && pm.getLaunchIntentForPackage(it.packageName) != null }
            .sortedByDescending { it.totalTimeInForeground }
            .take(300)
            .forEach {
                val label = try {
                    pm.getApplicationLabel(pm.getApplicationInfo(it.packageName, 0)).toString()
                } catch (e: Exception) { it.packageName }
                out.put(
                    JSONObject().put("package", it.packageName).put("app_label", label)
                        .put("day", today.toString())
                        .put("seconds", (it.totalTimeInForeground / 1000).toInt().coerceAtMost(86400))
                )
            }
        return out
    }
}
