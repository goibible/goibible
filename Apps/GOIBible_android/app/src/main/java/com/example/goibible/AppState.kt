package com.example.goibible

import android.content.SharedPreferences
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.example.goibible.data.BibleRepo

class PaneState(editionId: String, conical: Int, chapter: Int) {
    var editionId by mutableStateOf(editionId)
    var conical by mutableStateOf(conical)
    var chapter by mutableStateOf(chapter)

    /** Verse to scroll to once the chapter is shown (set by search), then cleared. */
    var pendingVerse by mutableStateOf<Int?>(null)
}

/**
 * All UI state + the "movie transport" navigation logic.
 * When split & syncLocked, chapter navigation drives both panes;
 * edition (language) stays per-pane.
 */
class AppState(val repo: BibleRepo, private val prefs: SharedPreferences) {

    var split by mutableStateOf(prefs.getBoolean("split", false))
        private set
    var syncLocked by mutableStateOf(prefs.getBoolean("syncLocked", false))
        private set
    var activePane by mutableStateOf(0)
    var showSettings by mutableStateOf(false)
    var showAbout by mutableStateOf(false)
    var showSearch by mutableStateOf(false)
    var showBookmarks by mutableStateOf(false)
    var showRandomizer by mutableStateOf(false)
    var bookmarkVersion by mutableStateOf(0)
        private set
    var darkMode by mutableStateOf(prefs.getBoolean("darkMode", true))
        private set
    var fontKey by mutableStateOf(prefs.getString("fontKey", "literata")!!)
        private set
    var fontSize by mutableStateOf(prefs.getInt("fontSize", 12))
        private set
    var editions by mutableStateOf(repo.editions())
        private set

    val panes = listOf(loadPane(0), loadPane(1))

    private fun loadPane(i: Int): PaneState {
        val defaultEdition = editions.firstOrNull { it.id == "GOI_En" }?.id
            ?: editions.first().id
        return PaneState(
            prefs.getString("p${i}_edition", defaultEdition)!!,
            prefs.getInt("p${i}_conical", 1),
            prefs.getInt("p${i}_chapter", 1)
        )
    }

    fun updateDarkMode(enabled: Boolean) {
        darkMode = enabled
        save()
    }

    fun updateFont(key: String) {
        fontKey = key
        save()
    }

    fun updateFontSize(size: Int) {
        fontSize = size.coerceIn(10, 28)
        save()
    }

    private fun save() {
        prefs.edit().apply {
            putBoolean("split", split)
            putBoolean("syncLocked", syncLocked)
            putBoolean("darkMode", darkMode)
            putString("fontKey", fontKey)
            putInt("fontSize", fontSize)
            panes.forEachIndexed { i, p ->
                putString("p${i}_edition", p.editionId)
                putInt("p${i}_conical", p.conical)
                putInt("p${i}_chapter", p.chapter)
            }
        }.apply()
    }

    fun refreshEditions() {
        editions = repo.editions()
        // If a removed edition was showing, fall back to the first remaining one.
        panes.forEach { p ->
            if (editions.none { it.id == p.editionId }) p.editionId = editions.first().id
        }
        save()
    }

    fun toggleSplit() {
        split = !split
        if (!split) activePane = 0
        save()
    }

    fun toggleSyncLock() {
        syncLocked = !syncLocked
        if (syncLocked) {
            // Snap the other pane to the active pane's position on lock.
            val src = panes[activePane]
            val dst = panes[1 - activePane]
            dst.conical = src.conical
            dst.chapter = src.chapter
        }
        save()
    }

    private fun targets(): List<PaneState> =
        if (split && syncLocked) panes else listOf(panes[activePane])

    fun setEdition(editionId: String) {
        val p = panes[activePane]
        p.editionId = editionId
        // Clamp position to what exists in this edition.
        val books = repo.books(editionId)
        if (books.none { it.conical == p.conical }) {
            p.conical = books.firstOrNull()?.conical ?: 1
            p.chapter = 1
        } else {
            p.chapter = p.chapter.coerceAtMost(repo.chapterCount(editionId, p.conical).coerceAtLeast(1))
        }
        save()
    }

    /** Step to the previous/next book available in each target pane's edition. */
    fun stepBook(delta: Int) {
        targets().forEach { p ->
            val books = repo.books(p.editionId)
            val idx = books.indexOfFirst { it.conical == p.conical }
            val next = idx + delta
            if (idx >= 0 && next in books.indices) {
                p.conical = books[next].conical
                p.chapter = 1
            }
        }
        save()
    }

    fun setBook(conical: Int) {
        targets().forEach { p ->
            p.conical = conical
            p.chapter = 1
        }
        save()
    }

    /** Jump straight to a verse (from search); respects lock sync like other navigation. */
    fun goToVerse(conical: Int, chapter: Int, verse: Int) {
        targets().forEach { p ->
            p.conical = conical
            p.chapter = chapter
            p.pendingVerse = verse
        }
        save()
    }

    fun goToBookmark(editionId: String, conical: Int, chapter: Int, verse: Int) {
        val p = panes[activePane]
        p.editionId = editionId
        p.conical = conical
        p.chapter = chapter
        p.pendingVerse = verse
        save()
    }

    fun goToRandomVerse(editionId: String, conical: Int, chapter: Int, verse: Int) {
        val p = panes[activePane]
        p.editionId = editionId
        p.conical = conical
        p.chapter = chapter
        p.pendingVerse = verse
        save()
    }

    fun toggleBookmark(editionId: String, conical: Int, chapter: Int, verse: Int) {
        if (repo.isBookmarked(editionId, conical, chapter, verse)) {
            repo.removeBookmark(editionId, conical, chapter, verse)
        } else {
            repo.addBookmark(editionId, conical, chapter, verse)
        }
        bookmarkVersion++
    }

    fun removeBookmark(id: Long) {
        repo.removeBookmark(id)
        bookmarkVersion++
    }

    fun seekChapter(chapter: Int) {
        targets().forEach { p ->
            val max = repo.chapterCount(p.editionId, p.conical).coerceAtLeast(1)
            p.chapter = chapter.coerceIn(1, max)
        }
        save()
    }

    fun firstChapter() = seekChapter(1)

    fun lastChapter() {
        targets().forEach { p ->
            p.chapter = repo.chapterCount(p.editionId, p.conical).coerceAtLeast(1)
        }
        save()
    }

    /** Next chapter; past the last chapter, roll into the next book available in the pane's edition. */
    fun nextChapter() {
        targets().forEach { p ->
            val max = repo.chapterCount(p.editionId, p.conical)
            if (p.chapter < max) {
                p.chapter++
            } else {
                val books = repo.books(p.editionId)
                val idx = books.indexOfFirst { it.conical == p.conical }
                if (idx >= 0 && idx < books.size - 1) {
                    p.conical = books[idx + 1].conical
                    p.chapter = 1
                }
            }
        }
        save()
    }

    /** Previous chapter; before chapter 1, roll into the last chapter of the previous book. */
    fun prevChapter() {
        targets().forEach { p ->
            if (p.chapter > 1) {
                p.chapter--
            } else {
                val books = repo.books(p.editionId)
                val idx = books.indexOfFirst { it.conical == p.conical }
                if (idx > 0) {
                    p.conical = books[idx - 1].conical
                    p.chapter = repo.chapterCount(p.editionId, p.conical).coerceAtLeast(1)
                }
            }
        }
        save()
    }
}
