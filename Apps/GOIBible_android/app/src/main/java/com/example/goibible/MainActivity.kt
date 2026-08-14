package com.example.goibible

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Modifier
import com.example.goibible.data.BibleRepo
import com.example.goibible.ui.AboutScreen
import com.example.goibible.ui.BookmarksScreen
import com.example.goibible.ui.RandomizerDialog
import com.example.goibible.ui.ReaderPane
import com.example.goibible.ui.SearchScreen
import com.example.goibible.ui.SettingsScreen
import com.example.goibible.ui.TransportBar
import com.example.goibible.ui.theme.GOIBibleTheme
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.collectLatest

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val repo = BibleRepo(applicationContext)
        val prefs = getSharedPreferences("goibible", MODE_PRIVATE)
        setContent {
            val state = remember { AppState(repo, prefs) }
            BackHandler(enabled = state.showSettings) {
                state.showSettings = false
            }
            BackHandler(enabled = state.showAbout) {
                state.showAbout = false
            }
            BackHandler(enabled = state.showSearch) {
                state.showSearch = false
            }
            BackHandler(enabled = state.showBookmarks) {
                state.showBookmarks = false
            }
            BackHandler(enabled = state.showRandomizer) {
                state.showRandomizer = false
            }
            GOIBibleTheme(darkTheme = state.darkMode, dynamicColor = false) {
                Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    when {
                        state.showSettings -> Scaffold { inner ->
                            Column(Modifier.padding(inner)) {
                                SettingsScreen(state) { state.showSettings = false }
                            }
                        }

                        state.showAbout -> Scaffold { inner ->
                            Column(Modifier.padding(inner)) {
                                AboutScreen { state.showAbout = false }
                            }
                        }

                        state.showSearch -> Scaffold { inner ->
                            Column(Modifier.padding(inner)) {
                                SearchScreen(state) { state.showSearch = false }
                            }
                        }

                        state.showBookmarks -> Scaffold { inner ->
                            Column(Modifier.padding(inner)) {
                                BookmarksScreen(state) { state.showBookmarks = false }
                            }
                        }

                        else -> ReaderScreen(state)
                    }
                }
            }
        }
    }
}

@Composable
fun ReaderScreen(state: AppState) {
    val listStates = listOf(rememberLazyListState(), rememberLazyListState())
    val active = state.panes[state.activePane]
    val chapterCount = remember(active.editionId, active.conical, state.editions) {
        state.repo.chapterCount(active.editionId, active.conical).coerceAtLeast(1)
    }

    // Lock sync: mirror the focused pane's scroll onto the other pane, verse-index aligned.
    if (state.split && state.syncLocked) {
        val src = listStates[state.activePane]
        val dst = listStates[1 - state.activePane]
        LaunchedEffect(state.activePane, state.syncLocked, state.split) {
            // On engage (or focus switch) snap the other pane to the focused pane's
            // position, after its chapter-change scroll-to-top has settled.
            delay(150)
            dst.scrollToItem(src.firstVisibleItemIndex, src.firstVisibleItemScrollOffset)
            snapshotFlow { src.firstVisibleItemIndex to src.firstVisibleItemScrollOffset }
                .collectLatest { (index, offset) ->
                    if (src.isScrollInProgress) dst.scrollToItem(index, offset)
                }
        }
    }

    Scaffold { inner ->
        Column(Modifier.fillMaxSize().padding(inner)) {
            val paneCount = if (state.split) 2 else 1
            for (i in 0 until paneCount) {
                ReaderPane(
                    pane = state.panes[i],
                    repo = state.repo,
                    editions = state.editions,
                    listState = listStates[i],
                    isActive = state.activePane == i,
                    highlight = state.split,
                    onActivate = { state.activePane = i },
                    onEdition = { state.setEdition(it) },
                    onBook = { state.setBook(it) },
                    onChapter = { state.seekChapter(it) },
                    onPrevBook = { state.stepBook(-1) },
                    onNextBook = { state.stepBook(1) },
                    onPrevChapter = { state.prevChapter() },
                    onNextChapter = { state.nextChapter() },
                    bookmarkVersion = state.bookmarkVersion,
                    onToggleBookmark = { editionId, conical, chapter, verse ->
                        state.toggleBookmark(editionId, conical, chapter, verse)
                    },
                    fontKey = state.fontKey,
                    fontSize = state.fontSize,
                    modifier = Modifier.weight(1f),
                )
            }
            TransportBar(
                chapter = active.chapter,
                chapterCount = chapterCount,
                split = state.split,
                syncLocked = state.syncLocked,
                onSeek = { state.seekChapter(it) },
                onFirst = { state.firstChapter() },
                onPrev = { state.prevChapter() },
                onNext = { state.nextChapter() },
                onLast = { state.lastChapter() },
                onToggleSplit = { state.toggleSplit() },
                onToggleLock = { state.toggleSyncLock() },
                onSearch = { state.showSearch = true },
                onBookmarks = { state.showBookmarks = true },
                onRandomizer = { state.showRandomizer = true },
                onSettings = { state.showSettings = true },
                onAbout = { state.showAbout = true },
            )
        }
    }
    if (state.showRandomizer) {
        RandomizerDialog(
            state = state,
            onClose = { state.showRandomizer = false },
        )
    }
}
