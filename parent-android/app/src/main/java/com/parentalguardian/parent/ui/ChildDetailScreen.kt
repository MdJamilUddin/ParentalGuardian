package com.parentalguardian.parent.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.parentalguardian.parent.data.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.time.LocalDate

@Composable
fun ChildDetailScreen(token: String, childId: Int, onBack: () -> Unit, onLogout: () -> Unit) {
    val scope = rememberCoroutineScope()
    var child by remember { mutableStateOf<Child?>(null) }
    var latest by remember { mutableStateOf<Loc?>(null) }
    var history by remember { mutableStateOf<List<Loc>>(emptyList()) }
    var usage by remember { mutableStateOf<List<UsageItem>>(emptyList()) }
    var battery by remember { mutableStateOf<Battery?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var code by remember { mutableStateOf<PairingCode?>(null) }
    var revoke by remember { mutableStateOf<Device?>(null) }

    suspend fun refresh() {
        val day = LocalDate.now().toString() // phone's local date, matches the child app
        val r = io(onLogout) {
            val c = Api.children(token).firstOrNull { it.id == childId }
            val l = Api.latestLocation(token, childId)
            val h = Api.locations(token, childId, 24)
            val u = Api.usage(token, childId, day)
            val b = Api.battery(token, childId)
            listOf(c, l, h, u, b)
        }
        r.onSuccess {
            @Suppress("UNCHECKED_CAST")
            child = it[0] as Child?; latest = it[1] as Loc?; history = it[2] as List<Loc>
            usage = it[3] as List<UsageItem>; battery = it[4] as Battery?; error = null
        }.onFailure { error = friendly(it) }
    }
    LaunchedEffect(Unit) { while (true) { refresh(); delay(60_000) } }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp).statusBarsPadding(),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = onBack) { Text("‹ Back") }
            Text(child?.name ?: "", style = MaterialTheme.typography.headlineMedium, modifier = Modifier.weight(1f))
            TextButton(onClick = { scope.launch { refresh() } }) { Text("Refresh") }
        }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }

        val devices = child?.devices.orEmpty()
        val activeDevices = devices.filter { !it.revoked }
        val sinceMin = activeDevices.mapNotNull { minutesSince(it.lastSeen) }.minOrNull()
        if (activeDevices.isNotEmpty() && (sinceMin == null || sinceMin > 120)) {
            Card(
                Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = androidx.compose.ui.graphics.Color(0xFFFFF4D6))
            ) {
                Text(
                    if (sinceMin == null) "This phone has not connected yet."
                    else "No update from the phone for ${fmtDuration((sinceMin * 60).toInt())}. It may be switched off or offline, or the app may have been stopped.",
                    Modifier.padding(14.dp)
                )
            }
        }
        if (devices.none { !it.revoked }) {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Connect your child's phone", style = MaterialTheme.typography.titleMedium)
                    Text("Install the child app, then enter a pairing code from here.")
                }
            }
        }

        // Battery
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp)) {
                Text("Battery", style = MaterialTheme.typography.titleMedium)
                val b = battery
                if (b == null) Text("No data yet") else {
                    Text("${b.level}%" + if (b.charging) "  (charging)" else "", fontSize = 28.sp)
                    Text("Updated ${fmtUtc(b.at)}", style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        // Location
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Location", style = MaterialTheme.typography.titleMedium)
                val l = latest
                if (l == null) Text("No location yet") else {
                    LocationMap(history, l, Modifier.fillMaxWidth().height(280.dp))
                    Text(
                        "Last seen ${fmtUtc(l.at)}" + (l.accuracy?.let { " (±${it.toInt()} m)" } ?: ""),
                        style = MaterialTheme.typography.bodySmall
                    )
                    Text("© OpenStreetMap contributors", style = MaterialTheme.typography.labelSmall)
                }
            }
        }

        // Usage
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("App usage today", style = MaterialTheme.typography.titleMedium)
                if (usage.isEmpty()) Text("No data yet")
                val total = usage.sumOf { it.seconds }
                if (usage.isNotEmpty()) Text("Total: ${fmtDuration(total)}", style = MaterialTheme.typography.bodySmall)
                usage.take(15).forEach {
                    Row(Modifier.fillMaxWidth()) {
                        Text(it.label ?: it.pkg, Modifier.weight(1f))
                        Text(fmtDuration(it.seconds))
                    }
                    LinearProgressIndicator(
                        progress = { (it.seconds.toFloat() / (usage.first().seconds.coerceAtLeast(1))).coerceIn(0f, 1f) },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }

        // Devices
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Phones", style = MaterialTheme.typography.titleMedium)
                devices.filter { !it.revoked }.forEach { d ->
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(d.name)
                            Text("Last seen ${fmtUtc(d.lastSeen)}", style = MaterialTheme.typography.bodySmall)
                        }
                        TextButton(onClick = { revoke = d }) { Text("Disconnect") }
                    }
                }
                Button(onClick = {
                    scope.launch {
                        io(onLogout) { Api.pairingCode(token, childId) }
                            .onSuccess { code = it }.onFailure { error = friendly(it) }
                    }
                }, modifier = Modifier.fillMaxWidth()) { Text("Add a phone (pairing code)") }
            }
        }
    }

    code?.let { c ->
        AlertDialog(
            onDismissRequest = { code = null },
            title = { Text("Pairing code") },
            text = {
                Column {
                    Text(c.code, fontSize = 40.sp, style = MaterialTheme.typography.headlineLarge)
                    Text("Enter this on your child's phone within 10 minutes. It works once.")
                }
            },
            confirmButton = { TextButton(onClick = { code = null; scope.launch { refresh() } }) { Text("Done") } }
        )
    }

    revoke?.let { d ->
        AlertDialog(
            onDismissRequest = { revoke = null },
            title = { Text("Disconnect ${d.name}?") },
            text = { Text("It will stop sending data and the child app will return to the pairing screen.") },
            confirmButton = {
                TextButton(onClick = {
                    revoke = null
                    scope.launch {
                        io(onLogout) { Api.revokeDevice(token, d.id) }.onFailure { error = friendly(it) }
                        refresh()
                    }
                }) { Text("Disconnect") }
            },
            dismissButton = { TextButton(onClick = { revoke = null }) { Text("Cancel") } }
        )
    }
}
