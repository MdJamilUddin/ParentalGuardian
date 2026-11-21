package com.parentalguardian.parent.ui

import com.parentalguardian.parent.data.Api
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** Runs a network call off the main thread. A 401 (expired/invalid login) triggers [onExpired]. */
suspend fun <T> io(onExpired: () -> Unit, block: () -> T): Result<T> {
    val r = withContext(Dispatchers.IO) { runCatching(block) }
    val e = r.exceptionOrNull()
    if (e is Api.ApiError && e.code == 401) onExpired()
    return r
}

fun friendly(e: Throwable?): String = when {
    e is Api.ApiError && e.code == 409 -> "That email is already registered."
    e is Api.ApiError && e.code == 401 -> "Wrong email or password."
    e is Api.ApiError && e.code == 429 -> "Too many attempts. Wait a few minutes and try again."
    e is Api.ApiError && e.code == 422 -> "Please check the details (password needs 8+ characters)."
    e is Api.ApiError -> "Server error (${e.code})."
    else -> "Can't reach the server. Check your connection."
}
