package com.example.goibible.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.unit.dp
import com.example.goibible.AppState
import com.example.goibible.data.SearchHit
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext

/**
 * Full-text verse search over the active pane's edition.
 * Tapping a result jumps the reader to that verse.
 */
@Composable
fun SearchScreen(state: AppState, onClose: () -> Unit) {
    var query by remember { mutableStateOf("") }
    var hits by remember { mutableStateOf<List<SearchHit>>(emptyList()) }
    val editionId = state.panes[state.activePane].editionId
    val editionName = state.editions.firstOrNull { it.id == editionId }?.displayName ?: editionId
    val focus = remember { FocusRequester() }

    LaunchedEffect(Unit) { focus.requestFocus() }
    LaunchedEffect(query) {
        delay(250) // debounce while typing
        hits = if (query.length < 2) emptyList()
        else withContext(Dispatchers.IO) { state.repo.search(editionId, query) }
    }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Search $editionName", style = MaterialTheme.typography.titleMedium)
            TextButton(onClick = onClose) { Text("Close") }
        }
        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            label = { Text("Search verses") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth().focusRequester(focus),
        )
        if (query.length >= 2) {
            Text(
                if (hits.size >= 100) "First 100 matches" else "${hits.size} matches",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(vertical = 8.dp),
            )
        }
        LazyColumn(Modifier.fillMaxSize()) {
            items(hits.size) { i ->
                val h = hits[i]
                Column(
                    Modifier
                        .fillMaxWidth()
                        .clickable {
                            state.goToVerse(h.conical, h.chapter, h.verse)
                            onClose()
                        }
                        .padding(vertical = 8.dp)
                ) {
                    Text(
                        "${h.bookName} ${h.chapter}:${h.verse}",
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary,
                    )
                    Text(h.text, style = MaterialTheme.typography.bodyMedium, maxLines = 3)
                }
                HorizontalDivider()
            }
        }
    }
}
