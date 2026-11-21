package com.parentalguardian.parent.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.text.KeyboardOptions
import com.parentalguardian.parent.data.Api
import kotlinx.coroutines.launch

@Composable
fun AuthScreen(onAuthed: (String) -> Unit) {
    val scope = rememberCoroutineScope()
    var register by remember { mutableStateOf(false) }
    var email by remember { mutableStateOf("") }
    var name by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp).statusBarsPadding(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("Parental Guardian", style = MaterialTheme.typography.headlineMedium)
        Text(if (register) "Create your parent account" else "Log in to see your children")
        OutlinedTextField(
            email, { email = it.trim() }, label = { Text("Email") }, singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email), modifier = Modifier.fillMaxWidth()
        )
        if (register) OutlinedTextField(
            name, { name = it }, label = { Text("Your name") }, singleLine = true, modifier = Modifier.fillMaxWidth()
        )
        OutlinedTextField(
            password, { password = it }, label = { Text("Password") }, singleLine = true,
            visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth()
        )
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        Button(
            enabled = !busy && email.isNotBlank() && password.length >= 8 && (!register || name.isNotBlank()),
            onClick = {
                scope.launch {
                    busy = true; error = null
                    val r = io({}) { if (register) Api.register(email, name.trim(), password) else Api.login(email, password) }
                    r.onSuccess(onAuthed).onFailure { error = friendly(it) }
                    busy = false
                }
            }
        ) { Text(if (busy) "Please wait..." else if (register) "Create account" else "Log in") }
        TextButton(onClick = { register = !register; error = null }) {
            Text(if (register) "I already have an account" else "Create a new account")
        }
    }
}
