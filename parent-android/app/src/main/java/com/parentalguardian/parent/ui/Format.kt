package com.parentalguardian.parent.ui

import java.time.Duration
import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

private val fmt = DateTimeFormatter.ofPattern("d MMM, h:mm a")

/** The server sends UTC timestamps without a zone; show them in the phone's local time. */
fun fmtUtc(s: String?): String {
    if (s == null) return "never"
    return try {
        LocalDateTime.parse(s.removeSuffix("Z")).atZone(ZoneOffset.UTC)
            .withZoneSameInstant(ZoneId.systemDefault()).format(fmt)
    } catch (e: Exception) { s }
}

fun fmtDuration(sec: Int): String {
    val h = sec / 3600
    val m = sec % 3600 / 60
    return if (h > 0) "${h}h ${m}m" else if (m > 0) "${m}m" else "<1m"
}

/** Minutes since a server (UTC) timestamp, or null if unknown. */
fun minutesSince(s: String?): Long? = try {
    if (s == null) null
    else Duration.between(LocalDateTime.parse(s.removeSuffix("Z")).toInstant(ZoneOffset.UTC), Instant.now()).toMinutes()
} catch (e: Exception) { null }
