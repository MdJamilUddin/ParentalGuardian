package com.parentalguardian.parent.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.parentalguardian.parent.data.Api
import com.parentalguardian.parent.data.NotifPrefs
import kotlinx.coroutines.launch

@Composable
fun NotificationsDialog(token: String, onDismiss: () -> Unit, onLogout: () -> Unit) {
    val scope = rememberCoroutineScope()
    var prefs by remember { mutableStateOf<NotifPrefs?>(null) }
    var info by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        io(onLogout) { Api.notifPrefs(token) }.onSuccess { prefs = it }.onFailure { info = friendly(it) }
    }

    fun update(p: NotifPrefs) {
        prefs = p
        scope.launch { io(onLogout) { Api.setNotifPrefs(token, p.offline, p.lowBattery) }.onFailure { info = friendly(it) } }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Alerts") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                val p = prefs
                if (p == null) Text(info ?: "Loading...") else {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("A phone stops reporting for 2 hours", Modifier.weight(1f))
                        Switch(p.offline, { update(p.copy(offline = it)) })
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Battery is low (15% or less)", Modifier.weight(1f))
                        Switch(p.lowBattery, { update(p.copy(lowBattery = it)) })
                    }
                    OutlinedButton(onClick = {
                        scope.launch {
                            io(onLogout) { Api.pushTest(token) }.onSuccess {
                                info = when {
                                    !it.configured -> "Push isn't set up on the server yet."
                                    it.registered == 0 -> "This phone isn't registered. Allow notifications, then reopen the app."
                                    it.sent == 0 -> "The server couldn't deliver it. Reopen the app and try again."
                                    else -> "Sent to ${it.sent} phone(s)."
                                }
                            }.onFailure { info = friendly(it) }
                        }
                    }) { Text("Send a test notification") }
                    info?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                }
            }
        },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Close") } }
    )
}
