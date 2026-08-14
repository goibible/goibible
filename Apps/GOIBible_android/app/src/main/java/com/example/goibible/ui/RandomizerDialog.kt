package com.example.goibible.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.example.goibible.AppState
import com.example.goibible.data.RandomVerse
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun RandomizerDialog(state: AppState, onClose: () -> Unit) {
    val activeEdition = state.panes[state.activePane].editionId
    var selectedEdition by remember(state.editions) {
        mutableStateOf(
            activeEdition.takeIf { id -> state.editions.any { it.id == id } }
                ?: state.editions.firstOrNull()?.id
                ?: ""
        )
    }
    var expanded by remember { mutableStateOf(false) }
    var randomVerse by remember { mutableStateOf<RandomVerse?>(null) }
    var loading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    suspend fun pickVerse() {
        if (selectedEdition.isBlank()) return
        loading = true
        randomVerse = withContext(Dispatchers.IO) {
            state.repo.randomVerse(selectedEdition)
        }
        loading = false
    }

    LaunchedEffect(selectedEdition) {
        pickVerse()
    }

    Dialog(onDismissRequest = onClose) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("Random Verse", style = MaterialTheme.typography.titleLarge)
                    TextButton(onClick = onClose) { Text("Close") }
                }

                Column {
                    OutlinedButton(
                        onClick = { expanded = true },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(
                            state.editions.firstOrNull { it.id == selectedEdition }?.displayName
                                ?: selectedEdition.ifBlank { "No editions installed" },
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                    DropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false },
                    ) {
                        state.editions.forEach { edition ->
                            DropdownMenuItem(
                                text = { Text(edition.displayName) },
                                onClick = {
                                    selectedEdition = edition.id
                                    expanded = false
                                },
                            )
                        }
                    }
                }

                val verse = randomVerse
                if (verse == null) {
                    Text(
                        if (loading) "Loading..." else "No verse available.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                } else {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(
                            "${verse.bookName} ${verse.chapter}:${verse.verse}",
                            color = MaterialTheme.colorScheme.primary,
                            fontWeight = FontWeight.Bold,
                            style = MaterialTheme.typography.titleMedium,
                        )
                        Text(
                            verse.editionName,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Text(
                            verse.text,
                            style = MaterialTheme.typography.bodyLarge,
                        )
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp, Alignment.End),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    val verse = randomVerse
                    TextButton(
                        enabled = verse != null,
                        onClick = {
                            if (verse != null) {
                                state.goToRandomVerse(
                                    verse.editionId,
                                    verse.conical,
                                    verse.chapter,
                                    verse.verse,
                                )
                                onClose()
                            }
                        },
                    ) {
                        Text("Go")
                    }
                    Button(
                        enabled = selectedEdition.isNotBlank() && !loading,
                        onClick = { scope.launch { pickVerse() } },
                    ) {
                        Text("New Verse")
                    }
                }
            }
        }
    }
}
