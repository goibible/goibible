package com.example.goibible.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.goibible.AppState
import com.example.goibible.R

@Composable
fun BookmarksScreen(state: AppState, onClose: () -> Unit) {
    val pane = state.panes[state.activePane]
    val bookmarks = remember(
        pane.editionId,
        pane.conical,
        pane.chapter,
        state.bookmarkVersion,
        state.editions,
    ) {
        state.repo.bookmarksNear(pane.editionId, pane.conical, pane.chapter)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Bookmarks", style = MaterialTheme.typography.headlineSmall)
            TextButton(onClick = onClose) { Text("Done") }
        }

        if (bookmarks.isEmpty()) {
            Text(
                "No bookmarks yet.",
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                items(bookmarks, key = { it.id }) { bookmark ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                state.goToBookmark(
                                    bookmark.editionId,
                                    bookmark.conical,
                                    bookmark.chapter,
                                    bookmark.verse,
                                )
                                onClose()
                            }
                            .padding(vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text(
                                "${bookmark.bookName} ${bookmark.chapter}:${bookmark.verse}",
                                fontWeight = FontWeight.Bold,
                            )
                            Text(
                                bookmark.editionName,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                            Text(
                                bookmark.text,
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis,
                                style = MaterialTheme.typography.bodyMedium,
                            )
                        }
                        IconButton(onClick = { state.removeBookmark(bookmark.id) }) {
                            Icon(
                                painterResource(R.drawable.ic_delete),
                                contentDescription = "Remove bookmark",
                            )
                        }
                    }
                    HorizontalDivider()
                }
            }
        }
    }
}
