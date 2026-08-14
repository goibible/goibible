package com.example.goibible.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.goibible.AppState
import com.example.goibible.R
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

private const val DownloadManifestUrl =
    "https://raw.githubusercontent.com/goibible/goibible/main/goi_db_download/manifest.json"
private const val DownloadBaseUrl =
    "https://raw.githubusercontent.com/goibible/goibible/main/goi_db_download/"

private data class DownloadEdition(
    val editionId: String,
    val displayName: String,
    val bcp47Tag: String,
    val file: String,
    val verseCount: Int,
)

/**
 * Manage editions: list installed, merge a new one from a local .db file
 * or by downloading, remove ones you no longer want.
 */
@Composable
fun SettingsScreen(state: AppState, onClose: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var status by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var url by remember { mutableStateOf("") }
    var downloadChoices by remember { mutableStateOf<List<DownloadEdition>>(emptyList()) }
    var showDownloadPicker by remember { mutableStateOf(false) }

    fun mergeFile(file: File, cleanup: Boolean) {
        scope.launch {
            busy = true
            status = "Merging…"
            val result = withContext(Dispatchers.IO) {
                try {
                    state.repo.mergeFrom(file)
                } finally {
                    if (cleanup) file.delete()
                }
            }
            result.fold(
                onSuccess = { status = "Added: $it"; state.refreshEditions() },
                onFailure = { status = "Failed: ${it.message}" },
            )
            busy = false
        }
    }

    val pickFile = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri: Uri? ->
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            busy = true
            status = "Copying file…"
            val tmp = withContext(Dispatchers.IO) {
                val f = File(context.cacheDir, "import.db")
                context.contentResolver.openInputStream(uri)?.use { input ->
                    f.outputStream().use { input.copyTo(it) }
                } ?: return@withContext null
                f
            }
            busy = false
            if (tmp == null) status = "Could not read file"
            else mergeFile(tmp, cleanup = true)
        }
    }

    fun download(targetUrl: String, label: String = "download") {
        val target = targetUrl.trim()
        if (target.isEmpty()) return
        scope.launch {
            busy = true
            status = "Downloading $label…"
            val tmp = withContext(Dispatchers.IO) {
                try {
                    val f = File(context.cacheDir, "download.db")
                    val conn = URL(target).openConnection() as HttpURLConnection
                    conn.connectTimeout = 15000
                    conn.readTimeout = 30000
                    conn.inputStream.use { input ->
                        f.outputStream().use { input.copyTo(it) }
                    }
                    conn.disconnect()
                    f
                } catch (e: Exception) {
                    status = "Download failed: ${e.message}"
                    null
                }
            }
            busy = false
            if (tmp != null) mergeFile(tmp, cleanup = true)
        }
    }

    fun loadDownloadChoices() {
        scope.launch {
            busy = true
            status = "Loading downloads…"
            val result = withContext(Dispatchers.IO) {
                try {
                    val conn = URL(DownloadManifestUrl).openConnection() as HttpURLConnection
                    conn.connectTimeout = 15000
                    conn.readTimeout = 30000
                    val body = conn.inputStream.bufferedReader().use { it.readText() }
                    conn.disconnect()
                    val editions = JSONObject(body).getJSONArray("editions")
                    List(editions.length()) { index ->
                        val item = editions.getJSONObject(index)
                        DownloadEdition(
                            editionId = item.getString("edition_id"),
                            displayName = item.optString("display_name", item.getString("edition_id")),
                            bcp47Tag = item.optString("bcp47_tag", item.optString("language_subtag", "")),
                            file = item.getString("file"),
                            verseCount = item.optInt("verse_count", 0),
                        )
                    }
                } catch (e: Exception) {
                    status = "Could not load downloads: ${e.message}"
                    emptyList()
                }
            }
            downloadChoices = result
            showDownloadPicker = result.isNotEmpty()
            if (result.isNotEmpty()) status = "Choose a download."
            busy = false
        }
    }

    if (showDownloadPicker) {
        AlertDialog(
            onDismissRequest = { showDownloadPicker = false },
            title = { Text("Download .db") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    downloadChoices.forEach { edition ->
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable(enabled = !busy) {
                                    showDownloadPicker = false
                                    download(DownloadBaseUrl + edition.file, edition.displayName)
                                }
                                .padding(vertical = 6.dp),
                        ) {
                            Text(edition.displayName, style = MaterialTheme.typography.bodyLarge)
                            Text(
                                "${edition.editionId} · ${edition.bcp47Tag} · ${edition.verseCount} verses",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            },
            confirmButton = {},
            dismissButton = {
                TextButton(onClick = { showDownloadPicker = false }) { Text("Cancel") }
            },
        )
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Settings", style = MaterialTheme.typography.headlineSmall)
            TextButton(onClick = onClose) { Text("Done") }
        }

        Text("Display", style = MaterialTheme.typography.titleMedium)
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Dark mode", style = MaterialTheme.typography.bodyLarge)
            Switch(checked = state.darkMode, onCheckedChange = { state.updateDarkMode(it) })
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Font", style = MaterialTheme.typography.bodyLarge)
            FontChoices.forEach { (key, name) ->
                FilterChip(
                    selected = state.fontKey == key,
                    onClick = { state.updateFont(key) },
                    label = { Text(name, fontFamily = readerFontFamily(key)) },
                )
            }
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Size ${state.fontSize}", style = MaterialTheme.typography.bodyLarge)
            Spacer(Modifier.width(12.dp))
            Slider(
                value = state.fontSize.toFloat(),
                onValueChange = { state.updateFontSize(it.toInt()) },
                valueRange = 10f..28f,
                steps = 17,
                modifier = Modifier.weight(1f),
            )
        }
        Text(
            "In the beginning God created the heavens and the earth.",
            fontFamily = readerFontFamily(state.fontKey),
            fontSize = state.fontSize.sp,
            lineHeight = (state.fontSize * 1.6f).sp,
        )

        HorizontalDivider()

        Text("Editions", style = MaterialTheme.typography.titleMedium)

        state.editions.forEach { e ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(Modifier.weight(1f)) {
                    Text(e.displayName, style = MaterialTheme.typography.bodyLarge)
                    Text(
                        "${e.id} · ${e.language}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                IconButton(
                    onClick = {
                        scope.launch {
                            withContext(Dispatchers.IO) { state.repo.removeEdition(e.id) }
                            state.refreshEditions()
                            status = "Removed ${e.displayName}"
                        }
                    },
                    enabled = state.editions.size > 1 && !busy,
                ) {
                    Icon(painterResource(R.drawable.ic_delete), contentDescription = "Remove ${e.displayName}")
                }
            }
        }

        HorizontalDivider()

        Text("Add edition", style = MaterialTheme.typography.titleMedium)
        OutlinedButton(
            onClick = { pickFile.launch(arrayOf("*/*")) },
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Pick .db file from storage") }

        OutlinedButton(
            onClick = ::loadDownloadChoices,
            enabled = !busy,
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Download .db") }

        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(
                value = url,
                onValueChange = { url = it },
                label = { Text("Download URL (.db)") },
                singleLine = true,
                modifier = Modifier.weight(1f),
            )
            Spacer(Modifier.width(8.dp))
            Button(onClick = { download(url) }, enabled = !busy && url.isNotBlank()) { Text("Get") }
        }

        if (status.isNotEmpty()) {
            Text(
                status,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.primary,
            )
        }
    }
}
