package com.example.goibible.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.goibible.PaneState
import com.example.goibible.data.BibleRepo
import com.example.goibible.data.Edition

/**
 * One reader window: "lang | Book | Ch N" header + verse list.
 * Any touch inside makes it the active pane (highlighted border).
 */
@Composable
fun ReaderPane(
    pane: PaneState,
    repo: BibleRepo,
    editions: List<Edition>,
    listState: LazyListState,
    isActive: Boolean,
    highlight: Boolean,
    onActivate: () -> Unit,
    onEdition: (String) -> Unit,
    onBook: (Int) -> Unit,
    onChapter: (Int) -> Unit,
    onPrevBook: () -> Unit,
    onNextBook: () -> Unit,
    onPrevChapter: () -> Unit,
    onNextChapter: () -> Unit,
    bookmarkVersion: Int,
    onToggleBookmark: (String, Int, Int, Int) -> Unit,
    fontKey: String,
    fontSize: Int,
    modifier: Modifier = Modifier,
) {
    val books = remember(pane.editionId, editions) { repo.books(pane.editionId) }
    val book = books.firstOrNull { it.conical == pane.conical }
    val chapterCount = remember(pane.editionId, pane.conical, editions) {
        repo.chapterCount(pane.editionId, pane.conical)
    }
    val verses = remember(pane.editionId, pane.conical, pane.chapter, editions) {
        repo.verses(pane.editionId, pane.conical, pane.chapter)
    }
    val bookmarkedVerses = remember(pane.editionId, pane.conical, pane.chapter, bookmarkVersion) {
        repo.bookmarkedVerses(pane.editionId, pane.conical, pane.chapter)
    }
    // Unique per edition — multiple English packages must not all read "EN".
    val edition = editions.firstOrNull { it.id == pane.editionId }
    val langLabel = edition?.let { "${it.language.uppercase()} · ${it.id}" } ?: "?"

    // Plain navigation starts the chapter at the top; a search jump (pendingVerse)
    // scrolls to its verse instead (+1 for the top spacer item).
    LaunchedEffect(pane.editionId, pane.conical, pane.chapter) {
        if (pane.pendingVerse == null) listState.scrollToItem(0)
    }
    LaunchedEffect(pane.pendingVerse) {
        val target = pane.pendingVerse ?: return@LaunchedEffect
        val idx = verses.indexOfFirst { it.num == target }
        if (idx >= 0) listState.scrollToItem(idx + 1)
        pane.pendingVerse = null
    }

    Column(
        modifier = modifier
            // Activate on any touch, without stealing the event from children.
            .pointerInput(onActivate) {
                awaitEachGesture {
                    awaitFirstDown(pass = PointerEventPass.Initial)
                    onActivate()
                }
            }
            .padding(horizontal = 12.dp, vertical = 4.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            HeaderPicker(label = langLabel) { close ->
                editions.forEach { e ->
                    DropdownMenuItem(
                        text = {
                            Column {
                                Text("${e.language.uppercase()} - ${e.id}")
                                Text(
                                    e.displayName,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        },
                        onClick = { onEdition(e.id); close() })
                }
            }
            HeaderPicker(
                label = book?.longName ?: "—",
                onPrev = onPrevBook,
                onNext = onNextBook,
            ) { close ->
                books.forEach { b ->
                    DropdownMenuItem(
                        text = { Text(b.longName) },
                        onClick = { onBook(b.conical); close() })
                }
            }
            HeaderPicker(
                label = "Ch ${pane.chapter}",
                onPrev = onPrevChapter,
                onNext = onNextChapter,
            ) { close ->
                (1..chapterCount).forEach { ch ->
                    DropdownMenuItem(
                        text = { Text("Chapter $ch") },
                        onClick = { onChapter(ch); close() })
                }
            }
        }

        Surface(
            modifier = Modifier.fillMaxSize(),
            shape = RoundedCornerShape(16.dp),
            border = BorderStroke(
                if (highlight && isActive) 2.dp else 1.dp,
                if (highlight && isActive) MaterialTheme.colorScheme.primary
                else MaterialTheme.colorScheme.outlineVariant
            ),
            color = MaterialTheme.colorScheme.surface,
        ) {
            if (verses.isEmpty()) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(
                        "Not available in this edition",
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            } else {
                LazyColumn(
                    state = listState,
                    modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    item { Box(Modifier.padding(top = 4.dp)) }
                    items(verses.size, key = { verses[it].num }) { i ->
                        val v = verses[i]
                        var menuExpanded by remember { mutableStateOf(false) }
                        Row(verticalAlignment = Alignment.Top) {
                            Box {
                                Text(
                                    "${v.num}",
                                    modifier = Modifier
                                        .clickable { menuExpanded = true }
                                        .padding(end = 8.dp, top = 2.dp),
                                    fontWeight = FontWeight.Bold,
                                    fontSize = (fontSize * 0.75).sp,
                                    color = if (v.num in bookmarkedVerses) MaterialTheme.colorScheme.tertiary
                                    else MaterialTheme.colorScheme.primary,
                                )
                                DropdownMenu(
                                    expanded = menuExpanded,
                                    onDismissRequest = { menuExpanded = false },
                                ) {
                                    DropdownMenuItem(
                                        text = {
                                            Text(
                                                if (v.num in bookmarkedVerses) "Remove bookmark"
                                                else "Add bookmark"
                                            )
                                        },
                                        onClick = {
                                            onToggleBookmark(pane.editionId, pane.conical, pane.chapter, v.num)
                                            menuExpanded = false
                                        },
                                    )
                                }
                            }
                            SelectionContainer(modifier = Modifier.weight(1f)) {
                                Text(
                                    buildAnnotatedString { append(v.text) },
                                    fontFamily = readerFontFamily(fontKey),
                                    fontSize = fontSize.sp,
                                    lineHeight = (fontSize * 1.6f).sp,
                                )
                            }
                        }
                    }
                    item { Box(Modifier.padding(bottom = 8.dp)) }
                }
            }
        }
    }
}

/**
 * `< label >` control: side arrows step prev/next, tapping the label opens a picker.
 * Without onPrev/onNext it is a plain tappable chip (the language selector).
 */
@Composable
private fun HeaderPicker(
    label: String,
    onPrev: (() -> Unit)? = null,
    onNext: (() -> Unit)? = null,
    content: @Composable (close: () -> Unit) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    Row(verticalAlignment = Alignment.CenterVertically) {
        if (onPrev != null) {
            Text(
                "‹",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier
                    .clickable(onClick = onPrev)
                    .padding(horizontal = 6.dp),
            )
        }
        Box {
            Surface(
                shape = RoundedCornerShape(8.dp),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
                color = MaterialTheme.colorScheme.surface,
                modifier = Modifier.clickable { expanded = true },
            ) {
                Text(
                    label,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                    style = MaterialTheme.typography.titleSmall,
                    maxLines = 1,
                )
            }
            DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                content { expanded = false }
            }
        }
        if (onNext != null) {
            Text(
                "›",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier
                    .clickable(onClick = onNext)
                    .padding(horizontal = 6.dp),
            )
        }
    }
}
