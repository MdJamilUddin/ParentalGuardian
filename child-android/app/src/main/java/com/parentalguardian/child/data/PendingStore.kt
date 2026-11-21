package com.parentalguardian.child.data

import android.content.Context
import org.json.JSONObject
import java.io.File

/** Offline queue (one JSON object per line) so nothing is lost without internet. */
class PendingStore(ctx: Context) {
    private val file = File(ctx.applicationContext.filesDir, "pending.jsonl")

    fun append(item: JSONObject) = synchronized(lock) {
        file.appendText(item.toString() + "\n")
        if (file.length() > 1_000_000) { // keep the queue bounded: drop the oldest entries
            val rest = file.readLines().drop(1000)
            file.writeText(rest.joinToString("\n", postfix = if (rest.isEmpty()) "" else "\n"))
        }
    }

    fun peek(max: Int): List<JSONObject> = synchronized(lock) {
        if (!file.exists()) emptyList()
        else file.useLines { lines -> lines.take(max).map { JSONObject(it) }.toList() }
    }

    fun drop(n: Int) = synchronized(lock) {
        if (!file.exists()) return@synchronized
        val rest = file.readLines().drop(n)
        file.writeText(rest.joinToString("\n", postfix = if (rest.isEmpty()) "" else "\n"))
    }

    companion object { private val lock = Any() }
}
