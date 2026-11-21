package com.parentalguardian.child.sync

import android.content.Context
import android.content.Intent
import com.parentalguardian.child.battery.BatteryCollector
import com.parentalguardian.child.data.Api
import com.parentalguardian.child.data.PendingStore
import com.parentalguardian.child.data.TokenStore
import com.parentalguardian.child.usage.UsageCollector
import org.json.JSONArray
import org.json.JSONObject

object Syncer {
    /** Uploads queued locations/battery plus today's usage. Throws on network errors (caller retries). */
    fun run(ctx: Context) {
        val store = TokenStore(ctx)
        val token = store.token ?: return
        val pending = PendingStore(ctx)
        pending.append(BatteryCollector.read(ctx))

        var usage: JSONArray? = UsageCollector.today(ctx)
        var rounds = 0
        do {
            val items = pending.peek(500)
            val locs = JSONArray()
            val bats = JSONArray()
            items.forEach {
                val copy = JSONObject(it.toString()).apply { remove("t") }
                if (it.optString("t") == "loc") locs.put(copy) else bats.put(copy)
            }
            val payload = JSONObject().put("locations", locs).put("battery", bats)
                .put("usage", usage ?: JSONArray())
            try {
                Api.sync(token, payload)
            } catch (e: Api.ApiError) {
                if (e.code == 401) { // parent revoked this device
                    store.token = null
                    ctx.stopService(Intent(ctx, GuardianService::class.java))
                    return
                }
                throw e
            }
            pending.drop(items.size)
            store.lastSyncMillis = System.currentTimeMillis()
            usage = null // usage is only sent once per run
        } while (items.size == 500 && ++rounds < 10)
    }
}
