package com.parentalguardian.parent.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.parentalguardian.parent.data.Api
import com.parentalguardian.parent.data.Child
import kotlinx.coroutines.launch

@Composable
fun ChildrenScreen(token: String, onOpen: (Int) -> Unit, onLogout: () -> Unit) {
    val scope = rememberCoroutineScope()
    var children by remember { mutableStateOf<List<Child>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var showAdd by remember { mutableStateOf(false) }
    var newName by remember { mutableStateOf("") }

    fun load() = scope.launch {
        io(onLogout) { Api.children(token) }
            .onSuccess { children = it; error = null }.onFailure { error = friendly(it) }
    }
    LaunchedEffect(Unit) { load() }

    Column(Modifier.fillMaxSize().padding(20.dp).statusBarsPadding(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text("My children", style = MaterialTheme.typography.headlineMedium, modifier = Modifier.weight(1f))
            TextButton(onClick = onLogout) { Text("Log out") }
        }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        val list = children
        if (list != null && list.isEmpty())
            Text("No children yet. Add one, then generate a pairing code and enter it on your child's phone.")
        LazyColumn(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(list.orEmpty()) { c ->
                Card(onClick = { onOpen(c.id) }, modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text(c.name, style = MaterialTheme.typography.titleLarge)
                        val active = c.devices.count { !it.revoked }
                        Text(if (active == 0) "No phone connected yet" else "$active phone(s) connected")
                    }
                }
            }
        }
        Button(onClick = { showAdd = true }, modifier = Modifier.fillMaxWidth()) { Text("Add child") }
    }

    if (showAdd) AlertDialog(
        onDismissRequest = { showAdd = false },
        title = { Text("Add child") },
        text = { OutlinedTextField(newName, { newName = it }, label = { Text("Child's name") }, singleLine = true) },
        confirmButton = {
            TextButton(enabled = newName.isNotBlank(), onClick = {
                scope.launch {
                    io(onLogout) { Api.addChild(token, newName.trim()) }
                        .onSuccess { newName = ""; showAdd = false; load() }.onFailure { error = friendly(it) }
                }
            }) { Text("Add") }
        },
        dismissButton = { TextButton(onClick = { showAdd = false }) { Text("Cancel") } }
    )
}
